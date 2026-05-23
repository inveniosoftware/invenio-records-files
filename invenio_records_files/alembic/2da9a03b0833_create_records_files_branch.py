# SPDX-FileCopyrightText: 2016-2019 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Create records_files branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2da9a03b0833"
down_revision = None
branch_labels = ("invenio_records_files",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
