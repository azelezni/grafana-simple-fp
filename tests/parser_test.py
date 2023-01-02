import unittest

import pytest
from pyparsing.exceptions import ParseBaseException

from grafana_sfp.parser import ExpressionParser


class ParserTest(unittest.TestCase):
    valid_expressions: dict = {
        'last(dropNN=true) > 0 for(60s)': {
            'reduce': ['last', ['dropNN', 'true']],
            'comparison': ['>'],
            'threshold': [0],
            'for': ['60s']
        },
        'last(dropNN=true) gt 0 for(60s)': {
            'reduce': ['last', ['dropNN', 'true']],
            'comparison': ['gt'],
            'threshold': [0],
            'for': ['60s']
        },
        'last(replaceNN=3) < 0 for(30m)': {
            'reduce': ['last', ['replaceNN', '3']],
            'comparison': ['<'],
            'threshold': [0],
            'for': ['30m']
        },
        'last(replaceNN=3) lt 0 for(30m)': {
            'reduce': ['last', ['replaceNN', '3']],
            'comparison': ['lt'],
            'threshold': [0],
            'for': ['30m']
        },
        'sum() <> 0:10': {
            'reduce': ['sum', []],
            'comparison': ['<>'],
            'threshold': [[0, 10]]
        },
        'sum() in 0:10': {
            'reduce': ['sum', []],
            'comparison': ['in'],
            'threshold': [[0, 10]]
        },
        'mean() >< 0:10 for(1d)mean() not_in 0:10 for(1d)': {
            'reduce': ['mean', []],
            'comparison': ['><'],
            'threshold': [[0, 10]], 'for': ['1d']
        }
    }

    invalid_expressions: dict = {
        'last(drop_nn=true) > 0 for(60s)': {},
        'last(replace_nn=3) < 0 for(30m)': {},
        'last(replace_nn=abc) < 0 for(30m)': {},
        'sum() lower_then 1': {},
        'avg() > 0 for(60s)': {},
        'last() > 0 for 60s': {},
        'last() > 0 for(60)': {}
    }

    def test_valid(self):
        parser = ExpressionParser()

        for exp, result in self.valid_expressions.items():
            data = parser.parse_expression(exp).asDict()
            assert data == result

    def test_invalid(self):
        parser = ExpressionParser()

        with pytest.raises(ParseBaseException):
            for exp, result in self.invalid_expressions.items():
                parser.parse_expression(exp).asDict()

    def test_all(self):
        self.test_valid()
        self.test_invalid()


if __name__ == '__main__':
    unittest.main()
