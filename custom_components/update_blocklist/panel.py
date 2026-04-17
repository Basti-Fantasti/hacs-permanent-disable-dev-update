"""Register the sidebar panel."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve panel.js and register the custom sidebar panel."""
    panel_js = Path(__file__).parent / "www" / "panel.js"

    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_URL, str(panel_js), cache_headers=False)]
    )

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="update-blocklist-panel",
        frontend_url_path=DOMAIN,
        module_url=PANEL_URL,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=True,
    )


async def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel on unload."""
    from homeassistant.components import frontend

    frontend.async_remove_panel(hass, DOMAIN)
