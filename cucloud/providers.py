import os
from cucloud.aws.provider import AwsProvider
from cucloud.azure.provider import AzureProvider

__author__ = 'emg33'


def aws(profile_name, env_name, dry_run=False, named_profile=False):
    aws_provider = AwsProvider(profile_name, env_name, dry_run=dry_run, named_profile=named_profile)

    return aws_provider


def azure(profile_name, env_name, dry_run=False, named_profile=False):
    azure_provider = AzureProvider(profile_name, env_name, dry_run=dry_run, named_profile=named_profile)

    return azure_provider


def get_provider(provider_name, profile_name=None, env_name=None, dry_run=False, named_profile=False):
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

    if os.environ.has_key('CUCLOUD_DRYRUN') and os.environ.get('CUCLOUD_DRYRUN') in ("yes", "true", "y", "t", "1"):
        dry_run = True

    if provider_name == 'aws':
        return aws(profile_name, env_name, dry_run, named_profile)
    elif provider_name == 'azure':
        return azure(profile_name, env_name, dry_run, named_profile)
    else:
        raise Exception('Unsupported provider "' + provider_name + '"')


