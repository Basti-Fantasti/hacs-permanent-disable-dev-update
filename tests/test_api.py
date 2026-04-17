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


async def test_add_block_endpoint(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "add1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    client = await hass_client()
    resp = await client.post(
        f"/api/{DOMAIN}/blocks",
        json={"device_id": device.id, "reason": "x"},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["device_id"] == device.id
    assert len(runtime["registry"].all_blocks()) == 1


async def test_remove_block_endpoint(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "rem1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )
    block = await runtime["scanner"].async_block_device(
        device_id=device.id, reason=""
    )

    client = await hass_client()
    resp = await client.delete(f"/api/{DOMAIN}/blocks/{block.id}")
    assert resp.status == 204
    assert runtime["registry"].get_block(block.id) is None


async def test_add_block_returns_400_for_missing_device_id(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/blocks", json={"reason": "x"})
    assert resp.status == 400


async def test_candidate_devices_returns_only_unblocked_devices_with_update_entities(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    d_with_update = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "wu")},
        manufacturer="Espressif", model="ESP", name="With Update",
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="U1",
        device_id=d_with_update.id,
    )

    d_no_update = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "nu")}
    )

    d_already_blocked = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "ab")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="U2",
        device_id=d_already_blocked.id,
    )
    await runtime["scanner"].async_block_device(
        device_id=d_already_blocked.id, reason=""
    )

    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/candidates")
    assert resp.status == 200
    data = await resp.json()
    ids = [c["device_id"] for c in data["candidates"]]
    assert d_with_update.id in ids
    assert d_no_update.id not in ids
    assert d_already_blocked.id not in ids


async def test_scan_endpoint_triggers_scan_all_when_no_block_id(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    calls: list[str] = []

    async def fake_scan_all(*, max_duration_seconds, per_device_timeout_seconds):
        calls.append("all")

    runtime["scanner"].async_scan_all = fake_scan_all  # type: ignore[method-assign]

    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/scan", json={})
    assert resp.status == 202
    await hass.async_block_till_done()
    assert calls == ["all"]


async def test_scan_endpoint_with_block_id_triggers_scan_block(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    calls: list[str] = []

    async def fake_scan_block(*, block_id, per_device_timeout_seconds):
        calls.append(block_id)

    runtime["scanner"].async_scan_block = fake_scan_block  # type: ignore[method-assign]

    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/scan", json={"block_id": "abc"})
    assert resp.status == 202
    await hass.async_block_till_done()
    assert calls == ["abc"]
