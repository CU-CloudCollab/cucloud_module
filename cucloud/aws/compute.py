import boto3
import boto3.utils
import abc

__author__ = 'emg33'


class Compute(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#client
        self.ec2client = boto3.client('ec2')
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#service-resource
        self.ec2resource = boto3.resource('ec2')

    def instances_tagged(self, tag_name, tag_values):
        """
        gets instances
        :rtype: list[EC2.Instance]
        """

        # find instances by tag
        instances = self.ec2resource.instances.filter(Filters=[{'Name': 'tag:' + tag_name, 'Values': tag_values}])

        return instances

    def instance_ids_tagged(self, tag_name, tag_values):
        instances = self.instances_tagged(tag_name, tag_values)

        instance_ids = [i.id for i in instances]

        return instance_ids


    def descr_instances_tagged(self, tag_name, tag_values):
        instance_ids = self.instance_ids_tagged(tag_name, tag_values)

        response = self.ec2client.describe_instances(
            InstanceIds=instance_ids
        )

        return response

    def start_instances_tagged(self, tag_name, tag_values):
        """
        start instances, initiates a waiter until the instances have started

        :param str tagname:
        :param list tagvalues:
        :return:
        """
        instance_ids = self.instance_ids_tagged(tag_name, tag_values)

        return self.start_instances(instance_ids)

    def stop_instances_tagged(self, tagname, tagvalues):
        """
        stop instances, initiates a waiter until the instances have stopped

        :param str tagname:
        :param list tagvalues:
        :return:
        """
        instances = self.instances_tagged(tagname, tagvalues)
        instance_ids = [i.id for i in instances]

        return self.stop_instances(instance_ids)

    def reboot_instances_tagged(self, tagname, tagvalues):
        """
        reboot instances, NO waiter

        :param str tagname:
        :param list tagvalues:
        :return:
        """
        instances = self.instances_tagged(tagname, tagvalues)
        instance_ids = [i.id for i in instances]

        return self.reboot_instances(instance_ids)

    def start_instances(self, instance_ids):
        """
        start instances, initiates a waiter until the instances have started

        :param list instance id
        :return:
        """
        response = self.ec2client.start_instances(
            InstanceIds=instance_ids,
            DryRun=False
        )

        waiter = self.ec2client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)

        return response

    def stop_instances(self, instance_ids):
        """
        stop instances, initiates a waiter until the instances have stopped

        :param list instance id
        :return:
        """
        response = self.ec2client.stop_instances(
            InstanceIds=instance_ids,
            Force=False
        )

        waiter = self.ec2client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=instance_ids)

        return response

    def reboot_instances(self, instance_ids):
        response = self.ec2client.reboot_instances(
            InstanceIds=instance_ids
        )

        return response

    def region_list(self):
        """
        Simply a wrapper for ec2.describe_regions()
        :return: list
        """

        # list all regions supporting EC2
        regions = self.ec2client.describe_regions()

        return regions['Regions']

    def print_instances_all(self):
        instances = self.ec2client.instances.all()

        # find by state
        #instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]):
        #instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['Running']}]):

        # find by id
        #ids = ['i-c758f13a']
        #instances = ec2.instances.filter(InstanceIds=ids)

        # find instances by tag
        #instances = ec2.instances.filter(Filters=[{'Name': 'tag:grysko-purpose', 'Values': ['stage']}])

        # loop through instances
        print "Id\tType\tState"
        for instance in instances:
            print instance.instance_id, instance.instance_type, instance.state['Name']
            for tag in instance.tags:
                print tag['Key'] + ': ' + tag['Value']
            print "\n"
            #instance.start()

        #for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
        #    print(status)
