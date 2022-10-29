import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEAddClick"


def coerce(value, _type):
    if isinstance(value, _type):
        result = value
    elif _type in (list, dict):
        result = json.loads(value)
    else:
        raise ValueError(f"The value cannot be coerced to a {str(_type)}.")
    return result


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
            event = coerce(cf.get("tc2techmodel", "{}") or "{}", dict)

            inc = messages[0]
            cf = inc["CustomFields"]
            alert = coerce(cf.get("tc2techmodel", "{}") or "{}", dict)
            if "events" not in alert:
                alert["events"] = []
            alert["events"].append(event)

            execute_command("setIncident", {"tc2techmodel": json.dumps(alert)})
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
