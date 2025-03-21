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

import json
import logging


class Logger:
    level_map = {
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
        "NOTSET": 0
    }

    @staticmethod
    def log(severity, message, req=None):
        """
        Emit a structured log message
        Args:
            severity (str): "INFO", "DEBUG", "ERROR" etc.
            message : The message to log
            req (flask.Request): The request object.
            <https://flask.pocoo.org/docs/1.0/api/#flask.Request>
        """

        entry = {
            "httpRequest": {
                "requestMethod": req.method,
                "requestUrl": req.url,
                "requestSize": req.content_length,
                "userAgent": req.user_agent.string,
                "remoteIp": req.headers.get("x-forwarded-for"),
                "protocol": req.scheme
            }
        } if req else message

        logging.log(Logger.level_map[severity], json.dumps(entry))
