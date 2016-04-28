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

"""API for manipulating files associated to a record."""

from functools import wraps

from flask import current_app
from invenio_db import db
from invenio_files_rest.errors import InvalidOperationError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records.api import Record as _Record
from invenio_records.errors import MissingModelError
from sqlalchemy.exc import IntegrityError

from .models import RecordsBuckets
from .utils import sorted_files_from_bucket


class FileObject(object):
    """Wrapper for files."""

    def __init__(self, bucket, obj):
        """Bind to current bucket."""
        self.obj = obj
        self.bucket = bucket

    def get_version(self, version_id=None):
        """Return specific version ``ObjectVersion`` instance or HEAD."""
        return ObjectVersion.get(bucket=self.bucket, key=self.obj.key,
                                 version_id=version_id)

    def __getattr__(self, key):
        """Proxy to ``obj``."""
        return getattr(self.obj, key)

    def __getitem__(self, key):
        """Proxy to ``obj``."""
        return getattr(self.obj, key)


def _writable(method):
    """Check that record is in defined status."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Send record for indexing."""
        if self.bucket.locked or self.bucket.deleted:
            raise InvalidOperationError()
        return method(self, *args, **kwargs)
    return wrapper


class FilesIterator(object):
    """Iterator for files."""

    def __init__(self, record, bucket):
        """Initialize iterator."""
        self._it = None
        self.record = record
        self.model = record.model
        self.bucket = bucket

        self.record.setdefault('_files', [])

    @property
    def keys(self):
        """Return file keys."""
        return [file_['key'] for file_ in self.record['_files']]

    def __len__(self):
        """Get number of files."""
        return ObjectVersion.get_by_bucket(self.bucket).count()

    def __iter__(self):
        """Get iterator."""
        self._it = iter(sorted_files_from_bucket(
            self.bucket, self.keys
        ))
        return self

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next file item."""
        obj = next(self._it)
        return FileObject(self.bucket, obj)

    def __contains__(self, key):
        """Test if file exists."""
        return ObjectVersion.get_by_bucket(
            self.bucket).filter_by(key=str(key)).count()

    def __getitem__(self, key):
        """Get a specific file."""
        obj = ObjectVersion.get(self.bucket, key)
        if obj:
            return FileObject(self.bucket, obj)
        raise KeyError(key)

    @_writable
    def __setitem__(self, key, stream):
        """Add file inside a deposit."""
        with db.session.begin_nested():
            # save the file
            obj = ObjectVersion.create(bucket=self.bucket, key=key,
                                       stream=stream)

            # update deposit['_files']
            if key not in self.record['_files']:
                self.record['_files'].append({'key': key})

    @_writable
    def __delitem__(self, key):
        """Delete a file from the deposit."""
        obj = ObjectVersion.delete(bucket=self.bucket, key=key)
        self.record['_files'] = [file_ for file_ in self.record['_files']
                                 if file_['key'] != key]
        if obj is None:
            raise KeyError(key)

    def sort_by(self, *ids):
        """Update files order."""
        files = {str(f_.file_id): f_.key for f_ in self}
        self.record['_files'] = [{'key': files.get(id_, id_)} for id_ in ids]

    @_writable
    def rename(self, old_key, new_key):
        """Rename a file."""
        assert new_key not in self

        file_ = self[old_key]
        # create a new version with the new name
        obj = ObjectVersion.create(
            bucket=self.bucket, key=new_key,
            _file_id=file_.obj.file_id
        )
        self.record['_files'][self.keys.index(old_key)]['key'] = new_key
        # delete the old version
        ObjectVersion.delete(bucket=self.bucket, key=old_key)
        return obj

    def dumps(self, bucket=None):
        """Serialize files from a bucket."""
        return [{
            'bucket': str(file_.bucket_id),
            'checksum': file_.file.checksum,
            'key': file_.key,  # IMPORTANT it must stay here!
            'size': file_.file.size,
            'version_id': str(file_.version_id),
        } for file_ in sorted_files_from_bucket(
            bucket or self.bucket, self.keys
        )]


class FilesMixin(object):
    """Implement files attribute for Record models."""

    def _create_bucket(self):
        """Return an instance of ``Bucket`` class.

        .. note:: Reimplement in children class for custom behavior.
        """
        return Bucket.create()

    @property
    def files(self):
        """Get files iterator."""
        if self.model is None:
            raise MissingModelError()

        if not self.model.records_buckets:
            try:
                self.model.records_buckets = RecordsBuckets(
                    bucket=self._create_bucket()
                )
            except IntegrityError:
                current_app.logger.exception('Check default bucket location.')
                return None

        return FilesIterator(self, bucket=self.model.records_buckets.bucket)


class Record(_Record, FilesMixin):
    """Define API for files manipulation using ``FilesMixin``."""
