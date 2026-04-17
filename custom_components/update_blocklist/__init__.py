"""Update Blocklist integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, PLATFORMS
from .coordinator import UpdateBlocklistCoordinator
from .registry import BlockRegistry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up update_blocklist from a config entry."""
    from .const import (
        CONF_PER_DEVICE_TIMEOUT_SECONDS,
        CONF_SCAN_MAX_DURATION_MINUTES,
        CONF_SCAN_START_TIME,
        DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
        DEFAULT_SCAN_MAX_DURATION_MINUTES,
        DEFAULT_SCAN_START_TIME,
    )

    hass.data.setdefault(DOMAIN, {})

    registry = BlockRegistry(hass)
    await registry.async_load()

    options = {
        CONF_SCAN_START_TIME: entry.options.get(CONF_SCAN_START_TIME, DEFAULT_SCAN_START_TIME),
        CONF_SCAN_MAX_DURATION_MINUTES: entry.options.get(CONF_SCAN_MAX_DURATION_MINUTES, DEFAULT_SCAN_MAX_DURATION_MINUTES),
        CONF_PER_DEVICE_TIMEOUT_SECONDS: entry.options.get(CONF_PER_DEVICE_TIMEOUT_SECONDS, DEFAULT_PER_DEVICE_TIMEOUT_SECONDS),
    }

    coordinator = UpdateBlocklistCoordinator(hass, registry)
    await coordinator.async_refresh()

    from .scanner import Scanner
    scanner = Scanner(hass, registry, coordinator, options)

    hass.data[DOMAIN][entry.entry_id] = {
        "registry": registry,
        "coordinator": coordinator,
        "options": options,
        "scanner": scanner,
    }

    remove_schedule = scanner.start_schedule()
    entry.async_on_unload(remove_schedule)

    entry.async_on_unload(entry.add_update_listener(_async_options_reload))

    # Register services and views once on first (only) setup.
    if len(hass.data[DOMAIN]) == 1:
        from .services import async_register_services, async_unregister_services

        async_register_services(hass)

        @callback
        def _on_remove():
            async_unregister_services(hass)

        entry.async_on_unload(_on_remove)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_options_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
