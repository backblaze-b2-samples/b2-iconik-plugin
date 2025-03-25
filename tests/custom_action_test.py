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

from urllib.parse import urlparse, parse_qs

import pytest

from b2_iconik_plugin.common import formats_match
from b2_iconik_plugin.create_custom_actions import main as create_custom_actions, CONTEXTS
from b2_iconik_plugin.delete_custom_actions import main as delete_custom_actions
from b2_iconik_plugin.iconik import Iconik
from tests.integration_test import B2_STORAGE_ID, LL_STORAGE_ID, ICONIK_ID, ICONIK_TOKEN, assert_environment_variables

TEST_URL = 'http://1.2.3.4/'

ACTION_ARGS = [
    (
        # Use different URLs so we know which is which when we are checking that actions exist!
        'http://4.3.2.1',
        B2_STORAGE_ID,
        LL_STORAGE_ID,
        None,
        "Add to LucidLink",
        "Remove from LucidLink",
        None,
    ),
    (
        'http://4.3.2.2',
        B2_STORAGE_ID,
        LL_STORAGE_ID,
        "ORIGINAL",
        "Add original file(s) to LucidLink",
        "Remove original file(s) from LucidLink",
        None,
    ),
    (
        'http://4.3.2.3',
        B2_STORAGE_ID,
        LL_STORAGE_ID,
        "ORIGINAL,PPRO_PROXY",
        "Add original, Premiere Pro proxy file(s) to LucidLink",
        "Remove original, Premiere Pro proxy file(s) from LucidLink",
        None,
    ),
    (
        'http://4.3.2.4',
        B2_STORAGE_ID,
        LL_STORAGE_ID,
        "ORIGINAL,EDIT_PROXY",
        "Add original, edit proxy file(s) to LucidLink",
        "Remove original, edit proxy file(s) from LucidLink",
        None,
    ),
]


def find_custom_actions(iconik, url, b2_storage_id, ll_storage_id, formats, add_title, remove_title):
    found = {}
    for action in iconik.get_custom_actions():
        if action["url"].startswith(url):
            url = urlparse(action["url"])
            query_params = parse_qs(url.query)
            if ([b2_storage_id] == query_params['b2_storage_id']
                    and [ll_storage_id] == query_params['ll_storage_id']
                    and formats_match(formats, query_params)):
                if url.path.endswith('add'):
                    assert action["title"] == add_title
                else:
                    assert action["title"] == remove_title
                found[action["context"]] = True
    return found


@pytest.mark.integration
@pytest.mark.parametrize("url,b2_storage_id,ll_storage_id,formats,add_title,remove_title,assert_environment_variables",
                         ACTION_ARGS, indirect=['assert_environment_variables'])
def test_create_custom_actions(url, b2_storage_id, ll_storage_id, formats, add_title, remove_title, assert_environment_variables):
    # formats needs to be undefined; otherwise argparse interprets None as the string 'None'
    if formats:
        create_custom_actions([url, b2_storage_id, ll_storage_id, formats])
    else:
        create_custom_actions([url, b2_storage_id, ll_storage_id])

    iconik = Iconik(ICONIK_ID, ICONIK_TOKEN)

    found = find_custom_actions(iconik, url, b2_storage_id, ll_storage_id, formats, add_title, remove_title)

    assert all(found[context] for context in CONTEXTS)


def test_create_custom_actions_missing_args():
    with pytest.raises(SystemExit):
        create_custom_actions([TEST_URL, B2_STORAGE_ID])

    with pytest.raises(SystemExit):
        create_custom_actions([TEST_URL])

    with pytest.raises(SystemExit):
        create_custom_actions([])


@pytest.mark.integration
@pytest.mark.parametrize("url,b2_storage_id,ll_storage_id,formats,add_title,remove_title,assert_environment_variables",
                         ACTION_ARGS, indirect=['assert_environment_variables'])
def test_delete_custom_actions(url, b2_storage_id, ll_storage_id, formats, add_title, remove_title, assert_environment_variables):
    # formats needs to be undefined; otherwise argparse interprets None as the string 'None'
    if formats:
        delete_custom_actions([url, formats])
    else:
        delete_custom_actions([url])

    iconik = Iconik(ICONIK_ID, ICONIK_TOKEN)

    found = find_custom_actions(iconik, url, b2_storage_id, ll_storage_id, formats, add_title, remove_title)

    assert 0 == len(found)


def test_delete_custom_actions_missing_args():
    with pytest.raises(SystemExit):
        delete_custom_actions([])
2
