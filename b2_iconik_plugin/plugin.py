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

# Flask application
# Run with
# $ flask --app plugin.py run

import os
from logging.config import dictConfig
from multiprocessing import Process, set_start_method

# Never put credentials in your code!
from dotenv import load_dotenv
from flask import Flask, request as flask_request
from flask_restx import Resource, Api

import b2_iconik_plugin
from b2_iconik_plugin.common import IconikHandler
from b2_iconik_plugin.logger import Logger

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s.%(msecs)03d, %(levelname)s, %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        },
    },
    'handlers': {
        'stdout': {
            'class': "logging.StreamHandler",
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }
    },
    'root': {
        'handlers': ['stdout'],
        'level': os.getenv('APP_LOG_LEVEL', 'INFO')},
})


class FlaskIconikHandler(IconikHandler):
    """
    Process the request in a subprocess
    """
    def start_process(self, request, iconik, b2_storage, ll_storage):
        if self.is_testing():
            # Process request synchronously so we can check results
            self.do_process(request, iconik, b2_storage, ll_storage)
        else:
            # Start a subprocess
            def process_request(request_, iconik_, b2_storage_, ll_storage_):
                self.do_process(request_, iconik_, b2_storage_, ll_storage_)

            p = Process(
                target=process_request,
                args=(request, iconik, b2_storage, ll_storage)
            )
            p.start()


class Plugin(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handler = kwargs['iconik_handler']

    def post(self, operation):  # noqa
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
        return self._handler.post(flask_request)

def create_app(test_config=None):
    app = Flask(__name__)

    load_dotenv()

    # TODO - check env vars

    if test_config is None:
        # Allow subprocess to run after request is handled
        # See https://github.com/benoitc/gunicorn/issues/2322#issuecomment-619910669
        set_start_method('spawn')
    else:
        # We don't spawn subprocesses when running tests
        app.config.from_mapping(test_config)

    api = Api(app)

    handler = FlaskIconikHandler(Logger(), os.environ['BZ_SHARED_SECRET'], app.config['TESTING'])

    api.add_resource(Plugin, '/<operation>', resource_class_kwargs={'iconik_handler': handler})

    app.logger.info(f"Backblaze B2 Storage Plugin for iconik version {b2_iconik_plugin.__version__} starting.")

    return app
