import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEWakeUpClicks"


def main():
    try:
        inc = demisto.incident()
        cf = inc["CustomFields"]
        message_id = cf.get("tc2techcemessageid")
        clicks = (
            execute_command(
                "getIncidents",
                {
                    "query": " ".join(
                        (
                            'type:"CleanEmail Click"',
                            f"tc2techcemessageid:{message_id}",
                            "tc2techceblocked:false",
                            "-status:2",
                        )
                    )
                },
            )["data"]
            or []
        )

        for clk in clicks:
            execute_command(
                "taskComplete",
                {
                    "id": "WaitForMessage",
                    "incidentId": clk["id"],
                    "comment": "Waken up by incident associated to related message.",
                    "input": "ReadyForUpdate",
                },
            )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
