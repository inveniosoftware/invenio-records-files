# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Link for file bucket creation."""

from flask import url_for
from invenio_records_rest import current_records_rest

from .api import Record


def default_bucket_link_factory(pid):
    """Factory for record bucket generation."""
    try:
        record = Record.get_record(pid.get_assigned_object())
        bucket = record.files.bucket

        return url_for('invenio_files_rest.bucket_api',
                       bucket_id=bucket.id, _external=True)
    except AttributeError:
        return None


def default_record_files_links_factory(pid, record=None, **kwargs):
    """Factory for record files links generation.

    :param pid: A Persistent Identifier instance.
    :returns: Dictionary containing a list of useful links for the record.
    """
    record_name = current_records_rest.default_endpoint_prefixes[pid.pid_type]
    record_endpoint = 'invenio_records_rest.{0}_item'.format(record_name)
    record_files_endpoint =\
        'invenio_records_files.{0}_bucket_api'.format(record_name)
    links = dict(
        self=url_for(record_endpoint, pid_value=pid.pid_value, _external=True),
        files=url_for(
            record_files_endpoint, pid_value=pid.pid_value, _external=True)
    )
    return links
