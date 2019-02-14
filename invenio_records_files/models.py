# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Define relation between records and buckets."""

from __future__ import absolute_import

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.types import UUIDType


class RecordsBuckets(db.Model):
    """Relationship between Records and Buckets."""

    __tablename__ = 'records_buckets'

    record_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    """Record related with the bucket."""

    bucket_id = db.Column(
        UUIDType,
        db.ForeignKey(Bucket.id),
        primary_key=True,
        nullable=False,
    )
    """Bucket related with the record."""

    bucket = db.relationship(Bucket)
    """Relationship to the bucket."""

    record = db.relationship(RecordMetadata)
    """It is used by SQLAlchemy for optimistic concurrency control."""

    @classmethod
    def create(cls, record, bucket):
        """Create a new RecordsBuckets and adds it to the session.

        :param record: Record used to relate with the ``Bucket``.
        :param bucket: Bucket used to relate with the ``Record``.
        :returns: The :class:`~invenio_records_files.models.RecordsBuckets`
            object created.
        """
        rb = cls(record=record, bucket=bucket)
        db.session.add(rb)
        return rb
