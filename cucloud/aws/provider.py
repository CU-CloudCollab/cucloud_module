import boto3
import json
import logging
import os
from cucloud.aws import compute
from cucloud.aws import dns
from cucloud.aws import dynamodb
from cucloud.aws import storage
from cucloud.provider import ProviderBase

__author__ = 'emg33'


class AwsProvider(ProviderBase):

    def __init__(self, profile_name, env_name, dry_run=False, named_profile=False):
        super(AwsProvider, self).__init__(profile_name, env_name, dry_run=dry_run)

        self._config = None
        self.use_named_profiles = str(named_profile)

        if os.environ.has_key('CUCLOUD_AWS_USE_NAMED_PROFILE'):
            self.use_named_profiles = os.environ.get('CUCLOUD_AWS_USE_NAMED_PROFILE')

        # support for lazy setting of the env variable
        if self.use_named_profiles.lower() in ("yes", "true", "y", "t", "1"):
            # select our connection profile, https://github.com/boto/boto3/pull/69
            # which AWS account are we going to use
            boto3.setup_default_session(profile_name=profile_name)
            print "Using AWS named profile '" + profile_name + "'"

        # Get the service resource.
        # http://boto3.readthedocs.org/en/latest/guide/dynamodb.html
        self.dynamodb = boto3.resource('dynamodb')

        # our config dict, created on demand with defaults in does not exist in the account
        self.config = self._get_config(self.profile_name, self.env_name)

    @property
    def config(self):
        """currently active configuration (json)"""
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    @config.deleter
    def config(self):
        del self._config

    def _find_config_tables(self):
        table_iterator = self.dynamodb.tables.filter(
            ExclusiveStartTableName='cucloud',
            Limit=10
        )

        return table_iterator

    def _table_exists(self, tables, table_name):
        return any(x for x in tables if x.name == table_name)

    def _create_profiles_table(self):
        logging.debug('About to create cucloud_profiles DynamoDB table')

        # Create the DynamoDB table, we don't need much horsepower here
        # limit to read/write of 1/1
        table = self.dynamodb.create_table(
            TableName='cucloud_profiles',
            KeySchema=[
                {
                    'AttributeName': 'profile',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'env',
                    'KeyType': 'RANGE'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'profile',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'env',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )

        # wait until the table exists
        table.meta.client.get_waiter('table_exists').wait(TableName='cucloud_profiles')

        logging.debug('Created cucloud_profiles DynamoDB table')

        return True

    def config_init(self):
        tables = self._find_config_tables()
        if not self._table_exists(tables, 'cucloud_profiles'):
            self._create_profiles_table()

    def add_profile(self, profile_name, env_name, json):
        table = self.dynamodb.Table('cucloud_profiles')

        response = table.put_item(
            Item={
                'profile': profile_name,
                'env': env_name,
                'config': json
            }
        )

    def save_profile(self):
        table = self.dynamodb.Table('cucloud_profiles')

        response = table.put_item(
            Item={
                'profile': self.profile_name,
                'env': self.env_name,
                'config': self.config
            }
        )

    def _get_config(self, profile_name, env_name):
        """
        Get the latest configuration stored in DynamoDB
        creates the DynamoDB cucloud_profiles table and initiates default values if needed

        :rtype : dict
        """
        self.config_init()

        config = self._fetch_config_from_dynamo(profile_name, env_name)
        # if config doesn't exist create a default one
        if not config:

            # config_version in event we want to change structure stored
            json_obj = {
                "instance_type": "t2.micro",
                "min_count": '1',
                "max_count": '1',
                "config_version": '1'
            }

            self.add_profile(profile_name, env_name, json_obj)
            config = self._fetch_config_from_dynamo(profile_name, env_name)
            if not config:
                raise Exception('Profile not found and could not be created')

        return config

    def _fetch_config_from_dynamo(self, profile_name, env_name):
        table = self.dynamodb.Table('cucloud_profiles')

        response = table.get_item(
            Key={
                'profile': profile_name,
                'env': env_name
            }
        )

        if not 'Item' in response:
            return None

        item = response['Item']

        config = item['config']

        return config

    # http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
    def byteify(self, input):
        if isinstance(input, dict):
            return {self.byteify(key):self.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def handle_args(self, args):
        if args.config_list:
            print 'Configuration for AWS profile: "' + self.profile_name + '", environment: "' + self.env_name + '"'
            print
            print "Key\t\t\tValue"
            # TODO: "hide" config_version and any other special keys
            for prop in self.config.iterkeys():
                print prop + "\t\t" + str(self.config[prop])

            return True

        elif args.config_set:
            # TODO: check for known keys?
            config_key = args.config_set[0]
            config_value = args.config_set[1]

            self.config[config_key] = config_value

            return self.save_profile()

        elif args.config_unset:
            # TODO: check for known keys?
            config_key = args.config_unset[0]

            # TODO: some keys should always reset to DEFAULT!
            self.config.pop(config_key, None)
            return self.save_profile()

        elif args.config_import:

            self.config = json.loads(args.infile.read())
            return self.save_profile()

        elif args.config_export:

            json_str = self.byteify(self.config)

            # "pretty print"
            print json.dumps(json_str, sort_keys=True,
                             indent=4, separators=(',', ': '))

            return True
        else:
            print 'Unable to handle arguments'

        return False

    def compute(self):
        """
        :return: cucloud.aws.compute.Compute
        """
        c = compute.Compute()
        c.dry_run = self.dry_run
        return c

    def storage(self):
        """
        :return: cucloud.aws.storage.Storage
        """
        s = storage.Storage()
        s.dry_run = self.dry_run
        return s

    def dns(self):
        """
        :return: cucloud.aws.dns.Dns
        """
        d = dns.Dns()
        return d
