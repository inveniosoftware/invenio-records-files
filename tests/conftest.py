# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
# Copyright (C) 2025 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

import os
import tempfile
import uuid
from copy import deepcopy

import pytest
from flask import Flask
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

from invenio_records_files import InvenioRecordsFiles
from invenio_records_files.api import Record
from invenio_records_files.views import create_blueprint_from_app


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture for use with pytest-invenio."""

    def _create_app(**config):
        app_ = Flask(
            __name__,
            instance_path=instance_path,
        )

        RECORDS_REST_ENDPOINTS_COPY = deepcopy(RECORDS_REST_ENDPOINTS)

        docid = deepcopy(RECORDS_REST_ENDPOINTS['recid'])
        docid['list_route'] = '/doc/'
        docid['item_route'] = '/doc/<pid(recid):pid_value>'
        RECORDS_REST_ENDPOINTS_COPY.update(
            docid=docid
        )
        # Endpoint with files support
        RECORDS_REST_ENDPOINTS_COPY['recid'].update(
            record_class=Record,
            item_route=(
                '/records/<pid(recid, record_class="invenio_records_files.api.Record"):pid_value>'  # noqa
            ),
            indexer_class=None,
        )

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
                    'docid': 'nofiles',
                }
            },
            RECORDS_REST_ENDPOINTS=RECORDS_REST_ENDPOINTS_COPY,
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

        return app_

    return _create_app


@pytest.fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


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
