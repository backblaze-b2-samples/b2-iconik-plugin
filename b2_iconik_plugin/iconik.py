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

from time import sleep

from requests import Session

from b2_iconik_plugin.logger import Logger

ASSET_OBJECT_TYPE = "assets"
COLLECTION_OBJECT_TYPE = "collections"

ICONIK_API_BASE = "https://app.iconik.io"
ICONIK_ASSETS_API = ICONIK_API_BASE + "/API/assets/v1"
ICONIK_FILES_API = ICONIK_API_BASE + "/API/files/v1"
ICONIK_JOBS_API = ICONIK_API_BASE + "/API/jobs/v1"
ICONIK_SETTINGS_API = ICONIK_API_BASE + "/API/settings/v1"
ICONIK_USERS_API = ICONIK_API_BASE + "/API/users/v1"

SUCCESS_STATUS_LIST = [
    "FINISHED",
    "SKIPPED"
]

DONE_STATUS_LIST = [
    "FINISHED",
    "SKIPPED",
    "FAILED",
    "ABORTED"
]


class Iconik:
    """The iconik object implements just enough of the iconik API for the plugin to work
    """

    def __init__(self, app_id, auth_token):
        if not app_id or not auth_token:
            raise ValueError("You must supply both app_id and auth_token")
        elif not isinstance(app_id, str):
            raise TypeError("app_id must be a string")
        elif not isinstance(auth_token, str):
            raise TypeError("auth_token must be a string")

        self.session = Session()

        self.logger = Logger()

        # Set iconik id and token headers
        self.session.headers.update({
            "App-ID": app_id,
            "Auth-Token": auth_token
        })

    def __request(self, method, url, json=None, params=None, raise_for_status=True):
        self.logger.log("DEBUG", {"method": method, "url": url, "json": json, "params": params})
        response = self.session.request(method, url, json=json, params=params)
        payload = response.json() if response.text else None
        self.logger.log("DEBUG", {"status_code": response.status_code, "payload": payload})
        if raise_for_status:
            response.raise_for_status()
        return response

    def __get(self, url, params=None, raise_for_status=True):
        return self.__request('GET', url, None, params, raise_for_status)

    def __delete(self, url, params=None, raise_for_status=True):
        return self.__request('DELETE', url, None, params, raise_for_status)

    def __post(self, url, json=None, params=None, raise_for_status=True):
        return self.__request('POST', url, json, params, raise_for_status)

    def __patch(self, url, json=None, params=None, raise_for_status=True):
        return self.__request('PATCH', url, json, params, raise_for_status)

    def get_objects(self, first_url, params=None):
        """
        Gets a list of objects from the iconik API. GETs the first_url and then
        GETs next_url from the response until it is empty.
        Args:
            first_url (str): The initial URL to GET
            params: Parameters to pass down to the underlying get()
        Returns:
            A list of objects
        """
        objects = []
        url = first_url
        while True:
            response = self.__get(url, params=params).json()
            objects.extend(response["objects"])
            # Next URL is a path relative to ICONIK_API_BASE
            url = ICONIK_API_BASE + response["next_url"] if response.get("next_url") else None
            if not url:
                break

        return objects

    def get_storage(self, id_=None, name=None):
        """
        Get a storage from its name or id. Note - if there are multiple storages
        with the same name, this function returns the first one returned
        by iconik
        Args:
            name (str): The name of a storage
            id_ (str): The id of a storage
        Returns:
            A storage
        """
        if id_:
            url = f"{ICONIK_FILES_API}/storages/{id_}/"
            params = None
        else:
            url = f"{ICONIK_FILES_API}/storages/"
            params = {"name": name}
        response = self.__get(url, params=params, raise_for_status=False)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        if "objects" in response.json():
            return response.json()["objects"][0]
        elif "id" in response.json():
            return response.json()
        else:
            return None

    def get_collection(self, id_):
        """
        Get a collection from its id
        Args:
            id_ (str): The collection id
        Returns:
            A collection
        """
        response = self.__get(f"{ICONIK_ASSETS_API}/collections/{id_}", None, False)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_collection_contents(self, id_, object_types):
        """
        Get the contents of a collection from its id
        Args:
            id_ (str): The collection id
            object_types (list of str): Optional list of object types to return
        Returns:
            A list of objects
        """
        url = f"{ICONIK_ASSETS_API}/collections/{id_}/contents/"
        if object_types:
            url += f"?object_types={','.join(object_types)}"
        return self.get_objects(url)

    def get_format(self, asset_id, name):
        """
        Get an asset's format from its name
        Args:
            asset_id (str): The asset id
            name (str): The name of a format
        Returns:
            A format
        """
        response = self.__get(f"{ICONIK_FILES_API}/assets/{asset_id}/formats/{name}/", raise_for_status=False)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_file_sets(self, asset_id, format_id, storage_id):
        """
        Get the file sets of a given format from a storage for an asset
        Args:
            asset_id (str): The asset id
            format_id (str): The format id
            storage_id (str): The storage id
        Returns:
            A list of file sets
        """
        return self.get_objects(
            f"{ICONIK_FILES_API}/assets/{asset_id}/formats/{format_id}/storages/{storage_id}/file_sets/")

    def delete_and_purge_file_set(self, asset_id, file_set_id):
        """
        Delete and purge all files from a file set
        Args:
            asset_id (str): The asset id
            file_set_id (str): The file set id
        """
        self.__delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/")
        self.__delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/purge/")

    def delete_asset_files(self, asset_id, format_names, storage_id):
        """
        Delete asset files of given formats from a storage, if they exist
        Args:
            asset_id (str): The asset id
            format_names (list of str): The format name
            storage_id (str): The storage id
        """
        for format_name in format_names:
            # Don't want to shadow the format built-in name
            format_obj = self.get_format(asset_id, format_name)
            if format_obj:
                file_sets = self.get_file_sets(asset_id, format_obj["id"], storage_id)
                if file_sets:
                    for file_set in file_sets:
                        self.delete_and_purge_file_set(asset_id, file_set["id"])

    def delete_collection_files(self, collection_id, format_names, storage_id):
        """
        Delete asset files of a given format from a storage for the given
        collection, and all subcollections within that collection.
        Args:
            collection_id (str): The collection id
            format_names (list of str): The format name
            storage_id (str): The storage id
        """
        for obj in self.get_collection_contents(collection_id, [COLLECTION_OBJECT_TYPE, ASSET_OBJECT_TYPE]):
            if obj["object_type"] == COLLECTION_OBJECT_TYPE:
                self.delete_collection_files(obj["id"], format_names, storage_id)
            elif obj["object_type"] == ASSET_OBJECT_TYPE:
                self.delete_asset_files(obj["id"], format_names, storage_id)

    def delete_files(self, request, format_names, storage_id):
        """
        Delete files of a given format from a storage for a custom action request
        Args:
            request (dict): A request containing a list of asset ids and/or
                            a list of collection ids
            format_names (list of str): The format name
            storage_id (str): The storage id
        """
        for asset_id in request["asset_ids"]:
            self.delete_asset_files(asset_id, format_names, storage_id)

        for collection_id in request["collection_ids"]:
            self.delete_collection_files(collection_id, format_names, storage_id)

    @staticmethod
    def job_succeeded(job):
        return job["status"] in SUCCESS_STATUS_LIST

    @staticmethod
    def job_done(job):
        return job["status"] in DONE_STATUS_LIST

    def copy_files(self, request, format_names, target_storage_id, sync=False):
        """
        Copy files of a given format to a storage for a custom action request
        Args:
            request (dict): A request containing a list of asset ids and/or
                            a list of collection ids
            format_names (list of str): The format names
            target_storage_id (str): The target storage id
            sync (bool):
        """
        job_ids = []

        # TODO - see if we can exclude non-existent asset/format combinations
        for format_name in format_names:
            if request.get("asset_ids") and len(request["asset_ids"]) > 0:
                payload = {
                    "object_ids": request["asset_ids"],
                    "object_type": "assets",
                    "format_name": format_name
                }
                response = self.__post(f"{ICONIK_FILES_API}/storages/{target_storage_id}/bulk/",
                                       json=payload)
                job_ids.append(response.json()["job_id"])

            if request.get("collection_ids") and len(request["collection_ids"]) > 0:
                payload = {
                    "object_ids": request["collection_ids"],
                    "object_type": "collections",
                    "format_name": format_name
                }

                response = self.__post(f"{ICONIK_FILES_API}/storages/{target_storage_id}/bulk/",
                                       json=payload)
                job_ids.append(response.json()["job_id"])

        if sync:
            # Wait for jobs to complete
            for job_id in job_ids:
                while True:
                    sleep(1)
                    response = self.__get(f"{ICONIK_JOBS_API}/jobs/{job_id}/")
                    job = response.json()
                    if self.job_done(job):
                        break
                if not self.job_succeeded(job):
                    return False

        return True

    def delete_action(self, action):
        return self.__delete(
            f"{ICONIK_ASSETS_API}/custom_actions/{action['context']}/{action['id']}"
        )

    def add_action(self, context, app_id, url, title, shared_secret):
        action = {
            "type": "POST",
            "context": context,
            "title": title,
            "url": url,
            "headers": {
                "x-bz-secret": shared_secret
            },
            "app_id": app_id
        }
        return self.__post(
            f"{ICONIK_ASSETS_API}/custom_actions/{context}/",
            json=action
        ).json()

    def create_asset(self, title, type_, collection_id=None, apply_default_acls=True):
        """
        Create a new asset
        """
        asset = {
            "title": title,
            "type": type_,
            "collection_id": collection_id,
        }
        return self.__post(
            f"{ICONIK_ASSETS_API}/assets/?apply_default_acls={'true' if apply_default_acls else 'false'}",
            json=asset
        ).json()

    def get_asset(self, asset_id):
        response =  self.__get(f"{ICONIK_ASSETS_API}/assets/{asset_id}/", None, False)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_current_user(self):
        return self.__get(f"{ICONIK_USERS_API}/users/current/").json()

    def get_system_settings(self):
        return self.__get(f"{ICONIK_SETTINGS_API}/system/current/").json()

    def create_format(self, asset_id, user_id, name, metadata, storage_methods):
        """
        Create format and associate to asset
        """
        format_ = {
            "user_id": user_id,
            "name": name,
            "metadata": metadata,
            "storage_methods": storage_methods
        }
        return self.__post(
            f"{ICONIK_FILES_API}/assets/{asset_id}/formats",
            json=format_
        ).json()

    def create_file_set(self, asset_id, format_id, storage_id, name, base_dir="", component_ids=None):
        """
        Create file set and associate to asset
        """
        file_set = {
            "format_id": format_id,
            "storage_id": storage_id,
            "base_dir": base_dir,
            "name": name,
            "component_ids": [] if component_ids is None else component_ids
        }
        return self.__post(
            f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets",
            json=file_set
        ).json()

    def get_asset_file_sets(self, asset_id):
        return self.get_objects(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/")

    def create_file(self, asset_id, original_name, size, type_, storage_id, file_set_id, format_id, directory_path=""):
        """
        Create file and associate to asset
        """
        file = {
            "original_name": original_name,
            "directory_path": directory_path,
            "size": size,
            "type": type_,
            "storage_id": storage_id,
            "file_set_id": file_set_id,
            "format_id": format_id
        }
        return self.__post(
            f"{ICONIK_FILES_API}/assets/{asset_id}/files",
            json=file
        ).json()

    def create_job(self, object_type, object_id, type_, status, title, metadata):
        """
        Create a new job
        """
        job = {
            "object_type": object_type,
            "object_id": object_id,
            "type": type_,
            "status": status,
            "title": title,
            "metadata": metadata
        }
        return self.__post(
            f"{ICONIK_JOBS_API}/jobs/",
            json=job
        ).json()

    def update_file(self, asset_id, file_id, status, progress_processed):
        """
        Update file information
        """
        file = {
            "status": status,
            "progress_processed": progress_processed
        }
        return self.__patch(
            f"{ICONIK_FILES_API}/assets/{asset_id}/files/{file_id}/",
            json=file
        ).json()

    def create_keyframe(self, asset_id, use_storage_transcode_ignore_pattern=True, priority=5):
        """
        Create keyframe and associate to asset
        """
        keyframe = {
            "use_storage_transcode_ignore_pattern": use_storage_transcode_ignore_pattern,
            "priority": priority,
        }
        return self.__post(
            f"{ICONIK_FILES_API}/assets/{asset_id}/keyframes",
            json=keyframe
        ).json()


    def update_job(self, job_id, status, progress_processed):
        """
        Create a new job
        """
        job = {
            "status": status,
            "progress_processed": progress_processed
        }
        return self.__patch(
            f"{ICONIK_JOBS_API}/jobs/{job_id}",
            json=job
        ).json()


    def add_assets_to_delete_queue(self, asset_ids):
        assets = {
            "ids" : asset_ids
        }
        self.__post(
            f"{ICONIK_ASSETS_API}/delete_queue/assets/",
            json=assets
        )

    def get_deleted_objects(self):
        return self.get_objects(f"{ICONIK_ASSETS_API}/delete_queue/assets/")

    def purge_assets_from_delete_queue(self, asset_ids):
        assets = {
            "ids" : asset_ids
        }
        self.__post(
            f"{ICONIK_ASSETS_API}/delete_queue/assets/purge/",
            json=assets
        )

    def delete_asset(self, asset_id):
        self.__delete(f"{ICONIK_ASSETS_API}/assets/{asset_id}/")

    def purge_asset(self, asset_id):
        self.__delete(f"{ICONIK_ASSETS_API}/assets/{asset_id}/purge/")
