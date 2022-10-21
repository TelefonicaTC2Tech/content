import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEAssignClient"


def main(**kwargs):
    try:
        inc = demisto.incident()
        instance = inc["sourceInstance"]

        clients = kwargs["clients"]
        if isinstance(clients, str):
            clients = json.loads(clients)

        portal_ids = execute_command(
            "jmespath",
            {
                "value": clients,
                "expression": f"[?eml.proofpoint.tap.instance=='{instance}'].portal | [0]",
            },
        )

        if any(
            (portal_ids is None, isinstance(portal_ids, str) and portal_ids == "None")
        ):
            raise Exception(f"Client with instance {instance} not found.")

        execute_command(
            "setIncident",
            {
                "tc2techtenantid": portal_ids["tenant_id"],
                "tc2techsocid": portal_ids["soc_id"],
                "tc2techclientid": portal_ids["client_id"],
            },
        )

    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main(**demisto.args())
