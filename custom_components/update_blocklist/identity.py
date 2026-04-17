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
