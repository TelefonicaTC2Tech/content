import json
import pathlib

import pytest

import demistomock as demisto
from TC2TechCEAssignClient import main

TEST_DATA_DIR = pathlib.Path(__file__).resolve().parent / "test_data"


def incidents():
    with open(TEST_DATA_DIR / "events.json", "r", encoding="utf-8") as fp:
        incs = json.load(fp)
    return incs


@pytest.fixture
def clients():
    with open(TEST_DATA_DIR / "clients.json", "r", encoding="utf-8") as fp:
        clts = json.load(fp)
    return clts


@pytest.fixture
def wrong_clients():
    with open(TEST_DATA_DIR / "wrong_clients.json", "r", encoding="utf-8") as fp:
        clts = json.load(fp)
    return clts


def execute_command(command, kwargs):
    result = None
    if command == "jmespath":
        result = {"tenant_id": 1, "soc_id": 1, "client_id": 7203}
    elif command == "setIncident":
        pass
    return result


@pytest.mark.parametrize("incident", incidents())
def test_assign_client(mocker, incident, clients):
    mocker.patch.object(demisto, "args", return_value={"clients": clients})
    mocker.patch.object(demisto, "incident", return_value=incident)
    exec_cmd_mock = mocker.patch(
        "TC2TechCEAssignClient.execute_command", side_effect=execute_command
    )
    instance = incident["sourceInstance"]
    query = f"[?eml.proofpoint.tap.instance=='{instance}'].portal | [0]"
    main(**demisto.args())
    exec_cmd_mock.assert_has_calls(
        [
            mocker.call("jmespath", {"value": clients, "expression": query}),
            mocker.call("setIncident", {"customFields": incident["CustomFields"]}),
        ]
    )
