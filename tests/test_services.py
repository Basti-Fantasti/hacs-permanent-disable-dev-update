"""Tests for services."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_block_service_adds_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "svc1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    await hass.services.async_call(
        DOMAIN, "block",
        {"device_id": device.id, "reason": "via service"},
        blocking=True,
    )
    await hass.async_block_till_done()

    blocks = runtime["registry"].all_blocks()
    assert len(blocks) == 1
    assert blocks[0].reason == "via service"


async def test_unblock_service_removes_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "svc2")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u2", device_id=device.id
    )

    block = await runtime["scanner"].async_block_device(
        device_id=device.id, reason=""
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "unblock", {"block_id": block.id}, blocking=True
    )
    await hass.async_block_till_done()

    assert runtime["registry"].get_block(block.id) is None
