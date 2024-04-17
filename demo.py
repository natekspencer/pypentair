"""Demo."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

from deepdiff import DeepDiff
from dotenv import set_key

from pypentair import Pentair, PentairAuthenticationError

logging.basicConfig(level=logging.DEBUG)

ENV_PATH = Path(".env")

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ID_TOKEN = os.getenv("ID_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")


async def main(keep_alive: bool = False) -> None:
    """Run main function."""
    use_token = all((ACCESS_TOKEN, ID_TOKEN, REFRESH_TOKEN))
    try:
        account = token_login() if use_token else password_login()
    except Exception as ex:  # pylint: disable=broad-except
        print(ex)
        return

    for key, value in account.get_tokens().items():
        set_key(ENV_PATH, key.upper(), value)

    devices = {}

    while True:
        try:
            _devices = account.get_devices()
            diff = DeepDiff(
                devices,
                _devices,
                ignore_order=True,
                report_repetition=True,
                verbose_level=2,
            )
            logging.debug(diff if diff else "No changes")
            devices = _devices
        except Exception as ex:  # pylint: disable=broad-except
            logging.error(ex)
        if not keep_alive:
            break
        await asyncio.sleep(30)

    for key, value in account.get_tokens().items():
        set_key(ENV_PATH, key.upper(), value)


def password_login() -> Pentair:
    """Login using username/password."""
    if not (username := USERNAME):
        username = input("Enter username: ")
    if not (password := PASSWORD):
        password = input("Enter password: ")
    account = Pentair(username=username)
    account.authenticate(password=password)
    return account


def token_login() -> Pentair:
    """Login using tokens."""
    account = Pentair(
        access_token=ACCESS_TOKEN, id_token=ID_TOKEN, refresh_token=REFRESH_TOKEN
    )
    try:
        account.get_user()
    except PentairAuthenticationError:
        return password_login()
    return account


parser = argparse.ArgumentParser(description="Login to Pentair Home and list devices.")
parser.add_argument(
    "-ka",
    "--keep-alive",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="If true, run indefinitely while polling every 30 seconds.",
)
args = parser.parse_args()

if __name__ == "__main__":
    asyncio.run(main(args.keep_alive))
