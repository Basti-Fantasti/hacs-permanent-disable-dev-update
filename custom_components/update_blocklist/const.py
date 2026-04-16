"""Constants for the update_blocklist integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "update_blocklist"
PLATFORMS: Final = ["sensor", "binary_sensor", "button"]

# Config entry / options keys
CONF_SCAN_START_TIME: Final = "scan_start_time"            # "HH:MM" string
CONF_SCAN_MAX_DURATION_MINUTES: Final = "scan_max_duration_minutes"
CONF_PER_DEVICE_TIMEOUT_SECONDS: Final = "per_device_timeout_seconds"

DEFAULT_SCAN_START_TIME: Final = "01:00"
DEFAULT_SCAN_MAX_DURATION_MINUTES: Final = 30
DEFAULT_PER_DEVICE_TIMEOUT_SECONDS: Final = 300

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.blocks"
STORAGE_VERSION: Final = 1

# Scan result statuses
SCAN_STATUS_OK: Final = "ok"
SCAN_STATUS_TIMEOUT: Final = "timeout"
SCAN_STATUS_ENTITY_GONE: Final = "entity_gone"
SCAN_STATUS_DISABLE_FAILED: Final = "disable_failed"
SCAN_STATUS_NEVER_SCANNED: Final = "never_scanned"

# Block lifecycle statuses
BLOCK_STATUS_ACTIVE: Final = "active"
BLOCK_STATUS_USER_OVERRIDDEN: Final = "user_overridden"
BLOCK_STATUS_ORPHAN: Final = "orphan"

# Rediscovery match types
MATCH_UNIQUE_ID: Final = "unique_id"
MATCH_FINGERPRINT: Final = "fingerprint"

# Event names
SIGNAL_BLOCKS_UPDATED: Final = f"{DOMAIN}_blocks_updated"

# Panel
PANEL_URL: Final = f"/{DOMAIN}/panel.js"
PANEL_TITLE: Final = "Update Blocklist"
PANEL_ICON: Final = "mdi:shield-lock-outline"
