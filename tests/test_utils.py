# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test utility functions."""

from __future__ import absolute_import, print_function

import pytest
from invenio_files_rest.models import Bucket
from invenio_records.api import Record as BaseRecord
from six import BytesIO
from werkzeug.exceptions import NotFound

from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets
from invenio_records_files.utils import file_download_ui, record_file_factory


def test_file_download_ui(app, db, location, record, generic_file):
    """Test file download UI."""
    with app.test_request_context():
        pid = type('PID', (object, ), {'pid_type': 'demo', 'pid_value': '1'})()
        response = file_download_ui(
            pid, record, filename=generic_file
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'

        response = file_download_ui(
            pid, record, filename=generic_file
        )

        with pytest.raises(NotFound):
            file_download_ui(pid, record)

        with pytest.raises(NotFound):
            file_download_ui(pid, record, filename='not_found')

    with app.test_request_context('/?download'):
        response = file_download_ui(
            pid, record, filename=generic_file
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'
        assert response.headers['Content-Disposition'] == \
            'attachment; filename={}'.format(generic_file)


def test_record_files_factory(app, db, location, record):
    """Test record file factory."""
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
