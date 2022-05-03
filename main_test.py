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

SHARED_SECRET = 'top_secret'
GCF_PROJECT_ID = '123456789'

# Random UUIDs for objects
JOB_ID = 'eff79bf8-c782-11ec-8e9b-b66ad3c6ae38'
ASSET_ID = '0d56db81-1b8e-4a68-9658-98ad9a94d841'
STORAGE_ID = 'fb7c234c-a96c-4fc9-babb-0235b2deb1d3'
FORMAT_ID = '0fcfe5f1-eb85-4529-9bd0-3e856b358c81'
FILE_SET_ID = '0436578d-8418-48b0-89ad-9c719b65137f'
COLLECTION_ID = '8ae20508-88b0-414e-8b4c-3fa2683e79e0'
STORAGE_COLLECTION_ID = '411496a5-0437-4215-a463-591329f8ff51'

WEBHOOK_PAYLOAD = {
    'system_domain_id': '57016980-6e13-11e8-ab5a-0a580a3c0f5c',
    'event_type': 'collections',
    'object_id': '7f1ad7f0-c715-11ec-972a-32f3401f5ebb',
    'user_id': '256ebe90-c0c8-11ec-9fcd-0648baddf8b3',
    'realm': 'contents',
    'operation': 'create',
    'data': {
        'collection_id': COLLECTION_ID,
        'date_created': '2022-04-28T17:07:59.469292+00:00',
        'object_id': ASSET_ID,
        'object_type': 'assets'
    },
    'request_id': 'eaf4c20c4095f007a059b77c640dbbf9'
}

WEBHOOK_STORAGE_PAYLOAD = {
    'system_domain_id': '57016980-6e13-11e8-ab5a-0a580a3c0f5c',
    'event_type': 'collections',
    'object_id': '7f1ad7f0-c715-11ec-972a-32f3401f5ebb',
    'user_id': '256ebe90-c0c8-11ec-9fcd-0648baddf8b3',
    'realm': 'contents',
    'operation': 'create',
    'data': {
        'collection_id': STORAGE_COLLECTION_ID,
        'date_created': '2022-04-28T17:07:59.469292+00:00',
        'object_id': ASSET_ID,
        'object_type': 'assets'
    },
    'request_id': 'eaf4c20c4095f007a059b77c640dbbf9'
}

ACTION_PAYLOAD = {
    "user_id": "256ebe90-c0c8-11ec-9fcd-0648baddf8b3",
    "system_domain_id": "57016980-6e13-11e8-ab5a-0a580a3c0f5c",
    "context": "ASSET",
    "action_id": "86f485b2-c71e-11ec-93c4-32f3401f5ebb",
    "asset_ids": [
        ASSET_ID
    ],
    "collection_ids": [],
    "saved_search_ids": [],
    "metadata_view_id": None,
    "metadata_values": None,
    "date_created": "2022-04-29T00:22:10.316685",
    "auth_token": "SECRET_SQUIRREL"
}


@pytest.fixture(scope="module")
def app():
    main.BZ_SHARED_SECRET = '12345678-1234-5678-90ab-1234567890ab'
    return flask.Flask(__name__)


def setup_mocks(mock_smc, responses):
    # Google Cloud Secret Manager
    secret_data = SHARED_SECRET.encode('utf-8')
    crc32c = google_crc32c.Checksum()
    crc32c.update(secret_data)
    mock_smc.return_value.access_secret_version.return_value.payload.data \
        = secret_data
    mock_smc.return_value.access_secret_version.return_value.payload.data_crc32c \
        = int(crc32c.hexdigest(), 16)

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
        match=[matchers.query_param_matcher({'name': os.environ['STORAGE_NAME']})],
        status=200
    )

    # Get collection by id
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}',
        json={"storage_id": None},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{main.ICONIK_ASSETS_API}/collections/{STORAGE_COLLECTION_ID}',
        json={"storage_id": STORAGE_ID},
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
@patch("main.secretmanager.SecretManagerServiceClient")
def test_get_secret(mock_smc):
    setup_mocks(mock_smc, responses)

    assert SHARED_SECRET == main.get_secret(GCF_PROJECT_ID, 'secret_name')


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_get_secret_badcrc(mock_smc):
    setup_mocks(mock_smc, responses)

    mock_smc.return_value.access_secret_version.return_value.payload.data_crc32c \
        = 'BAD_CRC'

    with pytest.raises(main.SecretError):
        main.get_secret(GCF_PROJECT_ID, 'secret_name')


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_webhook(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/webhook',
            method='POST',
            json=WEBHOOK_PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(main.iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_webhook_storage(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/webhook',
            method='POST',
            json=WEBHOOK_STORAGE_PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(main.iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'Skipping notification from mapped collection' \
            == response.get_data(as_text=True)


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_action(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/action',
            method='POST',
            json=ACTION_PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(main.iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_400_invalid(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/dummy', 
            method='POST',
            data='This is not JSON!',
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_400_missing(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/dummy', 
            method='POST',
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_401_invalid(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/dummy', 
            method='POST',
            json=WEBHOOK_PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: 'dummy'}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_401_missing(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/dummy', 
            method='POST',
            json=WEBHOOK_PAYLOAD):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_404(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/dummy', 
            method='POST',
            json=WEBHOOK_PAYLOAD,
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 404 == httperror.value.code


@responses.activate
@patch("main.secretmanager.SecretManagerServiceClient")
def test_iconik_handler_405(mock_smc, app):
    setup_mocks(mock_smc, responses)

    with app.test_request_context(
            path='/webhook', 
            method='GET', 
            headers={main.X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = main.iconik_handler(flask.request)
        assert 405 == httperror.value.code
