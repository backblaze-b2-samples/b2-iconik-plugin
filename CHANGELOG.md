# Changelog

## v1.2.2 (03/26/2025)

### Features

- Added resource at root URL
- Added ability for integration tests to use live plugin

### Changes

- Added instructions on creating venv, starting Gunicorn 

### Fixes

- Gunicorn needs parentheses on plugin:create_app()
- Fixed gevent workers

## v1.2.1 (03/25/2025)

### Fixes

- Updated app identifier for Gunicorn

## v1.2.0 (03/20/2025)

### Features

- Added Dockerfile
- Added integration tests
- Added LICENSE headers
- Added the `formats` query parameter to the `add` and `remove` operations

### Changes

- Major reorganization and refactoring to simplify logic
- Arguments to the `create_custom_actions` and `delete_custom_actions` scripts are now positional, and do not require flags such as `--endpoint` etc.

## v1.1.0 (04/24/2023)

### Features

- After validating the incoming request, the plugin now spawns a subprocess to add/remove files, ensuring it can return a response to iconik within ten seconds.
- Added version numbering

### Fixes

- The plugin now correctly processes subcollections.

## v1.0.0 (08/23/2022)

- First release of the Backblaze B2 Storage Plugin for iconik
