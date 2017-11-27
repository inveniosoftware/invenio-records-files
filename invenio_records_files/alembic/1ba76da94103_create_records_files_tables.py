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
