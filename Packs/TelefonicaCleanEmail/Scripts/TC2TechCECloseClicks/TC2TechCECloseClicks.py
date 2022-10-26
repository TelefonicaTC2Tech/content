import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCECloseClicks"
MAX_NUM_RELATED_INC = 10000


def main():
    try:
        inc = demisto.incident()
        cf = inc["CustomFields"]
        message_id = cf.get("tc2techcemessageid")
        clicks = execute_command(
            "getIncidents",
            {
                "query": " ".join(
                    (
                        'type:"CleanEmail Click"',
                        f"tc2techcemessageid:{message_id}",
                        "-status:2",
                    )
                ),
                "size": MAX_NUM_RELATED_INC,
            },
        )

        for clk in clicks:
            execute_command(
                "taskComplete",
                {
                    "id": "WaitForClosure",
                    "incidentId": clk["id"],
                    "comment": "Closed by associated message case.",
                    "input": "CaseClosed",
                },
            )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
