import boto3
import boto3.utils
import abc
from cucloud.dns import DnsBase

__author__ = 'emg33'


class Dns(DnsBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(Dns, self).__init__()
        self.r53client = boto3.client('route53')

    def hosted_domains(self):
        hosted_zones = self.r53client.list_hosted_zones()['HostedZones']

        return hosted_zones

    def print_zone_list(self):
        hosted_zones = self.r53client.list_hosted_zones()['HostedZones']
        for hosted_zone in hosted_zones:
            #print hosted_zone['Name'], hosted_zone['Id']
            record_sets = client.list_resource_record_sets(HostedZoneId=hosted_zone['Id'])['ResourceRecordSets']
            for record_set in record_sets:
                print record_set
                #print record_set['Name']
