from gcp import GcpLogger, get_project_id, get_secret, gcp_processor
from common import iconik_handler, SHARED_SECRET_NAME


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
    return iconik_handler(
        req,
        GcpLogger(project_id),
        gcp_processor,
        get_secret(project_id, SHARED_SECRET_NAME)
    )
