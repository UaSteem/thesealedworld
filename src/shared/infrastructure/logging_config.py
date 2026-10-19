import logging
import os
import re
import socket
import sys
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from codex_core.common.log_context import get_log_context
from codex_core.common.loguru_setup import InterceptHandler
from codex_core.common.loguru_setup import setup_logging as codex_setup_logging
from codex_core.settings import BaseCommonSettings
from loguru import logger

if TYPE_CHECKING:
    from loguru import Record

WARNING = 30

DEFAULT_NOISY_LOG_LEVELS: dict[str, int] = {
    "asyncio": WARNING,
    "hpack": WARNING,
    "httpcore": WARNING,
    "httpcore._trace": WARNING,
    "httpx": WARNING,
    "python_multipart": WARNING,
    "python_multipart.multipart": WARNING,
}

_PRIVATE_FIELDS = re.compile(
    r"(?:password|secret|token|authorization|cookie|email|recipient|subject|body|payload|"
    r"headers|credential|smtp|exception|detail|error$|error_message|response|"
    r"url|uri|query|dsn|bearer|^path$|^to$)",
    re.I,
)
_EVENT_NAME = re.compile(r"[A-Z][A-Za-z0-9]*\Z")


def _safe_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Remove known private field families; producers must still use safe metadata."""
    result: dict[str, Any] = {}
    for name, value in fields.items():
        if _PRIVATE_FIELDS.search(name):
            continue
        if isinstance(value, dict):
            result[name] = _safe_fields(value)
        elif value is None or isinstance(value, (str, int, float, bool)):
            result[name] = value
        else:
            # Never serialize arbitrary objects whose repr may contain credentials.
            result[name] = type(value).__name__
    return result


def _production_patcher(service_name: str) -> Callable[["Record"], None]:
    def patch(record: "Record") -> None:
        extra = _safe_fields({**record["extra"], **get_log_context()})
        extra["service"] = service_name
        exception = record["exception"]
        if exception:
            extra["error_type"] = exception.type.__name__ if exception.type else "Exception"
            extra["error_trace"] = [
                {"file": frame.f_code.co_filename, "line": line, "function": frame.f_code.co_name}
                for frame, line in traceback.walk_tb(exception.traceback)
            ]
            # diagnose=False alone still emits exception values, chains and source lines.
            record["exception"] = None
        if not _EVENT_NAME.fullmatch(record["message"]):
            record["message"] = "ExternalLogMessage"
        record["extra"] = extra

    return patch


def _setup_production_logging(settings: BaseCommonSettings, service_name: str, intercepted: list[str]) -> None:
    logger.remove()
    logger.configure(patcher=_production_patcher(service_name))
    logger.add(
        sys.stdout,
        level=getattr(settings, "log_level_console", "INFO"),
        serialize=True,
        colorize=False,
        filter=lambda record: not record["extra"].get("healthcheck", False),
        backtrace=False,
        diagnose=False,
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in intercepted:
        logging.getLogger(name).handlers = [InterceptHandler()]


def _runtime_instance_name() -> str | None:
    for env_name in ("CONTAINER_NAME", "HOSTNAME", "COMPUTERNAME"):
        value = os.getenv(env_name, "").strip()
        if value:
            return value

    hostname = socket.gethostname().strip()
    return hostname or None


def _service_name_with_runtime_instance(service_name: str, include_runtime_instance: bool) -> str:
    if not include_runtime_instance:
        return service_name

    instance_name = _runtime_instance_name()
    if not instance_name or instance_name == service_name:
        return service_name

    return f"{service_name}@{instance_name}"


def setup_logging(
    settings: BaseCommonSettings,
    service_name: str,
    intercept_loggers: list[str] | None = None,
    log_levels: dict[str, int] | None = None,
    include_runtime_instance: bool = False,
) -> None:
    """Configure Loguru via codex_core for any service (backend, frontend, workers)."""
    effective_log_levels = {**DEFAULT_NOISY_LOG_LEVELS, **(log_levels or {})}
    runtime_name = _service_name_with_runtime_instance(service_name, include_runtime_instance)
    if getattr(settings, "debug", True):
        codex_setup_logging(
            settings=settings,  # type: ignore[arg-type]
            service_name=runtime_name,
            intercept_loggers=intercept_loggers or [],
            log_levels=effective_log_levels,
        )
    else:
        _setup_production_logging(settings, runtime_name, intercept_loggers or [])
        for name, level in effective_log_levels.items():
            logging.getLogger(name).setLevel(level)

    # Prevent duplicates: codex_core installs InterceptHandler on both the
    # root logger (via basicConfig) and each named logger.  Without
    # propagate=False the message is caught by the named handler AND
    # bubbles up to root — producing two identical log lines.
    if intercept_loggers:
        for name in intercept_loggers:
            logging.getLogger(name).propagate = False
