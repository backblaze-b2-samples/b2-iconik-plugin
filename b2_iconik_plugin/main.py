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

from b2_iconik_plugin.common import IconikHandler, SHARED_SECRET_NAME
from b2_iconik_plugin.gcp import GcpLogger, get_project_id, get_secret


def gcp_iconik_handler(req):
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
    handler = IconikHandler(GcpLogger(project_id), get_secret(project_id, SHARED_SECRET_NAME))

    return handler.post(req)
