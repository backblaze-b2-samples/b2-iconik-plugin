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
import time

from flask import abort, Response

# Names for secrets
from b2_iconik_plugin.iconik import Iconik

DEFAULT_FORMAT_NAMES = "ORIGINAL,PPRO_PROXY"

AUTH_TOKEN_NAME = "iconik-token"
SHARED_SECRET_NAME = "bz-shared-secret"

X_BZ_SHARED_SECRET = "x-bz-secret"


class IconikHandler:
    def __init__(self, logger, shared_secret, iconik_id, format_names=None, testing=False):
        self._format_names = format_names
        self._logger = logger
        self._shared_secret = shared_secret
        self._iconik_id = iconik_id
        self._testing = testing

    def is_testing(self):
        return self._testing

    def post(self, req):
        """
        Handles iconik custom action.

        "/add" route copies specified assets to LucidLink
        "/remove" route copies specified assets to B2, then deletes
            those assets' files from LucidLink
        """
        start_time = time.perf_counter()
        self._logger.log("DEBUG", "Handler started")
        self._logger.log("DEBUG", req.get_data(as_text=True), req)

        # Authenticate caller via shared secret
        if req.headers.get(X_BZ_SHARED_SECRET) != self._shared_secret:
            self._logger.log("ERROR", f"Invalid {X_BZ_SHARED_SECRET} header")
            # 401 should always return a WWW-Authenticate header
            abort(
                401,
                response=Response(
                    status=401,
                    headers={"WWW-Authenticate": X_BZ_SHARED_SECRET}))

        # Only POST is allowed
        if req.method != "POST":
            self._logger.log("ERROR", f"Invalid method: {req.method}")
            abort(405)

        # Parse the request body as JSON; return None on any errors rather than
        # raising an exception
        request = req.get_json(silent=True)

        # Is JSON body missing or badly formed?
        if not request:
            self._logger.log("ERROR", f"Invalid JSON body: {req.get_data(as_text=True)}")
            abort(400)

        # Create an iconic API client per request, since it uses the auth_token
        iconik = Iconik(self._iconik_id, request.get("auth_token"))

        # The LucidLink storage
        ll_storage = iconik.get_storage(id_=req.args.get('ll_storage_id'))
        if not ll_storage:
            self._logger.log("ERROR", f"Can't find configured storage: {req.args.get('ll_storage_id')}")
            abort(500)

        # The B2 storage
        b2_storage = iconik.get_storage(id_=req.args.get("b2_storage_id"))
        if not b2_storage:
            self._logger.log("ERROR", f"Can't find configured storage: {req.args.get('b2_storage_id')}")
            abort(500)

        # Formats we need to copy/delete
        if "formats" in req.args:
            format_names = req.args.get("formats").split(',')
        else:
            # The formats that we're going to copy
            format_names = self._format_names
        format_names = [format_name.strip() for format_name in format_names]
        if len(format_names) == 0:
            self._logger.log("ERROR", "No format names in request or environment")

        # Check that context is as expected
        if request.get("context") not in ["ASSET", "COLLECTION", "BULK"]:
            self._logger.log("ERROR", f"Invalid context: {request.get('context')}")
            abort(400)

        # Perform the requested operation
        if req.path in ["/add", "/remove"]:
            request["action"] = req.path[1:]
            self.start_process(request, iconik, b2_storage, ll_storage, format_names)
        else:
            self._logger.log("ERROR", f"Invalid path: {req.path}")
            abort(404)

        self._logger.log("DEBUG", f"Handler complete in {(time.perf_counter() - start_time):.3f} seconds")
        return "OK"

    def start_process(self, request, iconik, b2_storage, ll_storage, format_names):
        self.do_process(request, iconik, b2_storage, ll_storage, format_names)

    def do_process(self, request, iconik, b2_storage, ll_storage, format_names):
        start_time = time.perf_counter()
        self._logger.log("DEBUG", "Processor started")

        if request["action"] == "add":
            # Copy files to LucidLink
            iconik.copy_files(request=request,
                              format_names=format_names,
                              target_storage_id=ll_storage["id"],
                              sync=self._testing)
        elif request["action"] == "remove":
            # Copy any original files to B2, waiting for job(s) to complete
            if iconik.copy_files(request=request,
                                 format_names=[format_names[0]],
                                 target_storage_id=b2_storage["id"],
                                 sync=True):
                # Delete files from LucidLink
                iconik.delete_files(request=request,
                                    format_names=format_names,
                                    storage_id=ll_storage["id"])

        self._logger.log("DEBUG", f"Processor complete in {(time.perf_counter() - start_time):.3f} seconds")


def check_environment_variables(names):
    for name in names:
        if name not in os.environ:
            raise ValueError(f'Environment variable {name} must be set')


def fix_formats(formats):
    """
    Just in case the user did something like `--formats 'ORIGINAL, EDIT_PROXY'`
    """
    return ','.join([f.strip() for f in formats.split(',')])

def formats_match(formats, query_params):
    return ((not formats and 'formats' not in query_params)
            or (formats and 'formats' in query_params and [formats] == query_params['formats']))
