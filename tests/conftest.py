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
from responses import matchers

from b2_iconik_plugin.gcp import GCP_PROJECT_ID_URL
from b2_iconik_plugin.iconik import ICONIK_ASSETS_API, ICONIK_JOBS_API
from b2_iconik_plugin.plugin import create_app
from tests.test_common import *


def pytest_configure(config):  # noqa
    responses.add(
        method=responses.GET,
        url=GCP_PROJECT_ID_URL,
        body=GCP_PROJECT_ID,
        match=[
            matchers.header_matcher({"Metadata-Flavor": "Google"}),
        ],
        status=200
    )

    config.addinivalue_line("markers", "integration: mark an integration test")


def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False, help="run integration tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        # --integration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    yield app


# Make a Flask client so we can do POST requests
@pytest.fixture
def client(app):
    return app.test_client()


# Set up all the iconik API responses we'll need
@pytest.fixture(scope="function", autouse=True)
def setup_iconik_responses():
    app_id = os.environ["ICONIK_ID"]

    # Get storage by id
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_FILES_API}/storages/{LL_STORAGE_ID}/',
        json={"id": LL_STORAGE_ID},
        match=[
            matchers.header_matcher({"App-ID": app_id}),
            matchers.header_matcher({"Auth-Token": AUTH_TOKEN})
        ],
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_FILES_API}/storages/{B2_STORAGE_ID}/',
        json={"id": B2_STORAGE_ID},
        match=[
            matchers.header_matcher({"App-ID": app_id}),
            matchers.header_matcher({"Auth-Token": AUTH_TOKEN})
        ],
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f"{ICONIK_FILES_API}/storages/{INVALID_STORAGE_ID}/",
        status=404
    )

    # Get collection by id
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/',
        json={"target_storage_id": None},
        status=200
    )

    # Get collection contents by id
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/',
        json={"objects": [{"id": SUBCOLLECTION_ID, "object_type": "collections"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_ASSETS_API}/collections/{SUBCOLLECTION_ID}/contents/',
        json={"objects": [{"id": ASSET_ID, "object_type": "assets"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": SUBCOLLECTION_ID, "object_type": "collections"}],
            "next_url": f"/API/assets/v1/collections/{MULTI_COLLECTION_ID}/contents/?page=2&per_page=1"
        },
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": ASSET_ID, "object_type": "assets"}]
        },
        match=[matchers.query_param_matcher({"page": 2, "per_page": 1})],
        status=200
    )

    # Queue file copy
    responses.add(
        method=responses.POST,
        url=f'{ICONIK_FILES_API}/storages/{LL_STORAGE_ID}/bulk/',
        json={
          'job_id': JOB_ID,
          'success': f'Queued copying of file sets to storage {LL_STORAGE_ID}'
        },
        status=200
    )
    responses.add(
        method=responses.POST,
        url=f'{ICONIK_FILES_API}/storages/{B2_STORAGE_ID}/bulk/',
        json={
            'job_id': JOB_ID,
            'success': f'Queued copying of file sets to storage {B2_STORAGE_ID}'
        },
        status=200
    )

    # Get formats
    for format_name, format_id in FORMATS.items():
        responses.add(
            method=responses.GET,
            url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{format_name}/',
            json={"id": format_id},
            status=200
        )

    # Get file sets
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{ORIGINAL_FORMAT_ID}/storages/{LL_STORAGE_ID}/file_sets/',
        json={"objects": [{"id": ORIGINAL_FILE_SET_ID}]},
        status=200
    )

    responses.add(
        method=responses.GET,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{PPRO_PROXY_FORMAT_ID}/storages/{LL_STORAGE_ID}/file_sets/',
        json={"objects": [{"id": PPRO_PROXY_FILE_SET_ID}]},
        status=200
    )

    # Delete file sets
    responses.add(
        method=responses.DELETE,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{ORIGINAL_FILE_SET_ID}/',
        status=200
    )

    responses.add(
        method=responses.DELETE,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{PPRO_PROXY_FILE_SET_ID}/',
        status=200
    )

    # Purge file sets
    responses.add(
        method=responses.DELETE,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{ORIGINAL_FILE_SET_ID}/purge/',
        status=200
    )

    responses.add(
        method=responses.DELETE,
        url=f'{ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{PPRO_PROXY_FILE_SET_ID}/purge/',
        status=200
    )

    # Get job by id
    responses.add(
        method=responses.GET,
        url=f'{ICONIK_JOBS_API}/jobs/{JOB_ID}/',
        json={
            "action_context": None,
            "children_progress": {},
            "created_by": "256ebe90-c0c8-11ec-9fcd-0648baddf8b3",
            "custom_type": None,
            "date_created": "2022-08-16T16:29:23.432000+00:00",
            "date_modified": "2022-08-16T16:29:28.821000+00:00",
            "error_message": None,
            "has_children": False,
            "id": JOB_ID,
            "job_context": None,
            "message": None,
            "metadata": {
                "storage": "9de01b48-cbf5-11ec-8723-561c9d77798a",
                "storage_id": "9de01b48-cbf5-11ec-8723-561c9d77798a"
            },
            "object_id": "2a91b690-1918-11ed-adef-8a11e7db04db",
            "object_type": "assets",
            "parent_id": None,
            "priority": 5,
            "progress": 100,
            "progress_processed": 1,
            "progress_total": 1,
            "related_objects": [],
            "status": "FINISHED",
            "steps": [],
            "title": "I did great things",
            "type": "DELETE"
        },
        status=200
    )
