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


"""Test module."""

from __future__ import absolute_import, print_function

import pytest
from invenio_files_rest.models import Bucket, ObjectVersion
from sqlalchemy.orm.exc import NoResultFound

from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets


@pytest.mark.parametrize('force,num_of_recordbuckets', [(False, 1), (True, 0)])
def test_cascade_action_record_delete(app, db, location, record_with_bucket,
                                      generic_file, force,
                                      num_of_recordbuckets):
    """Test cascade action on record delete, with force false."""
    record = record_with_bucket
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
