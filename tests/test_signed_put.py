"""Test signed requests and token refresh."""

from __future__ import annotations

import hashlib
import json
import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
import requests
from botocore.auth import SigV4Auth
from botocore.credentials import Credentials

from pypentair import Pentair
from pypentair.exceptions import PentairApiException

URL = "https://api.pentair.cloud/device/device-service/user/device/dev1"


def _token(expires_in: int) -> str:
    """Return an id token expiring in the given number of seconds."""
    return str(
        jwt.encode(
            {"exp": int(time.time()) + expires_in},
            "test-secret-key-for-unit-tests-only",
        )
    )


def _response(status: int, body: dict | str) -> requests.Response:
    """Return a response with the given status and a JSON or text body."""
    response = requests.Response()
    response.status_code = status
    response.reason = "Reason"
    response.url = URL
    content = body if isinstance(body, str) else json.dumps(body)
    response._content = content.encode()  # noqa: SLF001
    return response


@pytest.fixture
def pentair() -> Pentair:
    """Return a Pentair client with a mocked Cognito user and signer."""
    client = Pentair(refresh_token="refresh")
    user = MagicMock(id_token=_token(3600), access_token="a", refresh_token="r")
    client._user = user
    client.get_auth = MagicMock(  # type: ignore[method-assign]
        return_value=SigV4Auth(Credentials("k", "s", "t"), "execute-api", "us-west-2")
    )
    return client


def test_update_device_signs_body(pentair: Pentair) -> None:
    """Test the body is sent and covered by the signature."""
    ok = _response(200, {"data": {"code": "set_device_success"}})
    with patch("pypentair.pentair.requests.request", return_value=ok) as request:
        assert pentair.update_device("dev1", {"s14": "1"}) == {
            "data": {"code": "set_device_success"}
        }

    method, url = request.call_args.args
    kwargs = request.call_args.kwargs
    assert method == "put"
    assert url == URL
    assert json.loads(kwargs["data"]) == {"payload": {"s14": "1"}}
    assert "Authorization" in kwargs["headers"]
    pentair._user.renew_access_token.assert_not_called()  # type: ignore[union-attr]


def test_payload_hash_in_signature(pentair: Pentair) -> None:
    """Test the signed canonical request includes the body hash."""
    ok = _response(200, {"data": {"code": "set_device_success"}})
    auth = pentair.get_auth()
    with (
        patch.object(auth, "add_auth", wraps=auth.add_auth) as add_auth,
        patch("pypentair.pentair.requests.request", return_value=ok) as request,
    ):
        pentair.update_device("dev1", {"s14": "1"})
    signed = add_auth.call_args.args[0]
    sent = request.call_args.kwargs["data"]
    assert signed.body == sent
    assert auth.payload(signed) == hashlib.sha256(sent).hexdigest()


def test_update_device_unexpected_code(pentair: Pentair) -> None:
    """Test an unexpected response code raises."""
    bad = _response(200, {"data": {"code": "nope"}})
    with patch("pypentair.pentair.requests.request", return_value=bad):
        with pytest.raises(PentairApiException):
            pentair.update_device("dev1", {"s14": "1"})


def test_refresh_when_token_near_expiry(pentair: Pentair) -> None:
    """Test tokens are renewed before a request when close to expiry."""
    pentair._user.id_token = _token(60)  # type: ignore[union-attr]
    pentair._auth = MagicMock()
    ok = _response(200, {"data": []})
    with patch("pypentair.pentair.requests.request", return_value=ok):
        pentair.get_devices()
    pentair._user.renew_access_token.assert_called_once()  # type: ignore[union-attr]
    assert pentair._auth is None


def test_refresh_gets_new_credentials() -> None:
    """Test a refresh through get_auth replaces the signer credentials."""
    client = Pentair(refresh_token="refresh")
    client._user = MagicMock(
        check_token=MagicMock(return_value=False),
        id_token=_token(60),
        access_token="a",
        refresh_token="r",
    )
    client._auth = SigV4Auth(
        Credentials("old-access", "old-secret", "old-token"),
        "execute-api",
        "us-west-2",
    )
    identity_client = MagicMock()
    identity_client.get_id.return_value = {"IdentityId": "identity"}
    identity_client.get_credentials_for_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "new-access",
            "SecretKey": "new-secret",
            "SessionToken": "new-token",
        }
    }
    ok = _response(200, {"data": []})
    with (
        patch("pypentair.pentair.boto_client", return_value=identity_client),
        patch("pypentair.pentair.requests.request", return_value=ok),
    ):
        client.get_devices()

    identity_client.get_id.assert_called_once()
    identity_client.get_credentials_for_identity.assert_called_once()
    assert client._auth is not None
    assert client._auth.credentials.access_key == "new-access"
    assert client._auth.credentials.secret_key == "new-secret"
    assert client._auth.credentials.token == "new-token"


@pytest.mark.parametrize("status", [401, 403])
def test_retry_once_on_auth_error(pentair: Pentair, status: int) -> None:
    """Test a 401/403 refreshes tokens and retries once."""
    denied = _response(status, {"message": "denied"})
    ok = _response(200, {"data": {"code": "set_device_success"}})
    with patch(
        "pypentair.pentair.requests.request", side_effect=[denied, ok]
    ) as request:
        pentair.update_device("dev1", {"s14": "1"})
    assert request.call_count == 2
    pentair._user.renew_access_token.assert_called_once()  # type: ignore[union-attr]


def test_retry_only_once(pentair: Pentair) -> None:
    """Test a second auth error is raised instead of retried."""
    denied = _response(403, {"message": "denied"})
    with patch(
        "pypentair.pentair.requests.request", side_effect=[denied, denied]
    ) as request:
        with pytest.raises(requests.HTTPError):
            pentair.get_devices()
    assert request.call_count == 2
