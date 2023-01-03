import abc
import json

from grafana_sfp.grafana.alert import GrafanaAlertGroup, AlertGroupConfig
from grafana_sfp.helpers import ComplexEncoder


class BaseRunner(abc.ABC):
    alert_config: dict
    alert_groups: dict[str, list[GrafanaAlertGroup]]

    def __init__(self):
        self.alert_config = {}
        self.alert_groups = {}

    def alert_configs_to_alert_groups(self) -> None:
        alert_groups_config: dict[str, list[AlertGroupConfig]] = {}

        for path, data in self.alert_config.items():
            alert_groups_config[path] = []
            for group_config in data['groups']:
                alert_groups_config[path].append(AlertGroupConfig.from_dict(group_config))

        for path, data in alert_groups_config.items():
            self.alert_groups[path] = []
            for alert_group_config in data:
                self.alert_groups[path].append(GrafanaAlertGroup.from_alert_group_config(alert_group_config))

    def alert_groups_to_dict(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for name, data in self.alert_groups.items():
            groups = {
                'groups': [group for group in data]
            }
            # There's probably a better way to do this...
            out[name] = json.loads(json.dumps(groups, cls=ComplexEncoder))
        return out

    def load_and_convert(self, **kwargs) -> None:
        self.load_config(**kwargs)
        self.alert_configs_to_alert_groups()

    @abc.abstractmethod
    def load_config(self, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def save_config(self) -> None:
        pass

    @abc.abstractmethod
    def watch(self) -> None:
        pass
