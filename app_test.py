import os
import pytest
from test_common import *
from common import X_BZ_SHARED_SECRET

from plugin import create_app


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
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})

    assert 200 == response.status_code
    assert 'OK' == response.json

    assert_copy_call_counts(LL_STORAGE_ID, format_count=2)


@responses.activate
def test_iconik_handler_remove(client):
    response = client.post(f'/remove?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})

    assert 200 == response.status_code
    assert 'OK' == response.json

    assert_copy_call_counts(B2_STORAGE_ID, format_count=1)
    assert_delete_call_counts()


@responses.activate
def test_iconik_handler_400_invalid_content(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           data='This is not JSON!',
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_content(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_invalid_context(client):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=json,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_context(client):
    json = dict(PAYLOAD)
    del json["context"]
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=json,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_401_invalid(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: 'dummy'})
    assert 401 == response.status_code


@responses.activate
def test_iconik_handler_401_missing(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD)
    assert 401 == response.status_code


@responses.activate
def test_iconik_handler_404(client):
    response = client.post(f'/invalid?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 404 == response.status_code


@responses.activate
def test_iconik_handler_405(client):
    response = client.get('/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                          headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 405 == response.status_code


@responses.activate
def test_iconik_handler_500(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={INVALID_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: SHARED_SECRET})
    assert 500 == response.status_code
