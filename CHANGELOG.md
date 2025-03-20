# Changelog

## v1.2.0 (03/20/2025)

### Feature

- Major reorganization and refactoring to simplify logic
- Added Dockerfile
- Added integration test
- Added LICENSE headers

## v1.1.0 (04/24/2023)

### Feature

- After validating the incoming request, the plugin now spawns a subprocess to add/remove files, ensuring it can return a response to iconik within ten seconds.
- Added version numbering

### Fixes

- The plugin now correctly processes subcollections.

## v1.0.0 (08/23/2022)

- First release of the Backblaze B2 Storage Plugin for iconik
