import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCECaseClosed"


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
                            "status:2",
                        )
                    )
                },
            )["data"]
            or []
        )

        return_results(
            CommandResults(
                outputs_prefix="TC2Tech.OCM.caseClosed", outputs=len(messages) > 0
            )
        )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
