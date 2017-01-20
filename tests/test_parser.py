# -*- coding: utf-8 -*-

from __future__ import absolute_import

import pytest

from takayi.parser import Parser
from takayi.exc import ParseTypeError, InvalidHintsError


@pytest.fixture
def parser():
    return Parser()


def test_parse(parser):

    def func(x):
        # type: (int) -> int
        return x

    assert parser.parse(func) == {'args': 'int', 'return': 'int'}

    def a_test_func(x, y):
        # type: (int, int) -> int
        return x + y

    def another_test_func(x, y, z):
        # type: (int, str, int) -> int, str
        return 'hello worlr'

    assert parser.parse(a_test_func) == {'args': 'int, int', 'return': 'int'}
    assert parser.parse(another_test_func) == \
        {'args': 'int, str, int', 'return': 'int, str'}

    def error_test_func(x):
        # type: str -> (str)
        return x

    with pytest.raises(ParseTypeError):
        parser.parse(error_test_func)

    def invalid_hints(x, y):
        # hahah
        return None

    with pytest.raises(InvalidHintsError):
        parser.parse(invalid_hints)
