import json

import pytest


def test_lists_get(integration):
    kwargs = {"tenant_id": 1, "external_id": "trascoding"}
    result = integration.run("tc2tech-portal-lists-get", **kwargs)
    assert result.outputs.get("id") == 20109


@pytest.mark.skip
def test_lists_create(integration):
    kwargs = {}
    integration.run("tc2tech-portal-lists-create", **kwargs)


@pytest.mark.skip
def test_lists_update(integration):
    kwargs = {}
    integration.run("tc2tech-portal-lists-update", **kwargs)


@pytest.mark.skip
def test_lists_delete(integration):
    kwargs = {}
    integration.run("tc2tech-portal-lists-delete", **kwargs)


def test_rows_get(integration):
    search_filter = {
        "and": [
            {"eq": {"attribute": "tenantID", "value": "1"}},
            {"eq": {"attribute": "socID", "value": "1"}},
            {"eq": {"attribute": "clientID", "value": "1003"}},
        ]
    }
    kwargs = {
        "tenant_id": 1,
        "external_id": "trascoding",
        "filter": json.dumps(search_filter),
    }
    result = integration.run("tc2tech-portal-rows-get", **kwargs)
    assert result.outputs.get("items")[0]["taxId"] == "A28294726"


@pytest.mark.skip
def test_rows_create(integration):
    kwargs = {}
    integration.run("tc2tech-portal-rows-create", **kwargs)


@pytest.mark.skip
def test_rows_update(integration):
    kwargs = {}
    integration.run("tc2tech-portal-rows-update", **kwargs)


@pytest.mark.skip
def test_rows_delete(integration):
    kwargs = {}
    integration.run("tc2tech-portal-rows-delete", **kwargs)


@pytest.mark.skip
def test_versions_get(integration):
    kwargs = {}
    integration.run("tc2tech-portal-versions-get", **kwargs)


@pytest.mark.skip
def test_tags_get(integration):
    kwargs = {}
    integration.run("tc2tech-portal-tags-get", **kwargs)


@pytest.mark.skip
def test_tags_update(integration):
    kwargs = {}
    integration.run("tc2tech-portal-tags-update", **kwargs)


@pytest.mark.skip
def test_catalogs_get(integration):
    kwargs = {}
    integration.run("tc2tech-portal-catalogs-get", **kwargs)
