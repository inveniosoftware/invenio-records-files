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


"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask
from invenio_files_rest.errors import InvalidOperationError
from invenio_records.errors import MissingModelError
from six import BytesIO

from invenio_records_files.api import Record


def test_version():
    """Test version import."""
    from invenio_records_files import __version__
    assert __version__


def test_missing_location(app, db):
    """Test missing location."""
    assert Record.create({}).files is None


def test_files_property(app, db, location):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        Record({}).files

    record = Record.create({})

    assert 0 == len(record.files)
    assert 'invalid' not in record.files

    with pytest.raises(KeyError):
        record.files['invalid']

    bucket = record.files.bucket
    assert bucket

    # Create first file:
    record.files['hello.txt'] = BytesIO(b'Hello world!')

    file_0 = record.files['hello.txt']
    assert 'hello.txt' == file_0['key']
    assert 1 == len(record.files)

    # Update first file with new content:
    record.files['hello.txt'] = BytesIO(b'Hola mundo!')
    file_1 = record.files['hello.txt']
    assert 'hello.txt' == file_1['key']
    assert 1 == len(record.files)

    assert file_0['version_id'] != file_1['version_id']

    # Create second file and check number of items in files.
    record.files['second.txt'] = BytesIO(b'Second file.')
    file_2 = record.files['second.txt']
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


def test_files_protection(app, db, location):
    """Test record files property protection."""
    record = Record.create({})

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
