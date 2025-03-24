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

import pytest

from b2_iconik_plugin.common import X_BZ_SHARED_SECRET
from tests.test_common import *


@pytest.fixture(scope="function", autouse=True)
def setup_secrets(request):
    """
    Set environment variables for unit tests if they have not already been set for integration tests
    """
    if "ICONIK_ID" not in os.environ:
        os.environ["ICONIK_ID"] = APP_ID
    if "FORMAT_NAMES" not in os.environ:
        os.environ["FORMAT_NAMES"] = ",".join(FORMATS.keys())
    if "BZ_SHARED_SECRET" not in os.environ:
        os.environ["BZ_SHARED_SECRET"] = SHARED_SECRET
    if "ICONIK_TOKEN" not in os.environ:
        os.environ["ICONIK_TOKEN"] = AUTH_TOKEN


@responses.activate
def test_iconik_handler_add(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})

    assert 200 == response.status_code
    assert 'OK' == response.json

    assert_copy_call_counts(LL_STORAGE_ID, format_count=2)


@responses.activate
def test_iconik_handler_remove(client):
    response = client.post(f'/remove?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})

    assert 200 == response.status_code
    assert 'OK' == response.json

    assert_copy_call_counts(B2_STORAGE_ID, format_count=1)
    assert_delete_call_counts()


@responses.activate
def test_iconik_handler_400_invalid_content(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           data='This is not JSON!',
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_content(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_invalid_context(client):
    json = dict(PAYLOAD)
    json["context"] = "INVALID"
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=json,
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 400 == response.status_code


@responses.activate
def test_iconik_handler_400_missing_context(client):
    json = dict(PAYLOAD)
    del json["context"]
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                           json=json,
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
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
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 404 == response.status_code


@responses.activate
def test_iconik_handler_405(client):
    response = client.get('/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
                          headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 405 == response.status_code


@responses.activate
def test_iconik_handler_500(client):
    response = client.post(f'/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={INVALID_STORAGE_ID}',
                           json=PAYLOAD,
                           headers={X_BZ_SHARED_SECRET: os.environ["BZ_SHARED_SECRET"]})
    assert 500 == response.status_code
