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

        # Capture last known latest_version and current installed_version from state
        # before disabling.
        last_known_version: str | None = None
        installed_version: str | None = None
        for eid in update_entity_ids:
            state = self._hass.states.get(eid)
            if not state:
                continue
            if last_known_version is None and state.attributes.get("latest_version"):
                last_known_version = state.attributes["latest_version"]
            if installed_version is None and state.attributes.get("installed_version"):
                installed_version = state.attributes["installed_version"]
            if last_known_version is not None and installed_version is not None:
                break

        block = await self._registry.async_add_block(
            device_id=device_id,
            update_entity_ids=update_entity_ids,
            unique_ids=unique_ids,
            fingerprint=fingerprint,
            reason=reason,
            last_known_version=last_known_version,
            installed_version=installed_version,
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

    async def async_scan_block(
        self, *, block_id: str, per_device_timeout_seconds: int
    ) -> None:
        """Re-enable entity → wait for latest_version → re-disable."""
        block = self._registry.get_block(block_id)
        if block is None:
            _LOGGER.debug("Scan requested for unknown block %s", block_id)
            return

        ent_reg = er.async_get(self._hass)

        # Find the first still-existing update entity for this block.
        target_eid: str | None = None
        for eid in block.update_entity_ids:
            if ent_reg.async_get(eid) is not None:
                target_eid = eid
                break

        if target_eid is None:
            block.last_scan_at = datetime.now(UTC).isoformat()
            block.last_scan_status = SCAN_STATUS_ENTITY_GONE
            await self._registry.async_update_block(block)
            await self._coordinator.async_request_refresh()
            return

        # Re-enable.
        ent_reg.async_update_entity(target_eid, disabled_by=None)

        # Pre-skip known latest to reduce the notification surface.
        if block.last_known_version:
            try:
                await self._hass.services.async_call(
                    "update", "skip", {"entity_id": target_eid}, blocking=False
                )
            except Exception:  # noqa: BLE001
                _LOGGER.debug("update.skip not available yet for %s", target_eid)

        # Wait for latest_version to populate.
        new_version = await self._wait_for_latest_version(
            target_eid, per_device_timeout_seconds
        )

        block.last_scan_at = datetime.now(UTC).isoformat()
        if new_version is None:
            block.last_scan_status = SCAN_STATUS_TIMEOUT
        else:
            block.last_known_version = new_version
            block.last_scan_status = SCAN_STATUS_OK

        # Re-disable.
        ent_reg.async_update_entity(
            target_eid, disabled_by=er.RegistryEntryDisabler.INTEGRATION
        )

        await self._registry.async_update_block(block)
        await self._coordinator.async_request_refresh()

    async def _wait_for_latest_version(
        self, entity_id: str, timeout_seconds: int
    ) -> str | None:
        """Wait until the entity reports a `latest_version` attribute, or timeout."""
        done = asyncio.Event()
        captured: dict[str, str] = {}

        @callback
        def _on_change(event: Event) -> None:
            new_state = event.data.get("new_state")
            if new_state and new_state.attributes.get("latest_version"):
                captured["v"] = new_state.attributes["latest_version"]
                done.set()

        # Fast path: state already exists.
        state = self._hass.states.get(entity_id)
        if state and state.attributes.get("latest_version"):
            return state.attributes["latest_version"]

        remove = async_track_state_change_event(self._hass, [entity_id], _on_change)
        try:
            await asyncio.wait_for(done.wait(), timeout=timeout_seconds)
            return captured.get("v")
        except TimeoutError:
            return None
        finally:
            remove()

    async def async_scan_all(
        self,
        *,
        max_duration_seconds: int,
        per_device_timeout_seconds: int,
    ) -> None:
        """Scan every block in oldest-first order, bounded by max_duration_seconds."""
        import time
        started = time.monotonic()

        blocks = sorted(
            self._registry.all_blocks(),
            key=lambda b: b.last_scan_at or "",
        )
        for block in blocks:
            if time.monotonic() - started >= max_duration_seconds:
                _LOGGER.info(
                    "Scan window elapsed; %d blocks not scanned this cycle.",
                    len(blocks) - blocks.index(block),
                )
                break
            try:
                await self.async_scan_block(
                    block_id=block.id,
                    per_device_timeout_seconds=per_device_timeout_seconds,
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Scan failed for block %s", block.id)

    async def async_resolve_rediscovery(
        self, *, orphan_block_id: str, candidate_device_id: str | None, action: str
    ) -> bool:
        """Resolve a pending rediscovery item.

        action:
          - "accept": migrate the block to candidate_device_id, re-disable its entity
          - "decline": delete the block
          - "dismiss": remove the pending entry but keep the orphan block as-is
        """
        block = self._registry.get_block(orphan_block_id)
        if block is None:
            return False

        pending = [
            item
            for item in self._registry.pending_rediscovery
            if item["orphan_block_id"] != orphan_block_id
        ]

        if action == "decline":
            await self._registry.async_remove_block(orphan_block_id)
        elif action == "accept" and candidate_device_id is not None:
            dev_reg = dr.async_get(self._hass)
            ent_reg = er.async_get(self._hass)
            device = dev_reg.async_get(candidate_device_id)
            if device is None:
                return False
            update_entities = [
                e.entity_id for e in ent_reg.entities.values()
                if e.domain == "update" and e.device_id == candidate_device_id
            ]
            block.device_id = candidate_device_id
            block.update_entity_ids = update_entities
            block.unique_ids = [
                e.unique_id for e in ent_reg.entities.values()
                if e.domain == "update" and e.device_id == candidate_device_id and e.unique_id
            ]
            block.fingerprint = generate_fingerprint(
                manufacturer=device.manufacturer,
                model=device.model,
                name=device.name_by_user or device.name,
            )
            await self._registry.async_update_block(block)
            for eid in update_entities:
                ent_reg.async_update_entity(
                    eid, disabled_by=er.RegistryEntryDisabler.INTEGRATION
                )
        # "dismiss" path: pending list already pruned above.

        await self._registry.async_set_pending_rediscovery(pending)
        await self._coordinator.async_request_refresh()
        return True

    async def async_detect_rediscovery(self) -> None:
        """Scan for orphan blocks whose devices may have re-paired.

        Populates registry.pending_rediscovery.
        """
        dev_reg = dr.async_get(self._hass)
        ent_reg = er.async_get(self._hass)

        orphans = self._registry.find_orphans(dev_reg)

        pending: list[dict] = []

        # Preserve entries for orphans still pending (to avoid clobbering dismissed state).
        existing_by_orphan = {
            item["orphan_block_id"]: item
            for item in self._registry.pending_rediscovery
        }

        for orphan in orphans:
            candidates = self._registry.match_rediscovery_candidates(
                orphan, dev_reg, ent_reg
            )
            if not candidates:
                continue
            chosen = candidates[0]
            existing = existing_by_orphan.get(orphan.id)
            pending.append(
                existing
                or {
                    "orphan_block_id": orphan.id,
                    "candidate_device_id": chosen["device_id"],
                    "match_type": chosen["match_type"],
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )

        await self._registry.async_set_pending_rediscovery(pending)
        await self._coordinator.async_refresh()

    def start_schedule(self):
        """Install the nightly scan trigger at options[CONF_SCAN_START_TIME].

        Returns a callable that removes the listener.
        """
        from homeassistant.helpers.event import async_track_time_change

        from .const import (
            CONF_PER_DEVICE_TIMEOUT_SECONDS,
            CONF_SCAN_MAX_DURATION_MINUTES,
            CONF_SCAN_START_TIME,
        )

        hh_mm = self._options[CONF_SCAN_START_TIME]
        hour, minute = (int(x) for x in hh_mm.split(":"))

        async def _tick(_now):
            await self.async_scan_all(
                max_duration_seconds=self._options[CONF_SCAN_MAX_DURATION_MINUTES] * 60,
                per_device_timeout_seconds=self._options[CONF_PER_DEVICE_TIMEOUT_SECONDS],
            )

        return async_track_time_change(
            self._hass, _tick, hour=hour, minute=minute, second=0
        )
