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

import argparse
import os

from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv

from b2_iconik_plugin.common import fix_formats, formats_match
from b2_iconik_plugin.iconik import Iconik


def main(argv=None):
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Remove your plugin's custom actions from iconik"
    )
    parser.add_argument("endpoint", type=str,
                        help="your function's endpoint url")
    parser.add_argument("formats", type=str, nargs='?',
                        help="a comma-separated list of iconik asset formats")
    args = parser.parse_args(argv)

    if not args.endpoint:
        parser.print_usage()
        parser.exit(1)

    formats = fix_formats(args.formats) if args.formats else None

    iconik = Iconik(os.environ["ICONIK_ID"], os.environ["ICONIK_TOKEN"])

    for action in iconik.get_custom_actions():
        if action["url"].startswith(args.endpoint):
            url = urlparse(action["url"])
            query_params = parse_qs(url.query)
            if formats_match(formats, query_params):
                print(f"Deleting '{action['title']}' action for '{action['context']}'")
                iconik.delete_action(action)


if __name__ == "__main__":
    main()
