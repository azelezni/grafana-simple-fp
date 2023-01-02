from __future__ import annotations

import dataclasses
import enum
import logging

from grafana_sfp.enum_types import AlertExecErrState, AlertNoDataState, RelativeTimeRange
from grafana_sfp.constants import *


logger = logging.getLogger('grafana-simple-fp')


class AlertQueryConfigTypes(enum.Enum):
    PROMETHEUS = 'prometheus'
    ELASTICSEARCH = 'elasticsearch'


@dataclasses.dataclass
class AlertExecutionStateConfig:
    no_data: AlertNoDataState
    exec_err: AlertExecErrState


@dataclasses.dataclass
class AlertQueryConfig:
    type_: AlertQueryConfigTypes
    datasource: str
    expression: str


@dataclasses.dataclass
class AlertConditionConfig:
    expression: str


# noinspection SpellCheckingInspection
@dataclasses.dataclass
class AlertConfig:
    title: str
    labels: dict[str, str]
    annotations: dict[str, str]
    execution_state: AlertExecutionStateConfig
    timerange: RelativeTimeRange
    query: AlertQueryConfig
    condition: AlertConditionConfig

    @classmethod
    def from_dict(cls, config: dict) -> AlertConfig:
        execution_state = AlertExecutionStateConfig(
            no_data=config.get('execution_state', {}).get('noData', AlertNoDataState.NODATA),
            exec_err=config.get('execution_state', {}).get('execErr', AlertExecErrState.ERROR)
        )

        timerange = RelativeTimeRange(
            from_=config.get('timerange', {}).get('from_', ALERT_TIMERANGE_FROM),
            to_=config.get('timerange', {}).get('to_', ALERT_TIMERANGE_TO)
        )

        query = AlertQueryConfig(
            type_=AlertQueryConfigTypes[config['query']['type'].upper()],
            datasource=config['query']['datasource'],
            expression=config['query']['expression']
        )

        condition = AlertConditionConfig(expression=config['condition']['expression'])

        return cls(
            title=config['title'],
            labels=config['labels'],
            annotations=config['annotations'],
            execution_state=execution_state,
            timerange=timerange,
            query=query,
            condition=condition
        )


@dataclasses.dataclass
class AlertGroupConfig:
    name: str
    folder: str
    interval: str
    rules: list[AlertConfig]

    @classmethod
    def from_dict(cls, config: dict) -> AlertGroupConfig:
        rules = [AlertConfig.from_dict(rule) for rule in config['rules']]
        return cls(
            name=config['name'],
            folder=config['folder'],
            interval=config['interval'],
            rules=rules
        )
