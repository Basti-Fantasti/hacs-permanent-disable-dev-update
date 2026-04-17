"""Integration setup / unload tests."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def test_setup_and_unload_entry(hass):
    """A freshly added config entry sets up and unloads cleanly."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()

    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id) is True
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data[DOMAIN]
