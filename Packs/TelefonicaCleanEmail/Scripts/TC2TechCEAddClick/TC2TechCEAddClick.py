import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEAddClick"


class Utils:
    @staticmethod
    def coerce(value, _type):
        if isinstance(value, _type):
            result = value
        elif _type in (list, dict):
            result = json.loads(value)
        else:
            raise ValueError(f"The value cannot be coerced to a {str(_type)}.")
        return result


class DT:
    __MS_IN_S = 1000
    __ROD_FORMAT = "%Y-%m-%d %H:%M:%S.%f %Z"

    def __init__(self, dt):
        self.__dt = dt

    def to_epoch(self):
        return round(self.__dt.timestamp() * self.__MS_IN_S)

    @classmethod
    def from_xsoar(cls, value):
        dt = datetime.fromisoformat(value.split(".")[0]).astimezone(timezone.utc)
        return cls(dt)

    def __str__(self):
        return self.__dt.strftime(self.__ROD_FORMAT)


def note(event):
    blocked = event.get("name", "").endswith("blocked")
    status = "BLOCKED" if blocked else "PERMITTED"
    ext = event.get("extensions")
    click_dt = DT.from_xsoar(ext.get("clickTime"))
    threat_dt = DT.from_xsoar(ext.get("threatTime"))
    recipient = ext.get("recipient")

    lines = (
        f"[{status}] Click from user {recipient}",
        "----------------------------",
        f'GUID:\t{ext.get("GUID")}',
        f'Classification:\t{ext.get("classification")}',
        f'User agent:\t{ext.get("userAgent")}',
        f"Recipient:\t{recipient}",
        "\nSender",
        f'- Email:\t{ext.get("sender")}',
        f'- IP:\t{ext.get("senderIP")}',
        "\nClick",
        f'- IP:\t{ext.get("clickIP")}',
        f"- Time:\t{str(click_dt)}",
        "\nThreat",
        f'- ID:\t{ext.get("threatID")}',
        f"- Time:\t{str(threat_dt)}",
        f'- Status:\t{ext.get("threatStatus")}',
        f'- TAP URL:\t{ext.get("threatURL")}',
        f'- URL:\t{ext.get("url")}',
    )

    data = {
        "access": "Telefonica",
        "description": "\n".join(lines),
        "doneBy": {
            "affiliation": "Telefonica",
            "email": "global_automatizacion_orquestacion@telefonica.com",
            "name": "XSOAR",
            "phone": "",
        },
        "sourceSystem": "XSOAR",
    }
    return data


def main():
    try:
        inc = demisto.incident()
        cf = inc["CustomFields"]
        message_id = cf.get("tc2techcemessageid")
        messages = (
            execute_command(
                "getIncidents",
                {
                    "query": " ".join(
                        (
                            'type:"CleanEmail Message"',
                            f"tc2techcemessageid:{message_id}",
                            "-status:2",
                        )
                    )
                },
            )["data"]
            or []
        )

        if len(messages) > 0:
            event = Utils.coerce(cf.get("tc2techmodel", "{}") or "{}", dict)

            inc = messages[0]
            cf = inc["CustomFields"]

            alert = Utils.coerce(cf.get("tc2techmodel", "{}") or "{}", dict)
            if "events" not in alert:
                alert["events"] = []
            alert["events"].append(event)

            execute_command(
                "setIncident",
                {
                    "id": inc["id"],
                    "tc2techmodel": json.dumps(alert),
                    "tc2technewnotes": json.dumps([note(event)]),
                },
            )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
