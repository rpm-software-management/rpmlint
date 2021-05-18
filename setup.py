from setuptools import setup


setup(
    name='rpmlint',
    description='Check for common errors in RPM packages',
    long_description=('Rpmlint is a tool to check common errors in RPM packages.'
                      'Binary and source packages can be checked'),
    url='https://github.com/rpm-software-management/rpmlint',
    download_url='https://github.com/rpm-software-management/rpmlint',

    version='2.0.0',

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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Archiving :: Packaging',
    ],
    platforms=['Linux'],
    keywords=['RPM', '.spec', 'validator'],

    install_requires=[
        'pybeam',
        'pyxdg',
        'rpm',
        'toml',
        'zstd',
        'importlib-metadata;python_version<"3.8"',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-flake8',
        'pytest-xdist',
    ],

    packages=[
        'rpmlint',
        'rpmlint.checks',
    ],
    package_data={
        'rpmlint': ['configdefaults.toml'],
        'rpmlint.descriptions': ['*.toml'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'rpmdiff = rpmlint.cli:diff',
            'rpmlint = rpmlint.cli:lint',
        ],
    },
)
