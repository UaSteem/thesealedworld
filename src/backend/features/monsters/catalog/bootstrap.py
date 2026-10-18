"""Build a deterministic public-text snapshot; no database or random selection."""

import hashlib
import json
from pathlib import PurePosixPath
from urllib.parse import quote

from src.backend.features.monsters.catalog.bootstrap_contracts import MonsterCatalogBootstrapDTO
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import get_catalog

from .resources import texts as text_resources
from .texts import DEFAULT_LOCALE, localized_definition, normalize_locale


def _hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class MonsterCatalogBootstrapService:
    def __init__(self, catalog: MonsterCatalog | None = None):
        self.catalog = catalog if catalog is not None else get_catalog()

    def build(self, *, include_system: bool = False, locale: str = DEFAULT_LOCALE) -> MonsterCatalogBootstrapDTO:
        locale = normalize_locale(locale)
        available_locales = sorted(
            {language for translations in text_resources.MONSTER_TEXTS.values() for language in translations}
        )
        clans = self.catalog.find_clans(include_system=include_system)
        clan_ids = {clan.id for clan in clans}
        member_ids = {mid for clan in clans for mid in clan.member_ids}
        family_ids = {clan.family_id for clan in clans}
        sections = {
            "families": {
                f.id: dict(
                    id=f.id,
                    **localized_definition(f, locale),
                    tags=sorted(f.tags),
                    clan_ids=[cid for cid in f.clan_ids if cid in clan_ids],
                )
                for f in self.catalog.families.values()
                if f.id in family_ids
            },
            "clans": {
                c.id: dict(
                    id=c.id,
                    **localized_definition(c, locale),
                    tags=sorted(c.tags),
                    family_id=c.family_id,
                    member_ids=list(c.member_ids),
                )
                for c in clans
            },
            "members": {
                m.id: dict(
                    id=m.id,
                    **localized_definition(m, locale),
                    tags=sorted(m.tags),
                    family_id=m.family_id,
                    clan_id=m.clan_id,
                    variant_id=m.variant_id,
                    role=m.role,
                    assembly_cost=m.assembly_cost,
                    base_id=m.base_id,
                    image_source=m.image_source,
                    ability_ids=list(m.ability_ids),
                    image=dict(
                        asset_id=m.image.asset_id,
                        image_url=f"/static/images/monsters/catalog/{quote(m.image.asset_id, safe='')}{PurePosixPath(m.image.source_path).suffix}",
                        display_mirror=m.image.display_mirror,
                    )
                    if m.image
                    else None,
                )
                for m in self.catalog.members.values()
                if m.id in member_ids
            },
        }
        hashes = {key: _hash(value) for key, value in sections.items()}
        version = "monster-catalog:" + _hash(
            {
                "schema_version": 2,
                "locale": locale,
                "fallback_locale": DEFAULT_LOCALE,
                "available_locales": available_locales,
                **hashes,
            }
        )
        return MonsterCatalogBootstrapDTO(
            schema_version=2,
            locale=locale,
            fallback_locale=DEFAULT_LOCALE,
            available_locales=available_locales,
            version=version,
            **sections,
            manifest={"version": version, "sections": hashes},
        )
