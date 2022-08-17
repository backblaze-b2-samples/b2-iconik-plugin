import os
import pytest
import responses
from unittest.mock import patch
from test_constants import *
from common import X_BZ_SHARED_SECRET

from app import create_app
import iconik


@pytest.fixture(scope="function", autouse=True)
def setup_secrets(request):
    os.environ["BZ_SHARED_SECRET"] = SHARED_SECRET
    os.environ["ICONIK_TOKEN"] = AUTH_TOKEN


# Make a Flask client so we can do POST requests
@pytest.fixture(scope="module")
def client():
    with create_app().test_client() as client:
        yield client


@responses.activate
def test_iconik_handler_add(client):
    response = client.post('/add', 
        json=PAYLOAD,
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})

    assert 200 == response.status_code
    assert 'OK' == response.json

    # There should be two calls to bulk copy - one for the assert and one
    # for the collection
    assert responses.assert_call_count(
        f'{iconik.ICONIK_FILES_API}/storages/{LL_STORAGE_ID}/bulk/',
        2
    )


@responses.activate
def test_iconik_handler_remove(client):
    response = client.post('/remove',
        json=PAYLOAD,
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})

    assert 200 == response.status_code
    assert 'OK' == response.json

    # The asset should be deleted and purged twice - once directly
    # and once via the subcollection
    assert responses.assert_call_count(
        f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/', 
        2
    )
    assert responses.assert_call_count(
        f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/purge/', 
        2
    )


@responses.activate
def test_iconik_handler_400_invalid_content(client):
    response = client.post('/add', 
        data='This is not JSON!',
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_content(client):
    response = client.post('/add', 
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_invalid_context(client):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    response = client.post('/add', 
        json=json,
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_context(client):
    json = dict(PAYLOAD)
    del json["context"]
    response = client.post('/add', 
        json=json,
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_401_invalid(client):
    response = client.post('/add', 
        json=PAYLOAD,
        headers={X_BZ_SHARED_SECRET: 'dummy'})
    assert 401 == response.status_code


@responses.activate
def test_iconik_handler_401_missing(client):
    response = client.post('/add', 
        json=PAYLOAD)
    assert 401 == response.status_code


@responses.activate
def test_iconik_handler_404(client):
    response = client.post('/invalid', 
        json=PAYLOAD,
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 404 == response.status_code


@responses.activate
def test_iconik_handler_405(client):
    response = client.get('/add', 
        headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 405 == response.status_code


@responses.activate
def test_iconik_handler_500(client):
    with patch.dict(os.environ, {"LL_STORAGE_ID": INVALID_STORAGE_ID}):
        response = client.post('/add',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
        assert 500 == response.status_code
