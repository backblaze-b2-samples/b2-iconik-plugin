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
import hashlib
import logging
import os
from datetime import datetime
from time import sleep
from urllib.parse import urlparse

import pytest
import requests

from b2_iconik_plugin.common import X_BZ_SHARED_SECRET
from b2_iconik_plugin.iconik import Iconik
from tests.test_common import ACTION_ID
from tests.test_common import APP_ID

logger = logging.getLogger(__name__)

# Number of retries while waiting for iconik
MAX_RETRIES = 8

# Integration tests require a live iconik instance with two storages configured
# B2_STORAGE_ID must be a B2 storage, but LL_STORAGE_ID can be any storage type
B2_STORAGE_ID = os.environ['B2_STORAGE_ID']
LL_STORAGE_ID = os.environ['LL_STORAGE_ID']
ICONIK_ID = os.environ['ICONIK_ID']
ICONIK_TOKEN = os.environ['ICONIK_TOKEN']
BZ_SHARED_SECRET = os.environ['BZ_SHARED_SECRET']
PLUGIN_ENDPOINT = os.environ['PLUGIN_ENDPOINT'] if 'PLUGIN_ENDPOINT' in os.environ else ''

TEST_MPEG_URL = 'https://filesamples.com/samples/video/mpeg/sample_1920x1080.mpeg'

def upload_file_to_iconik(iconik, user_id, filename):
    asset = iconik.create_asset(filename, 'ASSET')
    format_ = iconik.create_format(asset['id'], user_id, 'ORIGINAL',
                                  [{"internet_media_type": "video/mp4"}], ["B2"])
    file_set = iconik.create_file_set(asset['id'], format_['id'], B2_STORAGE_ID, filename)

    get_response = requests.get(TEST_MPEG_URL, stream=True)
    get_response.raise_for_status()

    file = iconik.create_file(asset['id'], filename, len(get_response.content), 'FILE', B2_STORAGE_ID, file_set['id'], format_['id'])

    job = iconik.create_job(
        'assets',
        asset['id'],
        'TRANSFER',
        'STARTED',
        f'Upload {filename}',
        {
            "storage_id": B2_STORAGE_ID,
            "client_name": "B2 Iconik Plugin"
        })

    post_response = requests.post(
        file['upload_url'],
        data=get_response.content,
        headers={
            'Authorization': file['upload_credentials']['authorizationToken'],
            'X-Bz-File-Name': file['upload_filename'],
            'Content-Type': get_response.headers['content-type'],
            'Content-Length': str(len(get_response.content)),
            'X-Bz-Content-Sha1': hashlib.sha1(get_response.content).hexdigest()
        }
    )
    post_response.raise_for_status()

    iconik.update_file(asset['id'], file['id'], 'CLOSED', 100)
    iconik.create_keyframe(asset['id'])
    iconik.update_job(job['id'], 'FINISHED', 100)

    return asset


def create_custom_action_payload(user_id, system_domain_id, asset_id, auth_token):
    return {
        "user_id": user_id,
        "system_domain_id": system_domain_id,
        "context": "ASSET",
        "action_id": ACTION_ID,
        "asset_ids": [
            asset_id
        ],
        "collection_ids": [],
        "saved_search_ids": [],
        "metadata_view_id": None,
        "metadata_values": None,
        "date_created": datetime.now().isoformat(),
        "auth_token": auth_token
    }


@pytest.fixture
def assert_environment_variables():
    assert B2_STORAGE_ID, "Must set B2_STORAGE_ID environment variable for integration tests"
    assert LL_STORAGE_ID, "Must set LL_STORAGE_ID environment variable for integration tests"
    assert ICONIK_ID and ICONIK_ID != APP_ID, "Must set ICONIK_APP_ID environment variable for integration tests"
    assert ICONIK_TOKEN, "Must set ICONIK_TOKEN environment variable for integration tests"
    assert BZ_SHARED_SECRET, "Must set BZ_SHARED_SECRET environment variable for integration tests"


def wait_for_operation(fn):
    delay = 1
    for i in range(MAX_RETRIES):
        if fn():
            break
        logger.debug(f'Waiting {delay} seconds...')
        sleep(delay)
        delay *= 2


def wait_for_file_set_count(iconik, asset_id, count):
    wait_for_operation(lambda : count == len(iconik.get_asset_file_sets(asset_id)))


def wait_for_asset_deletion(iconik, asset_id):
    wait_for_operation(lambda : None == iconik.get_asset(asset_id))


def get_json(response):
    # We might be using Flask test client, where json is a string, or requests, where json is a method
    return response.json() if isinstance(response, requests.Response) else response.json


class TestAddRemove:
    asset = None

    @pytest.mark.integration
    def test_add_asset(self, integration_client, assert_environment_variables):
        iconik = Iconik(ICONIK_ID, ICONIK_TOKEN)
        system_settings = iconik.get_system_settings()
        user = iconik.get_current_user()
        filename = os.path.basename(urlparse(TEST_MPEG_URL).path)

        TestAddRemove.asset = upload_file_to_iconik(iconik, user['id'], filename)

        # Check that the asset is present in the correct storage
        file_sets = iconik.get_asset_file_sets(TestAddRemove.asset['id'])
        assert 1 == len(file_sets)
        assert B2_STORAGE_ID == file_sets[0]['storage_id']
        assert filename == file_sets[0]['name']

        # Simulate an 'add' custom action call from iconik
        payload = create_custom_action_payload(user['id'], system_settings['system_domain_id'], TestAddRemove.asset['id'], ICONIK_TOKEN)
        response = integration_client.post(
            f'{PLUGIN_ENDPOINT}/add?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            json=payload,
            headers={X_BZ_SHARED_SECRET: BZ_SHARED_SECRET}
        )

        # Check that the custom action succeeded
        assert 200 == response.status_code
        assert 'OK' == get_json(response)

        # wait for iconik to do its thing
        wait_for_file_set_count(iconik, TestAddRemove.asset['id'], 2)

        # Check that the asset is in both storages
        file_sets = iconik.get_asset_file_sets(TestAddRemove.asset['id'])
        assert 2 == len(file_sets)
        assert {B2_STORAGE_ID, LL_STORAGE_ID} == {file_set['storage_id'] for file_set in file_sets}
        assert all([filename == file_set['name'] for file_set in file_sets])

    @pytest.mark.integration
    def test_remove_asset(self, integration_client, assert_environment_variables):
        # Did the add succeed?
        assert TestAddRemove.asset

        iconik = Iconik(ICONIK_ID, ICONIK_TOKEN)
        system_settings = iconik.get_system_settings()
        user = iconik.get_current_user()
        filename = os.path.basename(urlparse(TEST_MPEG_URL).path)

        # Simulate a 'remove' custom action call from iconik
        payload = create_custom_action_payload(user['id'], system_settings['system_domain_id'], TestAddRemove.asset['id'], ICONIK_TOKEN)
        response = integration_client.post(
            f'{PLUGIN_ENDPOINT}/remove?b2_storage_id={B2_STORAGE_ID}&ll_storage_id={LL_STORAGE_ID}',
            json=payload,
            headers={X_BZ_SHARED_SECRET: BZ_SHARED_SECRET}
        )

        # Check that the custom action succeeded
        assert 200 == response.status_code
        assert 'OK' == get_json(response)

        # wait for iconik to do its thing
        wait_for_file_set_count(iconik, TestAddRemove.asset['id'], 1)

        # Check that the asset is in only the B2 storage
        file_sets = iconik.get_asset_file_sets(TestAddRemove.asset['id'])
        assert 1 == len(file_sets)
        assert B2_STORAGE_ID == file_sets[0]['storage_id']
        assert filename == file_sets[0]['name']

        # Delete and purge our asset immediately
        iconik.delete_asset(TestAddRemove.asset['id'])
        iconik.purge_asset(TestAddRemove.asset['id'])

        # wait for iconik to do its thing
        wait_for_asset_deletion(iconik, TestAddRemove.asset['id'])

        # Check that it's gone
        assert None == iconik.get_asset(TestAddRemove.asset['id'])
