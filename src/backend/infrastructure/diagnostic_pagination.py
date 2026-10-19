"""Bounded diagnostic SCAN pages; cursors are best effort during concurrent key churn."""

from __future__ import annotations

from typing import Any


async def scan_key_page(client: Any, *, match: str, cursor: str, limit: int) -> tuple[list[Any], str | None]:
    """Do one SCAN and hydrate at most limit keys.

    COUNT is a hint. Replay the same input SCAN cursor with a batch offset when
    Redis returns an oversized batch. The caller should keep the same limit;
    concurrent key churn may cause duplicates or omissions, as with Redis SCAN.
    No snapshot or complete enumeration is promised by a single page.
    """
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("limit must be an integer between 1 and 500")
    redis_cursor, offset = parse_scan_cursor(cursor)
    next_cursor, keys = await client.scan(redis_cursor, match=match, count=limit)
    end = min(offset + limit, len(keys))
    page = keys[offset:end]
    if end < len(keys):
        return page, f"{redis_cursor}:{end}"
    continuation = f"{int(next_cursor)}:0" if int(next_cursor) else None
    return page, continuation


def parse_scan_cursor(cursor: str) -> tuple[int, int]:
    """Validate a diagnostic cursor before issuing Redis calls."""
    parts = cursor.split(":") if isinstance(cursor, str) else []
    if len(parts) != 2 or any(not part.isascii() or not part.isdecimal() or len(part) > 20 for part in parts):
        raise ValueError("cursor must be redis_cursor:offset")
    redis_cursor, offset = map(int, parts)
    if redis_cursor > 2**64 - 1 or offset > 2**63 - 1:
        raise ValueError("cursor is out of range")
    return redis_cursor, offset
