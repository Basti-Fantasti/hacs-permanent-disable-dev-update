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
    a = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED Custom")
    b = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED Custom")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_case_insensitive_name():
    a = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED CUSTOM")
    b = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="wled custom")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_requires_manufacturer_and_model():
    a = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="X")
    b = generate_fingerprint(manufacturer="Shelly", model="ESP8266", name="X")
    assert fingerprint_matches(a, b) is False


def test_fingerprint_matches_tolerates_minor_name_differences():
    """Name differing by a trailing numeric suffix still matches if prefix is equal."""
    a = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED Strip")
    b = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED Strip 2")
    assert fingerprint_matches(a, b) is True


def test_fingerprint_matches_rejects_unrelated_names():
    a = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="WLED Strip")
    b = generate_fingerprint(manufacturer="Espressif", model="ESP8266", name="Completely Different")
    assert fingerprint_matches(a, b) is False
