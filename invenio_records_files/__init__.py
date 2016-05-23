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

"""Integration of records and files for Invenio.

Invenio-Records-Files provides basic API for integrating Invenio-Records and
Invenio-Files-REST.

Initialization
--------------
First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> from flask_cli import FlaskCLI
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> ext_cli = FlaskCLI(app)

Records-Files have no Flask extension, however it is dependent on
Invenio-Records and Invenio-Files-REST which must be initialized first:

>>> from invenio_db import InvenioDB
>>> ext_db = InvenioDB(app)
>>> from invenio_records import InvenioRecords
>>> from invenio_files_rest import InvenioFilesREST
>>> ext_filesrest = InvenioFilesREST(app)
>>> ext_records = InvenioRecords(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Last, since we're managing files, we need to create a base location. Here we
will create a location in a temporary directory:

>>> import tempfile
>>> tmppath = tempfile.mkdtemp()
>>> from invenio_files_rest.models import Location
>>> db.session.add(Location(name='default', uri=tmppath, default=True))
>>> db.session.commit()

Creating a record
-----------------
You use Invenio-Records-Files basic API by importing
``invenio_records_files.api.Record`` instead of
``invenio_records.api.Record``:

>>> from invenio_records_files.api import Record

This records class has special property ``files`` through which you can access
and create files. By default this property is ``None``:

>>> record = Record.create({})
>>> record.files is None
True

This is because no bucket have been assigned to the record yet.

Assigning a bucket
~~~~~~~~~~~~~~~~~~
You assign a bucket to a record through
:py:data:`invenio_records_files.models.RecordsBuckets`:

>>> from invenio_files_rest.models import Bucket
>>> from invenio_records_files.models import RecordsBuckets
>>> bucket = Bucket.create()
>>> record.model.records_buckets = RecordsBuckets(bucket=bucket)

Normally the bucket creation and bucket to record assignment is done by an
external module (e.g. Invenio-Deposit is one example of this).

The ``files`` property now has a value and we can e.g. ask for the number of
files:

>>> len(record.files)
0

Creating files
--------------
We are now ready to create our first file using the Invenio-Records-Files API:

>>> from six import BytesIO
>>> record.files['hello.txt'] = BytesIO(b'Hello, World')

In above example we create a file named ``hello.txt`` and assigns a *stream*
like object which will be saved as a new object in the bucket.

Accessing files
---------------
We can access the just stored file through the same API:

>>> len(record.files)
1
>>> 'hello.txt' in record.files
True
>>> fileobj = record.files['hello.txt']
>>> print(fileobj.key)
hello.txt

Metadata for files
------------------
Besides creating files we can also assign metadata to files:

>>> fileobj['filetype'] = 'txt'
>>> print(record.files['hello.txt']['filetype'])
txt

Certain key names are however reserved cannot be used for **setting** metadata:

>>> fileobj['key'] = 'test'
Traceback (most recent call last):
  ...
KeyError: 'key'

The reserved key names are all the properties which exists on
``invenio_files_rest.models:ObjectVersion``.

You can however still use the reserved keys for **getting** metadata:

>>> print(fileobj['key'])
hello.txt

Dumping files
-------------
You can make a dictionary of all files

>>> dump = record.files.dumps()
>>> for k in sorted(dump[0].keys()):
...     print(k)
bucket
checksum
filetype
key
size
version_id

This is also how files are stored inside the record in the ``_files`` key:

>>> print(record['_files'][0]['key'])
hello.txt

Extracting file from record
---------------------------
Some Invenio modules, e.g. Invenio-Previewer need to extract a file from
record and be resilient towards exactly which record class is being used. This
can done using the a record file factory:

>>> from invenio_records_files.utils import record_file_factory
>>> fileobj = record_file_factory(None, record, 'hello.txt')
>>> print(fileobj.key)
hello.txt

If a file does not exist or the record class has no files property, the
factory will return ``None``:

>>> fileobj = record_file_factory(None, record, 'invalid')
>>> fileobj is None
True
"""

from __future__ import absolute_import, print_function

from .version import __version__

__all__ = ('__version__', )
