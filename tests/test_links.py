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
from invenio_files_rest.models import Bucket
from invenio_records.models import RecordMetadata

from invenio_records_files.api import Record, RecordsBuckets
from invenio_records_files.links import default_bucket_link_factory


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
