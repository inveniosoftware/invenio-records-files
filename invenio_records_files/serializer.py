# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API serializers based on Invenio-Files-Rest."""

from flask import request, url_for
from invenio_files_rest.serializer import Bucket, BucketSchema, \
    ObjectVersion, ObjectVersionSchema
from marshmallow import post_dump


class RecordObjectVersionSchema(ObjectVersionSchema):
    """Schema for RecordObjectVersions."""

    def dump_links(self, o):
        """Dump links."""
        pid_value = request.view_args["pid_value"].value
        url_path = ".{0}".format(self.context.get("view_name"))
        params = {"versionId": o.version_id}
        url_for_self = url_for(
            url_path,
            pid_value=pid_value,
            key=o.key,
            _external=True,
            **(params if not o.is_head or o.deleted else {})
        )
        url_for_versions = url_for(
            url_path, pid_value=pid_value, key=o.key, _external=True, **params
        )

        data = {"self": url_for_self, "version": url_for_versions}

        if o.is_head and not o.deleted:
            url_for_uploads = "{0}?uploads".format(
                url_for(
                    url_path, pid_value=pid_value, key=o.key, _external=True
                )
            )
            data.update({"uploads": url_for_uploads})

        return data

    @post_dump(pass_many=True)
    def wrap(self, data, many):
        """Wrap response in envelope."""
        if not many:
            return data
        else:
            data = {"contents": data}
            bucket = self.context.get("bucket")
            if bucket:
                data.update(
                    RecordBucketSchema(context=self.context).dump(bucket).data
                )
            return data


class RecordBucketSchema(BucketSchema):
    """Schema for RecordBuckets."""

    def dump_links(self, o):
        """Dump links."""
        pid_value = request.view_args["pid_value"].value
        url_path = ".{0}".format(self.context.get("view_name"))
        url_for_self = url_for(url_path, pid_value=pid_value, _external=True)
        url_for_versions = "{0}?versions".format(url_for_self)
        url_for_uploads = "{0}?uploads".format(url_for_self)
        return {
            "self": url_for_self,
            "versions": url_for_versions,
            "uploads": url_for_uploads,
        }


serializer_mapping = {
    Bucket: RecordBucketSchema,
    ObjectVersion: RecordObjectVersionSchema,
}
