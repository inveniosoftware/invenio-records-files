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

"""Signal handlers."""

from __future__ import absolute_import

import base64

from invenio_files_rest.models import ObjectVersion


def index_attachments(sender, json=None, record=None,
                      index=None, doc_type=None):
    """Load and index attached files for given record.

    It iterates over ``_files`` field in ``record`` and checks if
    ``_attachment`` subfiled has been configured with following values:

    * ``True``/``False`` simply enables/disables automatic fulltext indexing
      for given file instance;
    * Alternativelly, one can provide a ``dict`` instance with all
      configuration options as defined in Elasticsearch guide on
      https://www.elastic.co/guide/en/elasticsearch/ search for
      mapper-attachment.

    .. note::
       Make sure that ``mapper-attachment`` plugin is installed and running
       in Elasticsearch when using this signal handler.
    """
    for index, data in enumerate(record['_files']):
        attachment = json['_files'][index].pop('_attachment', None)
        if attachment:
            obj = ObjectVersion.get(data['bucket'], data['key'],
                                    version_id=data.get('version_id'))
            attachment = attachment if isinstance(attachment, dict) else {}
            attachment.setdefault('_content', base64.b64encode(
                obj.file.storage().open().read()
            ).decode('utf-8'))
            json['_files'][index]['_attachment'] = attachment
