import abc
import os

__author__ = 'emg33'


def aws(profile_name, env_name):
    from cucloud.aws import provider

    aws_provider = provider.AwsProvider(profile_name, env_name)

    return aws_provider


def azure(profile_name, env_name):
    from cucloud.azure import provider

    azure_provider = provider.AzureProvider(profile_name, env_name)

    return azure_provider


def get_provider(provider_name, profile_name=None, env_name=None, named_profile=False):
    if not profile_name:
        if os.environ.has_key('CUCLOUD_PROFILE'):
            profile_name = os.environ.get('CUCLOUD_PROFILE')
        else:
            raise Exception('Profile name must be specified when using get_provider() or set Env var CUCLOUD_PROFILE')

    if not env_name:
        if os.environ.has_key('CUCLOUD_ENV'):
            env_name = os.environ.get('CUCLOUD_ENV')
        else:
            raise Exception('Environment name must be specified when using get_provider() or set Env var CUCLOUD_ENV')

    if provider_name == 'aws':
        return aws(profile_name, env_name, named_profile)
    elif provider_name == 'azure':
        return azure(profile_name, env_name, named_profile)
    else:
        raise Exception('Unsupported provider "' + provider_name + '"')


class ProviderBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def handle_args(self, args):
        """Handle command line arguments"""
        return
