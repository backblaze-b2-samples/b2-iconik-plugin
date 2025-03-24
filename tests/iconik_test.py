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
import requests

from b2_iconik_plugin import iconik
from tests.test_common import *


def test_iconik_app_id_none():
    with pytest.raises(ValueError) as value_error:
        iconik.Iconik(None, AUTH_TOKEN)
    assert str(value_error.value) == "You must supply both app_id and auth_token"


def test_iconik_auth_token_none():
    with pytest.raises(ValueError) as value_error:
        iconik.Iconik(os.environ["ICONIK_ID"], None)
    assert str(value_error.value) == "You must supply both app_id and auth_token"


def test_iconik_app_id_str():
    with pytest.raises(TypeError) as type_error:
        iconik.Iconik(123, AUTH_TOKEN)
    assert str(type_error.value) == "app_id must be a string"


def test_iconik_auth_token_str():
    with pytest.raises(TypeError) as type_error:
        iconik.Iconik(os.environ["ICONIK_ID"], 123)
    assert str(type_error.value) == "auth_token must be a string"


def test_iconik_session():
    client = iconik.Iconik(os.environ["ICONIK_ID"], AUTH_TOKEN)
    assert isinstance(client.session, requests.Session)
    assert client.session.headers['App-ID'] == os.environ["ICONIK_ID"]
    assert client.session.headers['Auth-Token'] == AUTH_TOKEN


@responses.activate
def test_get_objects_single_page():
    client = iconik.Iconik(os.environ["ICONIK_ID"], AUTH_TOKEN)
    objects = client.get_objects(f"{iconik.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/")
    assert 1 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]


@responses.activate
def test_get_objects_multiple_pages():
    client = iconik.Iconik(os.environ["ICONIK_ID"], AUTH_TOKEN)
    objects = client.get_objects(f"{iconik.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/")
    assert 2 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]
    assert ASSET_ID == objects[1]["id"]
