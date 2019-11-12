# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Records-Files REST integration."""

from __future__ import absolute_import, print_function

from functools import partial, wraps

from flask import Blueprint, abort, g, request
from invenio_files_rest.serializer import json_serializer
from invenio_files_rest.views import BucketResource, ObjectResource
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView
from marshmallow import missing
from six import iteritems
from six.moves.urllib.parse import urljoin
from webargs.flaskparser import use_kwargs

from invenio_records_files.models import RecordsBuckets

from .serializer import serializer_mapping


def create_blueprint_from_app(app):
    """Create blueprint from a Flask application.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    records_files_blueprint = Blueprint(
        'invenio_records_files',
        __name__,
        url_prefix='')

    for config_name, endpoints_to_register in \
            iteritems(app.config['RECORDS_FILES_REST_ENDPOINTS']):
        for endpoint_prefix in endpoints_to_register:
            record_item_path = \
                app.config[config_name][endpoint_prefix]['item_route']
            files_resource_endpoint_suffix = \
                endpoints_to_register[endpoint_prefix]
            files_resource_endpoint_suffix = \
                urljoin('/', files_resource_endpoint_suffix)
            bucket_view = RecordBucketResource.as_view(
                endpoint_prefix + '_bucket_api',
                serializers={
                    'application/json':
                        partial(
                            json_serializer,
                            view_name="{}_bucket_api".format(endpoint_prefix),
                            serializer_mapping=serializer_mapping),
                }
            )
            object_view = RecordObjectResource.as_view(
                endpoint_prefix + '_object_api',
                serializers={
                    'application/json':
                        partial(
                            json_serializer,
                            view_name="{}_object_api".format(endpoint_prefix),
                            serializer_mapping=serializer_mapping),
                }
            )
            records_files_blueprint.add_url_rule(
                '{record_item_path}{files_resource_endpoint_suffix}'
                .format(**locals()),
                view_func=bucket_view,
            )
            records_files_blueprint.add_url_rule(
                '{record_item_path}{files_resource_endpoint_suffix}/<path:key>'
                .format(**locals()),
                view_func=object_view,
            )

    return records_files_blueprint


def pass_bucket_id(f):
    """Decorate to retrieve a bucket."""
    @wraps(f)
    def decorate(*args, **kwargs):
        # We need to make sure to pass an empty string and not None which can
        # be the property's value if it is a Record with files,
        # but no attached bucket
        kwargs['bucket_id'] = getattr(kwargs['record'], 'bucket_id', '') or ''
        return f(*args, **kwargs)
    return decorate


class RecordBucketResource(BucketResource):
    """RecordBucket item resource."""

    @pass_record
    @pass_bucket_id
    def get(self, pid, record, **kwargs):
        """Get list of objects in the bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :kwargs: contains all the parameters used by the ObjectResource view in
            Invenio-Files-Rest
        :returns: The Flask response.
        """
        return super(RecordBucketResource, self).get(**kwargs)

    @pass_record
    @pass_bucket_id
    def head(self, pid, record, **kwargs):
        """Check the existence of the bucket.

        :param pid: The pid value of the record to get the bucket from.
        :kwargs: contains all the parameters used by the ObjectResource view in
            Invenio-Files-Rest
        """
        return super(RecordBucketResource, self).head(**kwargs)


class RecordObjectResource(ObjectResource):
    """RecordObject item resource."""

    @pass_record
    @pass_bucket_id
    def get(self, pid, record, **kwargs):
        """Get object or list parts of a multpart upload.

        :param pid: The pid value of the record to get the bucket from.
        :kwargs: contains all the parameters used by the ObjectResource view in
            Invenio-Files-Rest
        :returns: A Flask response.
        """
        return super(RecordObjectResource, self).get(**kwargs)

    @pass_record
    @pass_bucket_id
    def put(self, pid, record, **kwargs):
        """Update a new object or upload a part of a multipart upload.

        :param pid: The pid value of the record to get the bucket from.
        :kwargs: contains all the parameters used by the ObjectResource view in
            Invenio-Files-Rest
        :returns: A Flask response.
        """
        return super(RecordObjectResource, self).put(**kwargs)

    @pass_record
    @pass_bucket_id
    def delete(self, pid, record, **kwargs):
        """Delete an object or abort a multipart upload.

        :param pid: The pid value of the record to get the bucket from.
        :kwargs: contains all the parameters used by the ObjectResource view in
            Invenio-Files-Rest
        :returns: A Flask response.
        """
        return super(RecordObjectResource, self).delete(**kwargs)
