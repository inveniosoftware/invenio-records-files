# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implementention of various utility functions."""

from __future__ import absolute_import, print_function

from flask import abort, request
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.views import ObjectResource
from invenio_records.errors import MissingModelError


def sorted_files_from_bucket(bucket, keys=None):
    """Return files from bucket sorted by given keys.

    :param bucket: :class:`~invenio_files_rest.models.Bucket` containing the
        files.
    :param keys: Keys order to be used.
    :returns: Sorted list of bucket items.
    """
    keys = keys or []
    total = len(keys)
    sortby = dict(zip(keys, range(total)))
    values = ObjectVersion.get_by_bucket(bucket).all()
    return sorted(values, key=lambda x: sortby.get(x.key, total))


def record_file_factory(pid, record, filename):
    """Get file from a record.

    :param pid: Not used. It keeps the function signature.
    :param record: Record which contains the files.
    :param filename: Name of the file to be returned.
    :returns: File object or ``None`` if not found.
    """
    try:
        if not (hasattr(record, 'files') and record.files):
            return None
    except MissingModelError:
        return None

    try:
        return record.files[filename]
    except KeyError:
        return None


def file_download_ui(pid, record, _record_file_factory=None, **kwargs):
    """File download view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/files/<filename>',
                view_imp='invenio_records_files.utils:file_download_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    If ``download`` is passed as a querystring argument, the file is sent as an
    attachment.

    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    _record_file_factory = _record_file_factory or record_file_factory
    # Extract file from record.
    fileobj = _record_file_factory(
        pid, record, kwargs.get('filename')
    )

    if not fileobj:
        abort(404)

    obj = fileobj.obj

    # Check permissions
    ObjectResource.check_object_permission(obj)

    # Send file.
    return ObjectResource.send_object(
        obj.bucket, obj,
        expected_chksum=fileobj.get('checksum'),
        logger_data={
            'bucket_id': obj.bucket_id,
            'pid_type': pid.pid_type,
            'pid_value': pid.pid_value,
        },
        as_attachment=('download' in request.args)
    )
