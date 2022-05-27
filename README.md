iconik Storage Plugin for B2
============================

This plugin makes it easy to manage assets when using iconik storage options with different price/performance/functionality. For example, you can store master copies of full resolution assets in Backblaze B2 Cloud Storage, working on the iconik proxy files in iconik and Premiere Pro. When editing is complete, you can use the plugin to copy the masters to LucidLink for full-resolution corrections and rendering. Once the final renders are approved, you can again use the plugin to remove the copies from LucidLink, safe in the knowledge that the masters are safely archived in B2.

Here's how it works:

> A videographer saves full resolution video files to a Backblaze B2 Cloud Storage bucket, either directly or via iconik Storage Gateway. The director can review the footage in the iconik browser UI, set in and out points, and work with the iconik proxy files in Premiere Pro.
>
> When it's time to work with the full resolution files, a user right-clicks the assets and selects 'Add to LucidLink'. iconik sends a custom action notification to the plugin, which uses the iconik Files API to request that the files are copied to the LucidLink storage. iconik relays the request to an instance of iconik Storage Gateway, which retrieves the files from B2 and saves them to its local LucidLink Filespace.
>
> The production team can now access the full resolution assets via LucidLink, performing final corrections and rendering output in Premiere Pro at full resolution. Once the rendered deliverable is approved, a user can right-click the asset in iconik and select 'Remove from LucidLink'. iconik sends a custom action message to the plugin, which deletes the full resolution asset files from LucidLink, leaving the master copies in B2.

The plugin is implemented as a [Google Cloud Function](https://cloud.google.com/functions) in Python.

Deploy iconik Storage Gateway
-----------------------------

You must deploy both [iconik Storage Gateway](https://app.iconik.io/help/pages/isg/) (ISG) and the [LucidLink client](https://www.lucidlink.com/download) to a machine with access to iconik, LucidLink and B2. Either [Vultr](https://www.vultr.com/) or [Equinix Metal](https://metal.equinix.com/) are ideal for this purpose, as they both enjoy zero cost egress from B2. If you deploy ISG elsewhere, you will be paying $10/TB for data downloaded from B2.

Configure the LucidLink client to access the desired FileSpace. Configure ISG to use the LucidLink directory as [Files Storage](https://app.iconik.io/help/pages/isg/files_storage). Make a note of the storage name.

Create an iconik Application Token
----------------------------------

Create an [iconik Application Token](https://app.iconik.io/help/pages/admin/appl_tokens) for the iconik Storage Plugin and make a note of the token name and value.

Setup the Function
------------------

1. [Create a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
2. Ensure that [billing is enabled](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled) for the project.
3. Enable the **Cloud Functions**, **Cloud Build** and **Secret Manager** APIs.
4. If necessary, [install and initialize the gcloud CLI](https://cloud.google.com/sdk/docs).
5. Update and install gcloud components:

		gcloud components update

6. If necessary, [set up a Python development environment](https://cloud.google.com/python/docs/setup).
7. Clone this repository to a directory on your local machine:

		git clone git@github.com:backblaze-b2-samples/b2-iconik-plugin.git

Configure the Function
----------------------

Create a random string to use as a secret shared by iconik and the cloud function. For example, with `openssl`:

    openssl rand -hex 32

Create the file `.env.yaml` in the project directory, with the following content:

	ICONIK_ID: '<required: your iconik application token id>'
	FORMAT_NAME: '<optional: defaults to ORIGINAL>'
	STORAGE_NAME: '<required: target iconik storage>'
	STORAGE_PATH: '<optional: defaults to />'

[Create the following secrets](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create) in Google Secret Manager:

	iconik-token: '<your iconik application token value>'
	bz-shared-secret: '<your shared secret>'

Deploy the Function
-------------------

From the command line in the project directory, run

	gcloud functions deploy iconik_handler \
	--runtime python39 --trigger-http --allow-unauthenticated --env-vars-file .env.yaml

Make a note of the `httpsTrigger.url` property, or find it with:

    gcloud functions describe iconik_handler

It should look like this:

    https://GCP_REGION-PROJECT_ID.cloudfunctions.net/iconik_handler

You can view logs for the function with:

    gcloud functions logs read

Create iconik Custom Actions
----------------------------

Run the included `create_custom_actions.py` script with the iconik Application Token and shared secret as environment variables, like this:

	ICONIK_ID='<your iconik application token id>' \
		ICONIK_TOKEN='<your iconik application token value>' \
		BZ_SHARED_SECRET='<your shared secret>' \
		python create_custom_actions.py

You can delete the custom actions, if necessary, with:

	ICONIK_ID='<your iconik application token id>' \
		ICONIK_TOKEN='<your iconik application token value>' \
		python delete_custom_actions.py

Test the Integration
--------------------

Test adding a file to B2, then LucidLink:

* Copy a media file to B2. If you copy the file directly to B2, you will need to wait for iconik to scan the bucket. If you use iconik to do so, you will see the file in iconik immediately.
* Right click the file in the search page and select 'Add to LucidLink'
* Click the 'Admin' tab. You should see a new job with a name like 'Transfer asset myvideo.mp4 to LucidLink ISG'. The job should complete successfully.
* Verify that the file is available in the LucidLink Filespace.

> Note that, as well as right-clicking the file in the search space, you can right click a collection containing the file, or click on the gear in the upper right corner of the asset page or collection page.

You can now manipulate the file via LucidLink as you normally would.

Test deleting the file from LucidLink:

* Right click the file in the search page and select 'Remove from LucidLink'
* Click the 'Admin' tab. You should see a new job with a name like 'Delete myvideo.mp4 from LucidLink ISG'. The job should complete successfully.
* Verify that the file has been deleted from the LucidLink Filespace.
* Verify that the file is still available in B2.

Modifying the Code
------------------

You are free to modify the code for your own purposes.

`main_test.py` contains a set of system tests covering expected operation and various errors.

	% pytest main_test.py
	=============================================== test session starts ===============================================
	platform darwin -- Python 3.10.2, pytest-7.1.2, pluggy-1.0.0
	rootdir: /Users/ppatterson/src/backblaze-b2-mam-gateway
	collected 11 items                                                                                                

	main_test.py ...........                                                                                    [100%]

	=============================================== 11 passed in 0.60s ================================================
