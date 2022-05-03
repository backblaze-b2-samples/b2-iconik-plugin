from flask import abort, Response
from google.cloud import secretmanager

import google_crc32c
import json
import os
import requests

GCP_PROJECT_ID_URL = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
ICONIK_FILES_API = "https://app.iconik.io/API/files/v1"
ICONIK_ASSETS_API = "https://app.iconik.io/API/assets/v1"
X_BZ_SHARED_SECRET = "x-bz-secret"

# Global HTTP session provides connection pooling
session = requests.Session()


class SecretError(Exception):
    pass


def get_project_id():
    """
    Get the project id from Google Cloud
    Returns:
        A project id
    """
    response = requests.get(
        GCP_PROJECT_ID_URL,
        headers={"Metadata-Flavor": "Google"})
    response.raise_for_status()
    return response.text


def get_secret(project_id, secret_id):
    """
    Get a secret from the Google Cloud Secret Manager
    Args:
        project_id (str): The Google Cloud Function project id
        name (str): The secret id
    Returns:
        A secret
    """
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise SecretError("CRC check failed")

    return response.payload.data.decode("UTF-8")


def get_storage(name):
    """
    Get a storage from its name
    Args:
        name (str): The name of a storage
    Returns:
        A storage
    """
    response = session.get(f"{ICONIK_FILES_API}/storages/", params={"name": name})
    response.raise_for_status()
    return response.json()["objects"][0]


def get_collection(id):
    """
    Get a collection from its id
    Args:
        id (str): The collection id
    Returns:
        A collection
    """
    response = session.get(f"{ICONIK_ASSETS_API}/collections/{id}")
    response.raise_for_status()
    return response.json()


def get_format(asset_id, name):
    """
    Get an asset"s format from its name
    Args:
        asset_id (str): The asset id
        name (str): The name of a format
    Returns:
        A format
    """
    response = session.get(f"{ICONIK_FILES_API}/assets/{asset_id}/formats/{name}/")
    response.raise_for_status()
    return response.json()


def get_file_sets(asset_id, format_id, storage_id):
    """
    Get the file sets of a given format from a storage for an asset
    Args:
        asset_id (str): The asset id
        format_id (str): The format id
        storage_id (str): The storage id
    Returns:
        A list of file sets
    """
    response = session.get(f"{ICONIK_FILES_API}/assets/{asset_id}/formats/{format_id}/storages/{storage_id}/file_sets/")
    response.raise_for_status()
    return response.json()["objects"]


def delete_and_purge_file_set(asset_id, file_set_id):
    """
    Delete and purge all files from a file set
    Args:
        asset_id (str): The asset id
        file_set_id (str): The file set id
    """
    response = session.delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/")
    response.raise_for_status()
    response = session.delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/purge/")
    response.raise_for_status()


def delete_file(asset_id, format_name, storage_id):
    """
    Delete asset files of a given format from a storage
    Args:
        asset_ids (str): The asset id
        format_name (str): The format name
        storage_id (str): The storage id
    """
    format = get_format(asset_id, format_name)
    file_sets = get_file_sets(asset_id, format["id"], storage_id)
    for file_set in file_sets:
        delete_and_purge_file_set(asset_id, file_set["id"])


def delete_files(asset_ids, format_name, storage_id):
    """
    Delete files of a given format from a storage for a list of assets
    Args:
        asset_ids (str): A list of asset ids
        format_name (str): The format name
        storage_id (str): The storage id
    """
    for asset_id in asset_ids:
        delete_file(asset_id, format_name, storage_id)


def copy_files(asset_ids, format_name, storage_id, path):
    """
    Copy files of a given format to a storage for a list of assets
    Args:
        asset_id (str): A list of asset ids
        format_name (str): The format name
        storage_id (str): The storage id
    """
    payload = {
        "object_ids": asset_ids,
        "object_type": "assets",
        "file_path": path,
        "format_name": format_name
    }

    response = session.post(f"{ICONIK_FILES_API}/storages/{storage_id}/bulk/",
                            json=payload)
    response.raise_for_status()


def log(project_id, severity, message, req=None):
    """
    Emit a structured log message
    Args:
        project_id (str): The Google Cloud Function project id
        severity (str): "INFO", "DEBUG", "ERROR" etc
        message (str): The message to log
        req (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    """

    # Trace header code from 
    # https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
    global_log_fields = {}

    request_is_defined = "request" in globals() or "request" in locals()
    if request_is_defined and request:
        trace_header = request.headers.get("X-Cloud-Trace-Context")

        if trace_header:
            trace = trace_header.split("/")
            global_log_fields[
                "logging.googleapis.com/trace"
            ] = f"projects/{project_id}/traces/{trace[0]}"

    http_request = {
        "httpRequest": {
            "requestMethod": req.method,
            "requestUrl": req.url,
            "requestSize": req.content_length,
            "userAgent": req.user_agent.string,
            "remoteIp": req.headers.get("x-forwarded-for"),
            "protocol": req.scheme        
        }
    } if req else {}

    entry = global_log_fields | http_request | {
        "severity": severity,
        "message": message
    }

    print(json.dumps(entry))


def iconik_handler(req):
    """
    Handles iconik webhook and custom action.

    Webhook configuration:
        URL: (Your Google Cloud Function URL)/webhook
        Event type: Collections
        Object ID: (Empty)
        Realm: Contents
        Operation: Create

    Custom Action configuration:
        Context: Asset
        Type: Post
        URL: (Your Google Cloud Function URL)/action
        App Name: An application

    Args:
        req (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    project_id = get_project_id()

    log(project_id, "DEBUG", req.get_data(as_text=True), req)

    # Authenticate caller via shared secret
    if req.headers.get(X_BZ_SHARED_SECRET) \
        != get_secret(project_id, "bz-shared-secret"):
        log(project_id, "ERROR", f"Invalid {X_BZ_SHARED_SECRET} header")
        # 401 should always return a WWW-Authenticate header
        abort(
            401, 
            response=Response(
                status=401, 
                headers={"WWW-Authenticate": X_BZ_SHARED_SECRET}))

    # Only POST is allowed
    if req.method != "POST":
        log(project_id, "ERROR", f"Invalid method: {req.method}")
        abort(405)

    # Parse the request body as JSON; return None on any errors rather than
    # raising an exception
    request = req.get_json(silent=True)

    # Is JSON body missing or badly formed?
    if not request:
        log(project_id, "ERROR", f"Invalid JSON body: {req.get_data(as_text=True)}")
        abort(400)

    # Set iconik id and token headers
    session.headers.update({
        "App-ID": os.environ["ICONIK_ID"],
        "Auth-Token": get_secret(project_id, "iconik-token")
    })

    # The format that we're going to copy
    format_name = os.environ.get("FORMAT_NAME", "ORIGINAL")

    # The target storage
    storage_id = get_storage(os.environ["STORAGE_NAME"])["id"]

    # Path within the storage
    storage_path = os.environ.get("STORAGE_PATH", "/")

    # Add or remove files from the storage?
    if (req.path == "/add"):
        copy_files(asset_ids=request["asset_ids"], 
                   format_name=format_name,
                   storage_id=storage_id,
                   path=storage_path)        
    elif (req.path == "/remove"):
        delete_files(asset_ids=request["asset_ids"], 
                     format_name=format_name,
                     storage_id=storage_id)
    else:
        log(project_id, "ERROR", f"Invalid path: {req.path}")
        abort(404)

    log(project_id, "DEBUG", "Processing complete")
    return "OK"