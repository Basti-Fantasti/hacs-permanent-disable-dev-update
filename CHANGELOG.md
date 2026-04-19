# Changelog

## [1.0.2] - 2026-04-19

### Fixed
- Add-block and block-detail dialogs now fit mobile viewports. They no longer force a 400px minimum width, and scroll their content when the viewport is shorter than the dialog.
- Block detail view now shows the currently installed firmware version alongside the latest version seen, so it is clear which version the device is pinned to.

## [1.0.1] - 2026-04-18

### Fixed
- Brand images (`brand/icon.png` and variants) are now included in the release zip, required for HACS validation
- Release workflow now excludes `__pycache__` from the zip

### Changed
- README: added badges, screenshots, and a Contributing section

## [1.0.0] - 2026-04-17

### Added
- Persistent block list stored in HA `.storage`. Survives restarts, reloads, and re-pairs
- Sidebar panel to manage blocks: add, remove, scan individual devices
- Nightly scan window: briefly re-enables blocked entities to refresh latest-version info, then re-disables
- Shadow sensor per block exposing `last_known_version` and `last_scan_at`
- Binary sensor per block for scan-fault detection
- Rescan button entity per block
- Re-pair detection: orphaned blocks are matched to newly discovered devices by unique ID or fingerprint
- Rediscovery prompt in the panel for user-assisted re-mapping of orphaned blocks
- Services: `block`, `unblock`, `scan_now`, `scan_all`
- Config flow with options for scan start time, max duration, and per-device timeout
- English and German translations
- HACS support via `zip_release` with pre-built frontend bundle
