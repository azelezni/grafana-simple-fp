from __future__ import annotations

import dataclasses
import enum
import hashlib
import logging

from grafana_sfp.alert.config import AlertGroupConfig, AlertConfig, AlertQueryConfig, AlertQueryConfigTypes
from grafana_sfp.enum_types import AlertExecErrState, AlertNoDataState, RelativeTimeRange
from grafana_sfp.alert.condition import AlertCondition
from grafana_sfp.enum_types import AlertReduceMode
from grafana_sfp.constants import *


logger = logging.getLogger('grafana-simple-fp')


class GrafanaExpressionDataModelTypes(enum.Enum):
    REDUCE = 'reduce'
    THRESHOLD = 'threshold'


class GrafanaExpressionConditionModelTypes(enum.Enum):
    QUERY = 'query'


class ElasticSearchQueryDataModelBucketAggsTypes(enum.Enum):
    DATE_HISTOGRAM = 'date_histogram'
    HISTOGRAM = 'histogram'
    TERMS = 'terms'
    FILTERS = 'filters'


@dataclasses.dataclass
class GrafanaExpressionCondition:
    type_: str
    params: list[str]

    def to_dict(self) -> dict:
        return dict(
            type=self.type_,
            params=self.params
        )


@dataclasses.dataclass
class GrafanaExpressionConditionModel:
    type_: GrafanaExpressionConditionModelTypes
    evaluator: GrafanaExpressionCondition

    @classmethod
    def from_alert_condition(cls, type_: GrafanaExpressionConditionModelTypes,
                             alert_condition: AlertCondition) -> GrafanaExpressionConditionModel:
        if type_ == GrafanaExpressionConditionModelTypes.QUERY:
            evaluator = GrafanaExpressionCondition(
                type_=COMPARISON_OPERATOR_MAPPING[alert_condition.comparison_operator],
                params=alert_condition.threshold
            )
            return cls(
                type_=GrafanaExpressionConditionModelTypes.QUERY,
                evaluator=evaluator
            )

    def to_dict(self) -> dict:
        return dict(
            type=self.type_,
            evaluator=self.evaluator
        )


@dataclasses.dataclass
class GrafanaExpressionDataModelSettings:
    mode: AlertReduceMode
    replace_with_value: int | None

    @classmethod
    def from_alert_condition(cls, alert_condition: AlertCondition) -> GrafanaExpressionDataModelSettings:
        if alert_condition.reduce_function.mode in (AlertReduceMode.DROPNN, AlertReduceMode.STRICT):
            return cls(
                mode=alert_condition.reduce_function.mode,
                replace_with_value=None
            )
        elif alert_condition.reduce_function.mode == AlertReduceMode.REPLACENN:
            return cls(
                mode=alert_condition.reduce_function.mode,
                replace_with_value=int(alert_condition.reduce_function.mode_param)
            )
        else:
            raise NotImplementedError(f'Reduce mode {alert_condition.reduce_function.mode.value} is not supported')

    def to_dict(self) -> dict:
        return dict(
            mode=self.mode,
            replaceWithValue=self.replace_with_value
        )


@dataclasses.dataclass
class GrafanaExpressionDataModel:
    type_: GrafanaExpressionDataModelTypes
    expression: str
    reducer: str | None
    conditions: list[GrafanaExpressionConditionModel] | None
    settings: GrafanaExpressionDataModelSettings | None

    @property
    def type(self):
        return self.type_

    @classmethod
    def from_alert_condition(cls, model_type: GrafanaExpressionDataModelTypes,
                             alert_query_data: GrafanaAlertRuleData,
                             alert_condition: AlertCondition) -> GrafanaExpressionDataModel:
        if model_type == GrafanaExpressionDataModelTypes.REDUCE:
            settings = GrafanaExpressionDataModelSettings.from_alert_condition(
                alert_condition=alert_condition
            )
            return cls(
                type_=GrafanaExpressionDataModelTypes.REDUCE,
                expression=alert_query_data.ref_id,
                reducer=alert_condition.reduce_function.function,
                conditions=None,
                settings=settings
            )
        elif model_type == GrafanaExpressionDataModelTypes.THRESHOLD:
            conditions = GrafanaExpressionConditionModel.from_alert_condition(
                type_=GrafanaExpressionConditionModelTypes.QUERY,
                alert_condition=alert_condition
            )
            return cls(
                type_=GrafanaExpressionDataModelTypes.THRESHOLD,
                expression=alert_query_data.ref_id,
                reducer=None,
                conditions=[conditions],
                settings=None
            )

    def to_dict(self) -> dict:
        return dict(
            type=self.type_,
            expression=self.expression,
            reducer=self.reducer,
            conditions=self.conditions,
            settings=self.settings
        )


@dataclasses.dataclass
class PrometheusQueryDataModel:
    expr: str
    range_: bool

    @classmethod
    def from_alert_query_config(cls, alert_query_config: AlertQueryConfig) -> PrometheusQueryDataModel:
        return cls(
            expr=alert_query_config.expression,
            range_=True
        )

    def to_dict(self) -> dict:
        return dict(
            expr=self.expr,
            range=self.range_
        )


@dataclasses.dataclass
class ElasticSearchQueryDataModelBucketAggsSettings:
    interval: str

    def to_dict(self) -> dict:
        return dict(
            interval=self.interval
        )


@dataclasses.dataclass
class ElasticSearchQueryDataModelBucketAggs:
    field: str
    id_: str
    settings: ElasticSearchQueryDataModelBucketAggsSettings
    type_: ElasticSearchQueryDataModelBucketAggsTypes

    def to_dict(self) -> dict:
        return dict(
            field=self.field,
            id=self.id_,
            settings=self.settings,
            type=self.type_
        )


@dataclasses.dataclass
class ElasticSearchQueryDataModelMetrics:
    id_: str
    type_: str

    def to_dict(self) -> dict:
        return dict(
            id=self.id_,
            type=self.type_
        )


@dataclasses.dataclass
class ElasticSearchQueryDataModel:
    alias: str | None
    bucket_aggs: list[ElasticSearchQueryDataModelBucketAggs]
    metrics: list[ElasticSearchQueryDataModelMetrics]
    query: str
    time_field: str

    @classmethod
    def from_alert_query_config(cls, alert_query_config: AlertQueryConfig) -> ElasticSearchQueryDataModel:
        count_metric = ElasticSearchQueryDataModelMetrics(
            id_='1',
            type_='count'
        )
        date_histogram_agg_settings = ElasticSearchQueryDataModelBucketAggsSettings(
            interval='auto'
        )
        date_histogram_agg = ElasticSearchQueryDataModelBucketAggs(
            field=GRAFANA_ELASTICSEARCH_QUERY_TIMESTAMP_FIELD,
            id_='2',
            settings=date_histogram_agg_settings,
            type_=ElasticSearchQueryDataModelBucketAggsTypes.DATE_HISTOGRAM
        )
        return cls(
            alias=None,
            bucket_aggs=[date_histogram_agg],
            metrics=[count_metric],
            query=alert_query_config.expression,
            time_field=GRAFANA_ELASTICSEARCH_QUERY_TIMESTAMP_FIELD
        )

    def to_dict(self) -> dict:
        return dict(
            alias=self.alias,
            bucketAggs=self.bucket_aggs,
            metrics=self.metrics,
            query=self.query,
            timeField=self.time_field
        )


@dataclasses.dataclass
class GrafanaAlertRuleData:
    ref_id: str
    datasource_uid: str
    relative_time_range: RelativeTimeRange
    model: PrometheusQueryDataModel | GrafanaExpressionDataModel

    @classmethod
    def from_alert_query_config(cls, ref_id: str, alert_config: AlertConfig) -> GrafanaAlertRuleData:
        if alert_config.query.type_ == AlertQueryConfigTypes.PROMETHEUS:
            model = PrometheusQueryDataModel.from_alert_query_config(
                alert_query_config=alert_config.query
            )
        elif alert_config.query.type_ == AlertQueryConfigTypes.ELASTICSEARCH:
            model = ElasticSearchQueryDataModel.from_alert_query_config(
                alert_query_config=alert_config.query
            )
        else:
            raise NotImplementedError(f'Query datasource type "{alert_config.query.type_}" is not supported')
        return cls(
            ref_id=ref_id,
            datasource_uid=alert_config.query.datasource,
            relative_time_range=alert_config.timerange,
            model=model
        )

    @classmethod
    def from_alert_condition_config(cls, alert_query_data: GrafanaAlertRuleData, alert_config: AlertConfig) -> list[GrafanaAlertRuleData]:
        alert_condition = AlertCondition.from_expression(alert_config.condition.expression)

        reduce_ref_id = chr(ord(alert_query_data.ref_id) + 1)
        reduce_model = GrafanaExpressionDataModel.from_alert_condition(
            model_type=GrafanaExpressionDataModelTypes.REDUCE,
            alert_query_data=alert_query_data,
            alert_condition=alert_condition
        )
        reduce_data = cls(
            ref_id=reduce_ref_id,
            datasource_uid=GRAFANA_ALERT_EXPRESSION_DATASOURCE_UID,
            relative_time_range=alert_config.timerange,
            model=reduce_model
        )

        threshold_ref_id = chr(ord(alert_query_data.ref_id) + 2)
        threshold_model = GrafanaExpressionDataModel.from_alert_condition(
            model_type=GrafanaExpressionDataModelTypes.THRESHOLD,
            alert_query_data=reduce_data,
            alert_condition=alert_condition
        )
        threshold_data = cls(
            ref_id=threshold_ref_id,
            datasource_uid=GRAFANA_ALERT_EXPRESSION_DATASOURCE_UID,
            relative_time_range=alert_config.timerange,
            model=threshold_model
        )

        return [reduce_data, threshold_data]

    def to_dict(self) -> dict:
        return dict(
            refId=self.ref_id,
            datasourceUid=self.datasource_uid,
            relativeTimeRange=self.relative_time_range,
            model=self.model
        )


@dataclasses.dataclass
class GrafanaAlertRule:
    uid: str  # can't be longer then 40 characters (defined as varying(40) in Grafana)
    title: str
    labels: dict[str, str]
    annotations: dict[str, str]
    condition: str
    for_: str
    no_data_state: AlertNoDataState
    exec_err_state: AlertExecErrState
    data: list[GrafanaAlertRuleData]

    @classmethod
    def from_alert_config(cls, alert_config: AlertConfig) -> GrafanaAlertRule:
        uid = hashlib.sha1(bytes(alert_config.title, 'utf-8')).hexdigest()
        annotations = {
            'Condition': alert_config.condition.expression,
            **alert_config.annotations
        }
        alert_condition = AlertCondition.from_expression(alert_config.condition.expression)
        query_data = GrafanaAlertRuleData.from_alert_query_config(ref_id='A', alert_config=alert_config)
        grafana_expression_data = GrafanaAlertRuleData.from_alert_condition_config(alert_query_data=query_data, alert_config=alert_config)
        condition_data = list(filter(lambda data: data.model.type_ == GrafanaExpressionDataModelTypes.THRESHOLD, grafana_expression_data))[0]

        return cls(
            uid=uid,
            title=alert_config.title,
            labels=alert_config.labels,
            annotations=annotations,
            condition=condition_data.ref_id,
            for_=alert_condition.for_duration,
            no_data_state=alert_config.execution_state.no_data,
            exec_err_state=alert_config.execution_state.exec_err,
            data=[query_data, *grafana_expression_data]
        )

    def to_dict(self) -> dict:
        # Need to use unpacking because of 'for' keyword
        return dict(**{
            'uid': self.uid,
            'title': self.title,
            'labels': self.labels,
            'annotations': self.annotations,
            'condition': self.condition,
            'for': self.for_,
            'noDataState': self.no_data_state,
            'execErrState': self.exec_err_state,
            'data': self.data,
        })


@dataclasses.dataclass
class GrafanaAlertGroup:
    name: str
    folder: str
    interval: str
    rules: list[GrafanaAlertRule]

    @classmethod
    def from_alert_group_config(cls, alert_group_config: AlertGroupConfig) -> GrafanaAlertGroup:
        rules = [GrafanaAlertRule.from_alert_config(rule_config) for rule_config in alert_group_config.rules]
        return cls(
            name=alert_group_config.name,
            folder=alert_group_config.folder,
            interval=alert_group_config.interval,
            rules=rules
        )

    def to_dict(self) -> dict:
        return dict(
            name=self.name,
            folder=self.folder,
            interval=self.interval,
            rules=self.rules
        )
