import enum

import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEAWSSQSPreprocess"


class Operation(enum.Enum):
    CREATE = enum.auto()
    UPDATE = enum.auto()
    ASSIGN = enum.auto()
    CANCEL = enum.auto()
    CLOSE = enum.auto()
    REOPEN = enum.auto()
    SUSPEND = enum.auto()
    ADDNOTE = enum.auto()
    ERROR = enum.auto()
    NOOP = enum.auto()


class CaseStatus(enum.Enum):
    OPEN = enum.auto()
    INPROGRESS = enum.auto()
    SUSPENDED = enum.auto()
    RESOLVED = enum.auto()
    CANCELLED = enum.auto()
    CLOSED = enum.auto()


class QueueMessage:
    def __init__(self, incident):
        cf = incident["CustomFields"]
        self.__siid = cf.get("tc2techserviceincidentid") or None
        self.__related_incidents = None
        self.__case_id = cf.get("tc2techcaseid") or None
        self.__case_status = CaseStatus[cf.get("tc2techcasestatus", "").strip()]

        self.__raw = cf.get("tc2techraw", {}) or {}
        if isinstance(self.__raw, str):
            self.__raw = json.loads(self.__raw)

        op = cf.get("tc2techoperation", "").strip()
        if "," in op:
            self.__ops = {Operation[token] for token in op.split(",")}
        else:
            self.__ops = {Operation[op]}

    @property
    def case_status(self):
        return self.__case_status

    @property
    def operations(self):
        return self.__ops

    @property
    def related_incidents(self):
        if self.__related_incidents is None:
            self.__related_incidents = (
                execute_command(
                    "getIncidents",
                    {
                        "query": " ".join(
                            (
                                f"tc2techserviceincidentid:{str(self.__siid)}",
                                'type:"CleanEmail Message"',
                            )
                        )
                    },
                ).get("data", [])
                or []
            )
        return self.__related_incidents

    def mark_incidents(self):
        for inc in self.related_incidents:
            properties = {"id": inc["id"], "tc2techcaseid": self.__case_id}
            cf = inc["CustomFields"]
            if "tc2techservicedata" in cf:
                service = json.loads(cf["tc2techservicedata"])
                service["caseId"] = self.__case_id
                properties["tc2techservicedata"] = json.dumps(service)
            execute_command("setIncident", properties)
            execute_command(
                "taskComplete",
                {
                    "id": "WaitForClicks",
                    "incidentId": inc["id"],
                    "comment": "",
                    "input": "Update",
                },
            )

    def close_incidents(self):
        for inc in self.related_incidents:
            execute_command(
                "taskComplete",
                {
                    "id": "WaitForClicks",
                    "incidentId": inc["id"],
                    "comment": "",
                    "input": "Close",
                },
            )


def main():
    try:
        message = QueueMessage(demisto.incident())

        if all(
            (
                message.case_status == CaseStatus.OPEN,
                not message.operations.isdisjoint({Operation.CREATE, Operation.NOOP}),
            )
        ):
            message.mark_incidents()

        elif any(
            (
                not message.operations.isdisjoint({Operation.CLOSE, Operation.CANCEL}),
                all(
                    (
                        Operation.NOOP in message.operations,
                        message.case_status
                        in {CaseStatus.CLOSED, CaseStatus.CANCELLED},
                    )
                ),
            )
        ):
            message.close_incidents()

        return_results(True)

    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


""" ENTRY POINT """


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
