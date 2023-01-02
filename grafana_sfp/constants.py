ALERT_TIMERANGE_FROM = 600
ALERT_TIMERANGE_TO = 0

GRAFANA_ALERT_CONFIGMAP_PREFIX = 'grafana-'
GRAFANA_ALERT_EXPRESSION_DATASOURCE_UID = '-100'
GRAFANA_ELASTICSEARCH_QUERY_TIMESTAMP_FIELD = '@timestamp'

CONFIGMAP_ALERT_CONFIG_KEY = 'rules.yaml'

COMPARISON_OPERATOR_MAPPING = {
    '<': 'lt',
    '>': 'gt',
    '<>': 'within_range',
    '><': 'outside_range',
    'gt': 'gt',
    'lt': 'lt',
    'in': 'within_range',
    'not_in': 'outside_range',
}
