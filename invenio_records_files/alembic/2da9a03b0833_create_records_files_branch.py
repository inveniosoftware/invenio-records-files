# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create records_files branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2da9a03b0833'
down_revision = 'dbdbc1b19cf2'
branch_labels = (u'invenio_records_files',)
depends_on = 'dbdbc1b19cf2'


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
