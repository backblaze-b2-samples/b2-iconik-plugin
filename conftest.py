import iconik
import os
import pytest
import responses

from test_common import *
from responses import matchers


def pytest_generate_tests(metafunc):
    os.environ["ICONIK_ID"] = APP_ID
    os.environ["FORMAT_NAMES"] = ",".join(FORMATS.keys())


# Set up all the iconik API responses we'll need
@pytest.fixture(scope="function", autouse=True)
def setup_iconik_responses():
    # Get storage by id
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_FILES_API}/storages/{LL_STORAGE_ID}/',
        json={"id": LL_STORAGE_ID},
        match=[
            matchers.header_matcher({"App-ID": APP_ID}),
            matchers.header_matcher({"Auth-Token": AUTH_TOKEN})
        ],
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_FILES_API}/storages/{B2_STORAGE_ID}/',
        json={"id": B2_STORAGE_ID},
        match=[
            matchers.header_matcher({"App-ID": APP_ID}),
            matchers.header_matcher({"Auth-Token": AUTH_TOKEN})
        ],
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f"{iconik.ICONIK_FILES_API}/storages/{INVALID_STORAGE_ID}/",
        status=404
    )

    # Get collection by id
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/',
        json={"target_storage_id": None},
        status=200
    )

    # Get collection contents by id
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_ASSETS_API}/collections/{COLLECTION_ID}/contents/',
        json={"objects": [{"id": SUBCOLLECTION_ID, "type": "COLLECTION"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_ASSETS_API}/collections/{SUBCOLLECTION_ID}/contents/',
        json={"objects": [{"id": ASSET_ID, "type": "ASSET"}]},
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": SUBCOLLECTION_ID, "type": "COLLECTION"}],
            "next_url": f"/API/assets/v1/collections/{MULTI_COLLECTION_ID}/contents/?page=2&per_page=1"
        },
        status=200
    )
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_ASSETS_API}/collections/{MULTI_COLLECTION_ID}/contents/',
        json={
            "objects": [{"id": ASSET_ID, "type": "ASSET"}]
        },
        match=[matchers.query_param_matcher({"page": 2, "per_page": 1})],
        status=200
    )

    # Queue file copy
    responses.add(
        method=responses.POST, 
        url=f'{iconik.ICONIK_FILES_API}/storages/{LL_STORAGE_ID}/bulk/',
        json={
          'job_id': JOB_ID,
          'success': f'Queued copying of file sets to storage {LL_STORAGE_ID}'
        }, 
        status=200
    )
    responses.add(
        method=responses.POST,
        url=f'{iconik.ICONIK_FILES_API}/storages/{B2_STORAGE_ID}/bulk/',
        json={
            'job_id': JOB_ID,
            'success': f'Queued copying of file sets to storage {B2_STORAGE_ID}'
        },
        status=200
    )

    # Get formats
    for format_name, format_id in FORMATS.items():
        print("$$$", format_name, format_id)
        responses.add(
            method=responses.GET,
            url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{format_name}/',
            json={"id": format_id},
            status=200
        )

    # Get file sets
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{ORIGINAL_FORMAT_ID}/storages/{LL_STORAGE_ID}/file_sets/',
        json={"objects": [{"id": ORIGINAL_FILE_SET_ID}]},
        status=200
    )

    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/formats/{PPRO_PROXY_FORMAT_ID}/storages/{LL_STORAGE_ID}/file_sets/',
        json={"objects": [{"id": PPRO_PROXY_FILE_SET_ID}]},
        status=200
    )

    # Delete file sets
    responses.add(
        method=responses.DELETE,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{ORIGINAL_FILE_SET_ID}/',
        status=200
    )

    responses.add(
        method=responses.DELETE,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{PPRO_PROXY_FILE_SET_ID}/',
        status=200
    )

    # Purge file sets
    responses.add(
        method=responses.DELETE,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{ORIGINAL_FILE_SET_ID}/purge/',
        status=200
    )

    responses.add(
        method=responses.DELETE,
        url=f'{iconik.ICONIK_FILES_API}/assets/{ASSET_ID}/file_sets/{PPRO_PROXY_FILE_SET_ID}/purge/',
        status=200
    )

    # Get job by id
    responses.add(
        method=responses.GET,
        url=f'{iconik.ICONIK_JOBS_API}/jobs/{JOB_ID}/',
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
