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


def test_records_files_rest_integration(
        app, client, minted_record_with_bucket):
    """ Test Records Files Views"""
    pid, record = minted_record_with_bucket
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


def test_add_file_without_existing_bucket_passes(
        app, db, client, location,
        record_created_through_rest):
    """Test seemless bucket creation if missing.

    This is achieved by implementing _create_bucket.
    """
    pid = record_created_through_rest['id']
    test_data = 'test example'
    file_key = 'test.txt'
    res = client.put(
        '/records/{0}/files/{1}'.format(pid, file_key),
        data=test_data)
    res = client.get('/records/{0}/files/{1}'.format(pid, file_key))
    assert res.get_data(as_text=True) == test_data


def test_add_file_without_existing_bucket_fails(
        app, db, client, location, record_created_through_rest,
        remove_create_bucket):
    """Test that there is no bucket creation if missing.

    This is the default behaviour if _create_bucket is not implemented.
    """
    pid = record_created_through_rest['id']
    test_data = b'test example'
    file_key = 'test.txt'
    res = client.put(
        '/records/{0}/files/{1}'.format(pid, file_key),
        data=test_data)
    assert res.status_code == 404


def test_record_without_files(
        app, db, client, location, record_created_through_rest):
    """Test that there is no bucket creation if missing.

    This is the default behaviour if _create_bucket is not implemented.
    """
    pid = record_created_through_rest['id']
    test_data = b'test example'
    file_key = 'test.txt'
    res = client.put(
        '/basic_records/{0}/nofiles/{1}'.format(pid, file_key),
        data=test_data)
    assert res.status_code == 404
