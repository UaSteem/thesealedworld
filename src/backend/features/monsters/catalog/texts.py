"""Localized authored prose. Add locale keys in resources; mechanics never depend on language."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_LOCALE = "ru"


@dataclass(frozen=True, slots=True)
class MonsterTextDTO:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class ResolvedMonsterText:
    name: str
    description: str
    locale: str
    requested_locale: str
    fallback: bool


def normalize_locale(locale: str) -> str:
    return locale.strip().lower().replace("_", "-") or DEFAULT_LOCALE


def resolve_text(
    text_id: str, locale: str = DEFAULT_LOCALE, *, resources: Mapping | None = None
) -> ResolvedMonsterText:
    if resources is None:
        from .resources.texts import MONSTER_TEXTS

        resources = MONSTER_TEXTS
    if text_id not in resources:
        raise ValueError(f"Unknown monster text: {text_id}")
    translations = resources[text_id]
    if DEFAULT_LOCALE not in translations:
        raise ValueError(f"Missing default monster text: {text_id}")
    requested = normalize_locale(locale)
    candidates = dict.fromkeys((requested, requested.split("-")[0], DEFAULT_LOCALE))
    for candidate in candidates:
        if candidate in translations:
            text = translations[candidate]
            return ResolvedMonsterText(text.name, text.description, candidate, requested, candidate != requested)
    raise ValueError(f"Missing default monster text: {text_id}")


def localized_definition(value, locale: str = DEFAULT_LOCALE) -> dict:
    if not value.text_id:
        return dict(
            name=value.name,
            description=value.description,
            text_locale=DEFAULT_LOCALE,
            text_fallback=normalize_locale(locale) != DEFAULT_LOCALE,
        )
    text = resolve_text(value.text_id, locale)
    return dict(name=text.name, description=text.description, text_locale=text.locale, text_fallback=text.fallback)
