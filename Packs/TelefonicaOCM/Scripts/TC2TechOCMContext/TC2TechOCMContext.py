import enum

import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechOCMContext"


def coerce(value, _type):
    if isinstance(value, _type):
        result = value
    elif _type in (list, dict):
        result = json.loads(value)
    else:
        raise ValueError(f"The value cannot be coerced to a {str(_type)}.")
    return result


class Operation(enum.Enum):
    ATTACHMENT_ADD_PORTAL = enum.auto()
    CANCEL = enum.auto()
    CLOSE = enum.auto()
    CREATE = enum.auto()
    REACTIVATE = enum.auto()
    REOPEN = enum.auto()
    RESOLVE = enum.auto()
    SUSPEND = enum.auto()
    UPDATE = enum.auto()


class SearchClass(enum.Enum):
    SECURITY = "com.elevenpaths.sandas.input.SecurityAlert"
    SUPERVISION = "com.elevenpaths.sandas.input.SupervisionAlert"


def main(**kwargs):
    try:
        inc = demisto.incident()
        cf = inc["CustomFields"]
        ocm_model = coerce(cf.get("tc2techmodel", "{}") or "{}", dict)
        operation = Operation[kwargs["operation"]]
        search_class = SearchClass[kwargs["type"]]
        transcode = coerce(cf.get("tc2techtranscode", "{}") or "{}", dict)

        context = {
            "idIncCliente": cf.get("tc2techserviceincidentid"),
            "searchClass": search_class.value,
            "operation": operation.name,
            "lastEventSourceSystem": cf.get("tc2techsourcesystemid"),
            "securityAlerts": [],
            "supervisionAlerts": [],
            "rawEvent": json.dumps(ocm_model),
            "transcode": transcode,
        }

        if "queue" in kwargs:
            context["clientQueue"] = kwargs["queue"]

        if "tc2techcase" in cf:
            case = cf["tc2techcase"]
            if isinstance(case, str):
                case = json.loads(case)
            context["case"] = case

        if "tc2techservicedata" in cf:
            service = cf["tc2techservicedata"]
            if isinstance(service, str):
                service = json.loads(service)
            context["service"] = service

        alert_key = None
        if search_class == SearchClass.SECURITY:
            alert_key = "securityAlerts"
        elif search_class == SearchClass.SUPERVISION:
            alert_key = "supervisionAlerts"
        context[alert_key].append(ocm_model)

        return_results(
            CommandResults(
                outputs_prefix="TC2Tech.OCM.Context",
                outputs_key_field="idIncCliente",
                outputs=context,
            )
        )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main(**demisto.args())
