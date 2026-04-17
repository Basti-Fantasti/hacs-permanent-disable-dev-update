"""Integration-level sensor platform."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UpdateBlocklistCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: UpdateBlocklistCoordinator = runtime["coordinator"]

    async_add_entities(
        [
            BlockedCountSensor(coordinator, entry.entry_id),
            LastScanRunSensor(coordinator, entry.entry_id),
            NextScanAtSensor(coordinator, entry.entry_id),
        ]
    )

    known_ids: set[str] = set()

    @callback
    def _sync_shadow_entities() -> None:
        current_ids = {b["id"] for b in coordinator.data.get("blocks", [])}
        new_ids = current_ids - known_ids
        if new_ids:
            async_add_entities(
                [BlockShadowSensor(coordinator, entry.entry_id, bid) for bid in new_ids]
            )
            known_ids.update(new_ids)
        known_ids.intersection_update(current_ids | new_ids)

    _sync_shadow_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_shadow_entities))


def _integration_device(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Update Blocklist",
        manufacturer="update_blocklist",
        entry_type="service",
    )


class _IntegrationSensor(CoordinatorEntity[UpdateBlocklistCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: UpdateBlocklistCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = _integration_device(entry_id)


class BlockedCountSensor(_IntegrationSensor):
    _attr_name = "Blocked count"
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_blocked_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("blocks", []))


class LastScanRunSensor(_IntegrationSensor):
    _attr_name = "Last scan run"
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_last_scan_run"

    @property
    def native_value(self) -> str | None:
        times = [
            b.get("last_scan_at")
            for b in self.coordinator.data.get("blocks", [])
            if b.get("last_scan_at")
        ]
        return max(times) if times else None


class NextScanAtSensor(_IntegrationSensor):
    _attr_name = "Next scan at"
    _attr_icon = "mdi:clock-start"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_next_scan_at"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("next_scan_at")


class BlockShadowSensor(_IntegrationSensor):
    _attr_icon = "mdi:update"

    def __init__(self, coordinator, entry_id: str, block_id: str):
        super().__init__(coordinator, entry_id)
        self._block_id = block_id
        self._attr_unique_id = f"{entry_id}_{block_id}_blocked_update_status"
        block_data = self._block()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}:{block_id}")},
            via_device=(DOMAIN, entry_id),
            name=f"Blocked device {block_data['device_id']}" if block_data else None,
        )

    def _block(self) -> dict | None:
        for b in self.coordinator.data.get("blocks", []):
            if b["id"] == self._block_id:
                return b
        return None

    @property
    def available(self) -> bool:
        return self._block() is not None

    @property
    def name(self) -> str:
        return "Blocked update status"

    @property
    def native_value(self) -> str | None:
        b = self._block()
        return b.get("last_known_version") if b else None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        b = self._block()
        if not b:
            return None
        return {
            "installed_version": None,
            "last_scan_at": b.get("last_scan_at"),
            "last_scan_status": b.get("last_scan_status"),
            "blocked_since": b.get("created_at"),
            "reason": b.get("reason"),
            "matched_by": "device_id",
            "update_entity_ids": b.get("update_entity_ids", []),
        }
