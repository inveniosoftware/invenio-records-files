# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import imp
import json
import os
import shutil
import sys
import tempfile
import uuid
from copy import deepcopy

import pytest
from flask import Flask
from flask_login import LoginManager
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location
from invenio_files_rest.views import blueprint as files_rest_blueprint
from invenio_indexer import InvenioIndexer
from invenio_pidstore import InvenioPIDStore, current_pidstore
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.config import RECORDS_REST_ENDPOINTS
from invenio_records_rest.utils import PIDConverter, allow_all
from invenio_records_rest.views import \
    create_blueprint_from_app as records_rest_create_blueprint_from_app
from invenio_search import InvenioSearch
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_records_files import InvenioRecordsFiles
from invenio_records_files.api import FilesMixin, Record, RecordsBuckets
from invenio_records_files.views import create_blueprint_from_app


@pytest.fixture
def docid_record_type_endpoint():
    """."""
    docid = deepcopy(RECORDS_REST_ENDPOINTS['recid'])
    docid['list_route'] = '/doc/'
    docid['item_route'] = '/doc/<pid(recid):pid_value>'
    return docid


@pytest.fixture
def basic_record_type_endpoint():
    """."""
    basic = deepcopy(RECORDS_REST_ENDPOINTS['recid'])
    basic['list_route'] = '/basic/'
    basic['item_route'] = '/basic/<pid(recid):pid_value>'
    return basic


@pytest.fixture()
def RecordWithBucketCreation():
    """Add _create_bucket implementation to record class"""
    from invenio_records_files.api import Record

    module_name = 'test_api'
    test_api_module = imp.new_module(module_name)
    test_api_module.Record = Record
    sys.modules[module_name] = test_api_module
    return Record


@pytest.fixture()
def RecordWithoutFilesCreation():
    """Add _create_bucket implementation to record class"""
    from invenio_records.api import Record as RecordWithoutFiles

    module_name = 'test_api_no_files'
    test_api_module = imp.new_module(module_name)
    test_api_module.RecordWithoutFiles = RecordWithoutFiles
    sys.modules[module_name] = test_api_module
    return RecordWithoutFiles


@pytest.yield_fixture()
def app(request, docid_record_type_endpoint, basic_record_type_endpoint):
    """Flask application fixture."""
    from invenio_records.api import Record
    from invenio_records_files.api import Record as RecordFiles

    instance_path = tempfile.mkdtemp()
    app_ = Flask(__name__, instance_path=instance_path)

    RECORDS_REST_ENDPOINTS.update(
        docid=docid_record_type_endpoint,
        basic=basic_record_type_endpoint
    )

    # Endpoint with files support
    RECORDS_REST_ENDPOINTS['recid']['record_class'] = RecordFiles
    RECORDS_REST_ENDPOINTS['recid']['item_route'] = \
        '/records/<pid(recid, ' \
        'record_class="invenio_records_files.api.Record"):pid_value>'
    RECORDS_REST_ENDPOINTS['recid']['indexer_class'] = None

    # Endpoint without files support
    RECORDS_REST_ENDPOINTS['basic']['record_class'] = Record
    RECORDS_REST_ENDPOINTS['basic']['item_route'] = \
        '/records/<pid(recid, ' \
        'record_class="invenio_records.api.Record"):pid_value>'
    RECORDS_REST_ENDPOINTS['basic']['indexer_class'] = None

    # Application
    app_.config.update(
        FILES_REST_PERMISSION_FACTORY=lambda *a, **kw: type(
            'Allow', (object, ), {'can': lambda self: True}
        )(),
        SECRET_KEY='CHANGE_ME',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite://'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        RECORDS_FILES_REST_ENDPOINTS={
            'RECORDS_REST_ENDPOINTS': {
                'recid': 'files',
                'basic': 'nofiles',
            }
        },
        RECORDS_REST_ENDPOINTS=RECORDS_REST_ENDPOINTS,
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=allow_all,
    )

    app_.url_map.converters['pid'] = PIDConverter
    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioFilesREST(app_)
    InvenioIndexer(app_)
    InvenioPIDStore(app_)
    InvenioRecordsREST(app_)
    InvenioRecordsFiles(app_)
    app_.register_blueprint(files_rest_blueprint)
    app_.register_blueprint(create_blueprint_from_app(app_))
    app_.register_blueprint(records_rest_create_blueprint_from_app(app_))
    search = InvenioSearch(app_)
    search.register_mappings('records-files', 'data')

    with app_.app_context():
        yield app_

    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    drop_database(str(db_.engine.url))


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


@pytest.fixture()
def record(app, db):
    """Create a record."""
    record = {
        'title': 'fuu'
    }
    record = Record.create(record)
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def minted_record(app, db):
    """Create a test record."""
    data = {
        'title': 'fuu'
    }
    with db.session.begin_nested():
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid)
    return pid, record


@pytest.fixture()
def minted_record_no_bucket(app, db):
    """Create a test record."""
    data = {
        'title': 'fuu'
    }
    with db.session.begin_nested():
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid, with_bucket=False)
    return pid, record


@pytest.fixture()
def bucket(location, db):
    """Create a bucket."""
    b = Bucket.create()
    db.session.commit()
    return b


@pytest.fixture()
def generic_file(app, record):
    """Add a generic file to the record."""
    stream = BytesIO(b'test example')
    filename = 'generic_file.txt'
    record.files[filename] = stream
    record.files.dumps()
    record.commit()
    db_.session.commit()
    return filename
