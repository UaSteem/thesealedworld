# Regional Rifts And Season Flow

Status: exploratory proposal, not approved mechanics or a description of current runtime.
World direction: 12 factions in the full version; one faction in the first alpha.
See [ADR-0002](../../../adr/0002-faction-city-district-progression.md).

## Starting Territories

The old D4 starter layout is not the mandatory geography for all factions.
Starting population, settlements, routes and local threats need separate design.
Current D4 ids and map behavior remain implementation facts until a dedicated
migration; this documentation cleanup changes no catalogs or generated worlds.

## Monster Context Hash

Preserve stable context inputs used by existing consumers: biome id,
family/clan tier and normalized context tags. Existing starter-region or rift
tags must not be removed from runtime hashing merely because world lore changed.
Tags such as `rat_swarm`, `wolf_pack`, `bandit_gang`, and `goblin_tribe` can
express local encounter context without defining a single global capital.

## Family Tier Progression

The earlier proposal for broad variant availability is retained as a proposal:
family tier 1 can use variant tiers 0..2; family tier 2 can use variant tiers
0..3. Selected members scale from family tier. Verify actual generation rules
against the current Monsters implementation before relying on these ranges.

## Regional Direction

Possible regional content includes local rifts or ruptures, expedition routes,
settlements and outposts. Survival, storage, repair and scouting can support
regional activity. Concrete placement, access and threat rules remain open;
there is no required single hub or four global sources of world danger.

## Season Contribution — Proposal

Possible objective contributions include rift activity, settlement construction
and defense, scouting and route discovery, boss or elite encounters, delivered
resources and combat support. Scoring, rewards and season completion rules
require separate approval. This list does not add working counters or rewards.

The prior draft is preserved under
`docs/archive/game-design/world-before-factions-2026-10-28/` for history only.
