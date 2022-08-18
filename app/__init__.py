import os

# Never put credentials in your code!
from dotenv import load_dotenv
from flask import Flask, request
from flask_restful import Resource, Api
from common import iconik_handler

from logger import Logger


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
        return iconik_handler(request, self.logger, self.bz_shared_secret)


def create_app():
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(Plugin, '/<operation>')

    return app


app = create_app()
