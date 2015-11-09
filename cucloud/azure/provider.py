#import azure
import json
import logging
import os
from cucloud.provider import ProviderBase

__author__ = 'emg33'


class AzureProvider(ProviderBase):

    def __init__(self, profile_name, env_name, dry_run=False, named_profile=False):
        super(AzureProvider, self).__init__(profile_name, env_name, dry_run=dry_run)

    def handle_args(self, args):
        raise NotImplementedError('Azure Provider is not yet supported')