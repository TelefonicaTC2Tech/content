import json
import pathlib

import pytest

import demistomock as demisto
from TC2TechCEModelETL import main

TEST_DATA_DIR = pathlib.Path(__file__).resolve().parent / "test_data"


def incidents():
    with open(TEST_DATA_DIR / "events.json", "r", encoding="utf-8") as fp:
        incs = json.load(fp)
    return incs


def execute_command(incident):
    def run(command, kwargs):
        result = None
        if command == "setIncident":
            for key, value in kwargs.items():
                if key in incident:
                    incident[key] = value
                else:
                    incident["CustomFields"][key] = value
        return result

    return run


@pytest.mark.parametrize("incident", incidents())
def test_model_etl(mocker, incident):
    mocker.patch.object(demisto, "incident", return_value=incident)
    mocker.patch(
        "TC2TechCEModelETL.execute_command", side_effect=execute_command(incident)
    )
    main()
    assert len(incident["CustomFields"]["tc2techmodel"]) > 0
