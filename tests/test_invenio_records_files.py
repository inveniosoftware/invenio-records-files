# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import mock
import pytest
from flask import url_for
from invenio_files_rest.errors import InvalidOperationError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records.api import Record as BaseRecord
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata
from six import BytesIO

from invenio_records_files.api import FilesMixin, Record, RecordsBuckets
from invenio_records_files.links import default_bucket_link_factory
from invenio_records_files.utils import record_file_factory


def test_version():
    """Test version import."""
    from invenio_records_files import __version__
    assert __version__


def test_jsonschemas_import():
    """Test jsonschemas import."""
    from invenio_records_files import jsonschemas


def test_missing_location(app, db):
    """Test missing location."""
    assert Record.create({}).files is None


def test_files_property(app, db, location, bucket):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        Record({}).files

    record = Record.create({})
    RecordsBuckets.create(bucket=bucket, record=record.model)

    assert 0 == len(record.files)
    assert 'invalid' not in record.files
    # make sure that _files key is not added after accessing record.files
    assert '_files' not in record

    with pytest.raises(KeyError):
        record.files['invalid']

    bucket = record.files.bucket
    assert bucket

    # Create first file:
    record.files['hello.txt'] = BytesIO(b'Hello world!')

    file_0 = record.files['hello.txt']
    assert 'hello.txt' == file_0['key']
    assert 1 == len(record.files)
    assert 1 == len(record['_files'])

    # Update first file with new content:
    record.files['hello.txt'] = BytesIO(b'Hola mundo!')
    file_1 = record.files['hello.txt']
    assert 'hello.txt' == file_1['key']
    assert 1 == len(record.files)
    assert 1 == len(record['_files'])

    assert file_0['version_id'] != file_1['version_id']

    # Create second file and check number of items in files.
    record.files['second.txt'] = BytesIO(b'Second file.')
    record.files['second.txt']
    assert 2 == len(record.files)
    assert 'hello.txt' in record.files
    assert 'second.txt' in record.files

    # Check order of files.
    order_0 = [f['key'] for f in record.files]
    assert ['hello.txt', 'second.txt'] == order_0

    record.files.sort_by(*reversed(order_0))
    order_1 = [f['key'] for f in record.files]
    assert ['second.txt', 'hello.txt'] == order_1

    # Try to rename second file to 'hello.txt'.
    with pytest.raises(Exception):
        record.files.rename('second.txt', 'hello.txt')

    # Remove the 'hello.txt' file.
    del record.files['hello.txt']
    assert 'hello.txt' not in record.files
    # Make sure that 'second.txt' is still there.
    assert 'second.txt' in record.files

    with pytest.raises(KeyError):
        del record.files['hello.txt']

    # Now you can rename 'second.txt' to 'hello.txt'.
    record.files.rename('second.txt', 'hello.txt')
    assert 'second.txt' not in record.files
    assert 'hello.txt' in record.files


def test_files_unicode(app, db, location, record_with_bucket):
    record = record_with_bucket

    # Create a file with a unicode filename.
    record.files[u'hellö.txt'] = BytesIO(b'Hello world!')
    assert u'hellö.txt' in record.files


def test_files_extra_data(app, db, location, record_with_bucket):
    """Test record files property."""
    record = record_with_bucket

    # Create a file.
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    record['_files'] = record.files.dumps()
    assert record['_files'][0].get('type') is None

    # Set some metadata
    record.files['hello.txt']['type'] = 'txt'
    assert record.files['hello.txt']['type'] == 'txt'
    assert record.files['hello.txt'].get('type') == 'txt'
    assert record.files['hello.txt'].get('invalid', 'default') == 'default'
    assert record['_files'][0]['type'] == 'txt'

    # Dump it and get it again
    record['_files'] = record.files.dumps()
    assert record['_files'][0]['type'] == 'txt'
    assert record.files['hello.txt']['type'] == 'txt'

    # You cannot set a protected key (i.e. anything on ObjectVersion)
    for k in ['bucket', 'bucket_id', 'key', 'version_id', 'file_id', 'file',
              'is_head']:
        try:
            record.files['hello.txt'][k] = 'txt'
            assert False, "Could set a protected key {0}".format(k)
        except KeyError:
            pass
        assert record.files['hello.txt'].get(k)


def test_files_extra_data_in_dump(app, db, location, record_with_bucket):
    """Test if all neccessary properties are included in dumps() method."""
    record = record_with_bucket

    # Create a file.
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    record['_files'] = record.files.dumps()

    for k in ['bucket', 'checksum', 'key', 'size', 'version_id', 'file_id']:
        assert k in record['_files'][0]


def test_files_protection(app, db, location, record_with_bucket):
    """Test record files property protection."""
    record = record_with_bucket

    bucket = record.files.bucket
    assert bucket

    # Create first file:
    record.files['hello.txt'] = BytesIO(b'Hello world!')

    file_0 = record.files['hello.txt']
    assert 'hello.txt' == file_0['key']
    assert 1 == len(record.files)

    # Lock bucket.
    bucket.locked = True

    assert record.files.bucket.locked
    with pytest.raises(InvalidOperationError):
        del record.files['hello.txt']


def test_filesmixin(app, db, location, record):
    """Test bucket creation and assignment."""
    class CustomFilesMixin(FilesMixin):
        def _create_bucket(self):
            return Bucket.create()

    class CustomRecord(Record, CustomFilesMixin):
        pass

    record = CustomRecord.create({})
    assert record.files is not None

    record = Record.create({})
    assert record.files is None


def test_filesdescriptor(app, db, location, bucket,
                         record_with_bucket):
    """Test direct modification files property."""
    record = record_with_bucket

    record.files = {'hello.txt': BytesIO(b'Hello world!')}

    assert len(record.files) == 1
    assert len(record['_files']) == 1

    with pytest.raises(RuntimeError):
        record.files = {'world.txt': BytesIO(b'Hello world!')}


def test_bucket_modification(app, db, location, bucket,
                             record_with_bucket):
    """Test direct modification of bucket."""
    record = record_with_bucket

    record.files['hello.txt'] = BytesIO(b'Hello world!')
    record.files['hello.txt']['type'] = 'txt'

    # Modify bucket outside of record.files property
    ObjectVersion.create(bucket, 'second.txt', stream=BytesIO(b'Second'))

    # Bucket and record are out of sync:
    assert len(record.files) == 2
    assert len(record['_files']) == 1

    # Flush changes to ensure they are in sync.
    record.files.flush()
    assert len(record['_files']) == 2

    # Check that extra metadata is not overwritten.
    assert [f.get('type') for f in record.files] == ['txt', None]


def test_get_version(app, db, location, record_with_bucket):
    """Test bucket creation and assignment."""
    record = record_with_bucket
    record.files['hello.txt'] = BytesIO(b'v1')
    v1 = record.files['hello.txt'].version_id
    record.files['hello.txt'] = BytesIO(b'v2')
    v2 = record.files['hello.txt'].version_id
    assert v2 != v1
    assert record.files['hello.txt'].get_version().version_id == v2
    assert record.files['hello.txt'].get_version(v1).version_id == v1


def test_record_files_factory(app, db, location, record_with_bucket):
    """Test record file factory."""
    record = record_with_bucket
    record.files['test.txt'] = BytesIO(b'Hello world!')

    # Get a valid file
    fileobj = record_file_factory(None, record, 'test.txt')
    assert fileobj.key == 'test.txt'

    # Get a invalid file
    assert record_file_factory(None, record, 'invalid') is None

    # Record has no files property
    assert record_file_factory(None, Record({}), 'invalid') is None
    assert record_file_factory(None, BaseRecord({}), 'invalid') is None
    baserecord = BaseRecord.create({})
    RecordsBuckets(bucket=Bucket.create(), record=baserecord)
    assert record_file_factory(None, baserecord, 'invalid') is None


def test_bucket_link_factory_no_bucket(app, db, location, record):
    """Test bucket link factory without a bucket."""
    assert default_bucket_link_factory(None) is None


def test_bucket_link_factory_has_bucket(app, db, location, bucket):
    """Test bucket link factory retrieval of a bucket."""
    with app.test_request_context():
        with db.session.begin_nested():
            record = RecordMetadata()
            RecordsBuckets.create(record, bucket)
            db.session.add(record)
        pid = mock.Mock()
        pid.get_assigned_object.return_value = record.id
        assert default_bucket_link_factory(pid) == url_for(
            'invenio_files_rest.bucket_api', bucket_id=bucket.id,
            _external=True)


def test_alembic(app, db):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
