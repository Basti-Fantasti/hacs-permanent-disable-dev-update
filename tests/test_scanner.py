"""Tests for the scanner."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup_integration(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_block_device_disables_update_entity(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "wled")},
        manufacturer="Espressif", model="ESP8266", name="WLED Custom",
    )
    update_entity = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="AA:BB",
        device_id=device.id,
    )

    await scanner.async_block_device(device_id=device.id, reason="custom")
    await hass.async_block_till_done()

    updated = ent_reg.async_get(update_entity.entity_id)
    assert updated.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_block_device_raises_if_no_update_entity(hass):
    import pytest
    from homeassistant.helpers import device_registry as dr

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "no_update")}
    )

    with pytest.raises(ValueError, match="no update entity"):
        await scanner.async_block_device(device_id=device.id, reason="x")


async def test_unblock_reenables_update_entity_and_removes_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "w2")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u1", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    await scanner.async_unblock(block_id=block.id)
    await hass.async_block_till_done()

    assert registry.get_block(block.id) is None
    assert ent_reg.async_get(update.entity_id).disabled_by is None
