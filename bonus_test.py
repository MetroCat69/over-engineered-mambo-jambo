import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bonus import RemotePredicateResource
from predicate import Predicate
from types import SimpleNamespace


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"PREDICATE_SERVICE_URL": "http://test"}):
        yield


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client


@pytest.mark.asyncio
async def test_from_env_success(mock_env, mock_httpx_client):
    instance = await RemotePredicateResource.from_env()
    assert isinstance(instance, RemotePredicateResource)


@pytest.mark.asyncio
async def test_from_env_missing():
    if "PREDICATE_SERVICE_URL" in os.environ:
        del os.environ["PREDICATE_SERVICE_URL"]

    with pytest.raises(ValueError):
        await RemotePredicateResource.from_env()


@pytest.mark.asyncio
async def test_predicate_updates_on_200(mock_env, mock_httpx_client):
    json_str = '{"feature": ".x.y", "operation": {"operator": "eqTo", "operand": 5}}'

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json_str
    mock_response.headers = {"etag": "xyz"}

    client_instance = AsyncMock()
    client_instance.get.return_value = mock_response
    mock_httpx_client.return_value = client_instance

    resource = await RemotePredicateResource.from_env()
    await resource._fetch_predicate()

    assert isinstance(resource.predicate, Predicate)
    assert resource._etag == "xyz"

    root = SimpleNamespace(x=SimpleNamespace(y=5))
    assert resource.predicate.evaluate(root)

    await resource.close()


@pytest.mark.asyncio
async def test_predicate_not_modified_304(mock_env, mock_httpx_client):
    predicate_json = (
        '{"feature": ".x.y", "operation": {"operator": "eqTo", "operand": 10}}'
    )
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.text = predicate_json
    mock_response_200.headers = {"etag": "etag123"}

    mock_response_304 = MagicMock()
    mock_response_304.status_code = 304
    mock_response_304.headers = {"etag": "etag123"}

    client_instance = AsyncMock()
    client_instance.get.side_effect = [mock_response_200, mock_response_304]
    mock_httpx_client.return_value = client_instance

    resource = await RemotePredicateResource.from_env()
    await resource._fetch_predicate()
    assert resource._etag == "etag123"
    assert isinstance(resource.predicate, Predicate)

    # Second call shouldn't change anything
    await resource._fetch_predicate()
    assert resource._etag == "etag123"
    assert isinstance(resource.predicate, Predicate)

    await resource.close()


@pytest.mark.asyncio
async def test_predicate_property_before_load(mock_env, mock_httpx_client):
    client_instance = AsyncMock()
    client_instance.get.return_value = MagicMock(status_code=304)
    mock_httpx_client.return_value = client_instance

    resource = await RemotePredicateResource.from_env()

    with pytest.raises(ValueError, match="Predicate not loaded yet"):
        _ = resource.predicate

    await resource.close()
