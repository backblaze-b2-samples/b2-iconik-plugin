import flask
import google_crc32c
import os
import pytest
import re
import responses
from responses import matchers
from unittest.mock import patch
from werkzeug.exceptions import HTTPException

import main

AUTH_TOKEN = "SECRET_SQUIRREL"
SHARED_SECRET = 'top_secret'
GCF_PROJECT_ID = '123456789'
INVALID_STORAGE_NAME = 'INVALID'

# Random UUIDs for objects
JOB_ID = 'eff79bf8-c782-11ec-8e9b-b66ad3c6ae38'
ASSET_ID = '0d56db81-1b8e-4a68-9658-98ad9a94d841'
STORAGE_ID = 'fb7c234c-a96c-4fc9-babb-0235b2deb1d3'
FORMAT_ID = '0fcfe5f1-eb85-4529-9bd0-3e856b358c81'
FILE_SET_ID = '0436578d-8418-48b0-89ad-9c719b65137f'
COLLECTION_ID = '8ae20508-88b0-414e-8b4c-3fa2683e79e0'
SUBCOLLECTION_ID = 'bf049e70-6749-4e44-a85b-7457236cdf4e'
MULTI_COLLECTION_ID = '7e6abeea-4bff-4153-912d-2880617046ce'

PAYLOAD = {
    "user_id": "256ebe90-c0c8-11ec-9fcd-0648baddf8b3",
    "system_domain_id": "57016980-6e13-11e8-ab5a-0a580a3c0f5c",
    "context": "BULK",
    "action_id": "86f485b2-c71e-11ec-93c4-32f3401f5ebb",
    "asset_ids": [
        ASSET_ID
    ],
    "collection_ids": [
        SUBCOLLECTION_ID
    ],
    "saved_search_ids": [],
    "metadata_view_id": None,
    "metadata_values": None,
    "date_created": "2022-04-29T00:22:10.316685",
    "auth_token": AUTH_TOKEN
}

# Mocking Google Cloud Secret Manager
secret_data = SHARED_SECRET.encode('utf-8')
crc32c = google_crc32c.Checksum()
crc32c.update(secret_data)
secret_crc = int(crc32c.hexdigest(), 16)

MOCK_SMC = {
    "return_value.access_secret_version.return_value.payload.data": secret_data,
    "return_value.access_secret_version.return_value.payload.data_crc32c": secret_crc
}


# Make a Flask app so we can do app.test_request_context()
@pytest.fixture(scope="module")
def app():
    return flask.Flask(__name__)


# Set up all the Google Cloud and iconik API responses we'll need
@pytest.fixture(scope="function", autouse=True)
def setup_responses():
    main.BZ_SHARED_SECRET = '12345678-1234-5678-90ab-1234567890ab'

    # Google Cloud project id
    responses.add(
        method=responses.GET,
        url=main.GCP_PROJECT_ID_URL,
        body=GCF_PROJECT_ID,
        status=200
    )

    # iconik APIs

    # Get storage by name
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_FILES_API}/storages/',
        json={"objects": [{"id": STORAGE_ID}]},
        match=[matchers.query_param_matcher({"name": os.environ["STORAGE_NAME"]})],
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f"{main.ICONIK_FILES_API}/storages/",
        json={"objects": []},
        match=[matchers.query_param_matcher({"name": INVALID_STORAGE_NAME})],
        status=200
    )

    # Get collection by id
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}',
        json={"storage_id": None},
        status=200
    )

    # Get collection contents by id
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/',
        json={"objects": [{"id": SUBCOLLECTION_ID, "type": "COLLECTION"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{SUBCOLLECTION_ID}/contents/',
        json={"objects": [{"id": ASSET_ID, "type": "ASSET"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": SUBCOLLECTION_ID, "type": "COLLECTION"}],
            "next_url": f"/API/assets/v1/collections/{MULTI_COLLECTION_ID}/contents/?page=2&per_page=1"
        },
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": ASSET_ID, "type": "ASSET"}]
        },
        match=[matchers.query_param_matcher({"page": 2, "per_page": 1})],
        status=200
    )

    # Queue file copy
    responses.add(
        method = responses.POST, 
        url=f'{main.ICONIK_FILES_API}/storages/{STORAGE_ID}/bulk/', 
        json={
          'job_id': JOB_ID,
          'success': f'Queued copying of file sets to storage {os.environ["STORAGE_NAME"]}'
        }, 
        status=200
    )

    # Get format
    responses.add(
        method = responses.GET,
        url=f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{os.environ["FORMAT_NAME"]}/', 
        json={"id": FORMAT_ID}, 
        status=200
    )

    # Get file sets
    responses.add(
        method = responses.GET,
        url=f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{FORMAT_ID}/storages/{STORAGE_ID}/file_sets/', 
        json={"objects": [{"id": FILE_SET_ID}]}, 
        status=200
    )

    # Delete file set
    responses.add(
        method = responses.DELETE,
        url=f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/', 
        status=200
    )

    # Purge file set
    responses.add(
        method = responses.DELETE,
        url=f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/purge/', 
        status=200
    )


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_get_secret(_):
    assert SHARED_SECRET == main.get_secret(GCF_PROJECT_ID, 'secret_name')


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_get_secret_badcrc(mock_smc):
    mock_smc.return_value.access_secret_version.return_value.payload.data_crc32c \
        = 'BAD_CRC'

    with pytest.raises(main.SecretError):
        main.get_secret(GCF_PROJECT_ID, 'secret_name')


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_get_objects_single_page(mock_smc):
    objects = main.get_objects(main.session, 
        f"{main.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/")
    assert 1 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_get_objects_multiple_pages(mock_smc):
    objects = main.get_objects(main.session, 
        f"{main.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/")
    assert 2 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]
    assert ASSET_ID == objects[1]["id"]


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_add(_, app):
    with app.test_request_context(
            path='/add',
            method='POST',
            json=PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(main.iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)

        # There should be two calls to bulk copy - one for the assert and one
        # for the collection
        assert responses.assert_call_count(
            f'{main.ICONIK_FILES_API}/storages/{STORAGE_ID}/bulk/', 
            2
        )


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_remove(_, app):
    with app.test_request_context(
            path='/remove',
            method='POST',
            json=PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(main.iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)

        # The asset should be deleted and purged twice - once directly
        # and once via the subcollection
        assert responses.assert_call_count(
            f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/', 
            2
        )
        assert responses.assert_call_count(
            f'{main.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{FILE_SET_ID}/purge/', 
            2
        )


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_400_invalid_content(_, app):
    with app.test_request_context(
            path='/add', 
            method='POST',
            data='This is not JSON!',
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_400_missing_content(_, app):
    with app.test_request_context(
            path='/add', 
            method='POST',
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_400_invalid_context(_, app):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    with app.test_request_context(
            path='/add', 
            method='POST',
            json=json,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_400_missing_context(_, app):
    json = dict(PAYLOAD)
    del json["context"]
    with app.test_request_context(
            path='/add', 
            method='POST',
            json=json,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_401_invalid(_, app):
    with app.test_request_context(
            path='/add', 
            method='POST',
            json=PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: 'dummy'}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_401_missing(_, app):
    with app.test_request_context(
            path='/add', 
            method='POST',
            json=PAYLOAD):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_404(_, app):
    with app.test_request_context(
            path='/invalid', 
            method='POST',
            json=PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 404 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_405(_, app):
    with app.test_request_context(
            path='/add', 
            method='GET', 
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 405 == httperror.value.code

@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient", **MOCK_SMC)
def test_iconik_handler_500(_, app):
    os.environ["STORAGE_NAME"] = INVALID_STORAGE_NAME
    with app.test_request_context(
            path='/add',
            method='POST',
            json=PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 500 == httperror.value.code
