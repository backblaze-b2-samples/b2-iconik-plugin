import datetime
import json


class Logger:
    def log(self, severity, message, req=None):
        """
        Emit a structured log message
        Args:
            severity (str): "INFO", "DEBUG", "ERROR" etc
            message : The message to log
            req (flask.Request): The request object.
            <https://flask.pocoo.org/docs/1.0/api/#flask.Request>
        """

        http_request = {
            "httpRequest": {
                "requestMethod": req.method,
                "requestUrl": req.url,
                "requestSize": req.content_length,
                "userAgent": req.user_agent.string,
                "remoteIp": req.headers.get("x-forwarded-for"),
                "protocol": req.scheme
            }
        } if req else {}

        entry = http_request | {
            "timestamp": datetime.datetime.now().isoformat(sep=' '),
            "severity": severity,
            "message": message
        }

        print(json.dumps(entry), flush=True)
