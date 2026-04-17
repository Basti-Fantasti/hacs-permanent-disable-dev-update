"""Tests for panel API."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_list_blocks_returns_empty(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/blocks")
    assert resp.status == 200
    data = await resp.json()
    assert data == {"blocks": [], "pending_rediscovery": []}


async def test_list_blocks_includes_added_block(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="d1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="r", last_known_version="1.0",
    )
    await runtime["coordinator"].async_request_refresh()

    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/blocks")
    data = await resp.json()
    assert len(data["blocks"]) == 1
    assert data["blocks"][0]["reason"] == "r"


async def test_get_options_returns_current_options(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/options")
    assert resp.status == 200
    data = await resp.json()
    assert data["scan_start_time"] == "01:00"
