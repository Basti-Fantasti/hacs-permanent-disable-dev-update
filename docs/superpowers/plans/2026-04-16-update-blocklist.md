# Update Blocklist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `update_blocklist` HACS integration — a Home Assistant custom component that maintains a permanent block list for firmware updates of specific devices.

**Architecture:** Single HACS integration. Python backend in `custom_components/update_blocklist/`; Lit sidebar panel in `frontend/` built via Vite into `custom_components/update_blocklist/www/panel.js`. Blocked devices have their `update.*` entities disabled via the entity registry. A configurable nightly scan window briefly re-enables them to capture the latest available version into a shadow sensor, then re-disables.

**Tech Stack:**
- Python 3.12+, Home Assistant 2024.12.0+
- `pytest-homeassistant-custom-component` for backend tests
- `ruff` for Python linting/formatting
- TypeScript 5.x + Lit 3.x
- Vite 5.x + Vitest 1.x for the panel
- `@open-wc/testing-helpers` for Lit component tests
- GitHub Actions: `hassfest` + `hacs/action` (required for HACS default store)

**Reference:** The complete design is in `docs/superpowers/specs/2026-04-16-update-blocklist-design.md`. Read it before starting.

**Repository root (cwd for all commands):** `/mnt/x/git_local/hacs-permanent-disable-dev-update/`

**Phases:**
1. Repository scaffolding + HA/HACS metadata (Tasks 1–5)
2. Backend pure-logic modules: identity, store, registry (Tasks 6–12)
3. Config flow + options flow (Tasks 13–15)
4. Coordinator + entity platforms (Tasks 16–19)
5. Scanner (Tasks 20–24)
6. Services (Task 25)
7. Panel API (aiohttp views) (Tasks 26–30)
8. Frontend scaffolding + panel UI (Tasks 31–37)
9. Panel registration (`panel.py`) (Task 38)
10. Re-pair detection wiring (Task 39)
11. Safe uninstall + startup cleanup (Tasks 40–41)
12. Translations (Task 42)
13. CI workflows (Tasks 43–45)
14. Release docs (Task 46)

---

## Phase 1: Repository Scaffolding

### Task 1: Base repository files

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `README.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
*.egg-info/
.venv/
venv/

# Node
node_modules/
dist/
.vite/

# Editors
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build outputs (frontend build lands in custom_components/update_blocklist/www/, keep committed)
# but leave source maps out
*.map
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "update_blocklist"
version = "0.1.0"
description = "Home Assistant custom integration for permanently blocking device firmware updates"
requires-python = ">=3.12"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "ASYNC"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Create `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 Bastian Teufel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Create `README.md` (minimal, filled out in Task 46)**

```markdown
# Update Blocklist

Home Assistant custom integration for permanently blocking device firmware updates.

Full README and usage documentation will be populated before the first release.
```

- [ ] **Step 5: Create `CHANGELOG.md`**

```markdown
# Changelog

## [Unreleased]

### Added
- Initial scaffolding.
```

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml LICENSE README.md CHANGELOG.md
git commit -m "Add repository scaffolding"
```

---

### Task 2: HA integration manifest and HACS metadata

**Files:**
- Create: `custom_components/update_blocklist/manifest.json`
- Create: `hacs.json`
- Create: `info.md`

- [ ] **Step 1: Create `custom_components/update_blocklist/manifest.json`**

```json
{
  "domain": "update_blocklist",
  "name": "Update Blocklist",
  "version": "0.1.0",
  "documentation": "https://github.com/Basti-Fantasti/hacs-permanent-disable-dev-update",
  "issue_tracker": "https://github.com/Basti-Fantasti/hacs-permanent-disable-dev-update/issues",
  "codeowners": ["@Basti-Fantasti"],
  "config_flow": true,
  "integration_type": "service",
  "iot_class": "calculated",
  "dependencies": ["frontend", "http"],
  "requirements": []
}
```

- [ ] **Step 2: Create `hacs.json`**

```json
{
  "name": "Update Blocklist",
  "render_readme": true,
  "homeassistant": "2024.12.0",
  "zip_release": true,
  "filename": "update_blocklist.zip"
}
```

- [ ] **Step 3: Create `info.md` (shown in HACS browse UI)**

```markdown
# Update Blocklist

Permanently block firmware updates for specific devices.

Useful when a device's firmware must not change — custom WLED boards,
patched Zigbee coordinators, devices with broken upgrade paths.

Install, open the sidebar panel, add the devices you want to block.
```

- [ ] **Step 4: Commit**

```bash
git add custom_components/update_blocklist/manifest.json hacs.json info.md
git commit -m "Add integration manifest and HACS metadata"
```

---

### Task 3: Constants module

**Files:**
- Create: `custom_components/update_blocklist/const.py`

- [ ] **Step 1: Write `const.py` with the complete set of constants**

```python
"""Constants for the update_blocklist integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "update_blocklist"
PLATFORMS: Final = ["sensor", "binary_sensor", "button"]

# Config entry / options keys
CONF_SCAN_START_TIME: Final = "scan_start_time"            # "HH:MM" string
CONF_SCAN_MAX_DURATION_MINUTES: Final = "scan_max_duration_minutes"
CONF_PER_DEVICE_TIMEOUT_SECONDS: Final = "per_device_timeout_seconds"

DEFAULT_SCAN_START_TIME: Final = "01:00"
DEFAULT_SCAN_MAX_DURATION_MINUTES: Final = 30
DEFAULT_PER_DEVICE_TIMEOUT_SECONDS: Final = 300

# Storage
STORAGE_KEY: Final = f"{DOMAIN}.blocks"
STORAGE_VERSION: Final = 1

# Scan result statuses
SCAN_STATUS_OK: Final = "ok"
SCAN_STATUS_TIMEOUT: Final = "timeout"
SCAN_STATUS_ENTITY_GONE: Final = "entity_gone"
SCAN_STATUS_DISABLE_FAILED: Final = "disable_failed"
SCAN_STATUS_NEVER_SCANNED: Final = "never_scanned"

# Block lifecycle statuses
BLOCK_STATUS_ACTIVE: Final = "active"
BLOCK_STATUS_USER_OVERRIDDEN: Final = "user_overridden"
BLOCK_STATUS_ORPHAN: Final = "orphan"

# Rediscovery match types
MATCH_UNIQUE_ID: Final = "unique_id"
MATCH_FINGERPRINT: Final = "fingerprint"

# Event names
SIGNAL_BLOCKS_UPDATED: Final = f"{DOMAIN}_blocks_updated"

# Panel
PANEL_URL: Final = f"/{DOMAIN}/panel.js"
PANEL_TITLE: Final = "Update Blocklist"
PANEL_ICON: Final = "mdi:shield-lock-outline"
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/update_blocklist/const.py
git commit -m "Add const module with domain, defaults, and status enums"
```

---

### Task 4: Integration entry point (minimal)

**Files:**
- Create: `custom_components/update_blocklist/__init__.py`

- [ ] **Step 1: Write minimal `__init__.py`**

```python
"""Update Blocklist integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up update_blocklist from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/update_blocklist/__init__.py
git commit -m "Add minimal integration entry point"
```

---

### Task 5: Test infrastructure and first integration-loads test

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_init.py`
- Create: `requirements_test.txt`

- [ ] **Step 1: Create `requirements_test.txt`**

```
pytest>=8.0
pytest-asyncio>=0.23
pytest-homeassistant-custom-component>=0.13
ruff>=0.5
```

- [ ] **Step 2: Create `tests/__init__.py`**

```python
"""Tests for update_blocklist."""
```

- [ ] **Step 3: Create `tests/conftest.py`**

```python
"""Shared fixtures for update_blocklist tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom_components during tests."""
    yield
```

- [ ] **Step 4: Create the failing test `tests/test_init.py`**

```python
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
```

- [ ] **Step 5: Install test deps and run the test**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
pytest tests/test_init.py -v
```

Expected: PASS (entry point from Task 4 supports setup/unload).

- [ ] **Step 6: Commit**

```bash
git add tests/ requirements_test.txt
git commit -m "Add test infrastructure and setup/unload integration test"
```

---

## Phase 2: Backend Pure-Logic Modules

### Task 6: identity.py — fingerprint generation and matching

**Files:**
- Create: `custom_components/update_blocklist/identity.py`
- Create: `tests/test_identity.py`

- [ ] **Step 1: Write failing test `tests/test_identity.py`**

```python
"""Tests for identity fingerprint generation and matching."""
from __future__ import annotations

from custom_components.update_blocklist.identity import (
    fingerprint_matches,
    generate_fingerprint,
)


def test_generate_fingerprint_captures_all_fields():
    fp = generate_fingerprint(
        manufacturer="Espressif", model="ESP8266", name="WLED Custom Strip"
    )
    assert fp == {
        "manufacturer": "espressif",
        "model": "esp8266",
        "name": "wled custom strip",
    }


def test_generate_fingerprint_handles_none():
    fp = generate_fingerprint(manufacturer=None, model="ESP8266", name=None)
    assert fp == {"manufacturer": "", "model": "esp8266", "name": ""}


def test_generate_fingerprint_strips_whitespace():
    fp = generate_fingerprint(manufacturer="  Espressif  ", model="ESP", name="  X  ")
    assert fp["manufacturer"] == "espressif"
    assert fp["name"] == "x"


def test_fingerprint_matches_exact():
    a = generate_fingerprint("Espressif", "ESP8266", "WLED Custom")
    b = generate_fingerprint("Espressif", "ESP8266", "WLED Custom")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_case_insensitive_name():
    a = generate_fingerprint("Espressif", "ESP8266", "WLED CUSTOM")
    b = generate_fingerprint("Espressif", "ESP8266", "wled custom")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_requires_manufacturer_and_model():
    a = generate_fingerprint("Espressif", "ESP8266", "X")
    b = generate_fingerprint("Shelly", "ESP8266", "X")
    assert fingerprint_matches(a, b) is False


def test_fingerprint_matches_tolerates_minor_name_differences():
    """Name differing by a trailing numeric suffix still matches if prefix is equal."""
    a = generate_fingerprint("Espressif", "ESP8266", "WLED Strip")
    b = generate_fingerprint("Espressif", "ESP8266", "WLED Strip 2")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_rejects_unrelated_names():
    a = generate_fingerprint("Espressif", "ESP8266", "WLED Strip")
    b = generate_fingerprint("Espressif", "ESP8266", "Completely Different")
    assert fingerprint_matches(a, b) is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_identity.py -v
```

Expected: FAIL (module does not exist).

- [ ] **Step 3: Implement `custom_components/update_blocklist/identity.py`**

```python
"""Device identity — fingerprint generation and matching."""
from __future__ import annotations

from typing import TypedDict


class Fingerprint(TypedDict):
    manufacturer: str
    model: str
    name: str


def generate_fingerprint(
    *, manufacturer: str | None, model: str | None, name: str | None
) -> Fingerprint:
    """Normalize device metadata into a comparable fingerprint.

    Normalization: strip whitespace, lowercase. None becomes empty string.
    """
    return {
        "manufacturer": (manufacturer or "").strip().lower(),
        "model": (model or "").strip().lower(),
        "name": (name or "").strip().lower(),
    }


def fingerprint_matches(a: Fingerprint, b: Fingerprint) -> bool:
    """Return True if fingerprints plausibly describe the same physical device.

    Rules:
      - manufacturer and model must be equal and non-empty
      - names are considered equivalent if one is a prefix of the other (length
        within 4 characters) — tolerates trailing numeric suffixes on re-pair.
    """
    if not a["manufacturer"] or not a["model"]:
        return False
    if a["manufacturer"] != b["manufacturer"] or a["model"] != b["model"]:
        return False

    name_a = a["name"]
    name_b = b["name"]
    if name_a == name_b:
        return True
    # Prefix tolerance: one name is a prefix of the other within 4 extra chars.
    short, long = sorted([name_a, name_b], key=len)
    if long.startswith(short) and len(long) - len(short) <= 4:
        return True
    return False
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_identity.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/identity.py tests/test_identity.py
git commit -m "Add identity module with fingerprint generation and matching"
```

---

### Task 7: store.py — versioned Store wrapper (load/save)

**Files:**
- Create: `custom_components/update_blocklist/store.py`
- Create: `tests/test_store.py`

- [ ] **Step 1: Write failing test `tests/test_store.py`**

```python
"""Tests for the BlocksStore wrapper."""
from __future__ import annotations

from custom_components.update_blocklist.store import BlocksStore, StoredData


async def test_empty_load_returns_default_shape(hass):
    store = BlocksStore(hass)
    data = await store.async_load()
    assert data == StoredData(blocks=[], pending_rediscovery=[])


async def test_save_then_load_roundtrip(hass):
    store = BlocksStore(hass)
    data = StoredData(
        blocks=[{"id": "b1", "device_id": "d1", "reason": "test"}],
        pending_rediscovery=[],
    )
    await store.async_save(data)

    fresh = BlocksStore(hass)
    reloaded = await fresh.async_load()
    assert reloaded["blocks"][0]["id"] == "b1"
    assert reloaded["blocks"][0]["reason"] == "test"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_store.py -v
```

Expected: FAIL (module does not exist).

- [ ] **Step 3: Implement `custom_components/update_blocklist/store.py`**

```python
"""Persistent storage for the block registry."""
from __future__ import annotations

import asyncio
from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


class StoredData(TypedDict):
    blocks: list[dict]
    pending_rediscovery: list[dict]


def _empty() -> StoredData:
    return {"blocks": [], "pending_rediscovery": []}


class BlocksStore:
    """Versioned JSON store with a write lock."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[StoredData] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._lock = asyncio.Lock()

    async def async_load(self) -> StoredData:
        data = await self._store.async_load()
        if data is None:
            return _empty()
        # Ensure both keys exist even if an older/partial file is encountered.
        return {
            "blocks": list(data.get("blocks", [])),
            "pending_rediscovery": list(data.get("pending_rediscovery", [])),
        }

    async def async_save(self, data: StoredData) -> None:
        async with self._lock:
            await self._store.async_save(data)

    async def async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict
    ) -> dict:
        """Schema migration entry point. Currently no migrations."""
        return old_data
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_store.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/store.py tests/test_store.py
git commit -m "Add BlocksStore wrapper with async load/save and write lock"
```

---

### Task 8: store.py — .backup rotation and corruption fallback

**Files:**
- Modify: `custom_components/update_blocklist/store.py`
- Modify: `tests/test_store.py`

- [ ] **Step 1: Add failing tests to `tests/test_store.py`**

Append:

```python
import json


async def test_save_writes_backup_of_previous_file(hass, hass_storage):
    store = BlocksStore(hass)
    await store.async_save({"blocks": [{"id": "v1"}], "pending_rediscovery": []})
    await store.async_save({"blocks": [{"id": "v2"}], "pending_rediscovery": []})

    # hass_storage is a dict mapping storage keys to in-memory contents.
    # Our implementation should keep a "<STORAGE_KEY>.backup" entry.
    from custom_components.update_blocklist.const import STORAGE_KEY
    assert f"{STORAGE_KEY}.backup" in hass_storage
    assert hass_storage[f"{STORAGE_KEY}.backup"]["data"]["blocks"][0]["id"] == "v1"


async def test_load_falls_back_to_backup_when_main_is_corrupt(hass, hass_storage):
    from custom_components.update_blocklist.const import STORAGE_KEY

    # Seed main as corrupt JSON by injecting invalid shape; backup with valid data.
    hass_storage[STORAGE_KEY] = {"version": 1, "key": STORAGE_KEY, "data": "NOT A DICT"}
    hass_storage[f"{STORAGE_KEY}.backup"] = {
        "version": 1,
        "key": f"{STORAGE_KEY}.backup",
        "data": {"blocks": [{"id": "from_backup"}], "pending_rediscovery": []},
    }

    store = BlocksStore(hass)
    data = await store.async_load()
    assert data["blocks"][0]["id"] == "from_backup"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_store.py -v
```

Expected: FAIL (backup logic does not exist).

- [ ] **Step 3: Update `custom_components/update_blocklist/store.py`**

Replace the whole file with:

```python
"""Persistent storage for the block registry with backup rotation."""
from __future__ import annotations

import asyncio
import logging
from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)
_BACKUP_KEY = f"{STORAGE_KEY}.backup"


class StoredData(TypedDict):
    blocks: list[dict]
    pending_rediscovery: list[dict]


def _empty() -> StoredData:
    return {"blocks": [], "pending_rediscovery": []}


def _is_valid_shape(data: object) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("blocks"), list)
        and isinstance(data.get("pending_rediscovery"), list)
    )


class BlocksStore:
    """Versioned JSON store with backup-on-write and corruption fallback."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[StoredData] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._backup: Store[StoredData] = Store(hass, STORAGE_VERSION, _BACKUP_KEY)
        self._lock = asyncio.Lock()

    async def async_load(self) -> StoredData:
        raw = await self._store.async_load()
        if _is_valid_shape(raw):
            assert raw is not None
            return {
                "blocks": list(raw.get("blocks", [])),
                "pending_rediscovery": list(raw.get("pending_rediscovery", [])),
            }

        if raw is not None:
            _LOGGER.warning(
                "Main storage shape invalid (%r); attempting backup.", type(raw).__name__
            )

        backup = await self._backup.async_load()
        if _is_valid_shape(backup):
            assert backup is not None
            _LOGGER.warning("Loaded from .backup after corruption of main file.")
            return {
                "blocks": list(backup.get("blocks", [])),
                "pending_rediscovery": list(backup.get("pending_rediscovery", [])),
            }

        return _empty()

    async def async_save(self, data: StoredData) -> None:
        async with self._lock:
            # Roll previous main into backup before overwriting.
            previous = await self._store.async_load()
            if _is_valid_shape(previous):
                await self._backup.async_save(previous)
            await self._store.async_save(data)

    async def async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict
    ) -> dict:
        """Schema migration entry point. Currently no migrations."""
        return old_data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_store.py -v
```

Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/store.py tests/test_store.py
git commit -m "Add backup rotation and corruption fallback to BlocksStore"
```

---

### Task 9: registry.py — Block dataclass and CRUD

**Files:**
- Create: `custom_components/update_blocklist/registry.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write failing test `tests/test_registry.py`**

```python
"""Tests for the block registry."""
from __future__ import annotations

import pytest

from custom_components.update_blocklist.registry import Block, BlockRegistry


def _make_registry(hass):
    return BlockRegistry(hass)


async def test_add_block_returns_block_with_generated_id(hass):
    reg = _make_registry(hass)
    await reg.async_load()

    block = await reg.async_add_block(
        device_id="dev1",
        update_entity_ids=["update.wled"],
        unique_ids=["aa:bb"],
        fingerprint={"manufacturer": "e", "model": "m", "name": "n"},
        reason="custom firmware",
        last_known_version="1.0.0",
    )
    assert isinstance(block, Block)
    assert block.id
    assert block.device_id == "dev1"
    assert block.reason == "custom firmware"
    assert block.status == "active"


async def test_add_block_persists_across_instances(hass):
    reg = _make_registry(hass)
    await reg.async_load()
    added = await reg.async_add_block(
        device_id="dev1",
        update_entity_ids=["update.wled"],
        unique_ids=["aa:bb"],
        fingerprint={"manufacturer": "e", "model": "m", "name": "n"},
        reason="x",
        last_known_version=None,
    )

    reg2 = _make_registry(hass)
    await reg2.async_load()
    assert reg2.get_block(added.id) is not None


async def test_remove_block(hass):
    reg = _make_registry(hass)
    await reg.async_load()
    block = await reg.async_add_block(
        device_id="d", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await reg.async_remove_block(block.id)
    assert reg.get_block(block.id) is None


async def test_all_blocks_returns_list(hass):
    reg = _make_registry(hass)
    await reg.async_load()
    for i in range(3):
        await reg.async_add_block(
            device_id=f"d{i}", update_entity_ids=[f"update.a{i}"], unique_ids=[],
            fingerprint={"manufacturer": "", "model": "", "name": ""},
            reason="", last_known_version=None,
        )
    assert len(reg.all_blocks()) == 3


async def test_find_block_for_device(hass):
    reg = _make_registry(hass)
    await reg.async_load()
    added = await reg.async_add_block(
        device_id="dev-xyz", update_entity_ids=["update.a"], unique_ids=["u1"],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    assert reg.find_block_for_device("dev-xyz") is added
    assert reg.find_block_for_device("other") is None


async def test_add_block_rejects_duplicate_device_id(hass):
    reg = _make_registry(hass)
    await reg.async_load()
    await reg.async_add_block(
        device_id="dev1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    with pytest.raises(ValueError, match="already blocked"):
        await reg.async_add_block(
            device_id="dev1", update_entity_ids=["update.a"], unique_ids=[],
            fingerprint={"manufacturer": "", "model": "", "name": ""},
            reason="", last_known_version=None,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_registry.py -v
```

Expected: FAIL (module does not exist).

- [ ] **Step 3: Implement `custom_components/update_blocklist/registry.py`**

```python
"""Block registry — in-memory view backed by BlocksStore."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    BLOCK_STATUS_ACTIVE,
    SCAN_STATUS_NEVER_SCANNED,
)
from .identity import Fingerprint
from .store import BlocksStore, StoredData


@dataclass
class Block:
    id: str
    device_id: str
    update_entity_ids: list[str]
    unique_ids: list[str]
    fingerprint: Fingerprint
    reason: str
    created_at: str
    last_known_version: str | None
    last_scan_at: str | None
    last_scan_status: str
    status: str = BLOCK_STATUS_ACTIVE

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        return cls(
            id=data["id"],
            device_id=data["device_id"],
            update_entity_ids=list(data.get("update_entity_ids", [])),
            unique_ids=list(data.get("unique_ids", [])),
            fingerprint=data.get("fingerprint", {"manufacturer": "", "model": "", "name": ""}),
            reason=data.get("reason", ""),
            created_at=data["created_at"],
            last_known_version=data.get("last_known_version"),
            last_scan_at=data.get("last_scan_at"),
            last_scan_status=data.get("last_scan_status", SCAN_STATUS_NEVER_SCANNED),
            status=data.get("status", BLOCK_STATUS_ACTIVE),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BlockRegistry:
    """In-memory registry of blocks with persistence to BlocksStore."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store = BlocksStore(hass)
        self._blocks: dict[str, Block] = {}
        self._pending_rediscovery: list[dict[str, Any]] = []
        self._loaded = False

    async def async_load(self) -> None:
        data = await self._store.async_load()
        self._blocks = {b["id"]: Block.from_dict(b) for b in data["blocks"]}
        self._pending_rediscovery = list(data["pending_rediscovery"])
        self._loaded = True

    async def _persist(self) -> None:
        data: StoredData = {
            "blocks": [b.to_dict() for b in self._blocks.values()],
            "pending_rediscovery": list(self._pending_rediscovery),
        }
        await self._store.async_save(data)

    async def async_add_block(
        self,
        *,
        device_id: str,
        update_entity_ids: list[str],
        unique_ids: list[str],
        fingerprint: Fingerprint,
        reason: str,
        last_known_version: str | None,
    ) -> Block:
        if any(b.device_id == device_id for b in self._blocks.values()):
            raise ValueError(f"Device {device_id!r} is already blocked")

        block = Block(
            id=uuid.uuid4().hex,
            device_id=device_id,
            update_entity_ids=list(update_entity_ids),
            unique_ids=list(unique_ids),
            fingerprint=fingerprint,
            reason=reason,
            created_at=datetime.now(UTC).isoformat(),
            last_known_version=last_known_version,
            last_scan_at=None,
            last_scan_status=SCAN_STATUS_NEVER_SCANNED,
            status=BLOCK_STATUS_ACTIVE,
        )
        self._blocks[block.id] = block
        await self._persist()
        return block

    async def async_remove_block(self, block_id: str) -> Block | None:
        block = self._blocks.pop(block_id, None)
        if block is not None:
            await self._persist()
        return block

    async def async_update_block(self, block: Block) -> None:
        self._blocks[block.id] = block
        await self._persist()

    def get_block(self, block_id: str) -> Block | None:
        return self._blocks.get(block_id)

    def find_block_for_device(self, device_id: str) -> Block | None:
        return next(
            (b for b in self._blocks.values() if b.device_id == device_id), None
        )

    def find_block_for_entity(self, entity_id: str) -> Block | None:
        return next(
            (b for b in self._blocks.values() if entity_id in b.update_entity_ids),
            None,
        )

    def all_blocks(self) -> list[Block]:
        return list(self._blocks.values())

    @property
    def pending_rediscovery(self) -> list[dict[str, Any]]:
        return list(self._pending_rediscovery)

    async def async_set_pending_rediscovery(self, items: list[dict[str, Any]]) -> None:
        self._pending_rediscovery = list(items)
        await self._persist()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_registry.py -v
```

Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/registry.py tests/test_registry.py
git commit -m "Add BlockRegistry with add/remove/get/list/persist"
```

---

### Task 10: registry.py — orphan detection

**Files:**
- Modify: `custom_components/update_blocklist/registry.py`
- Modify: `tests/test_registry.py`

- [ ] **Step 1: Append failing test to `tests/test_registry.py`**

```python
async def test_find_orphans_returns_blocks_whose_device_is_missing(hass):
    from homeassistant.helpers import device_registry as dr

    reg = _make_registry(hass)
    await reg.async_load()

    dev_reg = dr.async_get(hass)
    # Create one real device.
    real = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "real")}
    )
    await reg.async_add_block(
        device_id=real.id, update_entity_ids=["update.real"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    # Create a block for a device_id that doesn't exist.
    await reg.async_add_block(
        device_id="nonexistent", update_entity_ids=["update.gone"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )

    orphans = reg.find_orphans(dev_reg)
    assert len(orphans) == 1
    assert orphans[0].device_id == "nonexistent"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_registry.py::test_find_orphans_returns_blocks_whose_device_is_missing -v
```

Expected: FAIL (method does not exist).

- [ ] **Step 3: Add `find_orphans` to `registry.py`**

Insert this method in the `BlockRegistry` class after `all_blocks`:

```python
    def find_orphans(self, device_registry) -> list[Block]:
        """Return blocks whose device_id no longer resolves to a real device."""
        orphans: list[Block] = []
        for block in self._blocks.values():
            if device_registry.async_get(block.device_id) is None:
                orphans.append(block)
        return orphans
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_registry.py -v
```

Expected: PASS (all 7 tests).

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/registry.py tests/test_registry.py
git commit -m "Add orphan detection to BlockRegistry"
```

---

### Task 11: registry.py — rediscovery candidate matching

**Files:**
- Modify: `custom_components/update_blocklist/registry.py`
- Modify: `tests/test_registry.py`

- [ ] **Step 1: Append failing tests to `tests/test_registry.py`**

```python
async def test_match_rediscovery_by_unique_id(hass):
    from homeassistant.helpers import device_registry as dr

    reg = _make_registry(hass)
    await reg.async_load()
    dev_reg = dr.async_get(hass)

    # Orphan block references "gone" device_id but captured unique_id "MAC1".
    block = await reg.async_add_block(
        device_id="gone", update_entity_ids=["update.x"], unique_ids=["MAC1"],
        fingerprint={"manufacturer": "e", "model": "m", "name": "n"},
        reason="", last_known_version=None,
    )

    # A new device has an entity with unique_id "MAC1".
    new_dev = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "new")}
    )
    from homeassistant.helpers import entity_registry as er
    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="MAC1",
        device_id=new_dev.id,
    )

    candidates = reg.match_rediscovery_candidates(block, dev_reg, ent_reg)
    assert candidates == [{"device_id": new_dev.id, "match_type": "unique_id"}]


async def test_match_rediscovery_by_fingerprint(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    reg = _make_registry(hass)
    await reg.async_load()
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    # Orphan block with a specific fingerprint but no matching unique_id in the new world.
    block = await reg.async_add_block(
        device_id="gone", update_entity_ids=["update.x"], unique_ids=["OLD_MAC"],
        fingerprint={"manufacturer": "espressif", "model": "esp8266", "name": "wled strip"},
        reason="", last_known_version=None,
    )

    new_dev = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "new")},
        manufacturer="Espressif", model="ESP8266", name="WLED Strip 2",
    )

    candidates = reg.match_rediscovery_candidates(block, dev_reg, ent_reg)
    assert {"device_id": new_dev.id, "match_type": "fingerprint"} in candidates
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_registry.py -v
```

Expected: FAIL (method does not exist).

- [ ] **Step 3: Add `match_rediscovery_candidates` to `registry.py`**

Add at the top of the module imports:

```python
from .identity import fingerprint_matches, generate_fingerprint
from .const import MATCH_UNIQUE_ID, MATCH_FINGERPRINT
```

Insert after `find_orphans` in `BlockRegistry`:

```python
    def match_rediscovery_candidates(
        self, block: Block, device_registry, entity_registry
    ) -> list[dict[str, str]]:
        """Find devices that plausibly represent a re-paired version of `block`.

        Returns a list of {"device_id": ..., "match_type": "unique_id"|"fingerprint"}.
        """
        results: list[dict[str, str]] = []
        seen: set[str] = set()

        # Match by unique_id on update entities.
        if block.unique_ids:
            for entry in entity_registry.entities.values():
                if entry.domain != "update":
                    continue
                if entry.unique_id in block.unique_ids and entry.device_id:
                    if entry.device_id not in seen:
                        results.append(
                            {"device_id": entry.device_id, "match_type": MATCH_UNIQUE_ID}
                        )
                        seen.add(entry.device_id)

        # Match by fingerprint on device registry.
        for dev in device_registry.devices.values():
            if dev.id in seen:
                continue
            fp = generate_fingerprint(
                manufacturer=dev.manufacturer,
                model=dev.model,
                name=dev.name or dev.name_by_user,
            )
            if fingerprint_matches(block.fingerprint, fp):
                results.append({"device_id": dev.id, "match_type": MATCH_FINGERPRINT})
                seen.add(dev.id)

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_registry.py -v
```

Expected: PASS (all 9 tests).

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/registry.py tests/test_registry.py
git commit -m "Add rediscovery candidate matching to BlockRegistry"
```

---

### Task 12: Wire BlockRegistry into integration setup

**Files:**
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Append failing test to `tests/test_init.py`**

```python
async def test_setup_creates_registry_in_hass_data(hass):
    from custom_components.update_blocklist.registry import BlockRegistry

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    assert isinstance(runtime["registry"], BlockRegistry)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_init.py -v
```

Expected: FAIL (no "registry" key).

- [ ] **Step 3: Update `__init__.py`**

Replace with:

```python
"""Update Blocklist integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .registry import BlockRegistry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up update_blocklist from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    registry = BlockRegistry(hass)
    await registry.async_load()

    hass.data[DOMAIN][entry.entry_id] = {"registry": registry}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/__init__.py tests/test_init.py
git commit -m "Wire BlockRegistry into integration setup"
```

---

## Phase 3: Config Flow + Options Flow

### Task 13: Config flow — single-step setup

**Files:**
- Create: `custom_components/update_blocklist/config_flow.py`
- Create: `tests/test_config_flow.py`

- [ ] **Step 1: Write failing test `tests/test_config_flow.py`**

```python
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
    """Attempting to add a second entry is aborted as single_instance_allowed."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    MockConfigEntry(domain=DOMAIN, data={}, options={}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config_flow.py -v
```

Expected: FAIL (config_flow module does not exist).

- [ ] **Step 3: Implement `custom_components/update_blocklist/config_flow.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config_flow.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/config_flow.py tests/test_config_flow.py
git commit -m "Add config flow with single-step setup and single-instance guard"
```

---

### Task 14: Options flow validation tests

**Files:**
- Modify: `tests/test_config_flow.py`

- [ ] **Step 1: Append tests for options flow**

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
pytest tests/test_config_flow.py -v
```

Expected: PASS (config_flow.py already implements validation from Task 13).

- [ ] **Step 3: Commit**

```bash
git add tests/test_config_flow.py
git commit -m "Add options flow validation tests"
```

---

### Task 15: Expose options values to setup

**Files:**
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Append failing test to `tests/test_init.py`**

```python
async def test_setup_stores_effective_options(hass):
    from custom_components.update_blocklist.const import (
        CONF_SCAN_START_TIME,
        CONF_SCAN_MAX_DURATION_MINUTES,
        CONF_PER_DEVICE_TIMEOUT_SECONDS,
    )

    entry = MockConfigEntry(
        domain=DOMAIN, data={},
        options={
            CONF_SCAN_START_TIME: "03:15",
            CONF_SCAN_MAX_DURATION_MINUTES: 20,
            CONF_PER_DEVICE_TIMEOUT_SECONDS: 120,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    opts = runtime["options"]
    assert opts[CONF_SCAN_START_TIME] == "03:15"
    assert opts[CONF_SCAN_MAX_DURATION_MINUTES] == 20
    assert opts[CONF_PER_DEVICE_TIMEOUT_SECONDS] == 120
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_init.py::test_setup_stores_effective_options -v
```

Expected: FAIL.

- [ ] **Step 3: Update `__init__.py` to compute and store effective options**

Replace `async_setup_entry` with:

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up update_blocklist from a config entry."""
    from .const import (
        CONF_PER_DEVICE_TIMEOUT_SECONDS,
        CONF_SCAN_MAX_DURATION_MINUTES,
        CONF_SCAN_START_TIME,
        DEFAULT_PER_DEVICE_TIMEOUT_SECONDS,
        DEFAULT_SCAN_MAX_DURATION_MINUTES,
        DEFAULT_SCAN_START_TIME,
    )

    hass.data.setdefault(DOMAIN, {})

    registry = BlockRegistry(hass)
    await registry.async_load()

    options = {
        CONF_SCAN_START_TIME: entry.options.get(
            CONF_SCAN_START_TIME, DEFAULT_SCAN_START_TIME
        ),
        CONF_SCAN_MAX_DURATION_MINUTES: entry.options.get(
            CONF_SCAN_MAX_DURATION_MINUTES, DEFAULT_SCAN_MAX_DURATION_MINUTES
        ),
        CONF_PER_DEVICE_TIMEOUT_SECONDS: entry.options.get(
            CONF_PER_DEVICE_TIMEOUT_SECONDS, DEFAULT_PER_DEVICE_TIMEOUT_SECONDS
        ),
    }

    hass.data[DOMAIN][entry.entry_id] = {
        "registry": registry,
        "options": options,
    }

    entry.async_on_unload(entry.add_update_listener(_async_options_reload))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/__init__.py tests/test_init.py
git commit -m "Apply options with defaults at setup; reload on options change"
```

---

## Phase 4: Coordinator and Entity Platforms

### Task 16: DataUpdateCoordinator

**Files:**
- Create: `custom_components/update_blocklist/coordinator.py`
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write failing test `tests/test_coordinator.py`**

```python
"""Tests for the UpdateBlocklistCoordinator."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def test_coordinator_exposes_registry_snapshot(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    coord = runtime["coordinator"]
    snap = coord.data
    assert isinstance(snap, dict)
    assert snap["blocks"] == []
    assert snap["pending_rediscovery"] == []


async def test_coordinator_refreshes_when_registry_changes(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    reg = runtime["registry"]
    coord = runtime["coordinator"]

    await reg.async_add_block(
        device_id="d1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await coord.async_request_refresh()
    await hass.async_block_till_done()

    assert len(coord.data["blocks"]) == 1
    assert coord.data["blocks"][0]["device_id"] == "d1"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_coordinator.py -v
```

Expected: FAIL (no coordinator).

- [ ] **Step 3: Implement `custom_components/update_blocklist/coordinator.py`**

```python
"""Coordinator — exposes registry snapshots to entities and the panel."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .registry import BlockRegistry

_LOGGER = logging.getLogger(__name__)


class UpdateBlocklistCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Publishes the current registry snapshot to entities and the panel."""

    def __init__(self, hass: HomeAssistant, registry: BlockRegistry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=None
        )
        self._registry = registry

    async def _async_update_data(self) -> dict[str, Any]:
        return {
            "blocks": [b.to_dict() for b in self._registry.all_blocks()],
            "pending_rediscovery": list(self._registry.pending_rediscovery),
        }
```

- [ ] **Step 4: Wire coordinator into setup — update `__init__.py`**

Replace the setup body (inside `async_setup_entry`, after building `options`) so it becomes:

```python
    coordinator = UpdateBlocklistCoordinator(hass, registry)
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "registry": registry,
        "coordinator": coordinator,
        "options": options,
    }
```

And add the import at top of `__init__.py`:

```python
from .coordinator import UpdateBlocklistCoordinator
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_coordinator.py tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/coordinator.py custom_components/update_blocklist/__init__.py tests/test_coordinator.py
git commit -m "Add UpdateBlocklistCoordinator and wire into setup"
```

---

### Task 17: Integration-level sensors

**Files:**
- Create: `custom_components/update_blocklist/sensor.py`
- Create: `tests/test_sensor.py`

- [ ] **Step 1: Write failing test `tests/test_sensor.py`**

```python
"""Tests for integration-level sensors."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def test_blocked_count_sensor_reports_zero_initially(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.update_blocklist_blocked_count")
    assert state is not None
    assert state.state == "0"


async def test_blocked_count_sensor_updates_when_block_added(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="d1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.update_blocklist_blocked_count")
    assert state.state == "1"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sensor.py -v
```

Expected: FAIL (no sensor platform).

- [ ] **Step 3: Implement `custom_components/update_blocklist/sensor.py`**

```python
"""Integration-level sensor platform."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
        # Populated by the scanner in Phase 5. Until then, None.
        return self.coordinator.data.get("next_scan_at")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sensor.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/sensor.py tests/test_sensor.py
git commit -m "Add integration-level sensors (blocked count, last scan, next scan)"
```

---

### Task 18: Per-block shadow sensor and diagnostic binary_sensor

**Files:**
- Modify: `custom_components/update_blocklist/sensor.py`
- Create: `custom_components/update_blocklist/binary_sensor.py`
- Create: `tests/test_per_block_entities.py`

- [ ] **Step 1: Write failing test `tests/test_per_block_entities.py`**

```python
"""Tests for per-block shadow sensor and diagnostic binary_sensor."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def test_adding_block_creates_shadow_sensor_and_binary_sensor(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="dev_wled_1",
        update_entity_ids=["update.wled_custom"],
        unique_ids=["AA:BB"],
        fingerprint={"manufacturer": "espressif", "model": "esp8266", "name": "wled custom"},
        reason="custom",
        last_known_version="0.14.2",
    )
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()

    # The shadow sensor is named using the block's device_id slug.
    state = hass.states.get("sensor.update_blocklist_dev_wled_1_blocked_update_status")
    assert state is not None
    assert state.state == "0.14.2"
    assert state.attributes["reason"] == "custom"

    binary = hass.states.get(
        "binary_sensor.update_blocklist_dev_wled_1_update_blocked"
    )
    assert binary is not None
    assert binary.state == "on"


async def test_removing_block_removes_entities(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    block = await runtime["registry"].async_add_block(
        device_id="dev_wled_2", update_entity_ids=["update.wled_2"],
        unique_ids=[], fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()

    await runtime["registry"].async_remove_block(block.id)
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.update_blocklist_dev_wled_2_blocked_update_status") is None
    assert hass.states.get("binary_sensor.update_blocklist_dev_wled_2_update_blocked") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_per_block_entities.py -v
```

Expected: FAIL.

- [ ] **Step 3: Update `sensor.py` to add per-block shadow sensors dynamically**

Append to `sensor.py` (and extend `async_setup_entry` to wire dynamic adds):

```python
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import SIGNAL_BLOCKS_UPDATED


class BlockShadowSensor(_IntegrationSensor):
    """Per-block shadow sensor — last known latest_version for the blocked device."""

    _attr_icon = "mdi:update"

    def __init__(self, coordinator, entry_id: str, block_id: str):
        super().__init__(coordinator, entry_id)
        self._block_id = block_id
        self._attr_unique_id = f"{entry_id}_{block_id}_blocked_update_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}:{block_id}")},
            via_device=(DOMAIN, entry_id),
            name=f"Blocked device {self._block()['device_id']}"
            if self._block()
            else None,
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
```

Modify `async_setup_entry` in `sensor.py` to also register shadow sensors dynamically. Replace the function with:

```python
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
        # Removed blocks: the entities become unavailable; HA cleans the unique_id
        # up from the registry on uninstall. We do not force-remove here — leaving
        # the entity rehydrates cleanly if the block is re-added in the same session.
        known_ids.intersection_update(current_ids | new_ids)

    _sync_shadow_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_shadow_entities))
```

Also add `from homeassistant.core import callback` to the imports at the top if not already present.

- [ ] **Step 4: Create `binary_sensor.py`**

```python
"""Per-block diagnostic binary_sensor indicating active block status."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BLOCK_STATUS_ACTIVE, DOMAIN
from .coordinator import UpdateBlocklistCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: UpdateBlocklistCoordinator = runtime["coordinator"]

    known_ids: set[str] = set()

    @callback
    def _sync() -> None:
        current_ids = {b["id"] for b in coordinator.data.get("blocks", [])}
        new_ids = current_ids - known_ids
        if new_ids:
            async_add_entities(
                [BlockedBinarySensor(coordinator, entry.entry_id, bid) for bid in new_ids]
            )
            known_ids.update(new_ids)

    _sync()
    entry.async_on_unload(coordinator.async_add_listener(_sync))


class BlockedBinarySensor(
    CoordinatorEntity[UpdateBlocklistCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True
    _attr_icon = "mdi:lock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id: str, block_id: str):
        super().__init__(coordinator)
        self._block_id = block_id
        self._attr_unique_id = f"{entry_id}_{block_id}_update_blocked"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}:{block_id}")},
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
        return "Update blocked"

    @property
    def is_on(self) -> bool:
        b = self._block()
        return bool(b) and b.get("status") == BLOCK_STATUS_ACTIVE
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_per_block_entities.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/sensor.py custom_components/update_blocklist/binary_sensor.py tests/test_per_block_entities.py
git commit -m "Add per-block shadow sensors and diagnostic binary sensors"
```

---

### Task 19: Per-block and integration-level buttons

**Files:**
- Create: `custom_components/update_blocklist/button.py`
- Modify: `tests/test_per_block_entities.py`

- [ ] **Step 1: Append failing test to `tests/test_per_block_entities.py`**

```python
async def test_scan_all_button_exists(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("button.update_blocklist_scan_all")
    assert state is not None


async def test_per_block_scan_now_button_appears_for_block(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="dev_btn_1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await runtime["coordinator"].async_request_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("button.update_blocklist_dev_btn_1_scan_now")
    assert state is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_per_block_entities.py -v
```

Expected: FAIL (no button platform).

- [ ] **Step 3: Implement `button.py`**

```python
"""Button platform — scan-all and per-block scan-now."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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

    async_add_entities([ScanAllButton(coordinator, entry.entry_id)])

    known_ids: set[str] = set()

    @callback
    def _sync() -> None:
        current_ids = {b["id"] for b in coordinator.data.get("blocks", [])}
        new_ids = current_ids - known_ids
        if new_ids:
            async_add_entities(
                [ScanNowButton(coordinator, entry.entry_id, bid) for bid in new_ids]
            )
            known_ids.update(new_ids)

    _sync()
    entry.async_on_unload(coordinator.async_add_listener(_sync))


def _integration_device(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Update Blocklist",
        manufacturer="update_blocklist",
        entry_type="service",
    )


class ScanAllButton(CoordinatorEntity[UpdateBlocklistCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:magnify-scan"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_scan_all"
        self._attr_device_info = _integration_device(entry_id)

    @property
    def name(self) -> str:
        return "Scan all"

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN, "scan_all", {}, blocking=True
        )


class ScanNowButton(CoordinatorEntity[UpdateBlocklistCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:magnify-scan"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id: str, block_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._block_id = block_id
        self._attr_unique_id = f"{entry_id}_{block_id}_scan_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}:{block_id}")}
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
        return "Scan now"

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN, "scan_now", {"block_id": self._block_id}, blocking=True
        )
```

*Note:* The `scan_all` and `scan_now` services are registered in Task 25. Before then the button presses will no-op with a warning — tests only check that the entities exist.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_per_block_entities.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/button.py tests/test_per_block_entities.py
git commit -m "Add scan-all and per-block scan-now buttons"
```

---

## Phase 5: Scanner

### Task 20: Scanner — `block_device` operation (disable entity, snapshot version)

**Files:**
- Create: `custom_components/update_blocklist/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write failing test `tests/test_scanner.py`**

```python
"""Tests for the scanner."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup_integration(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_block_device_disables_update_entity(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "wled")},
        manufacturer="Espressif", model="ESP8266", name="WLED Custom",
    )
    update_entity = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="AA:BB",
        device_id=device.id,
    )

    await scanner.async_block_device(device_id=device.id, reason="custom")
    await hass.async_block_till_done()

    updated = ent_reg.async_get(update_entity.entity_id)
    assert updated.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_block_device_raises_if_no_update_entity(hass):
    import pytest
    from homeassistant.helpers import device_registry as dr

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "no_update")}
    )

    with pytest.raises(ValueError, match="no update entity"):
        await scanner.async_block_device(device_id=device.id, reason="x")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scanner.py -v
```

Expected: FAIL (no scanner).

- [ ] **Step 3: Implement `custom_components/update_blocklist/scanner.py`**

```python
"""Scanner — block/unblock operations and periodic scan cycle."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

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
```

- [ ] **Step 4: Wire scanner into setup — update `__init__.py`**

In `async_setup_entry`, after the coordinator is built, add:

```python
    from .scanner import Scanner
    scanner = Scanner(hass, registry, coordinator, options)
    hass.data[DOMAIN][entry.entry_id]["scanner"] = scanner
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/scanner.py custom_components/update_blocklist/__init__.py tests/test_scanner.py
git commit -m "Add Scanner.async_block_device with entity disable choreography"
```

---

### Task 21: Scanner — `unblock` operation (re-enable entity, remove block)

**Files:**
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `tests/test_scanner.py`

- [ ] **Step 1: Append failing test**

```python
async def test_unblock_reenables_update_entity_and_removes_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "w2")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u1", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    await scanner.async_unblock(block_id=block.id)
    await hass.async_block_till_done()

    assert registry.get_block(block.id) is None
    assert ent_reg.async_get(update.entity_id).disabled_by is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py::test_unblock_reenables_update_entity_and_removes_block -v
```

Expected: FAIL.

- [ ] **Step 3: Add `async_unblock` to `scanner.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/scanner.py tests/test_scanner.py
git commit -m "Add Scanner.async_unblock with entity re-enable"
```

---

### Task 22: Scanner — single-device scan cycle

**Files:**
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `tests/test_scanner.py`

- [ ] **Step 1: Append failing tests**

```python
async def test_scan_block_captures_latest_version(hass):
    """A scan cycle re-enables, waits for latest_version, captures it, re-disables."""
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "scan1")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    # Simulate integration populating latest_version shortly after re-enable.
    async def _populate():
        # Wait for the scanner to re-enable the entity, then set state.
        for _ in range(50):
            if ent_reg.async_get(update.entity_id).disabled_by is None:
                hass.states.async_set(
                    update.entity_id, "on",
                    {"installed_version": "1.0.0", "latest_version": "1.2.3"},
                )
                return
            await asyncio.sleep(0.01)

    import asyncio as _a
    task = _a.create_task(_populate())
    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=5)
    await task

    updated = registry.get_block(block.id)
    assert updated.last_known_version == "1.2.3"
    assert updated.last_scan_status == "ok"
    assert ent_reg.async_get(update.entity_id).disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_scan_block_timeout_records_timeout_status(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "scan2")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u2", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=1)

    updated = registry.get_block(block.id)
    assert updated.last_scan_status == "timeout"


async def test_scan_block_entity_gone(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "scan3")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u3", device_id=device.id
    )

    block = await scanner.async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    # Remove entity before scan.
    ent_reg.async_remove(update.entity_id)

    await scanner.async_scan_block(block_id=block.id, per_device_timeout_seconds=1)

    updated = registry.get_block(block.id)
    assert updated.last_scan_status == "entity_gone"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scanner.py -v
```

Expected: FAIL.

- [ ] **Step 3: Add `async_scan_block` to `scanner.py`**

Add imports at top:

```python
from datetime import UTC, datetime
from homeassistant.core import Event, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    SCAN_STATUS_ENTITY_GONE,
    SCAN_STATUS_OK,
    SCAN_STATUS_TIMEOUT,
)
```

Add method:

```python
    async def async_scan_block(
        self, *, block_id: str, per_device_timeout_seconds: int
    ) -> None:
        """Re-enable entity → skip known latest → wait for fresh latest_version → re-disable."""
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
        except asyncio.TimeoutError:
            return None
        finally:
            remove()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/scanner.py tests/test_scanner.py
git commit -m "Add per-block scan cycle (re-enable, capture, re-disable)"
```

---

### Task 23: Scanner — scan-all and window-bounded cycle

**Files:**
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `tests/test_scanner.py`

- [ ] **Step 1: Append failing test**

```python
async def test_scan_all_visits_blocks_in_oldest_first_order(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er
    from datetime import UTC, datetime, timedelta

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]
    registry = runtime["registry"]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    created_blocks = []
    for i in range(3):
        d = dev_reg.async_get_or_create(
            config_entry_id="fake", identifiers={("demo", f"scanall{i}")}
        )
        ent_reg.async_get_or_create(
            domain="update", platform="demo", unique_id=f"u{i}", device_id=d.id
        )
        b = await scanner.async_block_device(device_id=d.id, reason="")
        # Assign last_scan_at manually so order is deterministic.
        b.last_scan_at = (datetime.now(UTC) - timedelta(days=3 - i)).isoformat()
        await registry.async_update_block(b)
        created_blocks.append(b)

    visited: list[str] = []

    async def fake_scan_block(*, block_id: str, per_device_timeout_seconds: int) -> None:
        visited.append(block_id)
        b = registry.get_block(block_id)
        b.last_scan_at = datetime.now(UTC).isoformat()
        b.last_scan_status = "ok"
        await registry.async_update_block(b)

    scanner.async_scan_block = fake_scan_block  # type: ignore[method-assign]

    await scanner.async_scan_all(
        max_duration_seconds=60, per_device_timeout_seconds=5
    )

    # Oldest-first → the block with last_scan_at three days ago first.
    assert visited[0] == created_blocks[0].id
    assert visited[-1] == created_blocks[-1].id
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py::test_scan_all_visits_blocks_in_oldest_first_order -v
```

Expected: FAIL (`async_scan_all` does not exist).

- [ ] **Step 3: Add `async_scan_all` to `scanner.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/scanner.py tests/test_scanner.py
git commit -m "Add scan-all with oldest-first ordering and duration cap"
```

---

### Task 24: Scanner — nightly schedule trigger

**Files:**
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_scanner.py`

- [ ] **Step 1: Append failing test**

```python
async def test_nightly_schedule_triggers_scan_at_configured_time(hass, freezer):
    from datetime import datetime, timedelta

    entry = await _setup_integration(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    scanner = runtime["scanner"]

    calls: list[str] = []
    async def fake_scan_all(*, max_duration_seconds, per_device_timeout_seconds):
        calls.append("scan_all")

    scanner.async_scan_all = fake_scan_all  # type: ignore[method-assign]

    # freezer available via pytest-homeassistant-custom-component fixtures.
    freezer.move_to(datetime(2026, 4, 16, 0, 59, 0))
    # Start schedule: default 01:00.
    remove = scanner.start_schedule()
    try:
        freezer.move_to(datetime(2026, 4, 16, 1, 0, 0))
        async_fire_time_changed = __import__(
            "pytest_homeassistant_custom_component.common",
            fromlist=["async_fire_time_changed"],
        ).async_fire_time_changed
        async_fire_time_changed(hass, datetime(2026, 4, 16, 1, 0, 0))
        await hass.async_block_till_done()

        assert calls == ["scan_all"]
    finally:
        remove()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py::test_nightly_schedule_triggers_scan_at_configured_time -v
```

Expected: FAIL.

- [ ] **Step 3: Add `start_schedule` to `scanner.py`**

Add import:

```python
from homeassistant.helpers.event import async_track_time_change
```

Add method:

```python
    def start_schedule(self):
        """Install the nightly scan trigger at options[CONF_SCAN_START_TIME].

        Returns a callable that removes the listener.
        """
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
```

- [ ] **Step 4: Wire schedule start into `__init__.py`**

After `scanner` is created in `async_setup_entry`:

```python
    remove_schedule = scanner.start_schedule()
    entry.async_on_unload(remove_schedule)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/scanner.py custom_components/update_blocklist/__init__.py tests/test_scanner.py
git commit -m "Add nightly scan schedule hook"
```

---

## Phase 6: Services

### Task 25: Services — block, unblock, scan_now, scan_all

**Files:**
- Create: `custom_components/update_blocklist/services.py`
- Create: `custom_components/update_blocklist/services.yaml`
- Modify: `custom_components/update_blocklist/__init__.py`
- Create: `tests/test_services.py`

- [ ] **Step 1: Write failing test `tests/test_services.py`**

```python
"""Tests for services."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_block_service_adds_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "svc1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    await hass.services.async_call(
        DOMAIN, "block",
        {"device_id": device.id, "reason": "via service"},
        blocking=True,
    )
    await hass.async_block_till_done()

    blocks = runtime["registry"].all_blocks()
    assert len(blocks) == 1
    assert blocks[0].reason == "via service"


async def test_unblock_service_removes_block(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "svc2")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u2", device_id=device.id
    )

    block = await runtime["scanner"].async_block_device(
        device_id=device.id, reason=""
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "unblock", {"block_id": block.id}, blocking=True
    )
    await hass.async_block_till_done()

    assert runtime["registry"].get_block(block.id) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_services.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `services.py`**

```python
"""Service registration for update_blocklist."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_PER_DEVICE_TIMEOUT_SECONDS,
    CONF_SCAN_MAX_DURATION_MINUTES,
    DOMAIN,
)

SERVICE_BLOCK = "block"
SERVICE_UNBLOCK = "unblock"
SERVICE_SCAN_NOW = "scan_now"
SERVICE_SCAN_ALL = "scan_all"


BLOCK_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Optional("reason", default=""): cv.string,
    }
)

UNBLOCK_SCHEMA = vol.Schema({vol.Required("block_id"): cv.string})
SCAN_NOW_SCHEMA = vol.Schema({vol.Required("block_id"): cv.string})
SCAN_ALL_SCHEMA = vol.Schema({})


def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services. Looks up scanner/registry from hass.data."""

    def _any_runtime() -> dict | None:
        data = hass.data.get(DOMAIN, {})
        return next(iter(data.values()), None) if data else None

    async def _block(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_block_device(
            device_id=call.data["device_id"], reason=call.data["reason"]
        )

    async def _unblock(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_unblock(block_id=call.data["block_id"])

    async def _scan_now(call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_scan_block(
            block_id=call.data["block_id"],
            per_device_timeout_seconds=runtime["options"][CONF_PER_DEVICE_TIMEOUT_SECONDS],
        )

    async def _scan_all(_call: ServiceCall) -> None:
        runtime = _any_runtime()
        if runtime is None:
            return
        await runtime["scanner"].async_scan_all(
            max_duration_seconds=runtime["options"][CONF_SCAN_MAX_DURATION_MINUTES] * 60,
            per_device_timeout_seconds=runtime["options"][CONF_PER_DEVICE_TIMEOUT_SECONDS],
        )

    hass.services.async_register(DOMAIN, SERVICE_BLOCK, _block, BLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNBLOCK, _unblock, UNBLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, _scan_now, SCAN_NOW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_ALL, _scan_all, SCAN_ALL_SCHEMA)


def async_unregister_services(hass: HomeAssistant) -> None:
    for svc in (SERVICE_BLOCK, SERVICE_UNBLOCK, SERVICE_SCAN_NOW, SERVICE_SCAN_ALL):
        hass.services.async_remove(DOMAIN, svc)
```

- [ ] **Step 4: Create `services.yaml`**

```yaml
block:
  name: Block device updates
  description: Permanently block updates for a device.
  fields:
    device_id:
      name: Device
      description: Home Assistant device ID to block.
      required: true
      selector:
        device: {}
    reason:
      name: Reason
      description: Free-form note explaining why this device is blocked.
      required: false
      selector:
        text:

unblock:
  name: Remove block
  description: Remove a previously added block.
  fields:
    block_id:
      name: Block ID
      description: Internal block ID (found in the panel or block sensor attributes).
      required: true
      selector:
        text:

scan_now:
  name: Scan a single block
  description: Immediately refresh the shadow version for one block.
  fields:
    block_id:
      name: Block ID
      required: true
      selector:
        text:

scan_all:
  name: Scan all blocks
  description: Immediately run a full scan cycle across all blocks.
```

- [ ] **Step 5: Register services in `__init__.py`**

Update `async_setup_entry` to call `async_register_services`:

```python
    from .services import async_register_services, async_unregister_services

    # Register once on first setup; subsequent entries are rejected by config flow.
    if len(hass.data[DOMAIN]) == 1:
        async_register_services(hass)

        @callback
        def _on_remove():
            async_unregister_services(hass)

        entry.async_on_unload(_on_remove)
```

And add `from homeassistant.core import callback` to the imports if missing.

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_services.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add custom_components/update_blocklist/services.py custom_components/update_blocklist/services.yaml custom_components/update_blocklist/__init__.py tests/test_services.py
git commit -m "Add block/unblock/scan_now/scan_all services"
```

---

## Phase 7: Panel API (aiohttp views)

### Task 26: Panel API — list blocks and options endpoints

**Files:**
- Create: `custom_components/update_blocklist/api.py`
- Modify: `custom_components/update_blocklist/__init__.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing test `tests/test_api.py`**

```python
"""Tests for panel API."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_list_blocks_returns_empty(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/blocks")
    assert resp.status == 200
    data = await resp.json()
    assert data == {"blocks": [], "pending_rediscovery": []}


async def test_list_blocks_includes_added_block(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    await runtime["registry"].async_add_block(
        device_id="d1", update_entity_ids=["update.a"], unique_ids=[],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="r", last_known_version="1.0",
    )
    await runtime["coordinator"].async_request_refresh()

    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/blocks")
    data = await resp.json()
    assert len(data["blocks"]) == 1
    assert data["blocks"][0]["reason"] == "r"


async def test_get_options_returns_current_options(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/options")
    assert resp.status == 200
    data = await resp.json()
    assert data["scan_start_time"] == "01:00"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `api.py`**

```python
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
```

- [ ] **Step 4: Register views in `__init__.py`**

Inside `async_setup_entry`, after registering services:

```python
    from .api import async_register_views
    if len(hass.data[DOMAIN]) == 1:
        async_register_views(hass)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/api.py custom_components/update_blocklist/__init__.py tests/test_api.py
git commit -m "Add panel API views: list blocks and get options"
```

---

### Task 27: Panel API — add/remove block endpoints

**Files:**
- Modify: `custom_components/update_blocklist/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Append failing tests**

```python
async def test_add_block_endpoint(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "add1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    client = await hass_client()
    resp = await client.post(
        f"/api/{DOMAIN}/blocks",
        json={"device_id": device.id, "reason": "x"},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["device_id"] == device.id
    assert len(runtime["registry"].all_blocks()) == 1


async def test_remove_block_endpoint(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "rem1")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )
    block = await runtime["scanner"].async_block_device(
        device_id=device.id, reason=""
    )

    client = await hass_client()
    resp = await client.delete(f"/api/{DOMAIN}/blocks/{block.id}")
    assert resp.status == 204
    assert runtime["registry"].get_block(block.id) is None


async def test_add_block_returns_400_for_missing_device_id(hass, hass_client):
    await _setup(hass)
    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/blocks", json={"reason": "x"})
    assert resp.status == 400
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```

Expected: FAIL.

- [ ] **Step 3: Extend `api.py`**

Append to `api.py`:

```python
import voluptuous as vol


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
```

And update `async_register_views` to also register both:

```python
def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(BlocksListView())
    hass.http.register_view(BlocksWriteView())
    hass.http.register_view(BlockItemView())
    hass.http.register_view(OptionsView())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/api.py tests/test_api.py
git commit -m "Add POST /blocks and DELETE /blocks/{id} panel API endpoints"
```

---

### Task 28: Panel API — candidate devices listing

**Files:**
- Modify: `custom_components/update_blocklist/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Append failing test**

```python
async def test_candidate_devices_returns_only_unblocked_devices_with_update_entities(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    d_with_update = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "wu")},
        manufacturer="Espressif", model="ESP", name="With Update",
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="U1",
        device_id=d_with_update.id,
    )

    d_no_update = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "nu")}
    )

    d_already_blocked = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "ab")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="U2",
        device_id=d_already_blocked.id,
    )
    await runtime["scanner"].async_block_device(
        device_id=d_already_blocked.id, reason=""
    )

    client = await hass_client()
    resp = await client.get(f"/api/{DOMAIN}/candidates")
    assert resp.status == 200
    data = await resp.json()
    ids = [c["device_id"] for c in data["candidates"]]
    assert d_with_update.id in ids
    assert d_no_update.id not in ids
    assert d_already_blocked.id not in ids
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::test_candidate_devices_returns_only_unblocked_devices_with_update_entities -v
```

Expected: FAIL.

- [ ] **Step 3: Append to `api.py`**

```python
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
```

Update `async_register_views` to also register `CandidatesView()`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/api.py tests/test_api.py
git commit -m "Add GET /candidates endpoint for panel add-dialog"
```

---

### Task 29: Panel API — scan trigger endpoint

**Files:**
- Modify: `custom_components/update_blocklist/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Append failing test**

```python
async def test_scan_endpoint_triggers_scan_all_when_no_block_id(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    calls: list[str] = []

    async def fake_scan_all(*, max_duration_seconds, per_device_timeout_seconds):
        calls.append("all")

    runtime["scanner"].async_scan_all = fake_scan_all  # type: ignore[method-assign]

    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/scan", json={})
    assert resp.status == 202
    await hass.async_block_till_done()
    assert calls == ["all"]


async def test_scan_endpoint_with_block_id_triggers_scan_block(hass, hass_client):
    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    calls: list[str] = []

    async def fake_scan_block(*, block_id, per_device_timeout_seconds):
        calls.append(block_id)

    runtime["scanner"].async_scan_block = fake_scan_block  # type: ignore[method-assign]

    client = await hass_client()
    resp = await client.post(f"/api/{DOMAIN}/scan", json={"block_id": "abc"})
    assert resp.status == 202
    await hass.async_block_till_done()
    assert calls == ["abc"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py -v
```

Expected: FAIL.

- [ ] **Step 3: Append to `api.py`**

```python
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
```

Update `async_register_views` to also register `ScanView()`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/api.py tests/test_api.py
git commit -m "Add POST /scan endpoint for panel-triggered scans"
```

---

### Task 30: Panel API — rediscovery resolution endpoint

**Files:**
- Modify: `custom_components/update_blocklist/api.py`
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Append failing test**

```python
async def test_resolve_rediscovery_accept_updates_block(hass, hass_client):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    registry = runtime["registry"]

    # Old orphan block.
    block = await registry.async_add_block(
        device_id="gone", update_entity_ids=["update.old"], unique_ids=["M1"],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await registry.async_set_pending_rediscovery(
        [{"orphan_block_id": block.id, "candidate_device_id": "newdev",
          "match_type": "unique_id", "detected_at": "2026-04-16T09:15:00Z"}]
    )

    # New device + update entity exists.
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    new_dev = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "newdev")}
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="M1", device_id=new_dev.id
    )

    client = await hass_client()
    resp = await client.post(
        f"/api/{DOMAIN}/rediscovery/resolve",
        json={"orphan_block_id": block.id, "candidate_device_id": new_dev.id, "action": "accept"},
    )
    assert resp.status == 200

    updated = registry.get_block(block.id)
    assert updated.device_id == new_dev.id
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::test_resolve_rediscovery_accept_updates_block -v
```

Expected: FAIL.

- [ ] **Step 3: Add resolve method to scanner**

Append to `scanner.py`:

```python
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
        # "dismiss" path: pending list already pruned below.

        await self._registry.async_set_pending_rediscovery(pending)
        await self._coordinator.async_request_refresh()
        return True
```

- [ ] **Step 4: Add view to `api.py`**

```python
class RediscoveryResolveView(_BaseView):
    url = f"/api/{DOMAIN}/rediscovery/resolve"
    name = f"api:{DOMAIN}:rediscovery:resolve"

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        runtime = _runtime(hass)
        if runtime is None:
            return web.Response(status=404)

        try:
            payload = await request.json()
        except ValueError:
            return self.json_message("Invalid JSON", status_code=400)

        schema = vol.Schema(
            {
                vol.Required("orphan_block_id"): str,
                vol.Optional("candidate_device_id"): vol.Any(str, None),
                vol.Required("action"): vol.In(["accept", "decline", "dismiss"]),
            }
        )
        try:
            data = schema(payload)
        except vol.Invalid as exc:
            return self.json_message(str(exc), status_code=400)

        ok = await runtime["scanner"].async_resolve_rediscovery(
            orphan_block_id=data["orphan_block_id"],
            candidate_device_id=data.get("candidate_device_id"),
            action=data["action"],
        )
        return web.Response(status=200 if ok else 404)
```

Update `async_register_views` to also register `RediscoveryResolveView()`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/api.py custom_components/update_blocklist/scanner.py tests/test_api.py
git commit -m "Add POST /rediscovery/resolve endpoint and scanner resolution logic"
```

---

## Phase 8: Frontend Panel (Lit + Vite)

### Task 31: Frontend scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/update-blocklist-panel.ts` (stub)
- Create: `frontend/.eslintrc.cjs`
- Create: `frontend/.prettierrc.json`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "update-blocklist-panel",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "dev": "vite build --watch",
    "test": "vitest run",
    "lint": "eslint 'src/**/*.ts'",
    "format": "prettier --write 'src/**/*.ts'"
  },
  "devDependencies": {
    "@open-wc/testing-helpers": "^3.0.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "eslint": "^8.57.0",
    "jsdom": "^24.0.0",
    "prettier": "^3.2.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vitest": "^1.4.0"
  },
  "dependencies": {
    "lit": "^3.1.0"
  }
}
```

- [ ] **Step 2: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "useDefineForClassFields": false,
    "experimentalDecorators": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "isolatedModules": true,
    "lib": ["ES2022", "DOM"],
    "types": ["vitest/globals"]
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create `frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../custom_components/update_blocklist/www"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/update-blocklist-panel.ts"),
      formats: ["es"],
      fileName: () => "panel.js",
    },
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
    sourcemap: false,
    target: "es2022",
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 4: Create `frontend/.eslintrc.cjs`**

```js
module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint"],
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  parserOptions: { ecmaVersion: 2022, sourceType: "module" },
  env: { browser: true, es2022: true },
};
```

- [ ] **Step 5: Create `frontend/.prettierrc.json`**

```json
{ "printWidth": 100, "semi": true, "singleQuote": false, "trailingComma": "all" }
```

- [ ] **Step 6: Create stub `frontend/src/update-blocklist-panel.ts`**

```ts
import { LitElement, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("update-blocklist-panel")
export class UpdateBlocklistPanel extends LitElement {
  render() {
    return html`<div>Update Blocklist — loading…</div>`;
  }
}
```

- [ ] **Step 7: Install deps and build**

```bash
cd frontend
npm install
npm run build
cd ..
```

Expected: `custom_components/update_blocklist/www/panel.js` created (should be a small ESM file).

- [ ] **Step 8: Commit**

```bash
git add frontend/ custom_components/update_blocklist/www/panel.js
git commit -m "Add frontend scaffolding (Lit + Vite) with stub panel"
```

---

### Task 32: Frontend — API client with tests

**Files:**
- Create: `frontend/src/api-client.ts`
- Create: `frontend/src/api-client.test.ts`

- [ ] **Step 1: Write failing test `frontend/src/api-client.test.ts`**

```ts
import { describe, it, expect, beforeEach, vi } from "vitest";
import { BlocklistApi } from "./api-client";

describe("BlocklistApi", () => {
  beforeEach(() => {
    (global as any).fetch = vi.fn();
  });

  it("listBlocks calls the list endpoint", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ blocks: [], pending_rediscovery: [] }),
    });

    const api = new BlocklistApi("TOKEN");
    const data = await api.listBlocks();
    expect(data).toEqual({ blocks: [], pending_rediscovery: [] });
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer TOKEN" }),
      }),
    );
  });

  it("addBlock posts to the blocks endpoint", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({ id: "b1" }),
    });

    const api = new BlocklistApi("T");
    const block = await api.addBlock("dev1", "reason");
    expect(block.id).toBe("b1");
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ device_id: "dev1", reason: "reason" }),
      }),
    );
  });

  it("removeBlock deletes the block", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    });

    const api = new BlocklistApi("T");
    await api.removeBlock("b1");
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks/b1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("listBlocks throws on non-2xx", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "boom",
    });

    const api = new BlocklistApi("T");
    await expect(api.listBlocks()).rejects.toThrow(/500/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- api-client
```

Expected: FAIL (module does not exist).

- [ ] **Step 3: Implement `frontend/src/api-client.ts`**

```ts
const BASE = "/api/update_blocklist";

export interface Block {
  id: string;
  device_id: string;
  update_entity_ids: string[];
  unique_ids: string[];
  fingerprint: { manufacturer: string; model: string; name: string };
  reason: string;
  created_at: string;
  last_known_version: string | null;
  last_scan_at: string | null;
  last_scan_status: string;
  status: string;
}

export interface Candidate {
  device_id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  update_entity_ids: string[];
}

export interface Options {
  scan_start_time: string;
  scan_max_duration_minutes: number;
  per_device_timeout_seconds: number;
}

export interface PendingRediscovery {
  orphan_block_id: string;
  candidate_device_id: string;
  match_type: "unique_id" | "fingerprint";
  detected_at: string;
}

export interface BlocksResponse {
  blocks: Block[];
  pending_rediscovery: PendingRediscovery[];
}

export class BlocklistApi {
  constructor(private token: string) {}

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const resp = await fetch(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
        ...(init.headers ?? {}),
      },
    });
    if (!resp.ok) {
      const body = typeof (resp as any).text === "function" ? await (resp as any).text() : "";
      throw new Error(`${resp.status} ${body}`);
    }
    if (resp.status === 204) return undefined as T;
    return (await resp.json()) as T;
  }

  listBlocks(): Promise<BlocksResponse> {
    return this.request<BlocksResponse>(`${BASE}/blocks`);
  }

  addBlock(deviceId: string, reason: string): Promise<Block> {
    return this.request<Block>(`${BASE}/blocks`, {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId, reason }),
    });
  }

  removeBlock(blockId: string): Promise<void> {
    return this.request<void>(`${BASE}/blocks/${encodeURIComponent(blockId)}`, {
      method: "DELETE",
    });
  }

  listCandidates(): Promise<{ candidates: Candidate[] }> {
    return this.request(`${BASE}/candidates`);
  }

  getOptions(): Promise<Options> {
    return this.request<Options>(`${BASE}/options`);
  }

  scan(blockId?: string): Promise<void> {
    return this.request<void>(`${BASE}/scan`, {
      method: "POST",
      body: JSON.stringify(blockId ? { block_id: blockId } : {}),
    });
  }

  resolveRediscovery(
    orphanBlockId: string,
    action: "accept" | "decline" | "dismiss",
    candidateDeviceId?: string,
  ): Promise<void> {
    return this.request<void>(`${BASE}/rediscovery/resolve`, {
      method: "POST",
      body: JSON.stringify({
        orphan_block_id: orphanBlockId,
        candidate_device_id: candidateDeviceId ?? null,
        action,
      }),
    });
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- api-client
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api-client.ts frontend/src/api-client.test.ts
git commit -m "Add typed BlocklistApi with Vitest coverage"
```

---

### Task 33: Frontend — blocks list view

**Files:**
- Create: `frontend/src/views/blocks-list.ts`
- Create: `frontend/src/views/blocks-list.test.ts`

- [ ] **Step 1: Write failing test**

```ts
import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./blocks-list";
import type { BlocksListView } from "./blocks-list";

describe("<blocks-list>", () => {
  it("renders an empty state when no blocks", async () => {
    const el = await fixture<BlocksListView>(tplHtml`<blocks-list .blocks=${[]}></blocks-list>`);
    expect(el.shadowRoot!.textContent).toMatch(/No blocks/i);
  });

  it("renders one row per block", async () => {
    const blocks = [
      { id: "b1", device_id: "d1", reason: "r", last_known_version: "1.0",
        update_entity_ids: [], unique_ids: [], fingerprint: {manufacturer:"",model:"",name:""},
        created_at: "", last_scan_at: null, last_scan_status: "ok", status: "active" },
    ];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const rows = el.shadowRoot!.querySelectorAll("[data-test='block-row']");
    expect(rows.length).toBe(1);
    expect(rows[0].textContent).toMatch(/r/);
  });

  it("dispatches remove event when remove button clicked", async () => {
    const blocks = [
      { id: "b1", device_id: "d1", reason: "r", last_known_version: null,
        update_entity_ids: [], unique_ids: [], fingerprint: {manufacturer:"",model:"",name:""},
        created_at: "", last_scan_at: null, last_scan_status: "ok", status: "active" },
    ];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );

    const events: CustomEvent[] = [];
    el.addEventListener("block-remove", (e) => events.push(e as CustomEvent));

    (el.shadowRoot!.querySelector("[data-test='remove-btn']") as HTMLButtonElement).click();
    expect(events.length).toBe(1);
    expect(events[0].detail).toEqual({ block_id: "b1" });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- blocks-list
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/views/blocks-list.ts`**

```ts
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { Block } from "../api-client";

@customElement("blocks-list")
export class BlocksListView extends LitElement {
  @property({ attribute: false }) blocks: Block[] = [];

  static styles = css`
    :host { display: block; }
    table { border-collapse: collapse; width: 100%; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--divider-color, #ccc); }
    .empty { padding: 16px; color: var(--secondary-text-color, #666); }
    button.remove { color: var(--error-color, #d33); }
  `;

  render() {
    if (!this.blocks.length) {
      return html`<div class="empty">No blocks. Use "Add block" to create one.</div>`;
    }
    return html`
      <table>
        <thead>
          <tr>
            <th>Device</th><th>Reason</th><th>Last known version</th>
            <th>Last scan</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          ${this.blocks.map(
            (b) => html`
              <tr data-test="block-row">
                <td>${b.device_id}</td>
                <td>${b.reason || "—"}</td>
                <td>${b.last_known_version ?? "unknown"}</td>
                <td>${b.last_scan_at ?? "never"}</td>
                <td>${b.status}</td>
                <td>
                  <button
                    class="remove"
                    data-test="remove-btn"
                    @click=${() => this._emitRemove(b.id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            `,
          )}
        </tbody>
      </table>
    `;
  }

  private _emitRemove(blockId: string) {
    this.dispatchEvent(
      new CustomEvent("block-remove", { detail: { block_id: blockId }, bubbles: true, composed: true }),
    );
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- blocks-list
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/
git commit -m "Add blocks-list view with empty state, rows, and remove event"
```

---

### Task 34: Frontend — add-block dialog

**Files:**
- Create: `frontend/src/views/add-block-dialog.ts`
- Create: `frontend/src/views/add-block-dialog.test.ts`

- [ ] **Step 1: Write failing test**

```ts
import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./add-block-dialog";
import type { AddBlockDialog } from "./add-block-dialog";
import type { Candidate } from "../api-client";

const candidate: Candidate = {
  device_id: "d1", name: "Test Device", manufacturer: "Espressif",
  model: "ESP", update_entity_ids: ["update.a"],
};

describe("<add-block-dialog>", () => {
  it("renders candidates as options", async () => {
    const el = await fixture<AddBlockDialog>(
      tplHtml`<add-block-dialog .candidates=${[candidate]}></add-block-dialog>`,
    );
    const options = el.shadowRoot!.querySelectorAll("option");
    expect(options.length).toBe(2); // placeholder + one candidate
    expect(options[1].textContent).toMatch(/Test Device/);
  });

  it("dispatches block-add event with form values", async () => {
    const el = await fixture<AddBlockDialog>(
      tplHtml`<add-block-dialog .candidates=${[candidate]}></add-block-dialog>`,
    );
    const select = el.shadowRoot!.querySelector("select") as HTMLSelectElement;
    const textarea = el.shadowRoot!.querySelector("textarea") as HTMLTextAreaElement;
    select.value = "d1";
    select.dispatchEvent(new Event("change"));
    textarea.value = "because reasons";
    textarea.dispatchEvent(new Event("input"));

    const events: CustomEvent[] = [];
    el.addEventListener("block-add", (e) => events.push(e as CustomEvent));
    (el.shadowRoot!.querySelector("button[type='submit']") as HTMLButtonElement).click();

    expect(events.length).toBe(1);
    expect(events[0].detail).toEqual({ device_id: "d1", reason: "because reasons" });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- add-block-dialog
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/views/add-block-dialog.ts`**

```ts
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { Candidate } from "../api-client";

@customElement("add-block-dialog")
export class AddBlockDialog extends LitElement {
  @property({ attribute: false }) candidates: Candidate[] = [];
  @state() private _deviceId = "";
  @state() private _reason = "";

  static styles = css`
    :host { display: block; padding: 16px; }
    form { display: flex; flex-direction: column; gap: 12px; }
    label { font-weight: 600; }
    select, textarea { padding: 8px; font: inherit; }
    .actions { display: flex; gap: 8px; justify-content: flex-end; }
  `;

  render() {
    return html`
      <form @submit=${this._onSubmit}>
        <label>
          Device to block
          <select @change=${(e: Event) => (this._deviceId = (e.target as HTMLSelectElement).value)}>
            <option value="">— select —</option>
            ${this.candidates.map(
              (c) => html`<option value=${c.device_id}>${c.name} (${c.manufacturer ?? ""} ${c.model ?? ""})</option>`,
            )}
          </select>
        </label>
        <label>
          Reason (optional)
          <textarea
            rows="3"
            @input=${(e: Event) => (this._reason = (e.target as HTMLTextAreaElement).value)}
          ></textarea>
        </label>
        <div class="actions">
          <button type="button" @click=${this._cancel}>Cancel</button>
          <button type="submit" ?disabled=${!this._deviceId}>Add block</button>
        </div>
      </form>
    `;
  }

  private _onSubmit(e: Event) {
    e.preventDefault();
    if (!this._deviceId) return;
    this.dispatchEvent(
      new CustomEvent("block-add", {
        detail: { device_id: this._deviceId, reason: this._reason },
        bubbles: true, composed: true,
      }),
    );
  }

  private _cancel() {
    this.dispatchEvent(new CustomEvent("cancel", { bubbles: true, composed: true }));
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- add-block-dialog
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/add-block-dialog.ts frontend/src/views/add-block-dialog.test.ts
git commit -m "Add add-block-dialog component with candidate select and reason"
```

---

### Task 35: Frontend — rediscovery prompt view

**Files:**
- Create: `frontend/src/views/rediscovery-prompt.ts`
- Create: `frontend/src/views/rediscovery-prompt.test.ts`

- [ ] **Step 1: Write failing test**

```ts
import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./rediscovery-prompt";
import type { RediscoveryPrompt } from "./rediscovery-prompt";

describe("<rediscovery-prompt>", () => {
  it("renders nothing when no pending items", async () => {
    const el = await fixture<RediscoveryPrompt>(
      tplHtml`<rediscovery-prompt .pending=${[]}></rediscovery-prompt>`,
    );
    expect(el.shadowRoot!.textContent!.trim()).toBe("");
  });

  it("emits resolve event with action and ids", async () => {
    const pending = [
      { orphan_block_id: "b1", candidate_device_id: "newdev",
        match_type: "unique_id" as const, detected_at: "now" },
    ];
    const el = await fixture<RediscoveryPrompt>(
      tplHtml`<rediscovery-prompt .pending=${pending}></rediscovery-prompt>`,
    );
    const events: CustomEvent[] = [];
    el.addEventListener("resolve", (e) => events.push(e as CustomEvent));

    (el.shadowRoot!.querySelector("[data-action='accept']") as HTMLButtonElement).click();
    expect(events[0].detail).toEqual({
      orphan_block_id: "b1", candidate_device_id: "newdev", action: "accept",
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- rediscovery-prompt
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/views/rediscovery-prompt.ts`**

```ts
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { PendingRediscovery } from "../api-client";

@customElement("rediscovery-prompt")
export class RediscoveryPrompt extends LitElement {
  @property({ attribute: false }) pending: PendingRediscovery[] = [];

  static styles = css`
    :host { display: block; }
    .item {
      background: var(--warning-color, #ffcc80);
      color: var(--primary-text-color, #000);
      padding: 12px; margin-bottom: 8px; border-radius: 4px;
    }
    .actions { margin-top: 8px; display: flex; gap: 8px; }
  `;

  render() {
    if (!this.pending.length) return html``;
    return html`
      ${this.pending.map(
        (p) => html`
          <div class="item">
            <div>
              <strong>Suspected re-pair.</strong>
              Blocked device appears to have returned as a new device
              (matched by ${p.match_type}). Re-apply block?
            </div>
            <div class="actions">
              <button data-action="accept" @click=${() => this._emit(p, "accept")}>
                Re-apply to this device
              </button>
              <button data-action="decline" @click=${() => this._emit(p, "decline")}>
                Delete block
              </button>
              <button data-action="dismiss" @click=${() => this._emit(p, "dismiss")}>
                Remind me later
              </button>
            </div>
          </div>
        `,
      )}
    `;
  }

  private _emit(
    p: PendingRediscovery,
    action: "accept" | "decline" | "dismiss",
  ) {
    this.dispatchEvent(
      new CustomEvent("resolve", {
        detail: {
          orphan_block_id: p.orphan_block_id,
          candidate_device_id: p.candidate_device_id,
          action,
        },
        bubbles: true, composed: true,
      }),
    );
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- rediscovery-prompt
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/rediscovery-prompt.ts frontend/src/views/rediscovery-prompt.test.ts
git commit -m "Add rediscovery-prompt view with accept/decline/dismiss actions"
```

---

### Task 36: Frontend — settings view (show current options)

**Files:**
- Create: `frontend/src/views/settings-view.ts`
- Create: `frontend/src/views/settings-view.test.ts`

- [ ] **Step 1: Write failing test**

```ts
import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./settings-view";
import type { SettingsView } from "./settings-view";

describe("<settings-view>", () => {
  it("displays current options", async () => {
    const opts = {
      scan_start_time: "02:15",
      scan_max_duration_minutes: 45,
      per_device_timeout_seconds: 120,
    };
    const el = await fixture<SettingsView>(
      tplHtml`<settings-view .options=${opts}></settings-view>`,
    );
    expect(el.shadowRoot!.textContent).toMatch(/02:15/);
    expect(el.shadowRoot!.textContent).toMatch(/45/);
    expect(el.shadowRoot!.textContent).toMatch(/120/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- settings-view
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/views/settings-view.ts`**

```ts
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { Options } from "../api-client";

@customElement("settings-view")
export class SettingsView extends LitElement {
  @property({ attribute: false }) options: Options | null = null;

  static styles = css`
    :host { display: block; padding: 16px; }
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; }
    dt { font-weight: 600; }
    .hint { color: var(--secondary-text-color, #666); margin-top: 16px; }
  `;

  render() {
    if (!this.options) return html`<div>Loading…</div>`;
    return html`
      <dl>
        <dt>Scan window start</dt><dd>${this.options.scan_start_time}</dd>
        <dt>Max duration (minutes)</dt><dd>${this.options.scan_max_duration_minutes}</dd>
        <dt>Per-device timeout (seconds)</dt><dd>${this.options.per_device_timeout_seconds}</dd>
      </dl>
      <div class="hint">
        Edit these values in Settings → Devices &amp; Services → Update Blocklist → Configure.
      </div>
    `;
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- settings-view
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/settings-view.ts frontend/src/views/settings-view.test.ts
git commit -m "Add settings-view component showing current options"
```

---

### Task 37: Frontend — root panel wiring

**Files:**
- Modify: `frontend/src/update-blocklist-panel.ts`

- [ ] **Step 1: Replace stub with full implementation**

```ts
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { BlocklistApi, type Block, type Candidate, type Options, type PendingRediscovery } from "./api-client";
import "./views/blocks-list";
import "./views/add-block-dialog";
import "./views/rediscovery-prompt";
import "./views/settings-view";

interface HomeAssistantLike {
  auth?: { accessToken: string };
}

@customElement("update-blocklist-panel")
export class UpdateBlocklistPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @state() private _blocks: Block[] = [];
  @state() private _pending: PendingRediscovery[] = [];
  @state() private _candidates: Candidate[] = [];
  @state() private _options: Options | null = null;
  @state() private _showAdd = false;
  @state() private _error: string | null = null;

  private _api(): BlocklistApi {
    return new BlocklistApi(this.hass?.auth?.accessToken ?? "");
  }

  static styles = css`
    :host { display: block; padding: 16px; font-family: var(--primary-font-family, sans-serif); }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    h1 { margin: 0; font-size: 1.4em; }
    button.primary {
      background: var(--primary-color, #03a9f4);
      color: white; border: 0; padding: 8px 14px; border-radius: 4px; cursor: pointer;
    }
    .error { color: var(--error-color, #d33); padding: 8px 0; }
    .overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.3);
      display: grid; place-items: center;
    }
    .dialog { background: var(--card-background-color, white); border-radius: 8px; min-width: 400px; }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._refresh();
  }

  private async _refresh(): Promise<void> {
    try {
      const [list, opts] = await Promise.all([this._api().listBlocks(), this._api().getOptions()]);
      this._blocks = list.blocks;
      this._pending = list.pending_rediscovery;
      this._options = opts;
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _openAdd(): Promise<void> {
    try {
      const { candidates } = await this._api().listCandidates();
      this._candidates = candidates;
      this._showAdd = true;
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onAdd(e: CustomEvent<{ device_id: string; reason: string }>): Promise<void> {
    try {
      await this._api().addBlock(e.detail.device_id, e.detail.reason);
      this._showAdd = false;
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onRemove(e: CustomEvent<{ block_id: string }>): Promise<void> {
    try {
      await this._api().removeBlock(e.detail.block_id);
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onResolve(
    e: CustomEvent<{ orphan_block_id: string; candidate_device_id: string;
                    action: "accept" | "decline" | "dismiss" }>,
  ): Promise<void> {
    try {
      await this._api().resolveRediscovery(
        e.detail.orphan_block_id, e.detail.action, e.detail.candidate_device_id,
      );
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  render() {
    return html`
      <header>
        <h1>Update Blocklist</h1>
        <button class="primary" @click=${this._openAdd}>Add block</button>
      </header>
      ${this._error ? html`<div class="error">${this._error}</div>` : html``}

      <rediscovery-prompt .pending=${this._pending} @resolve=${this._onResolve}></rediscovery-prompt>

      <blocks-list .blocks=${this._blocks} @block-remove=${this._onRemove}></blocks-list>

      <settings-view .options=${this._options}></settings-view>

      ${this._showAdd
        ? html`
            <div class="overlay" @click=${() => (this._showAdd = false)}>
              <div class="dialog" @click=${(e: Event) => e.stopPropagation()}>
                <add-block-dialog
                  .candidates=${this._candidates}
                  @block-add=${this._onAdd}
                  @cancel=${() => (this._showAdd = false)}
                ></add-block-dialog>
              </div>
            </div>
          `
        : html``}
    `;
  }
}
```

- [ ] **Step 2: Rebuild the frontend**

```bash
cd frontend && npm run build && cd ..
```

Expected: `custom_components/update_blocklist/www/panel.js` updated.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/update-blocklist-panel.ts custom_components/update_blocklist/www/panel.js
git commit -m "Wire root panel to API, blocks list, add dialog, rediscovery, settings"
```

---

## Phase 9: Panel Registration (Backend)

### Task 38: Register panel via `panel_custom`

**Files:**
- Create: `custom_components/update_blocklist/panel.py`
- Modify: `custom_components/update_blocklist/__init__.py`

- [ ] **Step 1: Implement `panel.py`**

```python
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
    from homeassistant.components import frontend
    frontend.async_remove_panel(hass, DOMAIN)
```

- [ ] **Step 2: Register panel in `__init__.py`**

Inside `async_setup_entry` after views are registered:

```python
    from .panel import async_register_panel, async_remove_panel
    if len(hass.data[DOMAIN]) == 1:
        await async_register_panel(hass)

        async def _remove_panel():
            await async_remove_panel(hass)

        entry.async_on_unload(_remove_panel)
```

- [ ] **Step 3: Smoke-test — panel loads without exception**

```bash
pytest tests/test_init.py -v
```

Expected: still PASS (tests don't inspect panel registration explicitly, but setup must not crash).

- [ ] **Step 4: Commit**

```bash
git add custom_components/update_blocklist/panel.py custom_components/update_blocklist/__init__.py
git commit -m "Register sidebar panel serving built panel.js"
```

---

## Phase 10: Re-pair Detection Wiring

### Task 39: Listen for device_registry_updated and populate pending_rediscovery

**Files:**
- Modify: `custom_components/update_blocklist/scanner.py`
- Modify: `custom_components/update_blocklist/__init__.py`
- Create: `tests/test_rediscovery.py`

- [ ] **Step 1: Write failing test `tests/test_rediscovery.py`**

```python
"""Tests for re-pair (rediscovery) detection."""
from __future__ import annotations

from datetime import UTC, datetime

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.update_blocklist.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_orphan_block_with_matching_unique_id_produces_pending(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    registry = runtime["registry"]
    scanner = runtime["scanner"]

    # Create orphan block referencing device "gone" and unique_id "U1".
    await registry.async_add_block(
        device_id="gone", update_entity_ids=["update.old"], unique_ids=["U1"],
        fingerprint={"manufacturer": "e", "model": "m", "name": "n"},
        reason="", last_known_version=None,
    )

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    new_dev = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "new")},
    )
    ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="U1", device_id=new_dev.id
    )

    await scanner.async_detect_rediscovery()

    pending = registry.pending_rediscovery
    assert len(pending) == 1
    assert pending[0]["candidate_device_id"] == new_dev.id
    assert pending[0]["match_type"] == "unique_id"


async def test_orphan_without_matches_stays_empty(hass):
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    registry = runtime["registry"]
    scanner = runtime["scanner"]

    await registry.async_add_block(
        device_id="gone", update_entity_ids=["update.old"], unique_ids=["Nope"],
        fingerprint={"manufacturer": "", "model": "", "name": ""},
        reason="", last_known_version=None,
    )
    await scanner.async_detect_rediscovery()
    assert registry.pending_rediscovery == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_rediscovery.py -v
```

Expected: FAIL.

- [ ] **Step 3: Add `async_detect_rediscovery` to `scanner.py`**

```python
    async def async_detect_rediscovery(self) -> None:
        """Scan for orphan blocks whose devices may have re-paired.

        Populates registry.pending_rediscovery.
        """
        dev_reg = dr.async_get(self._hass)
        ent_reg = er.async_get(self._hass)

        orphans = self._registry.find_orphans(dev_reg)

        pending: list[dict[str, object]] = []
        seen_orphan_ids: set[str] = set()

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
            seen_orphan_ids.add(orphan.id)
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
        await self._coordinator.async_request_refresh()
```

- [ ] **Step 4: Trigger detection in `__init__.py`**

Inside `async_setup_entry`, after scanner/schedule wire-up:

```python
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from homeassistant.helpers.device_registry import EVENT_DEVICE_REGISTRY_UPDATED

    async def _on_device_registry_update(_event):
        await scanner.async_detect_rediscovery()

    entry.async_on_unload(
        hass.bus.async_listen(EVENT_DEVICE_REGISTRY_UPDATED, _on_device_registry_update)
    )

    # Initial run so we surface pending items on startup.
    await scanner.async_detect_rediscovery()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_rediscovery.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/update_blocklist/scanner.py custom_components/update_blocklist/__init__.py tests/test_rediscovery.py
git commit -m "Detect re-paired devices and populate pending_rediscovery"
```

---

## Phase 11: Safe Uninstall and Startup Cleanup

### Task 40: Safe uninstall — re-enable entities on config entry removal

**Files:**
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Append failing test**

```python
async def test_removing_config_entry_reenables_all_entities(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "u_all")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    await runtime["scanner"].async_block_device(device_id=device.id, reason="")
    assert ent_reg.async_get(update.entity_id).disabled_by == er.RegistryEntryDisabler.INTEGRATION

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert ent_reg.async_get(update.entity_id).disabled_by is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_init.py::test_removing_config_entry_reenables_all_entities -v
```

Expected: FAIL (uninstall does not clean up).

- [ ] **Step 3: Add `async_remove_entry` to `__init__.py`**

```python
async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up when the integration is removed from HA."""
    from homeassistant.helpers import entity_registry as er

    # Runtime is already gone at this point; reload registry straight from store.
    from .registry import BlockRegistry

    registry = BlockRegistry(hass)
    await registry.async_load()

    ent_reg = er.async_get(hass)
    for block in registry.all_blocks():
        for eid in block.update_entity_ids:
            existing = ent_reg.async_get(eid)
            if existing and existing.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
                ent_reg.async_update_entity(eid, disabled_by=None)

    # Purge storage file by saving empty data (Store does not expose a delete).
    await registry._store.async_save({"blocks": [], "pending_rediscovery": []})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/__init__.py tests/test_init.py
git commit -m "Re-enable all blocked entities on config entry removal"
```

---

### Task 41: Startup cleanup — re-disable entities after interrupted scan

**Files:**
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Append failing test**

```python
async def test_startup_re_disables_blocked_entity_that_was_left_enabled(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    # Pre-load storage with a block pointing at an entity that currently has disabled_by=None.
    from custom_components.update_blocklist.const import STORAGE_KEY
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "restart1")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="rs", device_id=device.id
    )
    assert ent_reg.async_get(update.entity_id).disabled_by is None

    hass_storage = getattr(hass, "_update_blocklist_seeded_storage", None)
    if hass_storage is None:
        # Seed via the hass_storage fixture-like backdoor: simulate by directly calling registry.
        from custom_components.update_blocklist.registry import BlockRegistry
        reg = BlockRegistry(hass)
        await reg.async_load()
        await reg.async_add_block(
            device_id=device.id, update_entity_ids=[update.entity_id], unique_ids=["rs"],
            fingerprint={"manufacturer": "", "model": "", "name": ""},
            reason="", last_known_version=None,
        )

    # Bring up the integration.
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Entity should now be disabled.
    assert ent_reg.async_get(update.entity_id).disabled_by == er.RegistryEntryDisabler.INTEGRATION
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_init.py::test_startup_re_disables_blocked_entity_that_was_left_enabled -v
```

Expected: FAIL.

- [ ] **Step 3: Add startup cleanup to `async_setup_entry`**

After coordinator/scanner are created (and before platforms forward):

```python
    # Startup cleanup: any entity that is part of an active block but currently
    # disabled_by is None (e.g., interrupted scan) gets re-disabled.
    from homeassistant.helpers import entity_registry as er
    ent_reg = er.async_get(hass)
    for block in registry.all_blocks():
        if block.status != "active":
            continue
        for eid in block.update_entity_ids:
            existing = ent_reg.async_get(eid)
            if existing is not None and existing.disabled_by is None:
                ent_reg.async_update_entity(
                    eid, disabled_by=er.RegistryEntryDisabler.INTEGRATION
                )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/__init__.py tests/test_init.py
git commit -m "Re-disable entities left enabled by interrupted scan on startup"
```

---

### Task 41b: Runtime listener for user-initiated re-enables

**Files:**
- Modify: `custom_components/update_blocklist/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Append failing test to `tests/test_init.py`**

```python
async def test_user_manually_reenables_marks_block_as_user_overridden(hass):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id="fake", identifiers={("demo", "userov")}
    )
    update = ent_reg.async_get_or_create(
        domain="update", platform="demo", unique_id="u", device_id=device.id
    )

    block = await runtime["scanner"].async_block_device(device_id=device.id, reason="")
    await hass.async_block_till_done()

    # User manually re-enables through UI — simulate by direct registry update.
    ent_reg.async_update_entity(update.entity_id, disabled_by=None)
    await hass.async_block_till_done()

    updated = runtime["registry"].get_block(block.id)
    assert updated.status == "user_overridden"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_init.py::test_user_manually_reenables_marks_block_as_user_overridden -v
```

Expected: FAIL.

- [ ] **Step 3: Add entity_registry listener in `__init__.py`**

Inside `async_setup_entry`, after the startup cleanup block:

```python
    from homeassistant.helpers import entity_registry as er_helpers
    from homeassistant.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
    from .const import BLOCK_STATUS_USER_OVERRIDDEN

    ent_reg = er_helpers.async_get(hass)

    async def _on_entity_registry_updated(event) -> None:
        if event.data.get("action") != "update":
            return
        changes: dict = event.data.get("changes", {})
        if "disabled_by" not in changes:
            return

        entity_id = event.data.get("entity_id")
        block = registry.find_block_for_entity(entity_id)
        if block is None or block.status != "active":
            return

        ent_reg_entry = ent_reg.async_get(entity_id)
        if ent_reg_entry is None:
            return

        if ent_reg_entry.disabled_by is None:
            block.status = BLOCK_STATUS_USER_OVERRIDDEN
            await registry.async_update_block(block)
            await coordinator.async_request_refresh()

    entry.async_on_unload(
        hass.bus.async_listen(
            EVENT_ENTITY_REGISTRY_UPDATED, _on_entity_registry_updated
        )
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_init.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/__init__.py tests/test_init.py
git commit -m "Detect user-initiated re-enables and mark block as user_overridden"
```

---

## Phase 12: Translations

### Task 42: strings.json + en/de translations

**Files:**
- Create: `custom_components/update_blocklist/strings.json`
- Create: `custom_components/update_blocklist/translations/en.json`
- Create: `custom_components/update_blocklist/translations/de.json`

- [ ] **Step 1: Create `strings.json` (canonical English source)**

```json
{
  "title": "Update Blocklist",
  "config": {
    "step": {
      "user": {
        "title": "Add Update Blocklist",
        "description": "This integration lets you permanently block firmware updates for specific devices."
      }
    },
    "abort": {
      "single_instance_allowed": "Already configured. Only a single Update Blocklist instance is allowed."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Scan window",
        "description": "The integration briefly re-enables blocked update entities during this nightly window to refresh last-known version info, then re-disables them.",
        "data": {
          "scan_start_time": "Scan start time (HH:MM, 24h)",
          "scan_max_duration_minutes": "Max scan duration (minutes)",
          "per_device_timeout_seconds": "Per-device timeout (seconds)"
        }
      }
    },
    "error": {
      "invalid_time": "Time must be in HH:MM (24h) format.",
      "invalid_duration": "Duration must be at least 1 minute.",
      "invalid_timeout": "Timeout must be at least 10 seconds."
    }
  },
  "services": {
    "block": {
      "name": "Block device updates",
      "description": "Permanently block updates for a device.",
      "fields": {
        "device_id": {
          "name": "Device",
          "description": "Home Assistant device ID to block."
        },
        "reason": {
          "name": "Reason",
          "description": "Free-form note explaining why this device is blocked."
        }
      }
    },
    "unblock": {
      "name": "Remove block",
      "description": "Remove a previously added block.",
      "fields": {
        "block_id": {
          "name": "Block ID",
          "description": "Internal block ID."
        }
      }
    },
    "scan_now": {
      "name": "Scan a single block",
      "description": "Refresh the shadow version for one block immediately."
    },
    "scan_all": {
      "name": "Scan all blocks",
      "description": "Run a full scan cycle across all blocks immediately."
    }
  }
}
```

- [ ] **Step 2: Copy to `translations/en.json`**

English translation file — exact copy of `strings.json`:

```bash
cp custom_components/update_blocklist/strings.json custom_components/update_blocklist/translations/en.json
```

- [ ] **Step 3: Create `translations/de.json`**

```json
{
  "title": "Update-Sperrliste",
  "config": {
    "step": {
      "user": {
        "title": "Update-Sperrliste hinzufügen",
        "description": "Diese Integration sperrt dauerhaft Firmware-Updates für ausgewählte Geräte."
      }
    },
    "abort": {
      "single_instance_allowed": "Bereits eingerichtet. Es ist nur eine Instanz der Update-Sperrliste erlaubt."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Scan-Fenster",
        "description": "In diesem nächtlichen Zeitfenster aktiviert die Integration blockierte Update-Entitäten kurz, um die zuletzt bekannte Version zu erfassen, und deaktiviert sie anschließend wieder.",
        "data": {
          "scan_start_time": "Scan-Startzeit (HH:MM, 24h)",
          "scan_max_duration_minutes": "Maximale Scan-Dauer (Minuten)",
          "per_device_timeout_seconds": "Timeout pro Gerät (Sekunden)"
        }
      }
    },
    "error": {
      "invalid_time": "Zeit muss im Format HH:MM (24h) sein.",
      "invalid_duration": "Dauer muss mindestens 1 Minute betragen.",
      "invalid_timeout": "Timeout muss mindestens 10 Sekunden betragen."
    }
  },
  "services": {
    "block": {
      "name": "Geräte-Updates sperren",
      "description": "Sperrt dauerhaft Updates für ein Gerät.",
      "fields": {
        "device_id": {
          "name": "Gerät",
          "description": "Die Geräte-ID von Home Assistant."
        },
        "reason": {
          "name": "Grund",
          "description": "Freitext-Notiz, warum dieses Gerät gesperrt ist."
        }
      }
    },
    "unblock": {
      "name": "Sperre entfernen",
      "description": "Entfernt eine zuvor gesetzte Sperre.",
      "fields": {
        "block_id": {
          "name": "Sperr-ID",
          "description": "Interne Sperr-ID."
        }
      }
    },
    "scan_now": {
      "name": "Einzelne Sperre scannen",
      "description": "Aktualisiert die Schatten-Version für eine Sperre sofort."
    },
    "scan_all": {
      "name": "Alle Sperren scannen",
      "description": "Führt einen vollständigen Scan-Zyklus für alle Sperren sofort aus."
    }
  }
}
```

- [ ] **Step 4: Verify translation files are valid JSON**

```bash
python3 -m json.tool custom_components/update_blocklist/strings.json > /dev/null
python3 -m json.tool custom_components/update_blocklist/translations/en.json > /dev/null
python3 -m json.tool custom_components/update_blocklist/translations/de.json > /dev/null
```

Expected: no output, exit code 0 for each.

- [ ] **Step 5: Commit**

```bash
git add custom_components/update_blocklist/strings.json custom_components/update_blocklist/translations/
git commit -m "Add strings.json and English + German translations"
```

---

## Phase 13: CI Workflows

### Task 43: Hassfest + HACS validation workflow

**Files:**
- Create: `.github/workflows/validate.yml`

- [ ] **Step 1: Create `.github/workflows/validate.yml`**

```yaml
name: Validate

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 3 * * *"

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run hassfest
        uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: HACS Action
        uses: hacs/action@main
        with:
          category: integration
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "Add hassfest and HACS validation workflow"
```

---

### Task 44: Backend + frontend test workflow

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Create `.github/workflows/test.yml`**

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements_test.txt
      - name: Install dependencies
        run: pip install -r requirements_test.txt
      - name: Ruff lint
        run: ruff check .
      - name: Pytest
        run: pytest -v

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install
        run: npm ci
      - name: Lint
        run: npm run lint
      - name: Test
        run: npm test
      - name: Build
        run: npm run build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "Add Python + frontend test workflow"
```

---

### Task 45: Release workflow — tag → zip → GitHub release

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create `.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Build frontend
        run: |
          cd frontend
          npm ci
          npm run build
      - name: Zip integration
        run: |
          cd custom_components/update_blocklist
          zip -r /tmp/update_blocklist.zip .
      - name: Create GitHub release
        uses: softprops/action-gh-release@v2
        with:
          files: /tmp/update_blocklist.zip
          generate_release_notes: true
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Add release workflow: build frontend, zip, publish release"
```

---

## Phase 14: Release-Readiness Documentation

### Task 46: Flesh out README, manual test plan, issue templates, brand placeholders

**Files:**
- Modify: `README.md`
- Create: `docs/manual-test-plan.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `brands/icon.png` (placeholder)
- Create: `brands/logo.png` (placeholder)

- [ ] **Step 1: Replace `README.md` with full version**

```markdown
# Update Blocklist

Permanently block firmware updates for specific Home Assistant devices.

Useful when a device's firmware must not change:
- custom Chinese WLED boards that brick on stock firmware
- Zigbee coordinators running patched firmware
- devices with known-broken upgrade paths

Home Assistant's "Skip" button is per-version, not permanent. This integration
provides a persistent block list that survives restarts, re-pairs, and
integration reloads.

## How it works

When a device is blocked, its `update.*` entity is disabled via the entity
registry — no notifications, no install button, no install service call
succeeds. A shadow sensor exposes the last-known `latest_version`, refreshed
during a configurable nightly scan window by briefly re-enabling and
re-disabling the entity.

## Installation

### HACS (custom repo — until accepted to the default store)

1. Open HACS → Integrations → three-dot menu → Custom repositories
2. Add `https://github.com/Basti-Fantasti/hacs-permanent-disable-dev-update`, category `Integration`
3. Install "Update Blocklist" → Restart Home Assistant
4. Settings → Devices & Services → Add Integration → "Update Blocklist"

### Manual

1. Copy `custom_components/update_blocklist/` into your HA config's `custom_components/` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## First-time setup

Click Add Integration → Update Blocklist. No inputs needed — defaults apply.
Open the "Update Blocklist" entry in the HA sidebar to manage blocks.

## Scan window

Defaults: scan starts at `01:00`, runs for up to 30 minutes, per-device timeout
300 seconds. During the window, blocked entities are briefly re-enabled so HA
can refresh the latest-version information, then re-disabled.

Edit these in Settings → Devices & Services → Update Blocklist → Configure.

## Services

| Service | Description |
|---|---|
| `update_blocklist.block` | Block a device. Fields: `device_id`, `reason` (optional). |
| `update_blocklist.unblock` | Remove a block by `block_id`. |
| `update_blocklist.scan_now` | Refresh a single block's shadow version. Field: `block_id`. |
| `update_blocklist.scan_all` | Run a full scan cycle across all blocks. |

## Entities

**Per block:**
- `sensor.<device>_blocked_update_status` — last known latest version
- `binary_sensor.<device>_update_blocked` — on while block is active (diagnostic)
- `button.<device>_scan_now` — one-shot rescan

**Integration-level:**
- `sensor.update_blocklist_blocked_count`
- `sensor.update_blocklist_last_scan_run`
- `sensor.update_blocklist_next_scan_at`
- `button.update_blocklist_scan_all`

## Limitations

- During the scan window, a brief update notification may appear for a device
  if a new version was detected between re-enable and re-disable.
- If you re-pair a blocked device, the integration will detect it by unique_id
  or fingerprint and prompt you to re-apply the block.
- Only device firmware updates are blockable. HACS / HA Core / HA OS / add-on
  updates are out of scope.

## Development

Backend tests:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm test
```

## Translations

English and German ship with the integration. To contribute a new language,
copy `custom_components/update_blocklist/translations/en.json` to
`translations/<code>.json` and translate the strings. Open a pull request.

## License

MIT. See `LICENSE`.
```

- [ ] **Step 2: Create `docs/manual-test-plan.md`**

```markdown
# Manual Test Plan

Run these checks before each release — they cover scenarios hard to automate credibly.

## Install and first-time setup

- [ ] Add the repo as a HACS custom repository.
- [ ] Install the integration, restart HA.
- [ ] Add integration via Settings → Devices & Services.
- [ ] The "Update Blocklist" panel appears in the HA sidebar.
- [ ] No errors in the HA log at setup.

## Block a real device

- [ ] In the panel, click "Add block", pick a real device that has an `update.*` entity.
- [ ] Confirm the update entity is disabled (visible in entity settings).
- [ ] Confirm notification badges for that device's update are gone.
- [ ] Confirm the shadow sensor appears with `last_known_version`.

## Nightly scan

- [ ] Temporarily set scan start time to 1 minute from now via options flow.
- [ ] Wait for the scan window. Confirm the shadow sensor's `last_known_version`
      is updated (trigger an update becoming available on the real device first,
      or manually set a new `latest_version` via dev tools).
- [ ] After scan, confirm the update entity is re-disabled.

## Unblock

- [ ] Remove the block from the panel.
- [ ] Confirm the update entity is re-enabled.
- [ ] Confirm HA's normal update behavior returns.

## Uninstall

- [ ] Delete the integration via HA UI.
- [ ] Confirm all previously-disabled update entities are re-enabled.
- [ ] Confirm the panel is gone from the sidebar.
- [ ] Confirm no `update_blocklist` entities remain in the entity registry.

## Re-pair detection

- [ ] Block a Zigbee device.
- [ ] Re-pair the device in Zigbee2MQTT / ZHA (creates a new device_id).
- [ ] Confirm the panel shows a rediscovery prompt.
- [ ] Click "Re-apply to this device" and confirm the new entity is disabled.
```

- [ ] **Step 3: Create `.github/ISSUE_TEMPLATE/bug_report.yml`**

```yaml
name: Bug report
description: Report a bug in the Update Blocklist integration.
labels: [bug]
body:
  - type: textarea
    attributes:
      label: What happened
      description: Describe the problem.
    validations:
      required: true
  - type: textarea
    attributes:
      label: Steps to reproduce
    validations:
      required: true
  - type: input
    attributes:
      label: Home Assistant version
    validations:
      required: true
  - type: input
    attributes:
      label: Update Blocklist version
    validations:
      required: true
  - type: textarea
    attributes:
      label: Relevant log output
      render: shell
```

- [ ] **Step 4: Create `.github/ISSUE_TEMPLATE/feature_request.yml`**

```yaml
name: Feature request
description: Suggest an improvement.
labels: [enhancement]
body:
  - type: textarea
    attributes:
      label: Problem / motivation
    validations:
      required: true
  - type: textarea
    attributes:
      label: Proposed solution
    validations:
      required: true
```

- [ ] **Step 5: Create placeholder brand PNGs**

Generate two 256×256 PNG placeholders (solid blue with the text "UBL") using Python:

```bash
python3 - <<'PY'
from pathlib import Path
Path("brands").mkdir(exist_ok=True)

# Tiny Python-only solid-color PNGs without Pillow dependency:
# Use a pre-built 1x1 blue PNG scaled by the browser / HACS UI as fallback.
# This is a placeholder — real branding replaces these before release.
import base64
png_bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)
(Path("brands") / "icon.png").write_bytes(png_bytes)
(Path("brands") / "logo.png").write_bytes(png_bytes)
print("Wrote placeholder brand PNGs.")
PY
```

Note: these are 1×1 placeholders. Replace with proper 256×256 assets before HACS default-store submission and before opening the `home-assistant/brands` PR.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/manual-test-plan.md .github/ISSUE_TEMPLATE/ brands/
git commit -m "Add full README, manual test plan, issue templates, placeholder brands"
```

---

## Final Verification

After all 46 tasks complete, run the full suite and confirm green:

- [ ] **Run full backend tests**

```bash
source .venv/bin/activate
pytest -v
```

Expected: all tests PASS.

- [ ] **Run full frontend tests + build**

```bash
cd frontend
npm test
npm run build
cd ..
```

Expected: all tests PASS, `custom_components/update_blocklist/www/panel.js` built.

- [ ] **Lint clean**

```bash
ruff check .
cd frontend && npm run lint && cd ..
```

Expected: no errors.

- [ ] **Run hassfest locally (optional, CI also runs it)**

```bash
docker run --rm -v "$(pwd)":/github/workspace ghcr.io/home-assistant/hassfest:latest \
  --action validate --integration-path /github/workspace/custom_components/update_blocklist
```

Expected: exits 0.

- [ ] **Verify the manifest and hacs.json**

```bash
python3 -m json.tool custom_components/update_blocklist/manifest.json > /dev/null
python3 -m json.tool hacs.json > /dev/null
```

- [ ] **Push to GitHub** (once the remote is ready):

```bash
git remote add origin github-private:Basti-Fantasti/hacs-permanent-disable-dev-update.git
git push -u origin main
```

- [ ] **Release-readiness checklist** (tracked in the design doc §11, re-check here):
  - Public repo created, description set, issues enabled, topics set
  - At least one full GitHub release (push a tag `v0.1.0` once the plan is complete)
  - `hassfest` + `hacs/action` green in CI
  - Real branding PNGs replaced and submitted to `home-assistant/brands`
  - README screenshots added

---
