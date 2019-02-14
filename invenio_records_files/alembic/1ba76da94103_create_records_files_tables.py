# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create records files tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = '1ba76da94103'
down_revision = '2da9a03b0833'
branch_labels = ()
depends_on = (
    '2e97565eba72',  # invenio-files-rest
    '862037093962',  # invenio-records
)


def upgrade():
    """Upgrade database."""
    op.create_table(
        'records_buckets',
        sa.Column(
            'record_id',
            sqlalchemy_utils.types.uuid.UUIDType(),
            nullable=False),
        sa.Column(
            'bucket_id',
            sqlalchemy_utils.types.uuid.UUIDType(),
            nullable=False),
        sa.ForeignKeyConstraint(['bucket_id'], [u'files_bucket.id'], ),
        sa.ForeignKeyConstraint(['record_id'], [u'records_metadata.id'], ),
        sa.PrimaryKeyConstraint('record_id', 'bucket_id')
    )


def downgrade():
    """Downgrade database."""
    op.drop_table('records_buckets')
