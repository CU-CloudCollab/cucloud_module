import azure

__author__ = 'emg33'


class AzureProvider:

    def __init__(self, profile_name, env_name, named_profile=False):
        self.profile_name = profile_name
        self.env_name = env_name


    def handle_args(self, args):
        raise NotImplementedError('Azure Provider is not yet supported')