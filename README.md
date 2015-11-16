# cucloud module

#### Table of Contents
1. [About](#about)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)


## About

Python (2.7) package to provide a cloud agnostic interface to cloud hosting providers, initially focused on Amazon Web Services. It supports storing configuration values that can be managed either via the command line tool ``cucloud`` or in your own custom developed python with ``import cucloud``.

The ``cucloud`` module is intended to provide functionality requiring more customization than could otherwise be simply accomplished with a cloud specific command line interface, e.g. [AWS CLI](https://aws.amazon.com/cli/) or via straightforward chaining of aws cli functionality using [awsclpy](https://pypi.python.org/pypi/awsclpy). 

First step in independent development of the [Cloud-Library-Spec](https://github.com/CU-CloudCollab/Cloud-Library-Spec)

## Features

* Configuration management for multiple profiles and environments within each profile.
	* For the AWS provider, configuration is stored in DynamoDB and can be imported/exported as JSON.
* Compute:
	* Start, stop, reboot instances via instance id(s) or tag(s), including automatic de-registering on load balancers
	* Associate instances w/load balancer
* Storage:
	* Create storage snapshots - by volume_id(s) or all volumes attached to 1 or more instances.
		* Name - keeps same as source volume
		* Description - concat(name,-,MM-DD-YYYY)
		* snapshot.start_time should be used to determine future purging
    * Find or Delete snapshots - by specified policy, ex. ``{'daily': 4, 'weekly': 3, 'monthly': 6, 'yearly': -1}``
    * Manage snapshot policies via code or command line

#### Planned

Implemented features should add value -- leverage integrated configuration and/or be more advanced than straightforward SDK.

* Storage:
	* Restore volume snapshot
* Compute: 
	* Create Instance
	* Terminate instances
	* Associate Static IP - Possibly using new ``cucloud_TBD`` config table
* Misc/TBD:
	* findAMI (AMI -> AWS Specific)
	* deregister_image
	* rename_instance


## Installation

Requires ``boto3`` and ``python-dateutil``. ``cucloud`` is not currently available via PyPI.

0. Download the package
	```
	wget https://github.com/CU-CloudCollab/cucloud_module/archive/cucloud_module-<VERSION>.zip
	```

0. Extract
	```
	unzip cucloud_module-<VERSION>.zip
	```

0. Install module

	```
	# global install
	cd cucloud_module-<VERSION>
	python setup.py install

	# alternatively, in user space
	python setup.py install --user
	```

0. Alternatively, if simply managing configuration
	```
	# alternatively... if you simply need to use the CLI
	python -m cucloud-<VERSION>/cucloud --provider aws --profile=sandbox \
	       --env=dev --config-set instance_type '"t2.micro"'
	```


## Configuration

``cucloud`` automatically creates a configuration based DynamoDB table ``cucloud_profiles`` with defaults in which to store additional configuration.


### Environmental Variables

There are 5 CUCLOUD_ available environmental variables.

```
# (OPTIONAL, DEFAULT=aws)
# providers must be chosen from supported cucloud modules, currently only aws is supported
CUCLOUD_PROVIDER=aws

# (OPTIONAL, DEFAULT=False) 
# when using AWS, if you are using named connection profiles, set this to true
# your CUCLOUD_PROFILE value should then match your named profile name
# unset or set to false if you are using IAM role or AWS_ACCESS_KEY_ID=
CUCLOUD_AWS_USE_NAMED_PROFILE=true

# (OPTIONAL, DEFAULT=False)
# Enforces dryrun mode and makes no changes to your resources
CUCLOUD_DRYRUN=true

# (REQUIRED)
# profiles are user created, if you are using multiple profiles with 
# ~/.aws/credentials, your profile name must match
# If you use IAM role or AWS_ACCESS_KEY_ID= you still need to set a value
# but it will not effect your connection, suggested to match your account name
CUCLOUD_PROFILE=sandbox

# (REQUIRED)
# to allow different configuration values within a profile
CUCLOUD_ENV=dev
```

In addition to CUCLOUD_* specific vars, use of AWS named profiles is supported with ``~/.aws/config`` and ``~/.aws/credentials``.  For more information, see the [Configuring the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).

*Examples:*

*~/.aws/config*

```
[default]
output = json
region = us-east-1

[profile prod]
output = json
region = us-east-1

[profile sandbox]
output = json
region = us-east-1
```

*~/.aws/credentials*

```
[default]
aws_access_key_id = accesskey2
aws_secret_access_key = secretkey2

[prod]
aws_access_key_id = accesskey1
aws_secret_access_key = secretkey2

[sandbox]
aws_access_key_id = accesskey2
aws_secret_access_key = secretkey2
```

### Managing Profiles and Environments

When using cucloud from command line, you are recommend to set ``CUCLOUD_PROVIDER``, ``CUCLOUD_PROFILE``, ``CUCLOUD_ENV`` env vars, but you can override via command line.
If you are using named profiles with AWS and want to switch which account ``cucloud`` connects to, be sure to use ``CUCLOUD_AWS_USE_NAMED_PROFILE=True``

```
$ export CUCLOUD_PROVIDER=aws
$ export CUCLOUD_PROFILE=sandbox
$ export CUCLOUD_ENV=sandbox

$ cucloud --provider aws --profile=prod --env=stage --config-list
```

For each ``CUCLOUD_PROFILE`` (which likely maps to an AWS account), you can managing configuration values for multiple environments. For example, if you have a sandbox account mapped to a "sandbox" profile, you may have a dev and a test environment within the same account/profile.

```
# display list of existing values.
$ cucloud --env sandbox --config-list
$ cucloud --config-set <KEY> <VALUE>
$ cucloud --config-unset <KEY>
$ cucloud --profile sandbox --env test --config-export > config.json
$ cucloud --profile sandbox --env dev --config-import < config.json
```


### Managing Configuration

#### Command Line

The ``cucloud_module`` package provides a single CLI entry point: ``cucloud`` for managing configuration.

```
usage: cucloud [-h] [--provider {aws,azure}] [--profile PROFILE] [--env ENV]
               [--config-list] [--config-set key value] [--config-unset key]
               [--config-import] [--config-export]
               [infile] [outfile]

positional arguments:
  infile
  outfile

optional arguments:
  -h, --help            show this help message and exit
  --provider {aws,azure}
                        Choose cloud provider
  --profile PROFILE     Choose provider profile
  --env ENV             Choose profile environment
  --config-list         List configuration values
  --config-set key value
                        Set a configuration key + value
  --config-unset key    Unset a configuration key
  --config-import       Import JSON configuration
  --config-export       Export JSON configuration
```

#### Examples

Show our configuration values.
```
$ echo $CUCLOUD_PROVIDER $CUCLOUD_PROFILE $CUCLOUD_ENV
aws ssit-sb dev

$ cucloud --config-list
Configuration for AWS profile: "ssit-sb", environment: "dev"

Key					Value
instance_type		t2.micro
min_count			1
max_count			1
```

Set a specific configuration value. Strings must be escaped as shown. Dot notation is supported for dictionaries.
```
$ cucloud --config-set instance_type '"t2.small"'
$ cucloud --config-set min_count 4
$ cucloud --config-set snapshot_policies.longterm '{"daily": 7, "weekly": 4, "monthly": 6, "yearly": 3}'

$ cucloud --config-list
Configuration for AWS profile: "ssit-sb", environment: "dev"

Key					Value
instance_type		t2.small
min_count			4
max_count			1
snapshot_policies	{u'default': {u'yearly': Decimal('4'), u'monthly': Decimal('3'), u'daily': Decimal('1'), u'weekly': Decimal('2')},
                     u'longterm': {u'yearly': Decimal('3'), u'monthly': Decimal('6'), u'daily': Decimal('7'), u'weekly': Decimal('4')}}

```


Show values in a different profile
```
$ cucloud --config-list --profile ssit
Configuration for AWS profile: "ssit", environment: "dev"

Key					Value
instance_type		t2.micro
min_count			1
max_count			1
```


Unset a value
```
$ cucloud --config-set ami_id '"ami-12345"'
$ cucloud --config-list | grep ami
ami_id		ami-12345
$ cucloud --config-unset ami_id
$ cucloud --config-list | grep ami | wc -l
    0
```

#### Snapshot Policies

When setting a snapshot, via command line or code, you must set daily, weekly, monthly, and yearly values. 

* 0: Keep all snapshots matching tag
* -1: Keep NO snapshots matching tag.
* 1+ : Delete snapshots older than # x the snapshot tag. So daily: 7 deletes any 'daily' snapshots older than 7 days. It does not mean keep only 7 daily snapshots.
 
```
$ cucloud --config-set snapshot_policies.longterm '{"daily": 7, "weekly": 4, "monthly": 6, "yearly": 3}'
```

## Usage

Creating your own scripts leveraging the ``cucloud`` module.

```
#!/usr/bin/env python
from cucloud import providers

# initialize our AWS provider, relying on env vars: CUCLOUD_PROFILE and CUCLOUD_ENV
provider = providers.get_provider('aws')

# get our Compute class which will provide methods we want to use
compute = provider.compute()

# if we have specific instances we want to spin up...
instance_ids = ['i-cc2f296f']
# start, stop, reboot instances
compute.start_instances(instance_ids)
compute.stop_instances(instance_ids)
compute.reboot_instances(instance_ids)

# start/stop/reboot instances via tag
tag_values = ['web-001', 'web-002']
compute.start_instances_tagged('Name', tag_values)
compute.stop_instances_tagged('Name', tag_values)
compute.reboot_instances_tagged('Name', tag_values)
```
