import argparse
import os

from dotenv import load_dotenv
from functools import reduce
from iconik import Iconik, ICONIK_ASSETS_API

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

    iconik = Iconik(os.environ["ICONIK_ID"], os.environ["ICONIK_TOKEN"])

    endpoint = args.endpoint

    for operation in OPERATIONS:
        for context in CONTEXTS:
            iconik.add_action(context,
                              urljoin(endpoint, operation["path"]),
                              operation["title"],
                              os.environ["BZ_SHARED_SECRET"])


if __name__ == "__main__":
    main()
