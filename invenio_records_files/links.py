# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Link for file bucket creation."""

from flask import url_for

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
