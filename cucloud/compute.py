import abc

__author__ = 'emg33'


class ComputeBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.dry_run = False
