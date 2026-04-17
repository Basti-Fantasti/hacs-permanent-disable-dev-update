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


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(BlocksListView())
    hass.http.register_view(BlocksWriteView())
    hass.http.register_view(BlockItemView())
    hass.http.register_view(OptionsView())
