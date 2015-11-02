import boto3
import boto3.utils
import abc
import time

__author__ = 'emg33'


class Compute(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#client
        self.ec2client = boto3.client('ec2')
        # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#service-resource
        self.ec2resource = boto3.resource('ec2')
        # http://boto3.readthedocs.org/en/latest/reference/services/elb.html#client
        self.elbclient = boto3.client('elb')

    def instances_tagged(self, tag_key, tag_values):
        """
        gets instances
        :rtype: list[EC2.Instance]
        """

        # find instances by tag
        instances = self.ec2resource.instances.filter(Filters=[{'Name': 'tag:' + tag_key, 'Values': tag_values}])

        return instances

    def instance_ids_tagged(self, tag_key, tag_values):
        """
        :param tag_key: str
        :param tag_values: list[str]
        :return: list[str]
        """
        instances = self.instances_tagged(tag_key, tag_values)

        instance_ids = [i.id for i in instances]

        return instance_ids


    def descr_instances_tagged(self, tag_key, tag_values):
        instance_ids = self.instance_ids_tagged(tag_key, tag_values)

        response = self.ec2client.describe_instances(
            InstanceIds=instance_ids
        )

        return response

    def start_instances_tagged(self, tag_key, tag_values):
        """
        start instances, initiates a waiter until the instances have started

        :param tag_key: str
        :param tag_values: list[str]
        :return:
        """
        instance_ids = self.instance_ids_tagged(tag_key, tag_values)

        return self.start_instances(instance_ids)

    def stop_instances_tagged(self, tag_key, tag_values):
        """
        stop instances, initiates a waiter until the instances have stopped

        :param tag_key: str
        :param tag_values: list[str]
        :return:
        """
        instances = self.instances_tagged(tag_key, tag_values)
        instance_ids = [i.id for i in instances]

        return self.stop_instances(instance_ids)

    def reboot_instances_tagged(self, tag_key, tag_values):
        """
        reboot instances, NO waiter

        :param tag_key: str
        :param tag_values: list[str]
        :return:
        """
        instances = self.instances_tagged(tag_key, tag_values)
        instance_ids = [i.id for i in instances]

        return self.reboot_instances(instance_ids)

    def start_instances(self, InstanceIds):
        """
        start instances, initiates a waiter until the instances have started

        :param list instance id
        :return:
        """
        print "Issuing start instances for "
        print InstanceIds

        response = self.ec2client.start_instances(
            InstanceIds=InstanceIds
        )

        print "waiting until running"
        waiter = self.ec2client.get_waiter('instance_running')
        waiter.wait(InstanceIds=InstanceIds)
        print "Wait complete. Instances started."

        return response

    def attach_instance_to_balancer(self, InstanceId, LoadBalancerName):
        print "Registering " + InstanceId + " with elb: " + LoadBalancerName
        response = self.elbclient.register_instances_with_load_balancer(
            LoadBalancerName=LoadBalancerName,
            Instances=[{'InstanceId': InstanceId}]
        )
        return response

    def start_instance_and_attach_to_balancers(self, InstanceId, LoadBalancerNames):
        # start instances
        startresponse = self.start_instances([InstanceId])

        response = None
        # register with load balancer
        for LoadBalancerName in LoadBalancerNames:
            response = self.attach_instance_to_balancer(InstanceId, LoadBalancerName)

        # return the load response of registering
        return response

    def deregister_instances_from_all_balancers(self, InstanceIds):
        # de-register any instances if they're attached to balancers
        elbs = self.elbclient.describe_load_balancers()

        for elb in elbs['LoadBalancerDescriptions']:
            # get the list intersection of InstanceIds and elb['Instances']
            elbiids = [i['InstanceId'] for i in elb['Instances']]

            instance_ids_attached_to_balancer = list(set(InstanceIds).intersection(elbiids))
            if instance_ids_attached_to_balancer:
                print "Deregistering instances from elb '" + elb['LoadBalancerName'] + "'"
                print instance_ids_attached_to_balancer

                elb_instance_id_dict = []
                for i in instance_ids_attached_to_balancer:
                    elb_instance_id_dict.append({'InstanceId': i})

                self.elbclient.deregister_instances_from_load_balancer(
                    LoadBalancerName=elb['LoadBalancerName'],
                    Instances=elb_instance_id_dict
                )

                # FIXME: no waiters available, but we could verify manually using describe_load_balancers again?
                time.sleep(10)

        return

    def stop_instances(self, InstanceIds):
        """
        stop instances, initiates a waiter until the instances have stopped
        deregisters any load balancers if they're found

        :param list instance id
        :return:
        """
        self.deregister_instances_from_all_balancers(InstanceIds)

        print "Issuing stop instances for "
        print InstanceIds

        response = self.ec2client.stop_instances(
            InstanceIds=InstanceIds
        )

        print "Waiting until stopped"
        waiter = self.ec2client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=InstanceIds)
        print "Waiter complete. Instances have been stopped."

        return len(InstanceIds)

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

