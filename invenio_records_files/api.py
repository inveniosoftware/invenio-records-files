# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API for manipulating files associated to a record."""

from collections import OrderedDict
from functools import wraps

from invenio_db import db
from invenio_files_rest.errors import InvalidOperationError
from invenio_files_rest.models import Bucket, ObjectVersion
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
            # The bucket id is also stored here, in case we have records with
            # multiple buckets associated.
            'bucket': str(self.obj.bucket_id),
            'checksum': self.obj.file.checksum,
            'file_id': str(self.obj.file.id),
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
            return None
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
    """Record class with associated bucket.

    The record class implements a one-to-one relationship between a bucket and
    a record. A bucket is automatically created and associated with the record
    when the record is created with :py:data:`Record.create()` (unless
    ``with_bucket`` is set to ``False``).

    The bucket id is stored in the record metadata (by default in the
    ``_bucket`` key). You can implement your dump/load behavior for storing
    the bucket id in the record (or possibly somewhere else). You do this by
    creating a subclass of this class, and overriding the two classmethods
    :py:data:`Record.dump_bucket()` and :py:data:`Record.load_bucket()`.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the record."""
        self._bucket = None
        super(Record, self).__init__(*args, **kwargs)

    @classmethod
    def create(cls, data, id_=None, with_bucket=True, **kwargs):
        """Create a record and the associated bucket.

        :param with_bucket: Create a bucket automatically on record creation.
        """
        # Create bucket and store in record metadata.
        if with_bucket:
            bucket = cls.create_bucket(data)
            if bucket:
                cls.dump_bucket(data, bucket)
        # Create the record
        record = super(Record, cls).create(data, id_=id_, **kwargs)
        # Create link between record and bucket
        if with_bucket and bucket:
            RecordsBuckets.create(record=record.model, bucket=bucket)
            record._bucket = bucket
        return record

    @classmethod
    def create_bucket(cls, data):
        """Create a bucket for this record.

        Override this method to provide more advanced bucket creation
        capabilities. This method may return a new or existing bucket, or may
        return None, in case no bucket should be created.
        """
        return Bucket.create()

    @classmethod
    def dump_bucket(cls, data, bucket):
        """Dump the bucket id into the record metadata.

        Override this method to provide custom behavior for storing the bucket
        id in the record metadata. By default the bucket id is stored in the
        ``_bucket`` key. If you override this method, make sure you also
        override :py:data:`Record.load_bucket()`.

        This method is called after the bucket is created, but before the
        record is created in the database.

        :param data: A dictionary of the record metadata.
        :param bucket: The created bucket for the record.
        """
        data['_bucket'] = str(bucket.id)

    @classmethod
    def load_bucket(cls, record):
        """Load the bucket id from the record metadata.

        Override this method to provide custom behavior for retriving the
        bucket id from the record metadata. By default the bucket id is
        retrieved from the ``_bucket`` key. If you override this method, make
        sure you also  override :py:data:`Record.dump_bucket()`.

        :param record: A record instance.
        """
        return record.get('_bucket')

    @property
    def bucket_id(self):
        """Get bucket id from record metadata."""
        return self.load_bucket(self)

    @property
    def bucket(self):
        """Get bucket instance."""
        if self._bucket is None:
            if self.bucket_id:
                self._bucket = Bucket.get(self.bucket_id)
        return self._bucket

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
