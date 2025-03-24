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
from functools import reduce
from urllib.parse import urlencode

from dotenv import load_dotenv

from b2_iconik_plugin.common import check_environment_variables, fix_formats
from b2_iconik_plugin.iconik import Iconik

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
FORMATS = {
    'ORIGINAL': 'original',
    'PPRO_PROXY': 'Premiere Pro proxy',
    'EDIT_PROXY': 'edit proxy'
}


def urljoin(*args):
    """
    Utility function to combine parts of a URL in a sane way
    """
    return reduce(
        lambda a, b: (a.rstrip('/') + '/' + b.lstrip('/')),
        args
    ) if args else ''


def make_title(title, formats):
    if not formats:
        return title
    (verb, rest) = title.split(maxsplit=1)
    names = ', '.join([FORMATS[f] if f in FORMATS else f for f in formats.split(',')])
    return f'{verb} {names} file(s) {rest}'

def main(argv=None):
    load_dotenv()

    check_environment_variables(['ICONIK_ID', 'ICONIK_TOKEN'])

    parser = argparse.ArgumentParser(
        description="Add custom actions to iconik for the plugin"
    )
    parser.add_argument("endpoint", type=str,
                        help="your function's endpoint url")
    parser.add_argument("b2_storage_id", type=str,
                        help="the ID of the B2 storage in iconik")
    parser.add_argument("ll_storage_id", type=str,
                        help="the ID of the LucidLink storage in iconik")
    parser.add_argument("formats", type=str, nargs='?',
                        help="a comma-separated list of iconik asset formats")
    args = parser.parse_args(argv)

    query_params = { "b2_storage_id": args.b2_storage_id, "ll_storage_id": args.ll_storage_id }
    if args.formats:
        formats = fix_formats(args.formats)
        query_params["formats"] = formats
    else:
        formats = None

    iconik = Iconik(os.environ["ICONIK_ID"], os.environ["ICONIK_TOKEN"])

    for operation in OPERATIONS:
        for context in CONTEXTS:
            title = make_title(operation["title"], formats)
            print(f"Creating '{title}' action for '{context}'")
            iconik.add_action(context,
                              os.environ["ICONIK_ID"],
                              urljoin(args.endpoint, operation["path"]) + "?" + urlencode(query_params),
                              title,
                              os.environ["BZ_SHARED_SECRET"])


if __name__ == "__main__":
    main()
