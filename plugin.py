# Flask application
# Run with
# $ flask --app plugin.py run

import os

# Never put credentials in your code!
from dotenv import load_dotenv
from flask import Flask, request as flask_request
from flask_restful import Resource, Api
from common import iconik_handler
from logger import Logger
from multiprocessing import Process, set_start_method

_called_from_test = False


class Plugin(Resource):
    def __init__(self):
        load_dotenv()
        self.bz_shared_secret = os.environ['BZ_SHARED_SECRET']
        self.logger = Logger()

    def post(self, operation):
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

        Returns:
            The response text, or any set of values that can be turned into a
            Response object using `make_response`
            <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
        """
        return iconik_handler(flask_request, self.logger, app_processor, self.bz_shared_secret)


def app_processor(process_request, request, logger, iconik, b2_storage, ll_storage):
    if _called_from_test:
        # Process request synchronously so we can check results
        process_request(request, logger, iconik, b2_storage, ll_storage)
    else:
        # Start a subprocess
        p = Process(target=process_request, args=(request, logger, iconik, b2_storage, ll_storage))
        p.start()


def create_app():
    # We don't spawn subprocesses when running tests
    if not _called_from_test:
        # Allow subprocess to run after request is handled
        # See https://github.com/benoitc/gunicorn/issues/2322#issuecomment-619910669
        set_start_method('spawn')

    plugin_app = Flask(__name__)
    api = Api(plugin_app)

    api.add_resource(Plugin, '/<operation>')

    return plugin_app


app = create_app()
