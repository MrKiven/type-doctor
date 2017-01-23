# -*- coding: utf-8 -*-

import inspect
import re
import functools

from takayi.exc import ParseTypeError, InvalidHintsError

"""
    def ham(x, y):
        # type: (int, str) -> str
        # docstring here

    parse first line of docstring:
        type: (int, str) -> str

"""

START = 'start'

parse_pattern = re.compile(r'''
    (?P<{}>[# type:]+)\(
    (?P<args>[\w+, ]+)\).?->.?
    (?P<return>[\w+, ]*)
    '''.format(START), re.X)


_transmit_mapping = {
    'int': int,
    'str': str,
    'dict': dict,
    'set': set,
    'any': (int, str, dict, set)
}


class TypeHints(object):

    def __init__(self, func_name, arg_types, return_types):
        self.func_name = func_name
        self.arg_types = arg_types
        self.return_types = return_types

    @property
    def args(self):
        return map(lambda t: _transmit_mapping[t], self.arg_types)

    @property
    def returns(self):
        return map(lambda t: _transmit_mapping[t], self.return_types)

    @property
    def typehints(self):
        return self

    def __str__(self):
        """
        e.g. test(int, int) -> int
        """
        args = ''
        returns = ''
        for arg in self.arg_types:
            args += ''.join((arg, ', '))
        for ret in self.return_types:
            returns += ''.join((ret, ', '))
        # also remove the space
        return self.func_name + '(' + args[:-2] + ')' + ' -> ' + returns[:-2]

    def __repr__(self):
        return str(self)


def typehints(parser):
    def _(func):
        @functools.wraps(func)
        def __(*args):
            hints = parser.parse(func, deco=True)
            actually_args = map(lambda x: type(x), args)
            assert actually_args == hints.args, \
                "Parameter err: except => {}, actually => {}".format(
                    hints.args, actually_args)

            ret = func(*args)
            try:
                iter(ret)
                actually_returns = map(lambda x: type(x), ret)
            except TypeError:
                actually_returns = map(lambda x: type(x), [ret])
            assert actually_returns == hints.returns, \
                "Return err: except => {}, actually => {}".format(
                    hints.returns, actually_returns)

            return ret
        return __
    return _


class Parser(object):

    def __init__(self, pattern=parse_pattern):
        self._start = START
        self.pattern = pattern

    def parse(self, func, deco=False):
        """Parse first line of 'docstring'

        :param func: function to parse
        :param deco: Only use when using `typehints` decorator
        :return: :class:`TypeHints`
        """
        line = 2 if deco else 1
        type_docs = inspect.getsourcelines(func)[0][line].strip()
        if not type_docs.startswith('# type:'):
            raise InvalidHintsError("First line must be start like: `# type:`")
        drafts = self._match_types(type_docs)
        return self._parse(func.__name__, drafts)

    def _parse(self, name, t_d):
        if 'args' not in t_d and 'return' not in t_d:
            raise ParseTypeError("Parse err: %s" % t_d)
        args_types = [t.strip() for t in t_d['args'].split(',')]
        return_types = [t.strip() for t in t_d['return'].split(',')]
        return TypeHints(name, args_types, return_types)

    def _match_types(self, type_docs):
        """Match given string.

        :return: a dict, e.g.
            {'args': 'int, int', 'return': 'int'}
        """
        match = self.pattern.match(type_docs)
        result = None
        try:
            result = match.groupdict()
            if self._start in result:
                # useless key: `start`, pop it
                result.pop(self._start)
            return result
        except KeyError:
            return result
        except BaseException:
            raise ParseTypeError("Invalid type hints: {!r} ".format(type_docs))
