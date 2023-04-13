from flask import abort, Response

import os

# Names for secrets
from iconik import Iconik

AUTH_TOKEN_NAME = "iconik-token"
SHARED_SECRET_NAME = "bz-shared-secret"

X_BZ_SHARED_SECRET = "x-bz-secret"


def iconik_handler(req, logger, bz_shared_secret):
    """
    Handles iconik custom action.

    "/add" route copies specified assets to LucidLink
    "/remove" route copies specified assets to B2, then deletes
        those assets' files from LucidLink
    """
    logger.log("DEBUG", req.get_data(as_text=True), req)

    # Authenticate caller via shared secret
    if req.headers.get(X_BZ_SHARED_SECRET) != bz_shared_secret:
        logger.log("ERROR", f"Invalid {X_BZ_SHARED_SECRET} header")
        # 401 should always return a WWW-Authenticate header
        abort(
            401,
            response=Response(
                status=401,
                headers={"WWW-Authenticate": X_BZ_SHARED_SECRET}))

    # Only POST is allowed
    if req.method != "POST":
        logger.log("ERROR", f"Invalid method: {req.method}")
        abort(405)

    # Parse the request body as JSON; return None on any errors rather than
    # raising an exception
    request = req.get_json(silent=True)

    # Is JSON body missing or badly formed?
    if not request:
        logger.log("ERROR", f"Invalid JSON body: {req.get_data(as_text=True)}")
        abort(400)

    # The formats that we're going to copy
    format_names = os.environ.get("FORMAT_NAMES", "ORIGINAL,PPRO_PROXY").split(',')

    # Create an iconic API client
    iconik = Iconik(os.environ['ICONIK_ID'], request.get("auth_token"))

    # The LucidLink storage
    ll_storage = iconik.get_storage(id_=req.args.get('ll_storage_id'))
    if not ll_storage:
        logger.log("ERROR", f"Can't find configured storage: {req.args.get('ll_storage_id')}")
        abort(500)

    # The B2 storage
    b2_storage = iconik.get_storage(id_=req.args.get("b2_storage_id"))
    if not b2_storage:
        logger.log("ERROR", f"Can't find configured storage: {req.args.get('b2_storage_id')}")
        abort(500)

    # Check that context is as expected
    if request.get("context") not in ["ASSET", "COLLECTION", "BULK"]:
        logger.log("ERROR", f"Invalid context: {request.get('context')}")
        abort(400)

    # Perform the requested operation
    if req.path == "/add":
        # Copy files to LucidLink
        iconik.copy_files(request=request,
                          format_names=format_names,
                          target_storage_id=ll_storage["id"])
    elif req.path == "/remove":
        # Copy any original files to B2, waiting for job(s) to complete
        if iconik.copy_files(request=request,
                             format_names=[format_names[0]],
                             target_storage_id=b2_storage["id"],
                             sync=True):
            # Delete files from LucidLink
            iconik.delete_files(request=request,
                                format_names=format_names,
                                storage_id=ll_storage["id"])
    else:
        logger.log("ERROR", f"Invalid path: {req.path}")
        abort(404)

    logger.log("DEBUG", "Processing complete")
    return "OK"
