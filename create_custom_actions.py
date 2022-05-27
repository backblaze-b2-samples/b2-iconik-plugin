import argparse
import os
import requests

from dotenv import load_dotenv
from functools import reduce

ICONIK_ASSETS_API = "https://app.iconik.io/API/assets/v1"

CONTEXTS = ["ASSET", "COLLECTION", "BULK"]
OPERATIONS = [
    {
        "title": "Add to LucidLink",
        "path": "/add"
    },
    {
        "title": "Remove from LucidLink",
        "path": "/remove"
    }
]


def urljoin(*args):
    """
    Utility function to combine parts of a URL in a sane way
    """
    return reduce(
        lambda a, b: (a.rstrip('/') + '/' + b.lstrip('/')), 
        args
    ) if args else ''


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Add custom actions to iconik for your Google Cloud function"
    )
    parser.add_argument("endpoint", type=str,
                        help="your function's endpoint url")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({
        "App-ID": os.environ["ICONIK_ID"],
        "Auth-Token": os.environ["ICONIK_TOKEN"]
    })

    for operation in OPERATIONS:
        for context in CONTEXTS:
            action = {
                "type": "POST",
                "context": context,
                "title": operation["title"],
                "url": urljoin(args.endpoint, operation["path"]),
                "headers": {
                    "x-bz-secret": os.environ["BZ_SHARED_SECRET"]
                }
            }

            print(f"Creating '{operation['title']}' action for '{context}'")
            response = session.post(
                f"{ICONIK_ASSETS_API}/custom_actions/{context}/",
                json=action
            )
            response.raise_for_status()


if __name__ == "__main__":
    main()
