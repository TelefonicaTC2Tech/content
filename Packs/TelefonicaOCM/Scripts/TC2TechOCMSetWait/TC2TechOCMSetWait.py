import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechOCMSetWait"


def main(**kwargs):
    try:
        execute_command("setIncident", {"tc2techwait": argToBoolean(kwargs["wait"])})
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main(**demisto.args())
