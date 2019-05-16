
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Records-Files configuration."""

RECORDS_FILES_REST_ENDPOINTS = {}
"""REST endpoints configuration.

You can configure the REST API endpoint to access the record's
files as follows:

.. code-block:: python

    RECORDS_FILES_REST_ENDPOINTS = {
        '<*_REST_ENDPOINTS>': {
            '<record_pid_type>': '<endpoint_suffix>',
        }
    }

* ``<*_REST_ENDPOINTS>`` corresponds to `Invenio-Records-REST endpoint
  configurations names <https://invenio-records-rest.readthedocs.io/en/
  latest/configuration.html#invenio_records_rest.config
  .RECORDS_REST_ENDPOINTS>`_ you have defined in your application.

* ``<record_pid_type>`` is the PID type associated to the record defined in
  your `Invenio-Records-REST <https://invenio-records-rest.readthedocs.io/en/
  latest/configuration.html#invenio_records_rest.
  config.RECORDS_REST_ENDPOINTS>`_ like configuration.

* ``<endpoint_suffix>`` is the endpoint name to access the record's files.

.. code-block:: console

    {'recid': '/myawesomefiles'} -> /records/1/myawesomefiles

An example of this configuration is provided in the
`Integration with Invenio REST API
<usage.html#integration-with-invenio-rest-api>`_ section of the documentation.
"""
