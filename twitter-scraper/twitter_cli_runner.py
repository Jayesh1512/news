"""Standalone twitter-cli entrypoint with the X /home bootstrap fix."""

from __future__ import annotations

import os
from typing import Any


class XHomeBootstrapSession:
    def __init__(self, session: Any):
        self._session = session

    def get(self, url: str, *args: Any, **kwargs: Any):
        if url in {"https://x.com", "https://x.com/"}:
            url = "https://x.com/home"
            auth_token = os.getenv("TWITTER_AUTH_TOKEN", "")
            ct0 = os.getenv("TWITTER_CT0", "")
            if auth_token and ct0:
                headers = dict(kwargs.get("headers") or {})
                headers["Cookie"] = f"auth_token={auth_token}; ct0={ct0}"
                kwargs["headers"] = headers
        return self._session.get(url, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


def install_x_home_bootstrap_patch() -> None:
    from twitter_cli import client as twitter_client

    current_factory = twitter_client._get_cffi_session
    if getattr(current_factory, "_news_x_home_patch", False):
        return

    def patched_factory():
        session = current_factory()
        if isinstance(session, XHomeBootstrapSession):
            return session
        return XHomeBootstrapSession(session)

    patched_factory._news_x_home_patch = True  # type: ignore[attr-defined]
    twitter_client._get_cffi_session = patched_factory


def main() -> None:
    install_x_home_bootstrap_patch()
    from twitter_cli.cli import cli

    cli(prog_name="twitter")


if __name__ == "__main__":
    main()
