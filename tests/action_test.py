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
import os
from unittest import mock

import pytest

from b2_iconik_plugin.common import check_environment_variables, fix_formats
from b2_iconik_plugin.create_custom_actions import make_title

TITLES = [
    ("Add to LucidLink", [], "Add to LucidLink"),
    ("Add to LucidLink", "ORIGINAL", "Add original file(s) to LucidLink"),
    ("Add to LucidLink", "ORIGINAL,PPRO_PROXY", "Add original, Premiere Pro proxy file(s) to LucidLink"),
    ("Add to LucidLink", "EDIT_PROXY", "Add edit proxy file(s) to LucidLink"),
    ("Add to LucidLink", "ORIGINAL,PPRO_PROXY,EDIT_PROXY", "Add original, Premiere Pro proxy, edit proxy file(s) to LucidLink"),
    ("Add to LucidLink", "FOO", "Add FOO file(s) to LucidLink"),
    ("Add to LucidLink", "FOO,ORIGINAL", "Add FOO, original file(s) to LucidLink"),
]

ENV_VARS = [
    ([], {"FOO": "1"}, None),
    (["FOO"], {"FOO": "1"}, None),
    (["FOO"], {"FOO": "1", "BAR": "2"}, None),
    (["FOO"], {}, ValueError),
    (["FOO"], {"BAR": "2"}, ValueError),
    (["FOO", "BAR"], {"FOO": "1", "BAR": "2"}, None),
]

FORMATS = [
    ("A", "A"),
    ("A", " A"),
    ("A", "A "),
    ("A", " A "),
    ("A,B", "A , B"),
    ("A,B", " A , B "),
    ("A,B,C", "A,B,C"),
    ("A,B,C", " A , B, C "),
]


# From https://stackoverflow.com/a/77256931/33905
@pytest.fixture(scope="function")
def environment(monkeypatch, request):
    with mock.patch.dict(os.environ, clear=True):
        for k, v in request.param.items():
            monkeypatch.setenv(k, v)
        yield # This is the magical bit which restore the environment after


@pytest.mark.parametrize("title_in,formats,title_out", TITLES)
def test_make_title(title_in, formats, title_out):
    assert title_out == make_title(title_in, formats)


# From https://stackoverflow.com/a/33879151/33905
@pytest.mark.parametrize("vars,environment,err", ENV_VARS, indirect=["environment"])
def test_check_environment_variables(vars, environment, err):
    if err:
        with pytest.raises(err):
            check_environment_variables(vars)
    else:
        check_environment_variables(vars)


@pytest.mark.parametrize("expected,formats", FORMATS)
def test_fix_formats(expected, formats):
    assert expected == fix_formats(formats)
