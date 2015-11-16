import abc
import datetime
from dateutil.relativedelta import *
from dateutil.tz import *

__author__ = 'emg33'


class StorageBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.dry_run = False

    def is_valid_snapshot_tag(self, tag_name):
        return tag_name.lower() in ['daily', 'weekly', 'monthly', 'yearly']

    def verify_snapshot_tag(self, tag_name):
        if not self.is_valid_snapshot_tag(tag_name):
            raise ValueError('Invalid snapshot tag provided', tag_name)

    def is_valid_snapshot_policy(self, snapshot_policy):
        """verify if a valid snapshot policy"""
        policy_keys = ['daily', 'weekly', 'monthly', 'yearly']
        # expect dict
        if isinstance(snapshot_policy, dict):
            snapshot_policy_keys = list(set(snapshot_policy.keys()))

            if (len(snapshot_policy_keys) !=4 or len(list(set(snapshot_policy_keys) & set(policy_keys))) != 4):
                return False

            # expect keys to match
            for policy_key in policy_keys:
                if (not policy_key in snapshot_policy_keys
                    or not isinstance(snapshot_policy[policy_key], (int, long))
                    or snapshot_policy[policy_key] < -1):
                    return False
            return True
        return False

    def verify_snapshot_policy(self, snapshot_policy):
        """

        :rtype: object
        """
        if not self.is_valid_snapshot_policy(snapshot_policy):
            raise ValueError('Invalid snapshot policy', snapshot_policy)
        return True

    def get_old_dttm(self, snapshot_tag, policy_value):
        # set to UTC to avoid any issues
        if snapshot_tag == 'hourly':
            d = relativedelta(hours=policy_value)
        elif snapshot_tag == 'daily':
            d = relativedelta(days=policy_value)
        elif snapshot_tag == 'weekly':
            d = relativedelta(weeks=policy_value)
        elif snapshot_tag == 'monthly':
            d = relativedelta(months=policy_value)
        elif snapshot_tag == 'yearly':
            d = relativedelta(years=policy_value)

        now_dttm = datetime.datetime.now(tzlocal())
        consider_old_dttm = now_dttm - d

        return consider_old_dttm

    def explain_snapshot_policy(self, snapshot_policy):
        self.verify_snapshot_policy(snapshot_policy)

        print "Using snapshot policy:"
        # print snapshot_policy
        for snapshot_tag in ['daily', 'weekly', 'monthly', 'yearly']:
            policy_value = snapshot_policy[snapshot_tag]
            if policy_value == 0:
                print "Keep all '" + snapshot_tag + "' snapshots"
            elif policy_value == -1:
                print "Keep no '" + snapshot_tag + "' snapshots"
            else:
                old_dttm = self.get_old_dttm(snapshot_tag, policy_value)
                print "Delete '" + snapshot_tag + "' snapshots older than " + str(policy_value) + " (" + old_dttm.isoformat() + ")"

    def create_snapshot_policy(self, daily=0, weekly=0, monthly=0, yearly=0):
        snapshot_policy = {'daily': daily,
                           'weekly': weekly,
                           'monthly': monthly,
                           'yearly': yearly}

        return snapshot_policy
