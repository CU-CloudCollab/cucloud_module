import boto3
import boto3.utils
import abc
import datetime
from cucloud.storage import StorageBase

__author__ = 'emg33'


class Storage(StorageBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(Storage, self).__init__()

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

    def create_snapshot_volume(self, Volume=None, VolumeId=None, snapshot_tag=None):
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
        now = datetime.datetime.today()

        descr = self.get_name_given_tags(Volume.tags)
        if len(descr):
            descr += '-'
        descr += now.strftime('%Y-%m-%d')

        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#snapshot
        try:
            Snapshot = self.ec2resource.create_snapshot(
                VolumeId=Volume.id,
                Description=descr,
                DryRun=self.dry_run
            )

            # FIXME: waiter isnt responding correctly.
            # create a waiter until this is complete
            #waiter = self.ec2client.get_waiter('volume_available')
            #waiter.wait(
            #   VolumeIds=[volume.id]
            #)

            print "Snapshot initiated " + Snapshot.id + " from " + Volume.id
            print "  set description '" + descr + "'"

            if snapshot_tag:
                Volume.tags.append({'Key': 'cucloud-snapshot', 'Value': snapshot_tag.lower()})

            # set tags on the new snapshot
            if Volume.tags:
                self.ec2client.create_tags(
                    Resources=[Snapshot.id],
                    Tags=Volume.tags
                )

            return Snapshot

        except Exception:
            print "DRY-RUN Creating snapshot"
            pass

        return False

    def create_snapshot_volumes(self, Volumes=None, VolumeIds=None, snapshot_tag=None):
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
            Snapshot = self.create_snapshot_volume(Volume, snapshot_tag=snapshot_tag)
            Snapshots.append(Snapshot)

        return Snapshots

    def create_snapshot_all_instance_volumes(self, snapshot_tag=None, Instance=None, InstanceId=None):
        if not Instance and not InstanceId:
            raise Exception('Instance or InstanceId must be set')

        if not Instance:
            Instance = self.ec2resource.Instance(InstanceId)

        volumes = self.get_instance_volumes(Instance=Instance)

        snapshots = self.create_snapshot_volumes(Volumes=volumes, snapshot_tag=snapshot_tag)

        return snapshots

    def create_snapshot_all_instances_volumes(self, snapshot_tag=None, InstanceIds=None):
        if not InstanceIds:
            raise Exception('InstanceIds required')

        snapshots = []

        for InstanceId in InstanceIds:
            instance_snapshots = self.create_snapshot_all_instance_volumes(snapshot_tag=snapshot_tag, InstanceId=InstanceId)
            snapshots = snapshots + instance_snapshots

        return snapshots

    def delete_snapshot(self, SnapshotId):
        """
        :param SnapshotId: string
        :return: response
        """
        try:
            response = self.ec2client.delete_snapshot(
                SnapshotId=SnapshotId,
                DryRun=self.dry_run
            )
            print "Deleting: " + SnapshotId
            return response
        except Exception:
            print "DRY-RUN Deleting: " + SnapshotId

        print ""

        # no concept of waiter on snapshot delete

        return True

    def delete_snapshots(self, SnapshotIds):
        """Calls delete_snapshot on all passed SnapshotIds

        :param SnapshotIds: list
        :return:
        """
        for SnapshotId in SnapshotIds:
            self.delete_snapshot(SnapshotId)

        return True

    def find_old_snapshots(self, snapshot_policy=None, VolumeIds=None):
        self.verify_snapshot_policy(snapshot_policy)

        oldsnapshots = []

        # using keys
        for snapshot_tag in ['daily', 'weekly', 'monthly', 'yearly']:

            policy_value = snapshot_policy[snapshot_tag]
            if policy_value == 0:
                print "Keep all snapshots for " + snapshot_tag
                continue

            # calculate old_dttm based on snapshot_tag and snapshot_policy[snapshot_tag]
            consider_old_dttm = self.get_old_dttm(snapshot_tag, snapshot_policy[snapshot_tag])

            # find all snapshots for each of the VolumeIds
            # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_snapshots
            for VolumeId in VolumeIds:
                response = self.ec2client.describe_snapshots(
                    Filters=[
                        {'Name': 'volume-id',
                         'Values': [VolumeId]
                         },
                        {'Name': 'status',
                         'Values': ['completed']
                         },
                        {'Name': 'tag:cucloud-snapshot',
                         'Values': [snapshot_tag]}
                    ]
                )

                snapshots = response['Snapshots']
                for snapshot in snapshots:
                    snapshot_dttm = snapshot['StartTime']
                    # are we older than ... OR keep none
                    if snapshot_dttm <= consider_old_dttm or policy_value == -1:
                        oldsnapshots.append(snapshot)

        return oldsnapshots

    def delete_old_snapshots(self, snapshot_policy=None, VolumeIds=None):
        oldsnapshots = self.find_old_snapshots(snapshot_policy=snapshot_policy, VolumeIds=VolumeIds)

        for snapshot in oldsnapshots:
            print "Snapshot: " + snapshot['SnapshotId'] + ", from: " + snapshot['StartTime'].isoformat() + ", descr: " + snapshot['Description']
            self.delete_snapshot(snapshot['SnapshotId'])

        return oldsnapshots