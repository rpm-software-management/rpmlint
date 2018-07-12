#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup file for easy installation."""
import glob
import os
import shutil

from rpmlint import __version__
from setuptools import setup


# convert this to entrypoints
if not os.path.exists('build/_scripts'):
    os.makedirs('build/_scripts')
shutil.copyfile('scripts/rpmlint.py', 'build/_scripts/rpmlint')
shutil.copyfile('scripts/rpmdiff.py', 'build/_scripts/rpmdiff')

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Archiving :: Packaging',
    ],
    platforms=['Linux'],
    keywords=['RPM', '.spec', 'validator'],

    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov', 'pytest-flake8'],

    packages=['rpmlint'],

    data_files=[
        ('share/man/man1', glob.glob('man/*.1')),
        ('share/rpmlint', ['config']),
    ],
    scripts=[
        'build/_scripts/rpmlint',
        'build/_scripts/rpmdiff',
    ],
)
