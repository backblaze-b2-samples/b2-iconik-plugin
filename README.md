Backblaze B2 Storage Plugin for iconik
======================================

This plugin makes it easy to manage assets when using [iconik](https://www.iconik.io/) storage options with different price/performance/functionality. For example, you can store master copies of full resolution assets in [Backblaze B2 Cloud Storage](https://www.backblaze.com/b2/cloud-storage.html), working on the iconik proxy files in iconik and Premiere Pro. When editing is complete, you can use the plugin to copy the masters to a [LucidLink](https://www.lucidlink.com/) Filespace for full-resolution corrections and rendering. Once the final renders are approved, you can again use the plugin to remove the copies from LucidLink, safe in the knowledge that the masters are safely archived in B2.

Here's how it works:

> A videographer saves full resolution video files to a Backblaze B2 Cloud Storage bucket, either directly or via iconik Storage Gateway. The director can review the footage in the iconik browser UI, set in and out points, and work with the iconik proxy files in Premiere Pro.
>
> When it's time to work with the full resolution files, a user right-clicks the collections and/or assets and selects 'Add to LucidLink'. iconik sends a custom action notification to the plugin, which uses the iconik Files API to request that all the selected collections and assets are copied to the LucidLink storage. iconik relays the request to an instance of iconik Storage Gateway, which retrieves the files from B2 and saves them to its local LucidLink Filespace.
>
> The production team can now access the full resolution assets via LucidLink, performing final corrections and rendering output in Premiere Pro at full resolution. If the workflow includes creating files in LucidLink, you can configure the iconik Storage Gateway to automatically upload them to Backblaze B2.
> 
> Once the rendered deliverable is approved, a user can right-click the collections and/or assets in iconik and select 'Remove from LucidLink'. iconik sends a custom action message to the plugin, which ensures that all assets in LucidLink are present in Backblaze B2 before deleting the files from LucidLink.

The plugin is implemented in Python and may be deployed as a standalone Flask app or as a [Google Cloud Function](https://cloud.google.com/functions).

<!-- TOC -->
* [Create an iconik Storage for your Backblaze B2 Bucket](#create-an-iconik-storage-for-your-backblaze-b2-bucket)
* [Deploy iconik Storage Gateway](#deploy-iconik-storage-gateway)
* [Create an iconik Application Token](#create-an-iconik-application-token)
* [Deploy the Plugin](#deploy-the-plugin)
  * [In the Flask Development Server](#in-the-flask-development-server)
    * [Prerequisites](#prerequisites)
  * [As a Standalone Flask App in Gunicorn](#as-a-standalone-flask-app-in-gunicorn)
    * [Prerequisites](#prerequisites-1)
    * [Deployment](#deployment)
  * [In a Docker Container](#in-a-docker-container)
  * [As a Google Cloud Function](#as-a-google-cloud-function)
    * [Set up the function](#set-up-the-function)
    * [Configure the Function](#configure-the-function)
    * [Deploy the Function](#deploy-the-function)
* [Create iconik Custom Actions](#create-iconik-custom-actions)
* [Test the Integration](#test-the-integration)
* [Modifying the Code](#modifying-the-code)
<!-- TOC -->

Create an iconik Storage for your Backblaze B2 Bucket
-----------------------------------------------------

You must create an iconik Storage with Storage Purpose **Files** and Storage Type **Backblaze B2** with access to your Backblaze B2 bucket. Enable scan for the storage and set it to auto scan with an appropriate interval. Make a note of the storage ID.

Deploy iconik Storage Gateway
-----------------------------

You must deploy both [iconik Storage Gateway](https://app.iconik.io/help/pages/isg/) (ISG) and the [LucidLink client](https://www.lucidlink.com/download) to a machine with access to iconik, LucidLink and B2.  [Vultr](https://www.vultr.com/) is ideal for this purpose, as it enjoys zero cost egress from B2. If you deploy ISG elsewhere, you will be paying $10/TB for data downloaded from B2.

Configure the LucidLink client to access the desired FileSpace. Configure ISG to use the LucidLink directory as [Files Storage](https://app.iconik.io/help/pages/isg/files_storage). Make a note of the storage ID.

Create an iconik Application Token
----------------------------------

Create an [iconik Application Token](https://app.iconik.io/help/pages/admin/appl_tokens) for the plugin and make a note of the token id and value.

Configuration
-------------

Create a random string to use as a secret shared by iconik and the plugin. iconik will use this as a bearer token on 
custom action requests from iconik to the plugin. 

For example, with `openssl`:

    openssl rand -hex 32

Keep a note of the shared secret!

You will configure the plugin with the storage IDs of the Backblaze B2 Storage and the LucidLink (ISG) Storage, the iconik 
application token and its ID, and the shared secret.

You will set environment variables for the plugin with the iconik token ID and shared secret - the exact details vary 
depending on how you deploy the plugin. You will use the iconik token, storage IDs and shared secret when you
[create the custom actions in iconik](#create-iconik-custom-actions).

You will also need to decide which iconik Asset Formats the plugin should manipulate. The default list of formats is 
`ORIGINAL` and `PPRO_PROXY`. If you use a different proxy format, such as `EDIT_PROXY`, you can use that in place of 
`PPRO_PROXY`. Similarly, if you want the plugin to manipulate _only_ Premiere Pro proxy files, you can configure the format
list to b2 just `PPRO_PROXY`.

There are two ways to configure format names if you wish to do so: in the custom action or via environment variables. Set 
the format names in the custom action if you wish to create multiple custom actions for adding and removing files from 
LucidLink. For example, you might create a total of four custom actions:

* Add original files to LucidLink
* Add proxy files to LucidLink
* Remove original files from LucidLink
* Remove proxy files from LucidLink

If you wish to create just two custom actions, and you need a different list of format names from the default, `ORIGINAL` 
and `PPRO_PROXY`, you can set the format names via an environment variable. For example, to have the plugin add/remove 
just Premiere Pro proxy files, you would use:

```dotenv
FORMAT_NAMES=PPRO_PROXY
```

If you configure _both_ the custom actions and the environment variable, the list of formats passed by the custom action
takes precedence.

Deploy the Plugin
-----------------

### In the Flask Development Server

You can run it in Flask's development server for development and testing, but do not use the development server for 
production deployments.

#### Prerequisites

* [Python 3.9+](https://www.python.org/downloads/)
* [pip](https://pypi.org/project/pip/)

Clone this project:

	git clone https://github.com/backblaze-b2-samples/b2-iconik-plugin.git

Change to the plugin directory and install the required Python modules:

	cd b2-iconik-plugin
	pip install -r requirements.txt

Create a file in the plugin directory named `.env` containing your iconik token id, the shared secret you created and,
optionally, the iconik format names:

	ICONIK_ID='<required: your iconik application token id>'
	BZ_SHARED_SECRET='<required: your shared secret>'
	FORMAT_NAMES='<optional: defaults to ORIGINAL,PPRO_PROXY>'

Now you can run the app via Flask's development server

    flask --app b2_iconik_plugin/plugin.py run

### As a Standalone Flask App in Gunicorn

#### Prerequisites

* [Python 3.9+](https://www.python.org/downloads/)
* [pip](https://pypi.org/project/pip/)

#### Deployment

Clone this project:

	git clone https://github.com/backblaze-b2-samples/b2-iconik-plugin.git

Change to the plugin directory and install the required Python modules:

	cd b2-iconik-plugin
	pip install -r requirements.txt

Create a file in the plugin directory named `.env` containing your iconik token id, the shared secret you created and, 
optionally, the iconik format names:

	ICONIK_ID='<required: your iconik application token id>'
	BZ_SHARED_SECRET='<required: your shared secret>'
	FORMAT_NAMES='<optional: defaults to ORIGINAL,PPRO_PROXY>'

Open `systemd/b2-iconik-plugin.service` and edit the `User`,
`WorkingDirectory` and `ExecStart` entries to match your system configuration.

Deploy the plugin as a systemd service:

	sudo cp systemd/b2-iconik-plugin.service /etc/systemd/system
	sudo systemctl daemon-reload
	sudo systemctl start b2-iconik-plugin
	sudo systemctl status b2-iconik-plugin

You should see output similar to this:

	● b2-iconik-plugin.service - Backblaze B2 iconik Plugin
	Loaded: loaded (/etc/systemd/system/b2-iconik-plugin.service; disabled; vendor preset: enabled)
	Active: active (running) since Tue 2022-08-16 19:06:36 UTC; 11s ago
	Main PID: 743400 (gunicorn)
	Tasks: 5 (limit: 4678)
	Memory: 92.8M
	CPU: 804ms
	CGroup: /system.slice/b2-iconik-plugin.service
	├─743400 /usr/bin/python3 /home/pat/.local/bin/gunicorn -b localhost:8000 -w 4 plugin:app
	├─743401 /usr/bin/python3 /home/pat/.local/bin/gunicorn -b localhost:8000 -w 4 plugin:app
	├─743402 /usr/bin/python3 /home/pat/.local/bin/gunicorn -b localhost:8000 -w 4 plugin:app
	├─743403 /usr/bin/python3 /home/pat/.local/bin/gunicorn -b localhost:8000 -w 4 plugin:app
	└─743404 /usr/bin/python3 /home/pat/.local/bin/gunicorn -b localhost:8000 -w 4 plugin:app
	
	Aug 16 19:06:36 vultr systemd[1]: Started Backblaze B2 iconik Plugin.
	Aug 16 19:06:36 vultr gunicorn[743400]: [2022-08-16 19:06:36 +0000] [743400] [INFO] Starting gunicorn 20.1.0
	Aug 16 19:06:36 vultr gunicorn[743400]: [2022-08-16 19:06:36 +0000] [743400] [INFO] Listening at: http://127.0.0.1:8000 (743400)
	Aug 16 19:06:36 vultr gunicorn[743400]: [2022-08-16 19:06:36 +0000] [743400] [INFO] Using worker: sync
	Aug 16 19:06:36 vultr gunicorn[743401]: [2022-08-16 19:06:36 +0000] [743401] [INFO] Booting worker with pid: 743401
	Aug 16 19:06:36 vultr gunicorn[743402]: [2022-08-16 19:06:36 +0000] [743402] [INFO] Booting worker with pid: 743402
	Aug 16 19:06:36 vultr gunicorn[743403]: [2022-08-16 19:06:36 +0000] [743403] [INFO] Booting worker with pid: 743403
	Aug 16 19:06:36 vultr gunicorn[743404]: [2022-08-16 19:06:36 +0000] [743404] [INFO] Booting worker with pid: 743404

Your plugin's endpoint comprises the instance's public IP address or hostname plus the Gunicorn port number. For example, if your plugin is running at 1.2.3.4, and you left the Gunicorn port as the default 8000, your plugin endpoint is `http://1.2.3.4:8000/`

You can test connectivity to the plugin by opening `http://1.2.3.4:8000/add` in a browser. You should see an error response similar to:

    {"message": "The method is not allowed for the requested URL."}

Note - for production deployment, you should also [deploy Nginx as an HTTP proxy for Gunicorn](https://docs.gunicorn.org/en/stable/deploy.html#nginx-configuration) and [configure Nginx as an HTTPS server](http://nginx.org/en/docs/http/configuring_https_servers.html). 

### In a Docker Container

First, build a Docker image:

	docker build -t b2-iconik-plugin .

If you are building the image on one machine and deploying it on another, you will need to publish it to a container registry 
such as Docker Hub or GitHub Container Registry. 

You will need to define environment variables in your deployment environment, either in a `.env` file or an alternative mechanism.

	ICONIK_ID='<required: your iconik application token id>'
	BZ_SHARED_SECRET='<required: your shared secret>'
	FORMAT_NAMES='<optional: defaults to ORIGINAL,PPRO_PROXY>'

Now you can run the image. For example, to listen on port 80 on the host, and read environment variables from a `.env` file:

	docker run --env-file .env -p 80:8000 b2-iconik-plugin

### As a Google Cloud Function

#### Set up the function

1. [Create a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
2. Ensure that [billing is enabled](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled) for the project.
3. Enable the **Cloud Functions**, **Cloud Build** and **Secret Manager** APIs.
4. If necessary, [install and initialize the gcloud CLI](https://cloud.google.com/sdk/docs).
5. Update and install gcloud components:

		gcloud components update

6. If necessary, [set up a Python development environment](https://cloud.google.com/python/docs/setup).
7. Clone this repository to a directory on your local machine:

		git clone git@github.com:backblaze-b2-samples/b2-iconik-plugin.git

#### Configure the Function

Create the file `.env.yaml` in the project directory, with the following content:

	ICONIK_ID: '<required: your iconik application token id>'
	FORMAT_NAMES: '<optional: defaults to ORIGINAL,PPRO_PROXY>'

[Create the following secret](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create) in Google Secret Manager:

	bz-shared-secret: '<your shared secret>'

#### Deploy the Function

From the command line in the project directory, run

	gcloud functions deploy iconik_handler \
	--runtime python39 --trigger-http --allow-unauthenticated --env-vars-file .env.yaml

Make a note of the `httpsTrigger.url` property, or find it with:

    gcloud functions describe iconik_handler

It should look like this:

    https://<GCP_REGION-PROJECT_ID>.cloudfunctions.net/iconik_handler

You'll use this endpoint when you create the custom actions in iconik in the next step.

You can test connectivity to the plugin by opening `https://<GCP_REGION-PROJECT_ID>.cloudfunctions.net/iconik_handler/add` in a browser. You should see an error response similar to:

    {"message": "The method is not allowed for the requested URL."}

You can view logs for the function with:

    gcloud functions logs read

Create iconik Custom Actions
----------------------------

Run the included `create_custom_actions.py` script with the endpoint of the plugin and the two storage IDs as arguments. Note that you will need to provide an iconik application token as an environment variable:

	ICONIK_TOKEN = '<your iconik application token value>' \
	python -m b2_iconik_plugin.create_custom_actions <your plugin endpoint> \
        <your B2 storage ID in iconik> \
        <your LucidLink storage ID in iconik> \
        <optional, comma-separated list of formats>

For example:

	ICONIK_TOKEN = 'eyhjofprwehjpgrwpg.brwipgbrwjvkpbwripfgbirweupgbi.rgbkfjiewpofrjwrfn' \
	python -m b2_iconik_plugin.create_custom_actions https://myserver.example.com/ \
        73a746d2-a3ed-4d61-8fd9-aa8f37a27bbb \
        d39b62e1-c586-438a-a82b-70543c228c1b \
        PPRO_PROXY

You can delete the custom actions, if necessary, with:

	ICONIK_TOKEN = '<your iconik application token value>' \
	python -m b2_iconik_plugin.delete_custom_actions <your plugin endpoint> \
        <optional, comma-separated list of formats>

If you do not specify a list of formats, then this command will delete all custom actions that match the endpoint. If you do
supply a list of formats, only custom actions with matching format lists will be deleted.

Test the Integration
--------------------

Test adding a file to B2, then LucidLink:

* Copy a media file to B2. If you copy the file directly to B2, you will need to wait for iconik to scan the bucket. If you use iconik to do so, you will see the file in iconik immediately.
* Right-click the file in the search page and select 'Add to LucidLink'
* Click the 'Admin' tab. You should see a new job with a name like 'Transfer asset my_video.mp4 to LucidLink ISG'. The job should complete successfully.
* Verify that the file is available in the LucidLink Filespace.

> Note that, as well as right-clicking the file in the search space, you can right-click a collection containing the file, or click on the gear in the upper right corner of the asset page or collection page.

You can now manipulate the file via LucidLink as you normally would.

Test deleting the file from LucidLink:

* Right-click the file in the search page and select 'Remove from LucidLink'
* Click the 'Admin' tab. You should see a new job with a name like 'Delete my_video.mp4 from LucidLink ISG'. The job should complete successfully.
* Verify that the file has been deleted from the LucidLink Filespace.
* Verify that the file is still available in B2.

Modifying the Code
------------------

You are free to modify the code for your own purposes.

There is a set of tests covering expected operation and various errors. By default, only unit tests are executed:

```console
% pytest
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.1, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/ppatterson/src/b2-iconik-plugin
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.8.0, dotenv-0.5.2
collected 32 items                                                                                                                                                                                             

tests/app_test.py ...........                                                                                                                                                                            [ 34%]
tests/gcp_test.py ..                                                                                                                                                                                     [ 40%]
tests/iconik_test.py .......                                                                                                                                                                             [ 62%]
tests/integration_test.py s                                                                                                                                                                              [ 65%]
tests/main_test.py ...........                                                                                                                                                                           [100%]

=============================================================================================== warnings summary ===============================================================================================
...
================================================================================== 31 passed, 1 skipped, 3 warnings in 8.27s ===================================================================================
```

You can run integration tests also by running `pytest` with the `--integration` flag. Note that your test iconik
environment must have two storages, and you must create an application token in iconik. You do not need an ISG or
LucidLink to run the integration tests, since they simply copy and delete files in the iconik storages.

Tou must set the following environment variables:

```dotenv
B2_STORAGE_ID=<ID of your B2 storage>
LL_STORAGE_ID=<ID of another storage>
ICONIK_ID=<your iconik application token id> 
ICONIK_TOKEN=<your iconik application token> 
BZ_SHARED_SECRET=<a long random string>
```

You can run the integration test without the unit tests:

```console
% pytest --integration tests/integration_test.py 
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.1, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/ppatterson/src/b2-iconik-plugin
configfile: pytest.ini
plugins: anyio-4.8.0, dotenv-0.5.2
collected 1 item                                                                                                                                                                                               

tests/integration_test.py .                                                                                                                                                                              [100%]

=============================================================================================== warnings summary ===============================================================================================
...
======================================================================================== 1 passed, 3 warnings in 40.03s ========================================================================================
```

Troubleshooting
---------------

The default configuration, if you do not explicitly configure `FORMAT_NAMES`, is for the plugin to attempt to copy both the
`ORIGINAL` and `PPRO_PROXY` formats for each asset. You will see errors in the iconik jobs dashboard if you copy assets that
do not have a file for a configured format. If you are not creating `PPRO_PROXY` files, then set `FORMAT_NAMES` to `ORIGINAL`.
Conversely, if you are using a format other than `PPRO_PROXY`, you might want to set `FORMAT_NAMES` to a value such as 
`ORIGINAL, MY_COOL_FORMAT`.
