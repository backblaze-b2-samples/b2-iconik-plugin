import argparse
import os

from dotenv import load_dotenv
from iconik import Iconik, ICONIK_ASSETS_API


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Remove your Google Cloud function's custom actions from iconik"
    )
    parser.add_argument("endpoint", type=str,
                        help="your function's endpoint url")
    args = parser.parse_args()

    iconik = Iconik(os.environ["ICONIK_ID"], os.environ["ICONIK_TOKEN"])

    for action in iconik.get_objects(f"{ICONIK_ASSETS_API}/custom_actions/"):
        if action["url"].startswith(args.endpoint):
            print(f"Deleting '{action['title']}' action for '{action['context']}'")
            iconik.delete_action(action)


if __name__ == "__main__":
    main()
