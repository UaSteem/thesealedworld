from src.backend.features.monsters.catalog.resources.visuals import (
    build_clan_visual,
    build_member_visual,
    get_family_visual,
    version_generated_asset_url,
    version_visual_image_urls,
)


def test_prepared_visual_has_no_provider_request_metadata():
    family = get_family_visual("rat_swarm")
    clan = build_clan_visual("rat_swarm", clan_name="Clan", description="Description", context_tags=["sewer"])
    member = build_member_visual("rat_swarm", variant_key="rat", role="minion", member_name="Rat", appearance="Small")
    for visual in (family, clan, member):
        assert visual["image_url"] == "/static/images/monsters/families/rat_swarm.svg"
        assert not {"asset_payload", "storage_key", "image_model", "prompt_seed", "generated_image_url"}.intersection(visual)


def test_unknown_family_visual_is_explicitly_missing():
    assert get_family_visual("unknown")["status"] == "missing"
    assert get_family_visual("unknown")["image_url"] == ""


def test_generated_visual_urls_are_versioned_for_browser_cache_busting() -> None:
    visual = {
        "image_url": "/static/generated-assets/monsters/generated/members/rat.webp",
        "generated_image_url": "/static/generated-assets/monsters/generated/members/rat.webp",
        "placeholder_image_url": "/static/images/monsters/families/rat_swarm.svg",
        "asset_hash": "rat-image-bytes",
    }

    assert version_generated_asset_url(str(visual["image_url"]), visual) == (
        "/static/generated-assets/monsters/generated/members/rat.webp?v=rat-image-bytes"
    )
    assert version_visual_image_urls(visual)["placeholder_image_url"] == (
        "/static/images/monsters/families/rat_swarm.svg"
    )


def test_generated_visual_urls_drop_absolute_host_before_versioning() -> None:
    visual = {
        "image_url": "https://thesealedworld.com/static/generated-assets/monsters/generated/members/rat.webp",
        "asset_hash": "rat-image-bytes",
    }

    assert version_visual_image_urls(visual)["image_url"] == (
        "/static/generated-assets/monsters/generated/members/rat.webp?v=rat-image-bytes"
    )


def test_pending_visual_uses_previous_hash_for_previous_image_url() -> None:
    visual = {
        "image_url": "/static/generated-assets/monsters/generated/members/rat.webp",
        "previous_image_url": "/static/generated-assets/monsters/generated/members/rat.webp",
        "asset_hash": "next-prompt-hash",
        "previous_asset_hash": "previous-image-bytes",
    }

    assert version_visual_image_urls(visual)["image_url"] == (
        "/static/generated-assets/monsters/generated/members/rat.webp?v=previous-image-bytes"
    )
