# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test utility functions."""

from __future__ import absolute_import, print_function

import pytest
from werkzeug.exceptions import NotFound

from invenio_records_files.utils import file_download_ui


def test_file_download_ui(app, db, location, record_with_bucket, generic_file):
    """Test file download UI."""
    with app.test_request_context():
        pid = type('PID', (object, ), {'pid_type': 'demo', 'pid_value': '1'})()
        response = file_download_ui(
            pid, record_with_bucket, filename=generic_file
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'

        response = file_download_ui(
            pid, record_with_bucket, filename=generic_file
        )

        with pytest.raises(NotFound):
            file_download_ui(pid, record_with_bucket)

        with pytest.raises(NotFound):
            file_download_ui(pid, record_with_bucket, filename='not_found')

    with app.test_request_context('/?download'):
        response = file_download_ui(
            pid, record_with_bucket, filename=generic_file
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'
        assert response.headers['Content-Disposition'] == \
            'attachment; filename={}'.format(generic_file)
