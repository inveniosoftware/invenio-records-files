# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test view functions."""

from __future__ import absolute_import, print_function

import json

from six import BytesIO


def test_records_files_rest_integration(app, client, location, minted_record):
    """Test Records Files Views"""
    pid, record = minted_record
    test_data = b'test example'
    file_key = 'test.txt'

    # Upload a file.
    res = client.put(
        '/records/{0}/files/{1}'.format(pid.id, file_key),
        data=test_data)
    assert res.status_code == 200

    # Get the list of the records files.
    res = client.get('/records/{0}/files'.format(pid.id))
    assert json.loads(
        res.get_data(as_text=True))['contents'][0]['key'] == file_key
    assert len(json.loads(res.get_data(as_text=True))['contents']) == 1

    # Get the previously uploaded file.
    res = client.get('/records/{0}/files/{1}'.format(pid.id, file_key))
    assert res.data == test_data

    # Doc types shouldn't have files mounted as they are not configured.
    res = client.get('/doc/{0}/files'.format(pid.id))
    assert res.status_code == 404


def test_record_without_bucket(app, db, client, location,
                               minted_record_no_bucket):
    """Test that there is no bucket creation if missing."""
    pid, record = minted_record_no_bucket
    res = client.put(
        '/records/{0}/files/{1}'.format(pid.pid_value, 'test.txt'),
        data=b'test example'
    )
    assert res.status_code == 404


def test_record_no_files(app, db, client, location, minted_record_no_bucket):
    """Test that there is no bucket creation if missing."""
    pid, record = minted_record_no_bucket
    res = client.put(
        '/records/{0}/nofiles/{1}'.format(pid.pid_value, 'test.txt'),
        data=b'test example'
    )
    assert res.status_code == 404
