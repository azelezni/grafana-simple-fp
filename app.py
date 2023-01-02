import argparse
import logging
import os

from grafana_sfp.helpers import KvDictAppendAction
from grafana_sfp.runner.base import BaseRunner
from grafana_sfp.runner.cluster import ClusterRunner
from grafana_sfp.runner.local import LocalRunner

logger = logging.getLogger('grafana-simple-fp')
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logger.level)
logger_formatter = logging.Formatter('%(name)s - %(asctime)-15s %(levelname)-8s %(message)s')
stream_handler.setFormatter(logger_formatter)
logger.addHandler(stream_handler)


def main() -> None:
    runner: BaseRunner
    parser = argparse.ArgumentParser(description='Grafana Simple File Provisioning')

    parser.add_argument(
        '-m', '--mode', required=True,
        default='local', choices=['local', 'cluster'],
        help='Run mode, either local or cluster'
    )
    parser.add_argument(
        '-c', '--config', required=False,
        help='Path to config dir/file, for local mode only'
    )
    parser.add_argument(
        '-o', '--out', required=False,
        help='Path to output converted yaml, for local mode only'
    )
    parser.add_argument(
        '-l', '--label-selector', required=False,
        action=KvDictAppendAction, nargs=1,
        help='Label selector for filtering configmaps: key=value'
    )
    parser.add_argument(
        '-t', '--target-labels', required=False,
        action=KvDictAppendAction, nargs=1,
        help='Label to add to created configmaps: key=value'
    )
    parser.add_argument(
        '-w', '--watch', required=False,
        action='store_true',
        help='Enable watch mode'
    )
    args = parser.parse_args()

    if args.mode == 'local':
        runner = LocalRunner(config_path=args.config, output_path=args.out)
    elif args.mode == 'cluster':
        runner = ClusterRunner(label_selector=args.label_selector, target_labels=args.target_labels)
    else:
        raise NotImplementedError(f'Unrecognized run mode: {args.mode}')

    logger.info(f'Running in {args.mode} mode')
    runner.load_and_convert()
    runner.save_config()

    if args.watch:
        logger.info(f'Watching for configmap changes...')
        runner.watch()


if __name__ == '__main__':
    main()
