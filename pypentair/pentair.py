"""Pentair account."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Final
from urllib.parse import urljoin

import requests
from boto3 import client as boto_client
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from botocore.exceptions import ClientError
from pycognito import Cognito

from .const import CLIENT_ID, IDENTITY_POOL_ID, REGION_NAME, USER_POOL_ID
from .exceptions import PentairAuthenticationError
from .utils import REDACTED, decode, redact

_LOGGER = logging.getLogger(__name__)

BASE_URL: Final = "https://api.pentair.cloud/"
DEVICE_PATH: Final = "device/device-service/user/device/{device_id}"
DEVICES_PATH: Final = "device/device-service/user/devices"


class Pentair:
    """Pentair account."""

    _user: Cognito | None = None
    _auth: SigV4Auth | None = None

    def __init__(
        self,
        *,
        username: str | None = None,
        access_token: str | None = None,
        id_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize."""
        self._username = username
        self._access_token = access_token
        self._id_token = id_token
        self._refresh_token = refresh_token

    @property
    def access_token(self) -> str | None:
        """Return the access token."""
        return self._user.access_token if self._user else self._access_token

    @property
    def id_token(self) -> str | None:
        """Return the id token."""
        return self._user.id_token if self._user else self._id_token

    @property
    def refresh_token(self) -> str | None:
        """Return the refresh token."""
        return self._user.refresh_token if self._user else self._refresh_token

    def get_user(self) -> Cognito:
        """Return the Cognito user."""
        if self._user is None:
            self._user = Cognito(
                decode(USER_POOL_ID),
                decode(CLIENT_ID),
                username=self._username,
                access_token=self.access_token,
                id_token=self.id_token,
                refresh_token=self.refresh_token,
            )
            if self.access_token or self.id_token:
                try:
                    self._user.check_token()
                    self._user.verify_tokens()
                except ClientError as err:
                    _LOGGER.error(err)
                    raise PentairAuthenticationError(err) from err
        return self._user

    def get_auth(self) -> SigV4Auth:
        """Return the SigV4Auth."""
        if self.get_user().check_token() or self._auth is None:
            client = boto_client("cognito-identity", region_name=REGION_NAME)
            logins = {
                f"cognito-idp.{REGION_NAME}.amazonaws.com/{decode(USER_POOL_ID)}": self.id_token
            }
            response = client.get_id(
                IdentityPoolId=decode(IDENTITY_POOL_ID), Logins=logins
            )
            response = client.get_credentials_for_identity(
                IdentityId=response["IdentityId"], Logins=logins
            )
            credentials = Credentials(
                response["Credentials"]["AccessKeyId"],
                response["Credentials"]["SecretKey"],
                response["Credentials"]["SessionToken"],
            )
            self._auth = SigV4Auth(credentials, "execute-api", REGION_NAME)
        return self._auth

    def get_tokens(self) -> dict[str, str]:
        """Return the tokens."""
        if (user := self.get_user()).access_token:
            return {
                "access_token": user.access_token,
                "id_token": user.id_token,
                "refresh_token": user.refresh_token,
            }
        return {}

    def authenticate(self, password: str) -> None:
        """Authenticate a user."""
        try:
            self.get_user().authenticate(password=password)
        except ClientError as err:
            _LOGGER.error(err)
            raise PentairAuthenticationError(err) from err

    def logout(self) -> None:
        """Logout of all clients (including app)."""
        self.get_user().logout()

    def get_device(self, device_id: str) -> Any:
        """Get device."""
        return self.__get(DEVICE_PATH, path_params={"device_id": device_id})

    def get_devices(self) -> Any:
        """Get devices."""
        return self.__get(DEVICES_PATH)

    def __request(
        self,
        method: str,
        path: str,
        *,
        path_params: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make a request.

        Values in `path_params` identify the account's devices, so they are
        filled into `path` for the request but kept out of logs and errors.
        """
        params = path_params or {}
        url = path.format(**params)
        log_url = path.format(**dict.fromkeys(params, REDACTED))
        _LOGGER.debug(
            "Making %s request to %s with %s", method, log_url, redact(kwargs)
        )

        request = AWSRequest(
            method=method,
            url=urljoin(BASE_URL, url),
            headers={"x-amz-id-token": self.id_token},
        )
        self.get_auth().add_auth(request)
        prepped = request.prepare()
        try:
            response = requests.request(
                method, prepped.url, headers=prepped.headers, timeout=10, **kwargs
            )
            try:
                json = response.json()
            except ValueError:
                json = response.text
            _LOGGER.debug(
                "Received %s response from %s: %s",
                response.status_code,
                log_url,
                redact(json),
            )
            if (status_code := response.status_code) != 200:
                _LOGGER.error("Status: %s - %s", status_code, redact(json))
                response.raise_for_status()
        except requests.RequestException as err:
            message = str(err)
            values = [value for value in params.values() if value in message]
            if not values:
                raise
            for value in values:
                message = message.replace(value, REDACTED)
            # Re-raised without the original, whose message includes the URL
            raise type(err)(
                message, request=err.request, response=err.response
            ) from None
        return json

    def __get(self, path: str, **kwargs: Any) -> Any:
        """Make a get request."""
        return self.__request("get", path, **kwargs)

    def __post(  # pylint: disable=unused-private-member
        self, path: str, **kwargs: Any
    ) -> Any:
        """Make a post request."""
        return self.__request("post", path, **kwargs)
