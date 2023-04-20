from google.cloud import secretmanager

import google_crc32c
import json
import requests

GCP_PROJECT_ID_URL = "http://metadata.google.internal/computeMetadata/v1/project/project-id"


class SecretError(Exception):
    pass


def get_project_id():
    """
    Get the project id from Google Cloud
    Returns:
        A project id
    """
    response = requests.get(
        GCP_PROJECT_ID_URL,
        headers={"Metadata-Flavor": "Google"})
    response.raise_for_status()
    return response.text


def get_secret(project_id, secret_id):
    """
    Get a secret from the Google Cloud Secret Manager
    Args:
        project_id (str): The Google Cloud Function project id
        secret_id (str): The secret id
    Returns:
        A secret
    """
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise SecretError("CRC check failed")

    return response.payload.data.decode("UTF-8")


class GcpLogger:
    def __init__(self, project_id):
        self.project_id = project_id

    def log(self, severity, message, req=None):
        """
        Emit a structured log message
        Args:
            severity (str): "INFO", "DEBUG", "ERROR" etc
            message (str): The message to log
            req (flask.Request): The request object.
            <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
        """

        # Trace header code from
        # https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
        global_log_fields = {}

        request_is_defined = "request" in globals() or "request" in locals()
        if request_is_defined and request:
            trace_header = request.headers.get("X-Cloud-Trace-Context")

            if trace_header:
                trace = trace_header.split("/")
                global_log_fields[
                    "logging.googleapis.com/trace"
                ] = f"projects/{self.project_id}/traces/{trace[0]}"

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

        entry = global_log_fields | http_request | {
            "severity": severity,
            "message": message
        }

        print(json.dumps(entry))


def gcp_processor(process_request, request, logger, iconik, b2_storage, ll_storage):
    process_request(request, logger, iconik, b2_storage, ll_storage)
