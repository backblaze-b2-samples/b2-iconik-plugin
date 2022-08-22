from requests import Session
from time import sleep

from logger import Logger

ICONIK_API_BASE = "https://app.iconik.io"
ICONIK_ASSETS_API = ICONIK_API_BASE + "/API/assets/v1"
ICONIK_FILES_API = ICONIK_API_BASE + "/API/files/v1"
ICONIK_JOBS_API = ICONIK_API_BASE + "/API/jobs/v1"

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

    def __get(self, url, params=None, raise_for_status=True):
        self.logger.log("DEBUG", {"method": "GET", "url": url, "params": params})
        response = self.session.get(url, params=params)
        payload = response.json() if response.text else None
        self.logger.log("DEBUG", {"status_code": response.status_code, "payload": payload})
        if raise_for_status:
            response.raise_for_status()
        return response

    def __delete(self, url, raise_for_status=True):
        self.logger.log("DEBUG", {"method": "DELETE", "url": url})
        response = self.session.delete(url)
        payload = response.json() if response.text else None
        self.logger.log("DEBUG", {"status_code": response.status_code, "payload": payload})
        if raise_for_status:
            response.raise_for_status()
        return response

    def __post(self, url, json=None, raise_for_status=True):
        self.logger.log("DEBUG", {"method": "POST", "url": url, "json": json})
        response = self.session.post(url, json=json)
        payload = response.json() if response.text else None
        self.logger.log("DEBUG", {"status_code": response.status_code, "payload": payload})
        if raise_for_status:
            response.raise_for_status()
        return response

    def get_objects(self, first_url, params=None):
        """
        Gets a list of objects from the iconik API. GETs the first_url and then
        GETs next_url from the response until it is empty.
        Args:
            first_url (str): The initial URL to GET
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

    def get_storage(self, id=None, name=None):
        """
        Get a storage from its name or id. Note - if there are multiple storages
        with the same name, this function returns the first one returned
        by iconik
        Args:
            name (str): The name of a storage
            id (str): The id of a storage
        Returns:
            A storage
        """
        if id:
            url = f"{ICONIK_FILES_API}/storages/{id}/"
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

    def get_collection(self, id):
        """
        Get a collection from its id
        Args:
            id (str): The collection id
        Returns:
            A collection
        """
        response = self.__get(f"{ICONIK_ASSETS_API}/collections/{id}")
        return response.json()

    def get_collection_contents(self, id):
        """
        Get the contents of a collection from its id
        Args:
            id (str): The collection id
        Returns:
            A list of objects
        """
        return self.get_objects(f"{ICONIK_ASSETS_API}/collections/{id}/contents/")

    def get_format(self, asset_id, name):
        """
        Get an asset"s format from its name
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
        response = self.__delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/")
        response = self.__delete(f"{ICONIK_FILES_API}/assets/{asset_id}/file_sets/{file_set_id}/purge/")

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
        for object in self.get_collection_contents(collection_id):
            if object["type"] == "COLLECTION":
                self.delete_collection_files(object["id"], format_names, storage_id)
            elif object["type"] == "ASSET":
                self.delete_asset_files(object["id"], format_names, storage_id)

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

    def job_succeeded(self, job):
        return job["status"] in SUCCESS_STATUS_LIST

    def job_done(self, job):
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

        for format_name in format_names:
            if request.get("asset_ids") and len(request["asset_ids"]) > 0:
                payload = {
                    "object_ids": request["asset_ids"],
                    "object_type": "assets",
                    "format_name": format_name
                }
                print("@@@", target_storage_id)
                response = self.__post(f"{ICONIK_FILES_API}/storages/{target_storage_id}/bulk/",
                                       json=payload)
                job_ids.append(response.json()["job_id"])

            if request.get("collection_ids") and len(request["collection_ids"]) > 0:
                payload = {
                    "object_ids": request["collection_ids"],
                    "object_type": "collections",
                    "format_name": format_name
                }

                print("@@@", target_storage_id)
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
        response = self.__delete(
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
        response = self.__post(
            f"{ICONIK_ASSETS_API}/custom_actions/{context}/",
            json=action
        )
