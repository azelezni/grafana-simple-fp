from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Union, Optional

from grafana_sfp.enum_types import AlertReduceMode
from grafana_sfp.parser import ExpressionParser


logger = logging.getLogger('grafana-simple-fp')


@dataclass
class AlertConditionReduce:
    function: str
    mode: AlertReduceMode
    mode_param: Optional[Union[bool, int]]


@dataclass
class AlertCondition:
    reduce_function: AlertConditionReduce
    comparison_operator: str
    threshold: list[str]
    for_duration: str

    @classmethod
    def from_expression(cls, expression: str) -> AlertCondition:
        parser = ExpressionParser()
        condition_config = parser.parse_expression(expression).asDict()
        try:
            reduce_function = AlertConditionReduce(
                function=condition_config['reduce'][0],
                mode=AlertReduceMode[condition_config['reduce'][1][0].upper()],
                mode_param=condition_config['reduce'][1][1]
            )
        except IndexError:
            reduce_function = AlertConditionReduce(
                function=condition_config['reduce'][0],
                mode=AlertReduceMode.STRICT,
                mode_param=None
            )

        try:
            for_duration = condition_config['for'][0]
        except KeyError:
            for_duration = 0

        if type(condition_config['threshold'][0]) is int:
            threshold = [condition_config['threshold'][0]]
        else:
            threshold = condition_config['threshold'][0]

        return cls(
            reduce_function=reduce_function,
            comparison_operator=condition_config['comparison'][0],
            threshold=threshold,
            for_duration=for_duration
        )
