# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

import pytest
from invenio_db.utils import drop_alembic_version_table


def test_version():
    """Test version import."""
    from invenio_records_files import __version__
    assert __version__


def test_jsonschemas_import():
    """Test jsonschemas import."""
    from invenio_records_files import jsonschemas


# Unfixable error: "Revision f9843093f686 referenced from
# f9843093f686 -> 037afe10e9ff (head), Add user moderation fields. is not
# present"
# Skipping as in invenio-records
@pytest.mark.skip(reason="Caused by mergepoint?")
def test_alembic(app, db):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    # skip index from alembic migrations until sqlalchemy 2.0
    # https://github.com/sqlalchemy/sqlalchemy/discussions/7597
    def include_object(object, name, type_, reflected, compare_to):
        if name == "ix_uq_partial_files_object_is_head":
            return False

        return True

    app.config["ALEMBIC_CONTEXT"] = {"include_object": include_object}

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
