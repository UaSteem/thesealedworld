"""Bounded HTTP telemetry context without request URLs or path parameter values."""

from starlette.requests import Request

UNMATCHED_ROUTE = "<unmatched>"
_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"})


def safe_route_template(request: Request) -> str:
    """Use only the registered route after routing; never fall back to the raw URL.

    Before routing and for unmatched requests, a single bounded value is used.
    """
    route = getattr(request, "scope", {}).get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else UNMATCHED_ROUTE


def safe_http_method(request: Request) -> str:
    method = request.method.upper()
    return method if method in _HTTP_METHODS else "OTHER"
