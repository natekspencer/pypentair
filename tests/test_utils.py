"""Test utilities."""

from __future__ import annotations

from pypentair.utils import REDACTED, redact


def test_redact() -> None:
    """Test redact util method."""
    test_dict = {"email": "some_email"}
    assert redact(test_dict) == {"email": REDACTED}
