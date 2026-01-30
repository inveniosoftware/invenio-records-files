..
    This file is part of Invenio.
    Copyright (C) 2016-2019 CERN.
    Copyright (C) 2026 Graz University of Technology.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.



Changes
=======

Version v2.0.0 (released 2026-01-30)

- chore(context): apply marshmallow context change
- fix: PytestDeprecationWarning
- chore(setup): bump dependencies
- fix(docs): not found attr
- chore(black): update formatting to >= 26.0
- chore(setup): to be backwards compatible
- fix(tests): skip alembic test
- global: add compatibility to sqlalchemy >= 2.0
- fix: no module imp
- fix: missing module data.v7
- fix: sphinxwarning
- setup: change to reusable workflows
- fix: setuptools require underscores instead of dashes
- global: clean test infrastructure
- increase minimal python version to 3.7
- move check_manifest configuration to setup.cfg.
- fix docs compatibilty problem with Sphinx>=5.0.0
- add .git-blame-ignore-revs
- migrate to use black as opinionated auto formater
- migrate setup.py to setup.cfg

Version 1.2.2 (released 2024-01-18)

- add bucket_id index
- migrate CI to gh actions

Version 1.2.1 (released 2019-11-21)

- increase invenio-files-rest version to provide signals for d
  eletion and uploading files

Version 1.2.0 (released 2019-11-19)

- Adds link factory for files and record
- Fixes the blueprints building

Version 1.1.1 (released 2019-07-31)

- Fixes missing entry point definition for the extension, causing the extension
  and config not to be loaded.
- Fix issue with when used with Flask-Talisman.

Version 1.1.0 (released 2019-07-29)

- Backward incompatible changes to API.

Version 1.0.0 (released 2019-07-23)

- Initial public release.
