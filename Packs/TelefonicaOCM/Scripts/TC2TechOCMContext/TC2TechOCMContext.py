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


class Context:
    class SearchClass(enum.Enum):
        SECURITY = "com.elevenpaths.sandas.input.SecurityAlert"
        SUPERVISION = "com.elevenpaths.sandas.input.SupervisionAlert"

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

    def __init__(self, **kwargs):
        self.__incident_id = kwargs["id"]
        self.__type = self.SearchClass[kwargs["type"]]
        self.__op = self.Operation[kwargs["operation"]]
        self.__src_system_id = kwargs["src_system_id"]
        self.__raw = kwargs["raw"]
        self.__transcode = kwargs["transcode"]
        self.__queue = kwargs["queue"]
        self.__service = kwargs["service"]
        self.__new_notes = kwargs["new_notes"]

    def to_dict(self):
        data = {
            "idIncCliente": self.__incident_id,
            "searchClass": self.__type.value,
            "operation": self.__op.name,
            "lastEventSourceSystem": self.__src_system_id,
            "securityAlerts": [],
            "supervisionAlerts": [],
            "rawEvent": json.dumps(self.__raw),
            "transcode": self.__transcode,
        }

        if self.__queue is not None:
            data["clientQueue"] = self.__queue

        if len(self.__service) > 0:
            data["service"] = self.__service

        if all((self.__op == self.Operation.UPDATE, len(self.__new_notes) > 0)):
            data["newNotes"] = self.__new_notes

        alert_key = None
        if self.__type == self.SearchClass.SECURITY:
            alert_key = "securityAlerts"
        elif self.__type == self.SearchClass.SUPERVISION:
            alert_key = "supervisionAlerts"
        data[alert_key].append(self.__raw)

        return data


def main(**kwargs):
    try:
        inc = demisto.incident()
        cf = inc["CustomFields"]
        params = {
            "id": cf.get("tc2techserviceincidentid"),
            "type": kwargs["type"],
            "operation": kwargs["operation"],
            "src_system_id": cf.get("tc2techsourcesystemid"),
            "raw": coerce(cf.get("tc2techmodel", {}) or {}, dict),
            "transcode": coerce(cf.get("tc2techtranscode", {}) or {}, dict),
            "queue": kwargs.get("queue"),
            "service": coerce(cf.get("tc2techservicedata", {}) or {}, dict),
            "new_notes": coerce(cf.get("tc2technewnotes", []) or [], list),
        }
        execute_command("setIncident", {"tc2technewnotes": "[]"})

        context = Context(**params)

        return_results(
            CommandResults(
                outputs_prefix="TC2Tech.OCM.Context",
                outputs_key_field="idIncCliente",
                outputs=context.to_dict(),
            )
        )
    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main(**demisto.args())
