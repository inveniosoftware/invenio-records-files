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
        """Return specific version ``ObjectVersion`` instance or HEAD.

        :param version_id: Version ID of the object.
        :returns: :class:`~invenio_files_rest.models.ObjectVersion` instance or
            HEAD of the stored object.
        """
        return ObjectVersion.get(bucket=self.obj.bucket, key=self.obj.key,
                                 version_id=version_id)

    def get(self, key, default=None):
        """Proxy to ``obj``.

        :param key: Metadata key which holds the value.
        :returns: Metadata value of the specified key or default.
        """
        if hasattr(self.obj, key):
            return getattr(self.obj, key)
        return self.data.get(key, default)

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
        """Create a dump of the metadata associated to the record."""
        self.data.update({
            'bucket': str(self.obj.bucket_id),
            'checksum': self.obj.file.checksum,
            'key': self.obj.key,  # IMPORTANT it must stay here!
            'size': self.obj.file.size,
            'version_id': str(self.obj.version_id),
        })
        return self.data


def _writable(method):
    """Check that record is in defined status.

    :param method: Method to be decorated.
    :returns: Function decorated.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Send record for indexing.

        :returns: Execution result of the decorated method.

        :raises InvalidOperationError: It occurs when the bucket is locked or
            deleted.
        """
        if self.bucket.locked or self.bucket.deleted:
            raise InvalidOperationError()
        return method(self, *args, **kwargs)
    return wrapper


class FilesIterator(object):
    """Iterator for files."""

    def __init__(self, record, bucket=None, file_cls=None):
        """Initialize iterator."""
        self._it = None
        self.record = record
        self.model = record.model
        self.file_cls = file_cls or FileObject
        self.bucket = bucket
        self.filesmap = OrderedDict([
            (f['key'], f) for f in self.record.get('_files', [])
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
        return self.file_cls(obj, self.filesmap.get(obj.key, {}))

    def __contains__(self, key):
        """Test if file exists."""
        return ObjectVersion.get_by_bucket(
            self.bucket).filter_by(key=key).count()

    def __getitem__(self, key):
        """Get a specific file."""
        obj = ObjectVersion.get(self.bucket, key)
        if obj:
            return self.file_cls(obj, self.filesmap.get(obj.key, {}))
        raise KeyError(key)

    def flush(self):
        """Flush changes to record."""
        files = self.dumps()
        # Do not create `_files` when there has not been `_files` field before
        # and the record still has no files attached.
        if files or '_files' in self.record:
            self.record['_files'] = files

    @_writable
    def __setitem__(self, key, stream):
        """Add file inside a deposit."""
        with db.session.begin_nested():
            # save the file
            obj = ObjectVersion.create(
                bucket=self.bucket, key=key, stream=stream)
            self.filesmap[key] = self.file_cls(obj, {}).dumps()
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
        """Update files order.

        :param ids: List of ids specifying the final status of the list.
        """
        # Support sorting by file_ids or keys.
        files = {str(f_.file_id): f_.key for f_ in self}
        # self.record['_files'] = [{'key': files.get(id_, id_)} for id_ in ids]
        self.filesmap = OrderedDict([
            (files.get(id_, id_), self[files.get(id_, id_)].dumps())
            for id_ in ids
        ])
        self.flush()

    @_writable
    def rename(self, old_key, new_key):
        """Rename a file.

        :param old_key: Old key that holds the object.
        :param new_key: New key that will hold the object.
        :returns: The object that has been renamed.
        """
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
        self.filesmap[new_key] = self.file_cls(obj, old_data).dumps()
        del self[old_key]

        return obj

    def dumps(self, bucket=None):
        """Serialize files from a bucket.

        :param bucket: Instance of files
            :class:`invenio_files_rest.models.Bucket`. (Default:
            ``self.bucket``)
        :returns: List of serialized files.
        """
        return [
            self.file_cls(o, self.filesmap.get(o.key, {})).dumps()
            for o in sorted_files_from_bucket(bucket or self.bucket, self.keys)
        ]


class FilesMixin(object):
    """Implement files attribute for Record models.

    .. note::

       Implement ``_create_bucket()`` in subclass to allow files property
       to automatically create a bucket in case no bucket is present.
    """

    file_cls = FileObject
    """File class used to generate the instance of files. Default to
    :class:`~invenio_records_files.api.FileObject`
    """

    files_iter_cls = FilesIterator
    """Files iterator class used to generate the files iterator. Default to
    :class:`~invenio_records_files.api.FilesIterator`
    """

    def _create_bucket(self):
        """Return an instance of ``Bucket`` class.

        .. note:: Reimplement in children class for custom behavior.

        :returns: Instance of :class:`invenio_files_rest.models.Bucket`.
        """
        return None

    @property
    def files(self):
        """Get files iterator.

        :returns: Files iterator.
        """
        if self.model is None:
            raise MissingModelError()

        records_buckets = RecordsBuckets.query.filter_by(
            record_id=self.id).first()

        if not records_buckets:
            bucket = self._create_bucket()
            if not bucket:
                return None
            RecordsBuckets.create(record=self.model, bucket=bucket)
        else:
            bucket = records_buckets.bucket

        return self.files_iter_cls(self, bucket=bucket, file_cls=self.file_cls)

    @files.setter
    def files(self, data):
        """Set files from data."""
        current_files = self.files
        if current_files:
            raise RuntimeError('Can not update existing files.')
        for key in data:
            current_files[key] = data[key]


class Record(_Record, FilesMixin):
    """Define API for files manipulation using ``FilesMixin``."""

    def delete(self, force=False):
        """Delete a record and also remove the RecordsBuckets if necessary.

        :param force: True to remove also the
            :class:`~invenio_records_files.models.RecordsBuckets` object.
        :returns: Deleted record.
        """
        if force:
            RecordsBuckets.query.filter_by(
                record=self.model,
                bucket=self.files.bucket
            ).delete()
        return super(Record, self).delete(force)
