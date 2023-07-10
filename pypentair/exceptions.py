"""Exceptions."""


class PentairApiException(Exception):
    """General Pentair API exception."""


class PentairAuthenticationError(PentairApiException):
    """To indicate there is an issue authenticating."""
