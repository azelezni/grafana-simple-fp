import logging

import yaml

from kubernetes.client.models import V1ConfigMapList, V1ConfigMap
from kubernetes.client import V1ObjectMeta, exceptions
from kubernetes import config, client, watch
from kubernetes.client.api import CoreV1Api

from grafana_sfp.constants import GRAFANA_ALERT_CONFIGMAP_PREFIX, CONFIGMAP_ALERT_CONFIG_KEY
from grafana_sfp.enum_types import KubernetesEventTypes
from grafana_sfp.runner.base import BaseRunner


logger = logging.getLogger('grafana-simple-fp')


class ClusterRunner(BaseRunner):
    label_selector: str
    target_labels: dict[str, str]
    v1_client: CoreV1Api

    def __init__(self, label_selector: dict, target_labels: dict):
        try:
            config.load_kube_config()
        except config.config_exception.ConfigException:
            config.load_incluster_config()
        super().__init__()
        self.label_selector = ','.join([f'{label_key}={label_value}' for label_key, label_value in label_selector.items()])
        self.target_labels = target_labels
        self.v1_client = client.CoreV1Api()

    def load_config(self, **kwargs) -> None:
        logger.debug(f'getting configmaps with labels: {self.label_selector}')
        configmaps: V1ConfigMapList = self.v1_client.list_config_map_for_all_namespaces(label_selector=self.label_selector, **kwargs)
        for configmap in configmaps.items:
            key: str = f'{configmap.metadata.namespace}/{configmap.metadata.name}'
            try:
                self.alert_config[key] = yaml.safe_load(configmap.data[CONFIGMAP_ALERT_CONFIG_KEY])
            except yaml.YAMLError:
                logger.exception(f'Something went wrong when trying to read configmap {key}')

    def save_config(self) -> None:
        namespace: str
        name: str
        metadata: V1ObjectMeta
        configmap: V1ConfigMap
        out: dict[str, dict] = self.alert_groups_to_dict()

        for cm_name, conf in out.items():
            namespace, name = cm_name.split('/')
            metadata = V1ObjectMeta(name=f'{GRAFANA_ALERT_CONFIGMAP_PREFIX}{name}', namespace=namespace, labels=self.target_labels)

            configmap = client.V1ConfigMap(
                api_version='v1',
                kind='ConfigMap',
                metadata=metadata,
                data={
                    f'{name}-{CONFIGMAP_ALERT_CONFIG_KEY}': yaml.dump(conf)
                }
            )

            logger.debug(f'saving converted alert-config from configmap {name} to {GRAFANA_ALERT_CONFIGMAP_PREFIX}{name} in namespace {namespace}')
            try:
                self.v1_client.create_namespaced_config_map(namespace=namespace, body=configmap)
            except exceptions.ApiException:
                self.v1_client.replace_namespaced_config_map(
                    name=f'{GRAFANA_ALERT_CONFIGMAP_PREFIX}{name}',
                    namespace=namespace,
                    body=configmap
                )

    def watch(self) -> None:
        w: watch.Watch = watch.Watch()
        configmap: V1ConfigMap
        name: str
        namespace: str
        watch_args = dict(
            func=self.v1_client.list_config_map_for_all_namespaces,
            label_selector=self.label_selector
        )

        for event in w.stream(**watch_args):
            configmap = event['object']
            name = configmap.metadata.name
            namespace = event['object'].metadata.namespace

            if event['type'] == KubernetesEventTypes.DELETED.value:
                self.v1_client.delete_namespaced_config_map(
                    name=f'{GRAFANA_ALERT_CONFIGMAP_PREFIX}{name}',
                    namespace=namespace
                )
            else:
                self.load_and_convert(field_selector=f'metadata.name={name}')
                self.save_config()
