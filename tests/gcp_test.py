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
import re
from unittest.mock import patch, Mock

import google_crc32c
import pytest

from b2_iconik_plugin.gcp import GCP_PROJECT_ID_URL, get_secret, SecretError
from tests.test_common import *

GCF_PROJECT_ID = 'abcd1234'
GCP_SECRET_PATH = r'^projects/[a-z][a-zA-Z0-9-]+/secrets/([a-zA-Z0-9-_]+)/versions/'
BAD_CRC = 999999999


# Mocking Google Cloud Secret Manager
def mock_access_secret_version(request):
    secret_name = re.search(GCP_SECRET_PATH, request['name']).group(1)
    if secret_name in SECRETS:
        secret_data = SECRETS[secret_name].encode('utf-8')
        crc32c = google_crc32c.Checksum()
        crc32c.update(secret_data)
        secret_crc = int(crc32c.hexdigest(), 16)
        attrs = {
            "payload.data": secret_data,
            "payload.data_crc32c": secret_crc
        }
        return Mock(**attrs)
    else:
        # Maybe raise something?
        return None


def get_smsc_mock():
    mock = Mock()
    mock.return_value.access_secret_version = Mock(side_effect=mock_access_secret_version)
    return mock


@pytest.fixture(scope="function", autouse=True)
def mock_smc():
    with patch("b2_iconik_plugin.gcp.secretmanager.SecretManagerServiceClient", new_callable=get_smsc_mock) as mock_smc:
        yield mock_smc


def setup_gcp_responses():
    # Google Cloud project id
    responses.add(
        method=responses.GET,
        url=GCP_PROJECT_ID_URL,
        body=GCF_PROJECT_ID,
        status=200
    )


# Set up the Google Cloud response we'll need
@pytest.fixture(scope="module")
def setup_responses():
    setup_gcp_responses()


@responses.activate
def test_get_secret():
    assert os.environ["BZ_SHARED_SECRET"] == get_secret(GCF_PROJECT_ID, SHARED_SECRET_NAME)


@responses.activate
def test_get_secret_bad_crc(mock_smc):
    attrs = {
        "payload.data": SECRETS[SHARED_SECRET_NAME].encode('utf-8'),
        "payload.data_crc32c": BAD_CRC
    }
    mock_smc.return_value.access_secret_version = Mock(side_effect=lambda request: Mock(**attrs))

    with pytest.raises(SecretError):
        get_secret(GCF_PROJECT_ID, SHARED_SECRET_NAME)
