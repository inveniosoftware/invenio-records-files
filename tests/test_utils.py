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

        with pytest.raises(NotFound):
            file_download_ui(pid, record_with_bucket)

        with pytest.raises(NotFound):
            file_download_ui(pid, record_with_bucket, filename='not_found')
