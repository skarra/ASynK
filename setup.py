#!/usr/bin/python
##
## SPDX-FileCopyrightText: 2013 Cyril Bouthors <cyril@bouthors.org>
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

from setuptools import setup, find_packages

_google_deps = [
    'google-api-python-client>=2.0',
    'google-auth-httplib2>=0.1',
    'google-auth-oauthlib>=1.0',
]

_carddav_deps = [
    'caldav>=1.3.0',
]

_exchange_deps = [
    'msal>=1.28',
    'requests>=2.28',
]

setup(
    name='asynk',
    version='0.4.1',
    description='Synchronizes contacts across Google, CardDAV, Exchange, '
                'Outlook and BBDB',
    author='Sriram Karra',
    author_email='karra.etc@gmail.com',
    url='https://karra-asynk.appspot.com/',
    packages=find_packages(),

    python_requires='>=3.8',

    ## Core dependencies — always installed
    install_requires=[
        'demjson3>=3.0',
        'iso8601>=2.1',
        'simplejson>=3.0',
        'vobject>=0.9',
        'httplib2>=0.20',
    ],

    ## Optional backend-specific dependencies
    extras_require={
        'google':   _google_deps,
        'carddav':  _carddav_deps,
        'exchange': _exchange_deps,
        'all':      _google_deps + _carddav_deps + _exchange_deps,
    },
)
