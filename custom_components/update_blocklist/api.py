"""HTTP API used by the sidebar panel."""
from __future__ import annotations

import voluptuous as vol
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN


def _runtime(hass: HomeAssistant) -> dict | None:
    data = hass.data.get(DOMAIN, {})
    return next(iter(data.values()), None) if data else None


class _BaseView(HomeAssistantView):
    requires_auth = True


class BlocksListView(_BaseView):
    url = f"/api/{DOMAIN}/blocks"
    name = f"api:{DOMAIN}:blocks"

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return self.json({"blocks": [], "pending_rediscovery": []})
        data = runtime["coordinator"].data or {}
        return self.json(
            {
                "blocks": data.get("blocks", []),
                "pending_rediscovery": data.get("pending_rediscovery", []),
            }
        )


class OptionsView(_BaseView):
    url = f"/api/{DOMAIN}/options"
    name = f"api:{DOMAIN}:options"

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return self.json({}, status_code=404)
        return self.json(runtime["options"])


class BlocksWriteView(_BaseView):
    url = f"/api/{DOMAIN}/blocks"
    name = f"api:{DOMAIN}:blocks:write"

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return self.json_message("Integration not set up", status_code=404)

        try:
            payload = await request.json()
        except ValueError:
            return self.json_message("Invalid JSON", status_code=400)

        schema = vol.Schema(
            {
                vol.Required("device_id"): str,
                vol.Optional("reason", default=""): str,
            }
        )
        try:
            data = schema(payload)
        except vol.Invalid as exc:
            return self.json_message(str(exc), status_code=400)

        try:
            block = await runtime["scanner"].async_block_device(
                device_id=data["device_id"], reason=data["reason"]
            )
        except ValueError as exc:
            return self.json_message(str(exc), status_code=400)

        return self.json(block.to_dict(), status_code=201)


class BlockItemView(_BaseView):
    url = f"/api/{DOMAIN}/blocks/{{block_id}}"
    name = f"api:{DOMAIN}:blocks:item"

    async def delete(self, request: web.Request, block_id: str) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return web.Response(status=404)
        ok = await runtime["scanner"].async_unblock(block_id=block_id)
        return web.Response(status=204 if ok else 404)


class CandidatesView(_BaseView):
    url = f"/api/{DOMAIN}/candidates"
    name = f"api:{DOMAIN}:candidates"

    async def get(self, request: web.Request) -> web.Response:
        from homeassistant.helpers import device_registry as dr
        from homeassistant.helpers import entity_registry as er

        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return self.json({"candidates": []})

        dev_reg = dr.async_get(hass)
        ent_reg = er.async_get(hass)
        already_blocked_ids = {b.device_id for b in runtime["registry"].all_blocks()}

        devices_with_update: dict[str, list[str]] = {}
        for e in ent_reg.entities.values():
            if e.domain != "update" or not e.device_id:
                continue
            devices_with_update.setdefault(e.device_id, []).append(e.entity_id)

        candidates = []
        for device_id, entity_ids in devices_with_update.items():
            if device_id in already_blocked_ids:
                continue
            device = dev_reg.async_get(device_id)
            if device is None:
                continue
            candidates.append(
                {
                    "device_id": device_id,
                    "name": device.name_by_user or device.name or device_id,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "update_entity_ids": entity_ids,
                }
            )

        return self.json({"candidates": candidates})


class ScanView(_BaseView):
    url = f"/api/{DOMAIN}/scan"
    name = f"api:{DOMAIN}:scan"

    async def post(self, request: web.Request) -> web.Response:
        from .const import (
            CONF_PER_DEVICE_TIMEOUT_SECONDS,
            CONF_SCAN_MAX_DURATION_MINUTES,
        )

        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return web.Response(status=404)

        try:
            payload = await request.json()
        except ValueError:
            payload = {}

        block_id = payload.get("block_id")
        options = runtime["options"]
        scanner = runtime["scanner"]

        if block_id:
            hass.async_create_task(
                scanner.async_scan_block(
                    block_id=block_id,
                    per_device_timeout_seconds=options[CONF_PER_DEVICE_TIMEOUT_SECONDS],
                )
            )
        else:
            hass.async_create_task(
                scanner.async_scan_all(
                    max_duration_seconds=options[CONF_SCAN_MAX_DURATION_MINUTES] * 60,
                    per_device_timeout_seconds=options[CONF_PER_DEVICE_TIMEOUT_SECONDS],
                )
            )

        return web.Response(status=202)


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(BlocksListView())
    hass.http.register_view(BlocksWriteView())
    hass.http.register_view(BlockItemView())
    hass.http.register_view(OptionsView())
    hass.http.register_view(CandidatesView())
    hass.http.register_view(ScanView())
