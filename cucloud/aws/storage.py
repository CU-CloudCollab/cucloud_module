import boto3
import boto3.utils
import abc
from datetime import datetime

__author__ = 'emg33'


class Storage(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#client
        self.ec2client = boto3.client('ec2')
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#service-resource
        self.ec2resource = boto3.resource('ec2')

    def get_name_given_tags(self, tags):
        if not tags:
            return ''
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']

        return ''

    def get_instance_volumes(self, Instance=None, InstanceId=None):
        """
        :param Instance: EC2.Instance
        :param InstanceId: str
        :return: list[EC2.Volume]
        """
        if not Instance and not InstanceId:
            raise Exception('Instance or InstanceId must be set')

        if not Instance:
            Instance = self.ec2resource.Instance(InstanceId)

        return Instance.volumes.all()

    def create_snapshot_volume(self, Volume=None, VolumeId=None):
        """
        :param volume: EC2.volume
        :return: EC2.Snapshot
        """
        if not Volume and not VolumeId:
            raise Exception('Volume or VolumeId is required')
        if not Volume:
            Volume = self.ec2resource.Volume(VolumeId)

        # TODO: is this a root device? if, really should handle differently or at least warn

        # create the description, using today's date
        now = datetime.today()

        descr = self.get_name_given_tags(Volume.tags)
        if len(descr):
            descr += '-'
        descr += now.strftime('%Y-%m-%d')

        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#snapshot
        Snapshot = self.ec2resource.create_snapshot(
            VolumeId=Volume.id,
            Description=descr
        )

        # FIXME: waiter isnt responding correctly.
        # create a waiter until this is complete
        #waiter = self.ec2client.get_waiter('volume_available')
        #waiter.wait(
        #   VolumeIds=[volume.id]
        #)

        # set tags on the new snapshot
        if Volume.tags:
            self.ec2client.create_tags(
                Resources=[Snapshot.id],
                Tags=Volume.tags
            )

        return Snapshot

    def create_snapshot_volumes(self, Volumes=None, VolumeIds=None):
        """
        :param volumes: list[EC2.Volume]
        :return: list[EC2.Snapshot]
        """
        if not Volumes and not VolumeIds:
            raise Exception('Volumes or VolumeIds is required')
        if not Volumes:
            Volumes = []
            for VolumeId in VolumeIds:
                Volume = self.ec2resource.Volume(VolumeId)
                Volumes.append(Volume)

        Snapshots = []
        for Volume in Volumes:
            Snapshot = self.create_snapshot_volume(Volume)
            Snapshots.append(Snapshot)

        return Snapshots

    def create_snapshot_all_instance_volumes(self, Instance=None, InstanceId=None):
        if not Instance and not InstanceId:
            raise Exception('Instance or InstanceId must be set')

        if not Instance:
            Instance = self.ec2resource.Instance(InstanceId)

        volumes = self.get_instance_volumes(Instance=Instance)

        snapshots = self.create_snapshot_for_volumes(volumes)

        return snapshots

    def create_snapshot_all_instances_volumes(self, InstanceIds=None):
        if not InstanceIds:
            raise Exception('InstanceIds required')

        for InstanceId in InstanceIds:
            self.create_snapshot_all_instance_volumes(InstanceId=InstanceId)

        # FIXME: what do we want to return here?
        return True

    #def purge_old_instance_snapshots(self, instance_ids):
        # TODO: get snapshot_max_days from config?
        #raise NotImplementedError('Purge old instances not yet implemented')
        #return None