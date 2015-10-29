"""
cucloud
----
Python (2.7) package to provide a cloud agnostic interface to cloud hosting
providers, initially focused on Amazon Web Services. It supports storing
configuration values that can be managed either via the command line tool
cucloud or in your own custom developed python with import cucloud.

The cucloud module is intended to provide functionality requiring more
customization than could otherwise be simply accomplished with a cloud
specific command line interface, e.g. AWS CLI or via straightforward
chaining of aws cli functionality using awsclpy.

Attempts to follow: Python PEP0008 style guide - https://www.python.org/dev/peps/pep-0008/
"""
__author__ = 'emg33'

__version__ = '0.1.0'