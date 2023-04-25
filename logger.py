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
            severity (str): "INFO", "DEBUG", "ERROR" etc
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

