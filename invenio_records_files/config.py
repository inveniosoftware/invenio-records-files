
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
            '<endpoint-prefix>': '<endpoint-suffix>',
        }
    }

* ``<*_REST_ENDPOINTS>`` corresponds to `Invenio-Records-REST endpoint
  configurations names
  <https://invenio-records-rest.readthedocs.io/en/latest/configuration.html
  #invenio_records_rest.config.RECORDS_REST_ENDPOINTS>`_
  that you have defined in your application.

* ``<endpoint-prefix>`` is the unique name of the endpoint configuration as it
  is defined in `Invenio-Records-REST
  <https://invenio-records-rest.readthedocs.io/en/latest/configuration.html
  #invenio_records_rest.config.RECORDS_REST_ENDPOINTS>`_ like configuration.
  This needs to match an already existing endpoint name in the
  `<*_REST_ENDPOINTS>` configuration.

* ``<endpoint-suffix>`` is the endpoint path name to access the record's files.

.. code-block:: console

    {'recid': '/myawesomefiles'} -> /records/1/myawesomefiles

An example of this configuration is provided in the
`Integration with Invenio REST API
<usage.html#integration-with-invenio-rest-api>`_ section of the documentation.
"""
