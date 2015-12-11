#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'lxml>=3.4',
    'pySerial>=2.7',
]

test_requirements = [
    'nose>=1.3.4',
]

import sys
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 3):
    test_requirements += [
        'mock>=1.0.1',
    ]
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 4):
    requirements += [
        'enum34>=1.0.4',
    ]

setup(
    name='ticketml',
    version='0.2.3',
    description="TicketML is a simple markup language for receipt printers",
    long_description=readme + '\n\n' + history,
    author="Luke Granger-Brown",
    author_email='git@lukegb.com',
    url='https://github.com/lukegb/ticketml',
    packages=[
        'ticketml',
    ],
    package_dir={'ticketml':
                 'ticketml'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='ticketml',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'ticketml_print = ticketml.example_print:main',
        ],
    },
)
