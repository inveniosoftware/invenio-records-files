# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_cli import FlaskCLI
from invenio_db import db as db_
from invenio_db import InvenioDB
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location
from invenio_records import InvenioRecords
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_records_files.api import Record, RecordsBuckets


@pytest.yield_fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app_ = Flask(__name__, instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='CHANGE_ME',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite://'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
    )
    FlaskCLI(app_)
    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioFilesREST(app_)

    with app_.app_context():
        yield app_

    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


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
def bucket(location, db):
    """Create a bucket."""
    b = Bucket.create()
    db.session.commit()
    return b


@pytest.fixture()
def record_with_bucket(record, bucket, db):
    """Create a bucket."""
    record.model.records_buckets = RecordsBuckets(bucket=bucket)
    db.session.commit()
    return record


@pytest.fixture()
def generic_file(app, record):
    """Add a generic file to the record."""
    stream = BytesIO(b'test example')
    filename = 'generic_file.txt'
    record.files[filename] = stream
    db_.session.commit()
    return filename
