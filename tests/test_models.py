# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test module."""

from __future__ import absolute_import, print_function

import pytest
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from six import BytesIO
from sqlalchemy.orm.exc import NoResultFound

from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets


@pytest.mark.parametrize('force,num_of_recordbuckets', [(False, 1), (True, 0)])
def test_cascade_action_record_delete(app, db, location, record, generic_file,
                                      force, num_of_recordbuckets):
    """Test cascade action on record delete, with force false."""
    record_id = record.id
    bucket_id = record.files.bucket.id

    # check before
    assert len(RecordsBuckets.query.all()) == 1
    assert len(Bucket.query.all()) == 1
    assert len(Bucket.query.filter_by(id=bucket_id).all()) == 1
    assert ObjectVersion.get(bucket=bucket_id, key=generic_file)

    record.delete(force=force)

    # check after
    db.session.expunge(record.model)
    with pytest.raises(NoResultFound):
        record = Record.get_record(record_id)
    assert len(RecordsBuckets.query.all()) == num_of_recordbuckets
    assert len(Bucket.query.all()) == 1
    assert len(Bucket.query.filter_by(id=bucket_id).all()) == 1
    assert ObjectVersion.get(bucket=bucket_id, key=generic_file)


def test_creating_missing_bucket(
        app, db, client, location, RecordWithBucketCreation):
    record = RecordWithBucketCreation.create({'title': 'fuu'})
    record.files = {'test.txt': BytesIO(b'Test file data')}
    assert 'test.txt' in record.files
