# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

r"""Integration of records and files for Invenio.

Invenio-Records-Files provides basic API for integrating
`Invenio-Records <https://invenio-records.rtfd.io/>`_
and `Invenio-Files-REST <https://invenio-files-rest.rtfd.io/>`_.

Initialization
--------------
First create a Flask application:

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

Records-Files has no Flask extension, however it is dependent on
`Invenio-Records <https://invenio-records.rtfd.io/>`_ and
`Invenio-Files-REST <https://invenio-files-rest.rtfd.io/>`_ which must be
initialized first:

>>> from invenio_db import InvenioDB
>>> ext_db = InvenioDB(app)
>>> from invenio_records import InvenioRecords
>>> from invenio_files_rest import InvenioFilesREST
>>> ext_filesrest = InvenioFilesREST(app)
>>> ext_records = InvenioRecords(app)

In order for the following examples to work, you need to work within a
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work you need to create the database and tables
(note, in this example you use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Lastly, since you're managing files, you need to create a default location.
Here you will create a location in a temporary directory:

>>> import tempfile
>>> tmppath = tempfile.mkdtemp()
>>> from invenio_files_rest.models import Location
>>> db.session.add(Location(name='default', uri=tmppath, default=True))
>>> db.session.commit()

Creating a record
-----------------
You use Invenio-Records-Files basic API by importing
:py:class:`invenio_records_files.api.Record` instead of
:py:class:`invenio_records.api.Record`:

>>> from invenio_records_files.api import Record

This :py:data:`~invenio_records_files.api.Record` class has a special property
``files`` through which you can access and create files. By default the
class creates a bucket when you create a bucket:

>>> record = Record.create({})
>>> len(record.files)
0

You can also just create a record without an associated bucket:

>>> record_nobucket = Record.create({}, with_bucket=False)
>>> record_nobucket.files is None
True

Creating files
--------------
You are now ready to create you first file using the Invenio-Records-Files API:

>>> from six import BytesIO
>>> record.files['hello.txt'] = BytesIO(b'Hello, World')

In the above example you created a file named ``hello.txt`` as a new object
in the record bucket.

Accessing files
---------------
You can access the above file through the same API:

>>> len(record.files)
1
>>> 'hello.txt' in record.files
True
>>> fileobj = record.files['hello.txt']
>>> print(fileobj.key)
hello.txt

Metadata for files
------------------
Besides creating files you can also assign metadata to files:

>>> fileobj['filetype'] = 'txt'
>>> print(record.files['hello.txt']['filetype'])
txt

Certain key names are however reserved:

>>> fileobj['key'] = 'test'
Traceback (most recent call last):
  ...
KeyError: 'key'

The reserved key names are all the properties which already exist in
:py:class:`invenio_files_rest.models.ObjectVersion`.

You can however still use the reserved keys for **getting** metadata:

>>> print(fileobj['key'])
hello.txt

Dumping files
-------------
You can make a dictionary of all files:

>>> dump = record.files.dumps()
>>> for k in sorted(dump[0].keys()):
...     print(k)
bucket
checksum
file_id
filetype
key
size
version_id

Retrieve files from a record
----------------------------
Invenio-Records-Files provides an utility to retrieve files of a given
record.

>>> from invenio_records_files.utils import record_file_factory
>>> fileobj = record_file_factory(None, record, 'hello.txt')
>>> print(fileobj.key)
hello.txt


If a file does not exist or the record class has no files property, the
factory will return ``None``:

>>> fileobj = record_file_factory(None, record, 'invalid')
>>> fileobj is None
True

Some other Invenio modules such as
`Invenio-Previewer <https://invenio-previewer.rtfd.io/>`_
already use it to programmatically access record's files.

Integration with Invenio REST API
---------------------------------
Invenio-Records-Files provides REST endpoints to retrieve or upload the files
of a record:

.. code-block:: console

    # Upload a file named example.txt to the record with pid of 1
    $ curl -X PUT http://localhost:5000/api/records/1/files/example.txt \
           --data-binary @example.txt

    # Get the list of files for this record
    $ curl -X GET http://localhost:5000/api/records/1/files/

    # Download the file named ``example.txt`` of this record
    $ curl -X GET http://localhost:5000/api/records/1/files/example.txt \
           -o example.txt


Invenio-Records-Files provides the same REST endpoints for bucket and objects
available in `Invenio-Files-REST <https://invenio-files-rest.readthedocs.io/en/
latest/_modules/invenio_files_rest/views.html>`__,
by implicitly injecting the record's bucket ID to the request.

For example given the following configuration:

.. code-block:: python

    # Invenio-Records-REST
    RECORDS_REST_ENDPOINTS = {
        recid: {
            # ...,
            item_route='/records/<pid(recid):pid_value>',
            #...,
        },
        docid: {
            # ...,
            item_route='/documents/<pid(docid):pid_value>',
            #...,
        }
    }
    # Invenio-Records-Files
    RECORDS_FILES_REST_ENDPOINTS = {
        'RECORDS_REST_ENDPOINTS': {
            'recid': '/files',
            'docid': '/doc-files',
        },
        'DEPOSIT_REST_ENDPOINTS': {
            'depid': '/deposit-files,
        }
    }

You can access the files of a record with PID ``1`` using the
URL ``/api/records/1/files`` or of a document with PID ``123`` using
the URL ``/api/documents/123/doc-files``.

You can access a specific file, for instance ``example.txt``,
with the following URL ``/api/records/1/files/example.txt``.


Invenio-Records-Files endpoint offers the same functionality provided by
`Invenio-Files-REST API
<https://invenio-files-rest.readthedocs.io/en/latest/
api.html#module-invenio_files_rest.views>`__.
More information about handling files through the REST API can be found `here
<https://invenio-files-rest.readthedocs.io/en/latest/usage.html>`__.

Integration with Invenio-Records-UI
-----------------------------------
If you are using `Invenio-Records-UI <https://invenio-records-ui.RTFD.io/>`__,
you can easily add new views by defining new endpoints into your
``RECORDS_UI_ENDPOINTS`` configuration. In particular, you can add the
``file_download_ui`` endpoint:

.. code-block:: python

    RECORDS_UI_ENDPOINTS = dict(
        recid=dict(
            # ...
            route='/records/<pid_value/files/<filename>',
            view_imp='invenio_records_files.utils:file_download_ui',
            record_class='invenio_records_files.api:Record',
        )
    )

"""

from __future__ import absolute_import, print_function

from invenio_records_files.ext import InvenioRecordsFiles

from .version import __version__

__all__ = ('__version__', 'InvenioRecordsFiles')
