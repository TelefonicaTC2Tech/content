import enum

import demistomock as demisto
from CommonServerPython import *

MODULE_NAME = "TC2TechCEModelETL"


class Utils:
    __MS_IN_S = 1000

    @staticmethod
    def identity(value):
        return value

    @classmethod
    def iso_to_millis(cls, value):
        dt = datetime.fromisoformat(value.split(".")[0]).astimezone(timezone.utc)
        return round(dt.timestamp() * cls.__MS_IN_S)


#########################
# Case Management Model #
#########################
class Level(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


def extensions(ce_event):
    raw = ce_event.raw
    data = {}
    if ce_event.type == EventType.MESSAGE:
        data |= {
            key: raw.get(key)
            for key in (
                "ccAddresses",
                "clusterId",
                "completelyRewritten",
                "fromAddress",
                "GUID",
                "headerFrom",
                "headerReplyTo",
                "impostorScore",
                "malwareScore",
                "messageID",
                "messageSize",
                "messageTime",
                "modulesRun",
                "phishScore",
                "policyRoutes",
                "QID",
                "quarantineFolder",
                "quarantineRule",
                "recipient",
                "replyToAddress",
                "sender",
                "senderIP",
                "spamScore",
                "subject",
                "toAddresses",
                "xmailer",
            )
        }
    elif ce_event.type == EventType.CLICK:
        data |= {
            key: raw.get(key)
            for key in (
                "campaignId",
                "classification",
                "clickIP",
                "clickTime",
                "GUID",
                "id",
                "recipient",
                "sender",
                "senderIP",
                "threatID",
                "threatTime",
                "threatURL",
                "threatStatus",
                "url",
                "userAgent",
            )
        }

    for key, value in data.items():
        if isinstance(value, list):
            data[key] = ", ".join([str(entry) for entry in value])

    return {key: value for key, value in data.items() if value is not None}


def security(ce_event):
    data = {
        "product": "Targeted Attack Protection",
        "vendor": "Proofpoint",
    }

    if ce_event.type == EventType.MESSAGE:
        data |= {"sensor": ce_event.raw.get("cluster")}
    elif ce_event.type == EventType.CLICK:
        data |= {"user": ce_event.raw.get("recipient")}

    return {key: value for key, value in data.items() if value is not None}


def event(ce_event):
    raw = ce_event.raw
    click_id = raw.get("id")
    level = ce_event.level.name.capitalize()
    if ce_event.blocked:
        name = "Click blocked"
    else:
        name = "Click permitted"

    data = {
        "eventId": click_id,
        "extensions": extensions(ce_event),
        "impact": level,
        "name": name,
        "sourceEventId": click_id,
        "timestamp": Utils.iso_to_millis(raw.get("clickTime")),
    }
    return {key: value for key, value in data.items() if not value}


def alert(ce_event):
    raw = ce_event.raw
    message_id = raw.get("GUID")
    level = ce_event.level.name.capitalize()
    timestamp = Utils.iso_to_millis(raw.get("messageTime"))
    if ce_event.blocked:
        name = "Message blocked"
    else:
        name = "Message delivered"

    data = {
        "alertId": ce_event.service_incident_id,
        "detectedAt": timestamp,
        "updatedAt": timestamp,
        "extensions": extensions(ce_event),
        "impact": level,
        "name": name,
        "serviceId": "9",
        "severity": level,
        "signature": "CE:MESSAGE",
        "sourceAlertId": message_id,
        "sourceId": message_id,
        "tenantId": ce_event.tenant_id,
        "socId": ce_event.soc_id,
        "clientId": ce_event.client_id,
    }
    return {key: value for key, value in data.items() if value is not None}


##################
# Proofpoint TAP #
##################
class EventType(enum.Enum):
    CLICK = enum.auto()
    MESSAGE = enum.auto()


class Event:
    def __init__(self, incident):
        cf = incident.get("CustomFields", {}) or {}
        self.__tenant_id = cf.get("tc2techtenantid")
        self.__soc_id = cf.get("tc2techsocid")
        self.__client_id = cf.get("tc2techclientid")
        self.__service_incident_id = cf.get("tc2techserviceincidentid")
        self.__source_system_id = cf.get("tc2techsourcesystemid")
        self.__raw = json.loads(cf.get("tc2techraw", "{}") or "{}")
        self.__message_id = self.__raw.get("GUID")
        event_type = self.__raw.get("type", "") or ""
        tokens = event_type.strip().split()
        self.__type = EventType[tokens[0].rstrip("s").upper()]
        self.__blocked = tokens[1] == "blocked"
        if self.__type == EventType.MESSAGE:
            self.__level = Level.MEDIUM if self.__blocked else Level.HIGH
        elif self.__type == EventType.CLICK:
            self.__level = Level.HIGH if self.blocked else Level.CRITICAL
        self.__model = None

    def __load_model(self):
        func = Utils.identity
        if self.__type == EventType.CLICK:
            func = event
        elif self.__type == EventType.MESSAGE:
            func = alert
        self.__model = func(self)

    @property
    def tenant_id(self):
        return self.__tenant_id

    @property
    def soc_id(self):
        return self.__soc_id

    @property
    def client_id(self):
        return self.__client_id

    @property
    def service_incident_id(self):
        return self.__service_incident_id

    @property
    def source_system_id(self):
        return self.__source_system_id

    @property
    def message_id(self):
        return self.__message_id

    @property
    def blocked(self):
        return self.__blocked

    @property
    def type(self):
        return self.__type

    @property
    def level(self):
        return self.__level

    @property
    def raw(self):
        return self.__raw

    @property
    def model(self):
        if self.__model is None:
            self.__load_model()
        return self.__model


def main():
    try:
        inc = demisto.incident()
        event = Event(inc)
        execute_command(
            "setIncident",
            {
                "tc2techmodel": json.dumps(event.model),
                "tc2techcemessageid": event.message_id,
                "tc2techceblocked": event.blocked,
            },
        )

    except Exception:
        return_error("\n".join((MODULE_NAME, "Error:", traceback.format_exc())))


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
