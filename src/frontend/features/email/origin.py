"""Validate the configured origin used in bearer-token email links."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_DEV_ORIGIN = "http://localhost:8000"
_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def canonical_email_origin(value: str, *, allow_local_http: bool = False) -> str:
    """Use trusted configuration only, never request Host or forwarded headers."""
    if not value and allow_local_http:
        return _DEV_ORIGIN
    if not value or any(char.isspace() or ord(char) < 32 for char in value) or "\\" in value:
        raise ValueError("SITE_BASE_URL must be a canonical HTTPS origin for email links")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("SITE_BASE_URL has an invalid email origin") from exc
    if (
        not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.netloc.endswith(":")
        or "%" in hostname
    ):
        raise ValueError("SITE_BASE_URL must contain only an origin, without credentials, path, query or fragment")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            host = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("SITE_BASE_URL has an invalid hostname") from exc
        if len(host) > 253 or not all(_HOST_LABEL.fullmatch(label) for label in host.split(".")):
            raise ValueError("SITE_BASE_URL has an invalid hostname") from None
        is_loopback = host == "localhost" or host.endswith(".localhost")
    else:
        host = f"[{address}]" if address.version == 6 else str(address)
        is_loopback = address.is_loopback
    if parsed.scheme != "https" and not (parsed.scheme == "http" and allow_local_http and is_loopback):
        raise ValueError("SITE_BASE_URL must use HTTPS; HTTP is allowed only for local development")
    authority = f"{host}:{port}" if port is not None else host
    return f"{parsed.scheme}://{authority}"
