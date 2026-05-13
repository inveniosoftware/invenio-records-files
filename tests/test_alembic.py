# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
# Copyright (C) 2026 CESNET z.s.p.o.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Alembic upgrade tests."""

import pytest


def test_alembic(app, db):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    with app.app_context():
        if db.engine.name == "sqlite":
            raise pytest.skip("Upgrades are not supported on SQLite.")

        # ix_uq_partial_files_object_is_head is incorrectly handled for a long time,
        # so we need to exclude it from the comparison. In RDM-14 migrations, we have
        # removed it manually.
        def include_object(object, name, type_, reflected, compare_to):
            if name == "ix_uq_partial_files_object_is_head":
                return False

            return True

        app.config["ALEMBIC_CONTEXT"] = {"include_object": include_object}
        print(app.config["ALEMBIC"])

        assert not ext.alembic.compare_metadata()
        db.drop_all()
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target="2da9a03b0833")
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target="2da9a03b0833")
