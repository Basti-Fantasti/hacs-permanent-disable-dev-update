"""Tests for the config and options flows."""
from __future__ import annotations

from homeassistant import config_entries, data_entry_flow

from custom_components.update_blocklist.const import (
    CONF_PER_DEVICE_TIMEOUT_SECONDS,
    CONF_SCAN_MAX_DURATION_MINUTES,
    CONF_SCAN_START_TIME,
    DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
    DEFAULT_SCAN_MAX_DURATION_MINUTES,
    DEFAULT_SCAN_START_TIME,
    DOMAIN,
)


async def test_user_step_creates_entry_with_defaults(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Update Blocklist"
    assert result["options"] == {
        CONF_SCAN_START_TIME: DEFAULT_SCAN_START_TIME,
        CONF_SCAN_MAX_DURATION_MINUTES: DEFAULT_SCAN_MAX_DURATION_MINUTES,
        CONF_PER_DEVICE_TIMEOUT_SECONDS: DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
    }


async def test_only_one_entry_allowed(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    MockConfigEntry(domain=DOMAIN, data={}, options={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_accepts_valid_input(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SCAN_START_TIME: "02:30",
            CONF_SCAN_MAX_DURATION_MINUTES: 45,
            CONF_PER_DEVICE_TIMEOUT_SECONDS: 180,
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SCAN_START_TIME] == "02:30"


async def test_options_flow_rejects_invalid_time(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SCAN_START_TIME: "99:99",
            CONF_SCAN_MAX_DURATION_MINUTES: 30,
            CONF_PER_DEVICE_TIMEOUT_SECONDS: 300,
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {CONF_SCAN_START_TIME: "invalid_time"}
