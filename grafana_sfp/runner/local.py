import logging
import os

from glob import glob

import yaml

from grafana_sfp.runner.base import BaseRunner


logger = logging.getLogger('grafana-simple-fp')


class LocalRunner(BaseRunner):
    config_path: str
    output_path: str

    def __init__(self, config_path: str, output_path: str):
        super().__init__()
        self.config_path = config_path
        self.output_path = output_path

    def load_config(self) -> None:
        for path in glob(self.config_path):
            try:
                logger.debug(f'reading config file at path: {path}')
                with open(path, 'r') as infile:
                    self.alert_config[path] = yaml.safe_load(infile)
            except yaml.YAMLError:
                logger.exception(f'Something went wrong when trying to read config file {path}')
            except FileNotFoundError:
                logger.exception(f'Config file provided does not exist at path: {path}')

    def save_config(self) -> None:
        out = self.alert_groups_to_dict()
        for path, conf in out.items():
            new_path = os.path.join(self.output_path, os.path.basename(path))
            logger.debug(f'saving converted config from {path} to {new_path}')
            with open(new_path, 'w') as outfile:
                yaml.dump(conf, outfile)

    def watch(self) -> None:
        raise NotImplementedError('Watch is not implemented for local mode yet')
