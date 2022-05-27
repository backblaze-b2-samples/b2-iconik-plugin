import argparse
import os
import requests

from dotenv import load_dotenv
from functools import reduce
from main import get_objects

ICONIK_ASSETS_API = "https://app.iconik.io/API/assets/v1"

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
        description="Remove your Google Cloud function's custom actions from iconik"
    )
    parser.add_argument("endpoint", type=str,
                        help="your function's endpoint url")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({
        "App-ID": os.environ["ICONIK_ID"],
        "Auth-Token": os.environ["ICONIK_TOKEN"]
    })

    for action in get_objects(session, f"{ICONIK_ASSETS_API}/custom_actions/"):
        if action["url"].startswith(args.endpoint):
            print(f"Deleting '{action['title']}' action for '{action['context']}'")
            response = session.delete(
                f"{ICONIK_ASSETS_API}/custom_actions/{action['context']}/{action['id']}"
            )
            response.raise_for_status()        


if __name__ == "__main__":
    main()
