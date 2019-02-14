# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
