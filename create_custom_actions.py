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
        description="Add custom actions to iconik for the plugin"
    )
    parser.add_argument("--endpoint", type=str, nargs=1,
                        help="your function's endpoint url")
    parser.add_argument("--b2_storage_id", type=str, nargs='+',
                        help="the ID of the B2 storage in iconik")
    parser.add_argument("--ll_storage_id", type=str, nargs='+',
                        help="the ID of the LucidLink storage in iconik")
    args = parser.parse_args()

    if not args.endpoint or not args.b2_storage_id or not args.ll_storage_id:
        parser.print_usage()
        parser.exit(1)

    query_params = f"?b2_storage_id={args.b2_storage_id[0]}" if len(args.b2_storage_id) == 1 else ""
    if len(args.ll_storage_id) == 1:
        query_params += "&" if len(query_params) > 0 else "?"
        query_params += f"ll_storage_id={args.ll_storage_id[0]}"

    iconik = Iconik(os.environ["ICONIK_ID"], os.environ["ICONIK_TOKEN"])

    for operation in OPERATIONS:
        for context in CONTEXTS:
            title = operation["title"]
            print(f"Creating '{title}' action for '{context}'")
            iconik.add_action(context,
                              os.environ["ICONIK_ID"],
                              urljoin(args.endpoint[0], operation["path"]) + query_params,
                              title,
                              os.environ["BZ_SHARED_SECRET"])


if __name__ == "__main__":
    main()
