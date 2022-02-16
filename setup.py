# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio modules that integrates records and files."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'invenio-indexer>=1.1.0',
    'invenio-search[elasticsearch6]>=1.2.0',
    'mock>=1.3.0',
    'pytest-invenio>=1.4.0'
]

extras_require = {
    'docs': [
        'Sphinx>=3',
    ],
    'mysql': [
        'invenio-db[mysql,versioning]>=1.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]>=1.0.0',
    ],
    'sqlite': [
        'invenio-db[versioning]>=1.0.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)


install_requires = [
    'invenio-base>=1.2.5',
    'invenio-files-rest>=1.3.0',
    'invenio-records>=1.0.0',
    'invenio-records-rest>=1.6.3',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_records_files', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-records-files',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio records files',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-records-files',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_db.alembic': [
            'invenio_records_files = invenio_records_files:alembic',
        ],
        'invenio_db.models': [
            'invenio_records_files = invenio_records_files.models',
        ],
        'invenio_jsonschemas.schemas': [
            'records_files = invenio_records_files.jsonschemas',
        ],
        'invenio_base.apps': [
            'invenio_records_files = invenio_records_files:InvenioRecordsFiles'
        ],
        'invenio_base.api_apps': [
            'invenio_records_files = invenio_records_files:InvenioRecordsFiles'
        ],
        'invenio_base.api_blueprints': [
            'invenio_records_files = invenio_records_files.'
            'views:create_blueprint_from_app',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
