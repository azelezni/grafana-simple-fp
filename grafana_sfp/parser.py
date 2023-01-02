from pyparsing import *
from pyparsing.common import pyparsing_common as pc

from grafana_sfp.enum_types import AlertReduceMode


class ExpressionParser:
    left_par: Suppress
    right_par: Suppress
    colon: Suppress
    equal: Suppress
    min: And
    max: And
    mean: And
    sum: And
    count: And
    last: And
    reduce_mode: Word
    comparison_operator: Group
    for_duration: Group
    reduce_function: Group
    threshold: Group
    parser: Group
    _result: ParseResults

    def __init__(self) -> None:
        super().__init__()
        self.left_par, self.right_par, self.colon, self.equal = map(Suppress, '():=')
        self.reduce_mode = one_of(f'{AlertReduceMode.DROPNN.value} {AlertReduceMode.REPLACENN.value}') + self.equal + Word(alphanums)
        self.min, self.max, self.mean, self.sum, self.count, self.last = map(
            self.get_reduce_function, 'min max mean sum count last'.split()
        )
        self.comparison_operator = Group(one_of('< > <> >< gt lt in not_in'))('comparison')
        self.for_duration = Suppress('for') + Group(self.left_par + Word(alphanums) + self.right_par)('for')
        self.reduce_function = Group(self.min | self.max | self.mean | self.sum | self.count | self.last)('reduce')
        self.threshold = Group(Group(pc.integer + self.colon + pc.integer) | pc.integer)('threshold')
        self.parser = self.reduce_function + self.comparison_operator + self.threshold + Optional(self.for_duration)

    def get_reduce_function(self, name) -> Group:
        return Word(name) + Group(self.left_par + Optional(delimited_list(pc.integer | self.reduce_mode)) + self.right_par)

    def parse_expression(self, expression: str) -> ParseResults:
        return self.parser.parse_string(expression)
