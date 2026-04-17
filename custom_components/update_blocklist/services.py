"""Service registration for update_blocklist."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_PER_DEVICE_TIMEOUT_SECONDS,
    CONF_SCAN_MAX_DURATION_MINUTES,
    DOMAIN,
)

SERVICE_BLOCK = "block"
SERVICE_UNBLOCK = "unblock"
SERVICE_SCAN_NOW = "scan_now"
SERVICE_SCAN_ALL = "scan_all"


BLOCK_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Optional("reason", default=""): cv.string,
    }
)

UNBLOCK_SCHEMA = vol.Schema({vol.Required("block_id"): cv.string})
SCAN_NOW_SCHEMA = vol.Schema({vol.Required("block_id"): cv.string})
SCAN_ALL_SCHEMA = vol.Schema({})


def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services. Looks up scanner/registry from hass.data."""

    def _any_runtime() -> dict | None:
        data = hass.data.get(DOMAIN, {})
        return next(iter(data.values()), None) if data else None

    async def _block(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_block_device(
            device_id=call.data["device_id"], reason=call.data["reason"]
        )

    async def _unblock(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_unblock(block_id=call.data["block_id"])

    async def _scan_now(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_scan_block(
            block_id=call.data["block_id"],
            per_device_timeout_seconds=runtime["options"][CONF_PER_DEVICE_TIMEOUT_SECONDS],
        )

    async def _scan_all(_call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_scan_all(
            max_duration_seconds=runtime["options"][CONF_SCAN_MAX_DURATION_MINUTES] * 60,
            per_device_timeout_seconds=runtime["options"][CONF_PER_DEVICE_TIMEOUT_SECONDS],
        )

    hass.services.async_register(DOMAIN, SERVICE_BLOCK, _block, BLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNBLOCK, _unblock, UNBLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, _scan_now, SCAN_NOW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_ALL, _scan_all, SCAN_ALL_SCHEMA)


def async_unregister_services(hass: HomeAssistant) -> None:
    for svc in (SERVICE_BLOCK, SERVICE_UNBLOCK, SERVICE_SCAN_NOW, SERVICE_SCAN_ALL):
        hass.services.async_remove(DOMAIN, svc)
