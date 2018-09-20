#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup file for easy installation."""
import glob
import os
import shutil

from rpmlint.version import __version__
from setuptools import setup


# convert this to entrypoints
if not os.path.exists('build/_scripts'):
    os.makedirs('build/_scripts')
shutil.copyfile('scripts/lint.py', 'build/_scripts/rpmlint')

setup(
    name='rpmlint',
    description='Check for common errors in RPM packages',
    long_description=('Rpmlint is a tool to check common errors in RPM packages.'
                      'Binary and source packages can be checked'),
    url='https://github.com/rpm-software-management/rpmlint',
    download_url='https://github.com/rpm-software-management/rpmlint',

    version=__version__,

    author='Frédéric Lepied',
    author_email='flepied@mandriva.com',

    maintainer='RPMLint maintainers',
    maintainer_email='rpm-ecosystem@lists.rpm.org',

    license='License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Archiving :: Packaging',
    ],
    platforms=['Linux'],
    keywords=['RPM', '.spec', 'validator'],

    install_requires=['pyxdg', 'ConfigObj'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],

    packages=['rpmlint'],
    package_data={
        'rpmlint': ['rpmlint/configspec.cfg'],
    },
    include_package_data=True,
    data_files=[
        ('share/man/man1', glob.glob('man/*.1')),
    ],
    scripts=[
        'build/_scripts/rpmlint',
    ],
    entry_points={
        'console_scripts': [
            'rpmdiff = rpmlint:diff',
        ]
    },
)
