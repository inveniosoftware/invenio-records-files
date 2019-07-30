# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test API."""

from __future__ import absolute_import, print_function

import pytest
from invenio_files_rest.errors import InvalidOperationError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records.api import Record as BaseRecord
from invenio_records.errors import MissingModelError
from six import BytesIO

from invenio_records_files.api import Record


def test_missing_location(app, db):
    """Test missing location."""
    with pytest.raises(AttributeError):
        Record.create({}).files


def test_record_create(app, db, location):
    """Test record creation with only bucket."""
    record = Record.create({'title': 'test'})
    db.session.commit()
    assert record['_bucket'] == record.bucket_id
    assert '_files' not in record


def test_record_create_files(app, db, location):
    """Test record creation with bucket and files."""
    record = Record.create({'title': 'test'})
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    db.session.commit()
    assert record['_bucket'] == record.bucket_id
    assert record['_files']


def test_record_create_no_bucket(app, db, location):
    """Test record creation without bucket creation."""
    record = Record.create({}, with_bucket=False)
    db.session.commit()
    assert record.files is None
    assert '_bucket' not in record
    assert '_files' not in record


def test_record_custom_dumpload(app, db, location):
    """Test custom dump/load functions."""
    class MyRecord(Record):
        @classmethod
        def dump_bucket(cls, data, bucket):
            if '_buckets' not in data:
                data['_buckets'] = {}
            data['_buckets']['record'] = str(bucket.id)

        @classmethod
        def load_bucket(cls, record):
            return record.get('_buckets', {}).get('record')

    record = MyRecord.create({'title': 'test'})
    db.session.commit()
    assert record['_buckets']['record'] == record.bucket_id


def test_record_custom_bucket_creation(app, db, location):
    """Test custom dump/load functions."""
    class MyRecord(Record):
        @classmethod
        def create_bucket(cls, data):
            if data['with_bucket']:
                return Bucket.create()

    record = MyRecord.create({'with_bucket': True})
    assert record['_bucket']
    record = MyRecord.create({'with_bucket': False})
    assert '_bucket' not in record


def test_record_get_bucket(app, db, location):
    """Test retrival of the bucket from the record."""
    record = Record.create({'title': 'test'})
    db.session.commit()
    record = Record.get_record(record.id)
    assert str(record.bucket.id) == record['_bucket']


def test_record_get_bucket_with_no_bucket(app, db, location):
    """Test retrival of the bucket when no bucket is associated."""
    record = Record.create({'title': 'test'}, with_bucket=False)
    db.session.commit()
    record = Record.get_record(record.id)
    assert record.bucket is None
    assert record.files is None


def test_files_property(app, db, location):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        Record({}).files

    record = Record.create({})

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


def test_files_unicode(app, db, location, record):
    # Create a file with a unicode filename.
    record.files[u'hellö.txt'] = BytesIO(b'Hello world!')
    assert u'hellö.txt' in record.files


def test_files_extra_data(app, db, location, record):
    """Test record files property."""
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


def test_files_extra_data_in_dump(app, db, location, record):
    """Test if all neccessary properties are included in dumps() method."""
    # Create a file.
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    record['_files'] = record.files.dumps()

    for k in ['bucket', 'checksum', 'key', 'size', 'version_id', 'file_id']:
        assert k in record['_files'][0]


def test_files_protection(app, db, location, record):
    """Test record files property protection."""
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


def test_filesdescriptor(app, db, location, bucket, record):
    """Test direct modification files property."""
    record.files = {'hello.txt': BytesIO(b'Hello world!')}

    assert len(record.files) == 1
    assert len(record['_files']) == 1

    with pytest.raises(RuntimeError):
        record.files = {'world.txt': BytesIO(b'Hello world!')}


def test_bucket_modification(app, db, location, record):
    """Test direct modification of bucket."""
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    record.files['hello.txt']['type'] = 'txt'

    # Modify bucket outside of record.files property
    ObjectVersion.create(
        record.bucket, 'second.txt', stream=BytesIO(b'Second'))

    # Bucket and record are out of sync:
    assert len(record.files) == 2
    assert len(record['_files']) == 1

    # Flush changes to ensure they are in sync.
    record.files.flush()
    assert len(record['_files']) == 2

    # Check that extra metadata is not overwritten.
    assert [f.get('type') for f in record.files] == ['txt', None]


def test_get_version(app, db, location, record):
    """Test bucket creation and assignment."""
    record.files['hello.txt'] = BytesIO(b'v1')
    v1 = record.files['hello.txt'].version_id
    record.files['hello.txt'] = BytesIO(b'v2')
    v2 = record.files['hello.txt'].version_id
    assert v2 != v1
    assert record.files['hello.txt'].get_version().version_id == v2
    assert record.files['hello.txt'].get_version(v1).version_id == v1
