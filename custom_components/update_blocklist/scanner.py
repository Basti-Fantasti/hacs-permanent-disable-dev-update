"""Scanner — block/unblock operations and periodic scan cycle."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    SCAN_STATUS_ENTITY_GONE,
    SCAN_STATUS_OK,
    SCAN_STATUS_TIMEOUT,
)
from .coordinator import UpdateBlocklistCoordinator
from .identity import generate_fingerprint
from .registry import Block, BlockRegistry

_LOGGER = logging.getLogger(__name__)


class Scanner:
    """Owns the block/unblock choreography and the scan cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        registry: BlockRegistry,
        coordinator: UpdateBlocklistCoordinator,
        options: dict[str, Any],
    ) -> None:
        self._hass = hass
        self._registry = registry
        self._coordinator = coordinator
        self._options = options

    async def async_block_device(self, *, device_id: str, reason: str) -> Block:
        """Create a block for `device_id` and disable its update entity(ies)."""
        dev_reg = dr.async_get(self._hass)
        ent_reg = er.async_get(self._hass)

        device = dev_reg.async_get(device_id)
        if device is None:
            raise ValueError(f"Device {device_id!r} does not exist")

        update_entities = [
            e
            for e in ent_reg.entities.values()
            if e.domain == "update" and e.device_id == device_id
        ]
        if not update_entities:
            raise ValueError(f"Device {device_id!r} has no update entity")

        unique_ids = [e.unique_id for e in update_entities if e.unique_id]
        update_entity_ids = [e.entity_id for e in update_entities]

        fingerprint = generate_fingerprint(
            manufacturer=device.manufacturer,
            model=device.model,
            name=device.name_by_user or device.name,
        )

        # Capture last known latest_version from state before disabling.
        last_known_version = None
        for eid in update_entity_ids:
            state = self._hass.states.get(eid)
            if state and state.attributes.get("latest_version"):
                last_known_version = state.attributes["latest_version"]
                break

        block = await self._registry.async_add_block(
            device_id=device_id,
            update_entity_ids=update_entity_ids,
            unique_ids=unique_ids,
            fingerprint=fingerprint,
            reason=reason,
            last_known_version=last_known_version,
        )

        for eid in update_entity_ids:
            ent_reg.async_update_entity(
                eid, disabled_by=er.RegistryEntryDisabler.INTEGRATION
            )

        await self._coordinator.async_request_refresh()
        return block

    async def async_unblock(self, *, block_id: str) -> bool:
        """Remove a block and re-enable its update entities."""
        block = self._registry.get_block(block_id)
        if block is None:
            return False

        ent_reg = er.async_get(self._hass)
        for eid in block.update_entity_ids:
            entry = ent_reg.async_get(eid)
            if entry is None:
                continue
            if entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
                ent_reg.async_update_entity(eid, disabled_by=None)

        await self._registry.async_remove_block(block_id)
        await self._coordinator.async_request_refresh()
        return True
