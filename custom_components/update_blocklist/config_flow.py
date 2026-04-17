"""Config flow for update_blocklist integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN


class UpdateBlocklistConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for update_blocklist."""

    VERSION = 1
