"""Tests for integration-level sensors."""
from __future__ import annotations
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.update_blocklist.const import DOMAIN


async def test_blocked_count_sensor_reports_zero_initially(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.update_blocklist_blocked_count")
    assert state is not None
    assert state.state == "0"


async def test_blocked_count_sensor_updates_when_block_added(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="d1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()
    state = hass.states.get("sensor.update_blocklist_blocked_count")
    assert state.state == "1"
