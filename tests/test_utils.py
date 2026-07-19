"""Test utilities."""

from __future__ import annotations

from datetime import datetime
from typing import cast

import pytest

from pypentair.utils import REDACTED, get_api_field_name_and_value, redact

from .common import INTELLIFLO_SENSOR


def test_redact() -> None:
    """Test redact util method."""
    test_dict = {"email": "some_email"}
    assert redact(test_dict) == {"email": REDACTED}


@pytest.mark.parametrize(
    "key,name,value",
    [
        ("s1", "Device time", datetime(2024, 4, 17, 16, 23, 0)),
        ("s6", "Wifi mac address", "1C5A0840C400"),
        ("s18", "Current power", 183),
        ("s19", "Current motor speed", 43.2),
        ("s25", "Pump enabled status", True),
        ("s26", "Current estimated flow", 38.0),
    ],
)
def test_field_mapping(key: str, name: str, value: str | float | datetime) -> None:
    """Test field name/value mapping."""
    fields = cast(dict, INTELLIFLO_SENSOR["fields"])
    assert get_api_field_name_and_value(key, fields[key]) == (name, value)


def test_field_mapping_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test field name/value mapping logs an appropriate error."""
    key = "s1"
    val = "00"
    name, value = get_api_field_name_and_value(key, val)
    assert name == "Device time"
    assert value == val
    assert (
        "Could not convert key 's1 (Device time)' value '00': time data '00' does not match format '%y%m%d%H%M%S'"
        in caplog.messages
    )


@pytest.mark.parametrize(
    "key,name,value",
    [
        ("s1", "Device time", datetime(2026, 6, 8, 8, 26, 0)),
        ("s13", "RSSI", -74),
        ("s17", "Current pressure", 74.4),
        ("s18", "Current power", 221),
        ("s19", "Current motor speed", 50.0),
        ("s26", "Current estimated flow", 27.0),
        ("s2", "Finished good serial number", "serial"),
    ],
)
def test_field_mapping_structured_payload(
    key: str, name: str, value: str | int | float | datetime
) -> None:
    """Test field mapping with the newer structured (dict-wrapped) payload."""
    raw_values = {
        "s1": "260608082600",
        "s13": "-74",
        "s17": "744",
        "s18": "221",
        "s19": "500",
        "s26": "270",
        "s2": "serial",
    }
    wrapped = {
        "name": "whatever",
        "min": "NA",
        "max": "NA",
        "unit": "unit",
        "type": "STR",
        "category": "status",
        "cloud": False,
        "visible": True,
        "home": False,
        "value": raw_values[key],
        "timestamp": "1780921579",
        "delivered": "1780921580034",
    }
    assert get_api_field_name_and_value(key, wrapped) == (name, value)
