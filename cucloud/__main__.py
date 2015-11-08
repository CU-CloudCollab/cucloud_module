import argparse
import logging
import os
import sys
import providers
from . import __version__

__author__ = 'emg33'


def _create_parser():
    parser = argparse.ArgumentParser(prog='cucloud')

    supported_providers = ['aws', 'azure']

    parser.add_argument('--provider', choices=supported_providers, help='Choose cloud provider')
    parser.add_argument('--profile', type=str, help='Choose provider profile')
    parser.add_argument('--env',  type=str, help='Choose profile environment')

    parser.add_argument('--config-list', help='List configuration values', action='store_true')
    parser.add_argument('--config-set', metavar=('key', 'value'), nargs=2, help='Set a configuration key + value')
    parser.add_argument('--config-unset', metavar=('key'), nargs=1, help='Unset a configuration key')
    parser.add_argument('--config-import', help='Import JSON configuration', action='store_true')
    parser.add_argument('--config-export', help='Export JSON configuration', action='store_true')

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

    # we set default provider in main() to avoid ignoring ENV
    parser.set_defaults(provider=None, profile=None, env=None)

    return parser;


def setup_logging():
    # TODO: use config file for logging: https://docs.python.org/2/howto/logging.html or just use syslog
    logging.basicConfig(filename='cucloud.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
    logging.debug('cucloud v: %s', __version__)


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    setup_logging()

    parser = _create_parser()
    args = parser.parse_args()

    # provider selection: prioritize args over over E=CUCLOUD_PROVIDER
    if args.provider:
        provider_name = args.provider
    elif os.environ.has_key('CUCLOUD_PROVIDER'):
        provider_name = os.environ.get('CUCLOUD_PROVIDER')
    else:
        provider_name = 'aws'

    # profile selection: prioritize args over E=CUCLOUD_PROFILE
    if args.profile:
        profile_name = args.profile
        logging.info('Using cloud profile "%s" set via arguments', profile_name)
    elif os.environ.has_key('CUCLOUD_PROFILE'):
        profile_name = os.environ.get('CUCLOUD_PROFILE')
        logging.info('Using cloud profile "%s" set in env', profile_name)
    else:
        logging.fatal('No cloud profile selected')
        raise Exception('Cloud profile must be configured or set via command line')

    # env selection: prioritize args over E=CUCLOUD_ENV
    if args.env:
        env_name = args.env
        logging.info('Using profile environment "%s" set via arguments', env_name)
    elif os.environ.has_key('CUCLOUD_ENV'):
        env_name = os.environ.get('CUCLOUD_ENV')
        logging.info('Using profile environment "%s" set via arguments', env_name)
    else:
        logging.fatal('No profile environment selected')
        raise Exception('Cloud profile environment must be configured or set via command line')

    provider = providers.get_provider(provider_name, profile_name, env_name)

    return provider.handle_args(args)


# this allows us to call this both via python -m cucloud
# and allow the command line entry_point to work
if __name__ == "__main__":
    main()