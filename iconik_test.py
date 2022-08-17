import iconik
import pytest
import requests
import responses

from test_constants import *

def test_iconik_app_id_none():
    with pytest.raises(ValueError) as value_error:
        client = iconik.Iconik(None, AUTH_TOKEN)
    assert str(value_error.value) == "You must supply both app_id and auth_token"


def test_iconik_app_id_none():
    with pytest.raises(ValueError) as value_error:
        client = iconik.Iconik(APP_ID, None)
    assert str(value_error.value) == "You must supply both app_id and auth_token"


def test_iconik_app_id_str():
    with pytest.raises(TypeError) as type_error:
        client = iconik.Iconik(123, AUTH_TOKEN)
    assert str(type_error.value) == "app_id must be a string"


def test_iconik_app_id_str():
    with pytest.raises(TypeError) as type_error:
        client = iconik.Iconik(APP_ID, 123)
    assert str(type_error.value) == "auth_token must be a string"


def test_iconik_session():
    client = iconik.Iconik(APP_ID, AUTH_TOKEN)
    assert isinstance(client.session, requests.Session)
    assert client.session.headers['App-ID'] == APP_ID
    assert client.session.headers['Auth-Token'] == AUTH_TOKEN


@responses.activate
def test_get_objects_single_page():
    client = iconik.Iconik(APP_ID, AUTH_TOKEN)
    objects = client.get_objects(f"{iconik.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/")
    assert 1 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]


@responses.activate
def test_get_objects_multiple_pages():
    client = iconik.Iconik(APP_ID, AUTH_TOKEN)
    objects = client.get_objects(f"{iconik.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/")
    assert 2 == len(objects)
    assert SUBCOLLECTION_ID == objects[0]["id"]
    assert ASSET_ID == objects[1]["id"]
