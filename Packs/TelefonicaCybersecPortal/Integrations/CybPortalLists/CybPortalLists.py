import enum
import json
import traceback
from typing import Dict

import jwt
import requests
import requests.auth
import urllib3

import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

MODULE_NAME = "CybPortalLists"
# Disable insecure warnings
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)  # pylint: disable=no-member


def snake_to_camel(value):
    words = value.split("_")
    for index, word in enumerate(words):
        if index > 0:
            words[index] = word.capitalize()
        else:
            words[index] = word.lower()

    return "".join(words)


class Method(enum.Enum):
    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    DELETE = enum.auto()


class Module(enum.Enum):
    LISTS = enum.auto()
    ROWS = enum.auto()
    VERSIONS = enum.auto()
    TAGS = enum.auto()
    CATALOGS = enum.auto()


class Action(enum.Enum):
    GET = enum.auto()
    CREATE = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()


class JwtAuth(requests.auth.AuthBase):
    __ALGORITHM = "HS512"
    __VALIDITY_PERIOD = timedelta(hours=1)

    def __init__(self, api_url, credentials):
        self.__authorize_url = f"{api_url}/oauth2/token"
        self.__app_id = credentials.get("identifier")
        self.__api_key = credentials.get("password")

    def generate_token(self):
        expiration = datetime.now() + self.__VALIDITY_PERIOD
        payload = {
            "aud": self.__authorize_url,
            "exp": str(round(expiration.timestamp())),
            "iss": self.__app_id,
            "prn": self.__app_id,
            "sub": self.__app_id,
        }
        data = {
            "client_assertion": jwt.encode(
                payload, self.__api_key, algorithm=self.__ALGORITHM
            ),
            "grant_type": "client_credentials",
            "client_assertion_type": ":".join(
                (
                    "urn",
                    "ietf",
                    "params",
                    "oauth",
                    "client-assertion-type",
                    "jwt-bearer",
                )
            ),
        }
        response = requests.post(self.__authorize_url, data=data)
        return response.json().get("access_token", None)

    def __call__(self, req: requests.PreparedRequest) -> requests.PreparedRequest:
        if "Authorization" not in req.headers:
            token = self.generate_token()
            if token is not None:
                req.headers["Authorization"] = f"Bearer {token}"
        return req


class Client(BaseClient):  # type: ignore
    __DEFAULT_RESULT_LIMIT = 1000
    __DEFAULT_OFFSET = 0
    __url_params = {
        Module.LISTS: [
            {"prefix": "tenants", "key": "tenantId"},
            {"prefix": "socs", "key": "socId"},
            {"prefix": "clients", "key": "clientId"},
            {"prefix": "lists", "key": "listId"},
            {"prefix": "listsexternal", "key": "externalId"},
            {"prefix": "services", "key": "serviceId"},
        ],
        Module.ROWS: [
            {"prefix": "tenants", "key": "tenantId"},
            {"prefix": "socs", "key": "socId"},
            {"prefix": "clients", "key": "clientId"},
            {"prefix": "lists", "key": "externalId"},
            {"prefix": "rows", "key": "rowId"},
        ],
        Module.VERSIONS: [
            {"prefix": "tenants", "key": "tenantId"},
            {"prefix": "socs", "key": "socId"},
            {"prefix": "clients", "key": "clientId"},
            {"prefix": "lists", "key": "externalId"},
        ],
        Module.TAGS: [
            {"prefix": "tenants", "key": "tenantId"},
            {"prefix": "socs", "key": "socId"},
            {"prefix": "clients", "key": "clientId"},
            {"prefix": "tags", "key": "tagId"},
        ],
        Module.CATALOGS: [
            {"prefix": "tenants", "key": "tenantId"},
            {"prefix": "socs", "key": "socId"},
            {"prefix": "clients", "key": "clientId"},
            {"prefix": "catalogs", "key": "externalId"},
        ],
    }

    def __init__(self, base_url, credentials, verify=True):
        api_url = urljoin(base_url, "/api")
        headers: Dict = {
            "Accept": "application/vnd.elevenpaths.sandas.v1+json",
            "Content-Type": "application/vnd.elevenpaths.sandas.v1+json",
        }
        super().__init__(
            urljoin(api_url, "/lists"),
            verify=verify,
            headers=headers,
            auth=JwtAuth(api_url, credentials),
        )

    def __method(self, module: Module, action: Action, **kwargs) -> Method:
        method = Method.POST
        if all(
            (
                action == Action.GET,
                module in (Module.LISTS, Module.ROWS, Module.TAGS),
                "filter" not in kwargs,
            )
        ):
            method = Method.GET
        elif all((action == Action.UPDATE, module != Module.TAGS)):
            method = Method.PUT
        elif action == Action.DELETE:
            method = Method.DELETE

        return method

    def __endpoint(self, module: Module, action: Action, **kwargs) -> str:
        parts = []
        for param in self.__url_params[module]:
            name = param["key"]
            if name in kwargs:
                parts.extend([param["prefix"], str(kwargs[name])])

        if module == Module.LISTS:
            if action == Action.GET:
                if "filter" in kwargs:
                    parts.extend(["lists", "search"])
                elif not any(("listId" in kwargs, "externalId" in kwargs)):
                    generic = kwargs.get("generic", False) or False
                    parts.append("clientlists" if generic else "lists")
            elif action == Action.CREATE:
                parts.append("lists")
        elif module == Module.ROWS:
            if action == Action.GET and "filter" in kwargs:
                parts.extend(["rows", "search"])
            elif any(
                (
                    action == Action.CREATE,
                    action == Action.DELETE and "rowId" not in kwargs,
                )
            ):
                parts.append("rows")
        elif module == Module.VERSIONS and action == Action.GET:
            parts.append("versions")
        elif module == Module.TAGS:
            parts.append("search" if "filter" in kwargs else "tags")
        elif module == Module.CATALOGS and action == Action.GET:
            parts.extend(["rows", "search"])

        return "/".join(parts)

    def __body(self, module: Module, action: Action, **kwargs) -> Dict:
        if action == Action.GET:
            body = {
                "filter": kwargs.get("filter", {}) or {},
                "fields": kwargs.get("fields", []) or [],
                "limit": kwargs.get("limit", self.__DEFAULT_RESULT_LIMIT)
                or self.__DEFAULT_RESULT_LIMIT,
                "offset": kwargs.get("offset", self.__DEFAULT_OFFSET)
                or self.__DEFAULT_OFFSET,
                "sort": kwargs.get("sort", []) or [],
            }
        else:
            body = kwargs.get("data", {}) or {}

        return body

    def test(self):
        return self._auth.generate_token() is not None

    def request(self, module: Module, action: Action, **kwargs):
        method = self.__method(module, action, **kwargs)
        req_kwargs: Dict = {
            "url_suffix": f"/{self.__endpoint(module, action, **kwargs)}",
            "raise_on_status": True,
        }
        if method in (Method.POST, Method.PUT):
            req_kwargs["json_data"] = self.__body(module, action, **kwargs)
        return self._http_request(method.name, **req_kwargs)


class Integration:
    def __init__(self, client) -> None:
        self.__client = client

    def test(self):
        if self.__client.test():
            return_results("ok")
        else:
            raise Exception("Authorization error: make sure API creds are correct.")

    def run(self, command, **kwargs):
        parts = command.split("-")
        module = Module[parts[-2].upper()]
        action = Action[parts[-1].upper()]

        kwargs = {snake_to_camel(key): value for key, value in kwargs.items()}
        for key in ("tenantId", "socId", "clientId"):
            if key in kwargs:
                kwargs[key] = int(kwargs[key])

        if action == Action.GET:
            if "generic" in kwargs:
                kwargs["generic"] = kwargs["generic"].lower() == "true"
            for key in ("limit", "offset"):
                if key in kwargs:
                    kwargs[key] = int(kwargs[key])
            for key in ("filter", "fields", "sort"):
                if key in kwargs:
                    kwargs[key] = json.loads(kwargs[key])
        elif action in (Action.CREATE, Action.UPDATE):
            kwargs["data"] = json.loads(kwargs[key])

        results = self.__client.request(module, action, **kwargs)

        if isinstance(results, dict):
            results = CommandResults(
                outputs_prefix=f"Telefonica.Portal.{module.name.capitalize()}",
                outputs=results,
            )

        return results


def main(**kwargs) -> None:
    base_url = kwargs.get("url", "").rstrip("/")
    credentials = kwargs.get("credentials", {}) or {}
    verify_certificate = not kwargs.get("insecure", False)
    client = Client(base_url, credentials, verify=verify_certificate)
    integration = Integration(client)
    command = demisto.command()
    kwargs = demisto.args()
    LOG(f"Command being called is {command}")  # type: ignore
    try:
        if command == "test-module":
            integration.test()
        elif command == "tc2tech-portal-lists-get":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-lists-create":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-lists-update":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-lists-delete":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-rows-get":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-rows-create":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-rows-update":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-rows-delete":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-versions-get":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-tags-get":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-tags-update":
            return_results(integration.run(command, **kwargs))
        elif command == "tc2tech-portal-catalogs-get":
            return_results(integration.run(command, **kwargs))
    except Exception:
        return_error(  # type: ignore
            "\n".join(
                (
                    MODULE_NAME,
                    f"Failed to execute {command} command.",
                    "Error:",
                    traceback.format_exc(),
                )
            )
        )


if __name__ in ("__main__", "__builtin__", "builtins"):
    main(**demisto.params())
