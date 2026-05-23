# SPDX-FileCopyrightText: 2019 CERN.
# SPDX-License-Identifier: MIT

"""Flask extension for the Invenio-Records-Files."""

from __future__ import absolute_import, print_function

from invenio_records_files import config


class InvenioRecordsFiles(object):
    """Invenio-Records-Files extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-records-files"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("RECORDS_FILES_"):
                app.config.setdefault(k, getattr(config, k))
