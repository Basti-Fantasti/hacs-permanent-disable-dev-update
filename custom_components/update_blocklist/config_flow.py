"""Config flow for update_blocklist."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_PER_DEVICE_TIMEOUT_SECONDS,
    CONF_SCAN_MAX_DURATION_MINUTES,
    CONF_SCAN_START_TIME,
    DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
    DEFAULT_SCAN_MAX_DURATION_MINUTES,
    DEFAULT_SCAN_START_TIME,
    DOMAIN,
)

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


def _default_options() -> dict[str, Any]:
    return {
        CONF_SCAN_START_TIME: DEFAULT_SCAN_START_TIME,
        CONF_SCAN_MAX_DURATION_MINUTES: DEFAULT_SCAN_MAX_DURATION_MINUTES,
        CONF_PER_DEVICE_TIMEOUT_SECONDS: DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
    }


class UpdateBlocklistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """First-time setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

        return self.async_create_entry(
            title="Update Blocklist",
            data={},
            options=_default_options(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return UpdateBlocklistOptionsFlow(config_entry)


class UpdateBlocklistOptionsFlow(config_entries.OptionsFlow):
    """Edit scan window and timeout defaults."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = {**_default_options(), **self._entry.options}

        if user_input is not None:
            errors: dict[str, str] = {}
            if not _TIME_RE.match(user_input[CONF_SCAN_START_TIME]):
                errors[CONF_SCAN_START_TIME] = "invalid_time"
            if user_input[CONF_SCAN_MAX_DURATION_MINUTES] < 1:
                errors[CONF_SCAN_MAX_DURATION_MINUTES] = "invalid_duration"
            if user_input[CONF_PER_DEVICE_TIMEOUT_SECONDS] < 10:
                errors[CONF_PER_DEVICE_TIMEOUT_SECONDS] = "invalid_timeout"

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_options_schema(user_input),
                    errors=errors,
                )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=_options_schema(current))


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_START_TIME, default=defaults[CONF_SCAN_START_TIME]
            ): str,
            vol.Required(
                CONF_SCAN_MAX_DURATION_MINUTES,
                default=defaults[CONF_SCAN_MAX_DURATION_MINUTES],
            ): vol.All(int, vol.Range(min=1, max=240)),
            vol.Required(
                CONF_PER_DEVICE_TIMEOUT_SECONDS,
                default=defaults[CONF_PER_DEVICE_TIMEOUT_SECONDS],
            ): vol.All(int, vol.Range(min=10, max=1800)),
        }
    )
