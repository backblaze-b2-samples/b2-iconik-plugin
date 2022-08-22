import flask
import os
import pytest
import re
import responses
import requests
from responses import matchers
from unittest.mock import patch, Mock
from werkzeug.exceptions import HTTPException
from test_common import *
from gcp_test import get_smsc_mock, setup_gcp_responses, GCF_PROJECT_ID
from common import X_BZ_SHARED_SECRET

from gcp import GcpLogger
from main import gcp_iconik_handler
import iconik


# Make a Flask app so we can do app.test_request_context()
@pytest.fixture(scope="module")
def app():
    return flask.Flask(__name__)


# Make a Flask app so we can do app.test_request_context()
@pytest.fixture(scope="module")
def logger():
    return GcpLogger(GCF_PROJECT_ID)


@pytest.fixture(scope="function", autouse=True)
def setup_secrets(request):
    setup_gcp_responses()
    with patch("gcp.secretmanager.SecretManagerServiceClient", new_callable=get_smsc_mock) as mock_smc:
        yield mock_smc


@responses.activate
def test_iconik_handler_add(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(gcp_iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)

        assert_copy_call_counts(LL_STORAGE_ID, format_count=0)


@responses.activate
def test_iconik_handler_remove(app, logger):
    with app.test_request_context(
            path=f'/remove?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):

        response = flask.Response(gcp_iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)

        assert_copy_call_counts(B2_STORAGE_ID, format_count=1)
        assert_delete_call_counts()


@responses.activate
def test_iconik_handler_400_invalid_content(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            data='This is not JSON!',
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
def test_iconik_handler_400_missing_content(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
def test_iconik_handler_400_invalid_context(app, logger):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=json,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
def test_iconik_handler_400_missing_context(app, logger):
    json = dict(PAYLOAD)
    del json["context"]
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=json,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 400 == httperror.value.code


@responses.activate
def test_iconik_handler_401_invalid(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: 'dummy'}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
def test_iconik_handler_401_missing(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 401 == httperror.value.code


@responses.activate
def test_iconik_handler_404(app, logger):
    with app.test_request_context(
            path=f'/invalid?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 404 == httperror.value.code


@responses.activate
def test_iconik_handler_405(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='GET', 
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 405 == httperror.value.code

@responses.activate
def test_iconik_handler_500(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={INVALID_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: SHARED_SECRET}):
        with pytest.raises(HTTPException) as httperror:
            response = gcp_iconik_handler(flask.request)
        assert 500 == httperror.value.code
