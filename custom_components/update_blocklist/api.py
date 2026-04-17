"""HTTP API used by the sidebar panel."""
from __future__ import annotations

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


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(BlocksListView())
    hass.http.register_view(OptionsView())
