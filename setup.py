#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup file for easy installation."""
from setuptools import setup
import glob
from rpmlint import __version__

setup(
    name='rpmlint',
    description='RPM file QA correctness validator',
    long_description='Command-line tool for RPM files QA validation',
    url='https://github.com/rpm-software-management/rpmlint',
    download_url='https://github.com/rpm-software-management/rpmlint',

    version=__version__,

    author='Frédéric Lepied',
    author_email='flepied@mandriva.com',

    maintainer='Neal Gompa',
    maintainer_email='ngompa13@gmail.com',

    license='License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE V2 OR LATER (GPLV2+)',
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE V2 OR LATER (GPLV2+)',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Text Processing',
    ],
    platforms=['Linux'],
    keywords=['RPM', '.spec', 'validator'],

    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],

    packages=['rpmlint'],

    data_files=[
        ('lib/obs/service/', glob.glob('obs/*')),
        ('share/spec-cleaner', glob.glob('data/*')),
    ],

    entry_points={
        'console_scripts': ['rpmlint = spec_cleaner:main']},
)
