"""Test Pentair devices."""

from __future__ import annotations

from .common import SALT_SENSOR


def test_salt_sensor() -> None:
    """Test salt sensor."""
    assert isinstance(SALT_SENSOR, dict)
