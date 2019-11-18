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

from flask import Blueprint
from invenio_files_rest.serializer import json_serializer
from invenio_files_rest.views import BucketResource, ObjectResource
from invenio_records_rest.views import pass_record
from six import iteritems
from six.moves.urllib.parse import urljoin

from .serializer import serializer_mapping


def create_blueprint_from_app(app):
    """Create blueprint from a Flask application.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    records_files_blueprint = Blueprint(
        "invenio_records_files", __name__, url_prefix=""
    )

    for rest_endpoint_config, rec_files_mappings in iteritems(
        app.config["RECORDS_FILES_REST_ENDPOINTS"]
    ):
        for endpoint_prefix, files_path_name in iteritems(rec_files_mappings):
            if endpoint_prefix not in app.config[rest_endpoint_config]:
                raise ValueError(
                    'Endpoint {0} is not present in {1}'.format(
                        endpoint_prefix, rest_endpoint_config))
            # e.g. /api/records/<recid>
            rec_item_route = app.config[rest_endpoint_config][endpoint_prefix][
                "item_route"
            ]
            # e.g. /files
            files_path_name = urljoin("/", files_path_name)
            bucket_view = RecordBucketResource.as_view(
                endpoint_prefix + "_bucket_api",
                serializers={
                    "application/json": partial(
                        json_serializer,
                        view_name="{}_bucket_api".format(endpoint_prefix),
                        serializer_mapping=serializer_mapping,
                    )
                },
            )
            object_view = RecordObjectResource.as_view(
                endpoint_prefix + "_object_api",
                serializers={
                    "application/json": partial(
                        json_serializer,
                        view_name="{}_object_api".format(endpoint_prefix),
                        serializer_mapping=serializer_mapping,
                    )
                },
            )
            records_files_blueprint.add_url_rule(
                "{rec_item_route}{files_path_name}".format(**locals()),
                view_func=bucket_view,
            )
            records_files_blueprint.add_url_rule(
                "{rec_item_route}{files_path_name}/<path:key>".format(
                    **locals()
                ),
                view_func=object_view,
            )

    return records_files_blueprint


def pass_bucket_id(f):
    """Decorate to retrieve a bucket."""
    @wraps(f)
    def decorate(*args, **kwargs):
        """Get the bucket id from the record and pass it as kwarg."""
        kwargs["bucket_id"] = getattr(kwargs["record"], "bucket_id", "")
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
