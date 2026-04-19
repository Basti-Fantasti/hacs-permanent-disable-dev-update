"""Tests for the scanner."""
from __future__ import annotations

import asyncio

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


async def test_scan_block_captures_latest_version(hass):
    """A scan cycle re-enables, waits for latest_version, captures it, re-disables."""
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "scan1")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    # Simulate integration populating latest_version shortly after re-enable.
    async def _populate():
        # Wait for the scanner to re-enable the entity, then set state.
        for _ in range(50):
            if ent_reg.async_get(update.entity_id).disabled_by is None:
                hass.states.async_set(
                    update.entity_id, "on",
                    {"installed_version": "1.0.0", "latest_version": "1.2.3"},
                )
                return
            await asyncio.sleep(0.01)

    task = asyncio.create_task(_populate())
    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=5)
    await task

    updated = registry.get_block(block.id)
    assert updated.last_known_version == "1.2.3"
    assert updated.last_scan_status == "ok"
    assert ent_reg.async_get(update.entity_id).disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_scan_block_timeout_records_timeout_status(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "scan2")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u2", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=1)

    updated = registry.get_block(block.id)
    assert updated.last_scan_status == "timeout"


async def test_scan_block_entity_gone(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "scan3")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u3", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    # Remove entity before scan.
    ent_reg.async_remove(update.entity_id)

    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=1)

    updated = registry.get_block(block.id)
    assert updated.last_scan_status == "entity_gone"


async def test_scan_all_visits_blocks_in_oldest_first_order(hass):
    from datetime import UTC, datetime, timedelta

    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    created_blocks = []
    for i in range(3):
        d = dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id, identifiers={("demo", f"scanall{i}")}
        )
        ent_reg.async_get_or_create(
            domain="update", platform="demo", unique_id=f"u{i}", device_id=d.id
        )
        b = await scanner.async_block_device(device_id=d.id, reason="")
        # Assign last_scan_at manually so order is deterministic.
        b.last_scan_at = (datetime.now(UTC) - timedelta(days=3 - i)).isoformat()
        await registry.async_update_block(b)
        created_blocks.append(b)

    visited: list[str] = []

    async def fake_scan_block(*, block_id: str, per_device_timeout_seconds: int) -> None:
        visited.append(block_id)
        b = registry.get_block(block_id)
        b.last_scan_at = datetime.now(UTC).isoformat()
        b.last_scan_status = "ok"
        await registry.async_update_block(b)

    scanner.async_scan_block = fake_scan_block  # type: ignore[method-assign]

    await scanner.async_scan_all(
        max_duration_seconds=60, per_device_timeout_seconds=5
    )

    # Oldest-first → the block with last_scan_at three days ago first.
    assert visited[0] == created_blocks[0].id
    assert visited[-1] == created_blocks[-1].id


async def test_block_device_captures_installed_version(hass):
    """Blocking captures both latest_version and installed_version from state."""
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("demo", "iv1")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="uiv", device_id=device.id
    )

    hass.states.async_set(
        update.entity_id, "on",
        {"installed_version": "1.9.0", "latest_version": "2.0.0"},
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    assert block.last_known_version == "2.0.0"
    assert block.installed_version == "1.9.0"


async def test_nightly_schedule_triggers_scan_at_configured_time(hass, freezer):
    from datetime import datetime

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    calls: list[str] = []

    async def fake_scan_all(*, max_duration_seconds, per_device_timeout_seconds):
        calls.append("scan_all")

    scanner.async_scan_all = fake_scan_all  # type: ignore[method-assign]

    # freezer available via pytest-homeassistant-custom-component fixtures.
    freezer.move_to(datetime(2026, 4, 16, 0, 59, 0))
    # Start schedule: default 01:00.
    remove = scanner.start_schedule()
    try:
        freezer.move_to(datetime(2026, 4, 16, 1, 0, 0))
        async_fire_time_changed = __import__(
            "pytest_homeassistant_custom_component.common",
            fromlist=["async_fire_time_changed"],
        ).async_fire_time_changed
        async_fire_time_changed(hass, datetime(2026, 4, 16, 1, 0, 0))
        await hass.async_block_till_done()

        assert calls == ["scan_all"]
    finally:
        remove()
