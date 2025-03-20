# MIT License
#
# Copyright (c) 2025 Backblaze
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
from unittest.mock import patch

import flask
import pytest
from werkzeug.exceptions import HTTPException

from b2_iconik_plugin.common import X_BZ_SHARED_SECRET
from b2_iconik_plugin.gcp import GcpLogger
from b2_iconik_plugin.main import gcp_iconik_handler
from tests.gcp_test import get_smsc_mock, setup_gcp_responses, GCF_PROJECT_ID
from tests.test_common import *


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
    with patch("b2_iconik_plugin.gcp.secretmanager.SecretManagerServiceClient", new_callable=get_smsc_mock) as mock_smc:
        yield mock_smc


@responses.activate
def test_iconik_handler_add(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):

        response = flask.Response(gcp_iconik_handler(flask.request))

        assert 200 == response.status_code
        assert 'OK' == response.get_data(as_text=True)

        assert_copy_call_counts(LL_STORAGE_ID, format_count=2)


@responses.activate
def test_iconik_handler_remove(app, logger):
    with app.test_request_context(
            path=f'/remove?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):

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
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 400 == http_error.value.code


@responses.activate
def test_iconik_handler_400_missing_content(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 400 == http_error.value.code


@responses.activate
def test_iconik_handler_400_invalid_context(app, logger):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=json,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 400 == http_error.value.code


@responses.activate
def test_iconik_handler_400_missing_context(app, logger):
    json = dict(PAYLOAD)
    del json["context"]
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=json,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 400 == http_error.value.code


@responses.activate
def test_iconik_handler_401_invalid(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: 'dummy'}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 401 == http_error.value.code


@responses.activate
def test_iconik_handler_401_missing(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 401 == http_error.value.code


@responses.activate
def test_iconik_handler_404(app, logger):
    with app.test_request_context(
            path=f'/invalid?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 404 == http_error.value.code


@responses.activate
def test_iconik_handler_405(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            method='GET',
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 405 == http_error.value.code

@responses.activate
def test_iconik_handler_500(app, logger):
    with app.test_request_context(
            path=f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={INVALID_STORAGE_ID}',
            method='POST',
            json=PAYLOAD,
            headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]}):
        with pytest.raises(HTTPException) as http_error:
            gcp_iconik_handler(flask.request)
        assert 500 == http_error.value.code
