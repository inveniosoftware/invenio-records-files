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

from collections import OrderedDict
from functools import wraps

from invenio_db import db
from invenio_files_rest.errors import InvalidOperationError
from invenio_files_rest.models import ObjectVersion
from invenio_records.api import Record as _Record
from invenio_records.errors import MissingModelError

from .models import RecordsBuckets
from .utils import sorted_files_from_bucket


class FileObject(object):
    """Wrapper for files."""

    def __init__(self, obj, data):
        """Bind to current bucket."""
        self.obj = obj
        self.data = data

    def get_version(self, version_id=None):
        """Return specific version ``ObjectVersion`` instance or HEAD."""
        return ObjectVersion.get(bucket=self.obj.bucket, key=self.obj.key,
                                 version_id=version_id)

    def __getattr__(self, key):
        """Proxy to ``obj``."""
        return getattr(self.obj, key)

    def __getitem__(self, key):
        """Proxy to ``obj`` and ``data``."""
        if hasattr(self.obj, key):
            return getattr(self.obj, key)
        return self.data[key]

    def __setitem__(self, key, value):
        """Proxy to ``data``."""
        if hasattr(self.obj, key):
            raise KeyError(key)
        self.data[key] = value

    def dumps(self):
        """Create a dump."""
        self.data.update({
            'bucket': str(self.obj.bucket_id),
            'checksum': self.obj.file.checksum,
            'key': self.obj.key,  # IMPORTANT it must stay here!
            'size': self.obj.file.size,
            'version_id': str(self.obj.version_id),
        })
        return self.data


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
        self.filesmap = OrderedDict([
            (f['key'], f) for f in self.record['_files']
        ])

    @property
    def keys(self):
        """Return file keys."""
        return self.filesmap.keys()

    def __len__(self):
        """Get number of files."""
        return ObjectVersion.get_by_bucket(self.bucket).count()

    def __iter__(self):
        """Get iterator."""
        self._it = iter(sorted_files_from_bucket(self.bucket, self.keys))
        return self

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next file item."""
        obj = next(self._it)
        return FileObject(obj, self.filesmap.get(obj.key, {}))

    def __contains__(self, key):
        """Test if file exists."""
        return ObjectVersion.get_by_bucket(
            self.bucket).filter_by(key=str(key)).count()

    def __getitem__(self, key):
        """Get a specific file."""
        obj = ObjectVersion.get(self.bucket, key)
        if obj:
            return FileObject(obj, self.filesmap.get(obj.key, {}))
        raise KeyError(key)

    def flush(self):
        """Flush changes to record."""
        self.record['_files'] = list(self.filesmap.values())

    @_writable
    def __setitem__(self, key, stream):
        """Add file inside a deposit."""
        with db.session.begin_nested():
            # save the file
            obj = ObjectVersion.create(
                bucket=self.bucket, key=key, stream=stream)
            self.filesmap[key] = FileObject(obj, {}).dumps()
            self.flush()

    @_writable
    def __delitem__(self, key):
        """Delete a file from the deposit."""
        obj = ObjectVersion.delete(bucket=self.bucket, key=key)

        if obj is None:
            raise KeyError(key)

        if key in self.filesmap:
            del self.filesmap[key]
            self.flush()

    def sort_by(self, *ids):
        """Update files order."""
        assert len(self.filesmap) == len(ids)

        self.filesmap = OrderedDict([(f['key'], f) for f in sorted(
            self.filesmap.values(),
            key=lambda x: ids.index(x['key'])
        )])
        self.flush()

    @_writable
    def rename(self, old_key, new_key):
        """Rename a file."""
        assert new_key not in self
        assert old_key != new_key

        file_ = self[old_key]
        old_data = self.filesmap[old_key]

        # Create a new version with the new name
        obj = ObjectVersion.create(
            bucket=self.bucket, key=new_key,
            _file_id=file_.obj.file_id
        )

        # Delete old key
        self.filesmap[new_key] = FileObject(obj, old_data).dumps()
        del self[old_key]

        return obj

    def dumps(self, bucket=None):
        """Serialize files from a bucket."""
        return [
            FileObject(o, self.filesmap.get(o.key, {})).dumps()
            for o in sorted_files_from_bucket(bucket or self.bucket, self.keys)
        ]


class FilesMixin(object):
    """Implement files attribute for Record models.

    .. note::

       Implement ``_create_bucket()`` in subclass to allow files property
       to automatically create a bucket in case no bucket is present.
    """

    def _create_bucket(self):
        """Return an instance of ``Bucket`` class.

        .. note:: Reimplement in children class for custom behavior.
        """
        return None

    @property
    def files(self):
        """Get files iterator."""
        if self.model is None:
            raise MissingModelError()

        if not self.model.records_buckets:
            bucket = self._create_bucket()
            if not bucket:
                return None

            self.model.records_buckets = RecordsBuckets(
                bucket=bucket
            )

        return FilesIterator(self, bucket=self.model.records_buckets.bucket)


class Record(_Record, FilesMixin):
    """Define API for files manipulation using ``FilesMixin``."""
