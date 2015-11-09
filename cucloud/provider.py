import abc

__author__ = 'emg33'


class ProviderBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, profile_name, env_name, dry_run=False, named_profile=False):
        self._profile_name = None
        self._env_name = None

        # construct
        self.profile_name = profile_name
        self.env_name = env_name
        self.dry_run = dry_run

    @abc.abstractmethod
    def handle_args(self, args):
        """Handle command line arguments"""
        return

    @property
    def profile_name(self):
        """currently active profile"""
        return self._profile_name

    @profile_name.setter
    def profile_name(self, value):
        self._profile_name = value

    @profile_name.deleter
    def profile_name(self):
        del self._profile_name

    @property
    def env_name(self):
        """default selected name of env"""
        return self._env_name

    @env_name.setter
    def env_name(self, value):
        self._env_name = value

    @env_name.deleter
    def env_name(self):
        del self._env_name
