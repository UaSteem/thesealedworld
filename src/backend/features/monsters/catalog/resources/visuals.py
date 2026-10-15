from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

GENERATED_ASSET_URL_MARKER = "/static/generated-assets/"
FAMILY_IMAGE_URLS = {
    family_id: f"/static/images/monsters/families/{family_id}.svg"
    for family_id in ("bandit_gang", "goblin_tribe", "rat_swarm", "wolf_pack")
}


def get_family_visual(family_id: str) -> dict[str, object]:
    image_url = FAMILY_IMAGE_URLS.get(family_id, "")
    return {
        "status": "placeholder" if image_url else "missing",
        "source": "family_default" if image_url else "none",
        "image_url": image_url,
        "placeholder_image_url": image_url,
    }


def build_clan_visual(
    family_id: str,
    *,
    clan_name: str,
    description: str,
    context_tags: list[str],
    member_roster: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    # Prepared content supplies images; narrative does not create an API request.
    visual = get_family_visual(family_id)
    visual["scope"] = "monster_clan"
    return visual


def build_member_visual(
    family_id: str,
    *,
    variant_key: str,
    role: str,
    member_name: str,
    appearance: str,
    visual_hint: str = "",
    context_tags: list[str] | None = None,
    clan_name: str = "",
) -> dict[str, object]:
    visual = get_family_visual(family_id)
    visual["scope"] = "monster_member_template"
    visual["variant_key"] = variant_key
    return visual


def version_generated_asset_url(url: str | None, visual: dict[str, Any] | None = None) -> str | None:
    canonical_url = _canonical_generated_asset_url(url)
    if not canonical_url or GENERATED_ASSET_URL_MARKER not in canonical_url:
        return canonical_url
    version = _visual_cache_version(canonical_url, visual or {})
    if not version:
        return canonical_url
    return _with_query_param(canonical_url, "v", version)


def version_visual_image_urls(visual: dict[str, Any]) -> dict[str, Any]:
    versioned = dict(visual)
    for key in ("image_url", "generated_image_url", "placeholder_image_url", "previous_image_url"):
        value = versioned.get(key)
        if isinstance(value, str) and value:
            versioned[key] = version_generated_asset_url(value, versioned)
    return versioned


def _visual_cache_version(url: str, visual: dict[str, Any]) -> str:
    if url == visual.get("previous_image_url"):
        previous_hash = str(visual.get("previous_asset_hash") or "")
        if previous_hash:
            return previous_hash
    for key in ("asset_hash", "content_hash", "image_hash"):
        value = str(visual.get(key) or "")
        if value:
            return value
    size_bytes = visual.get("size_bytes")
    if size_bytes:
        return f"size-{size_bytes}"
    return ""


def _with_query_param(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    query = [(name, item) for name, item in parse_qsl(parts.query, keep_blank_values=True) if name != key]
    query.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _canonical_generated_asset_url(url: str | None) -> str | None:
    if not url:
        return url
    parts = urlsplit(url)
    if GENERATED_ASSET_URL_MARKER not in parts.path:
        return url
    return urlunsplit(("", "", parts.path, parts.query, parts.fragment))
