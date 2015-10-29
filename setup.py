from setuptools import setup
from cucloud import __version__

requires = ['boto3',
            'botocore']

setup_options = dict(
    name='cucloud',
    version=__version__,
    description='Python Implementation of the Cornell Cloud Library Spec ',
    classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
    keywords=[
        'aws',
        'amazon web services',
        'command line interface',
        'cornell university',
        'cloud agnostic'
    ],
    author='Cornell University',
    author_email='emg33@cornell.edu',
    maintainer='Eric Grysko',
    maintainer_email='emg33@cornell.edu',
    url='https://github.com/CU-CloudCollab/cucloud_module',
    packages=['cucloud','cucloud.aws'],
    entry_points = {
        'console_scripts': ['cucloud = cucloud.__main__:main'],
    },
    license='License :: Other/Proprietary License',
    install_requires=requires,
    zip_safe=False
)

setup(**setup_options)
