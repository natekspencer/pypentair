"""Test that requests keep device identifiers out of logs and errors."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
import requests

from pypentair import Pentair
from pypentair.utils import REDACTED

DEVICE_ID = "PNRA5SSS100089E0D6"
URL = f"https://api.pentair.cloud/device/device-service/user/device/{DEVICE_ID}"


def _response(status_code: int, body: str) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.reason = "Reason"
    response.url = URL
    response._content = body.encode()
    return response


@pytest.fixture
def pentair() -> Iterator[Pentair]:
    """Return a client that skips AWS authentication."""
    client = Pentair(username="user@example.com")
    with patch.object(Pentair, "get_auth", return_value=MagicMock()):
        yield client


def test_get_device_redacts_device_id_in_logs(
    pentair: Pentair, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the device ID is used in the request but not logged."""
    body = f'{{"data": {{"deviceId": "{DEVICE_ID}", "fields": {{}}}}}}'
    with (
        caplog.at_level(logging.DEBUG, logger="pypentair"),
        patch("requests.request", return_value=_response(200, body)) as request,
    ):
        data = pentair.get_device(DEVICE_ID)

    assert request.call_args.args[1] == URL
    assert data["data"]["deviceId"] == DEVICE_ID
    assert DEVICE_ID not in caplog.text
    assert f"user/device/{REDACTED}" in caplog.text


def test_http_error_redacts_device_id(
    pentair: Pentair, caplog: pytest.LogCaptureFixture
) -> None:
    """Test an HTTP error keeps its type and response but not the device ID."""
    body = f'{{"message": "Unauthorized", "deviceId": "{DEVICE_ID}"}}'
    with (
        caplog.at_level(logging.DEBUG, logger="pypentair"),
        patch("requests.request", return_value=_response(401, body)),
        pytest.raises(requests.HTTPError) as exc_info,
    ):
        pentair.get_device(DEVICE_ID)

    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 401
    assert DEVICE_ID not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert DEVICE_ID not in caplog.text


def test_non_json_error_body_raises_http_error(pentair: Pentair) -> None:
    """Test an error response without a JSON body still raises an HTTP error."""
    with (
        patch("requests.request", return_value=_response(502, "<html>Bad</html>")),
        pytest.raises(requests.HTTPError) as exc_info,
    ):
        pentair.get_device(DEVICE_ID)

    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 502


def test_connection_error_redacts_device_id(pentair: Pentair) -> None:
    """Test a connection error keeps its type but not the device ID."""
    error = requests.ConnectionError(
        f"Max retries exceeded with url: /device/device-service/user/device/{DEVICE_ID}"
    )
    with (
        patch("requests.request", side_effect=error),
        pytest.raises(requests.ConnectionError) as exc_info,
    ):
        pentair.get_device(DEVICE_ID)

    assert DEVICE_ID not in str(exc_info.value)
    assert REDACTED in str(exc_info.value)


def test_error_without_device_id_is_unchanged(pentair: Pentair) -> None:
    """Test errors that don't mention a device ID are raised as is."""
    error = requests.Timeout("Read timed out")
    with (
        patch("requests.request", side_effect=error),
        pytest.raises(requests.Timeout) as exc_info,
    ):
        pentair.get_devices()

    assert exc_info.value is error


def test_non_json_error_body_redacts_device_id(
    pentair: Pentair, caplog: pytest.LogCaptureFixture
) -> None:
    """Test a non-JSON error body is logged by type and size only."""
    other_device_id = "PNRA5IF3100000"
    body = f"<html>Devices {DEVICE_ID}, {other_device_id}</html>"
    response = _response(500, body)
    response.headers["Content-Type"] = "text/html"
    with (
        caplog.at_level(logging.DEBUG, logger="pypentair"),
        patch("requests.request", return_value=response),
        pytest.raises(requests.HTTPError),
    ):
        pentair.get_devices()

    assert DEVICE_ID not in caplog.text
    assert other_device_id not in caplog.text
    assert f"{REDACTED} (text/html, {len(body)} bytes)" in caplog.text


def test_non_json_success_body_raises_decode_error(pentair: Pentair) -> None:
    """Test a successful response without a JSON body is not returned as text."""
    with (
        patch("requests.request", return_value=_response(200, "<html>OK</html>")),
        pytest.raises(requests.JSONDecodeError),
    ):
        pentair.get_device(DEVICE_ID)


def test_error_redacts_percent_encoded_device_id(pentair: Pentair) -> None:
    """Test a device ID is redacted where it appears percent-encoded in a URL."""
    device_id = "Pool Pump"
    error = requests.ConnectionError(
        "Max retries exceeded with url: /device/device-service/user/device/Pool%20Pump"
    )
    with (
        patch("requests.request", side_effect=error),
        pytest.raises(requests.ConnectionError) as exc_info,
    ):
        pentair.get_device(device_id)

    assert "Pool%20Pump" not in str(exc_info.value)
    assert REDACTED in str(exc_info.value)
