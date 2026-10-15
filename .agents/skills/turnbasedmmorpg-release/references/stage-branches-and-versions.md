# TurnBasedMMORPG Release Flow

## Purpose

Give every change an unambiguous answer to three questions:

1. **Which branch does this go into?**
2. **What does it do to the version number?**
3. **Does it require wiping player progress and, if so, what announcement is owed?**

This skill is the source of truth for those three. Other release-adjacent skills
(changelog discipline, deployment ops) follow the decisions made here.

## Read First

- `.agents/skills/turnbasedmmorpg-release/references/changelog.md` — how Unreleased entries and tag summaries are written.
- `.agents/skills/turnbasedmmorpg-release/references/deployment.md` — compose layers, image tags, manual deploy gates.
- `.agents/skills/turnbasedmmorpg-project/references/repository-operations.md` — repository-wide rules and skill umbrella.

## Stage Model

The public surface uses exactly three stages. They are stored in
`FrontendSettings.release_stage` (default `alpha`) and rendered by
`UIRenderer` as `release_stage_label` for the landing/footer.

| Stage | Player promise | When it applies |
|---|---|---|
| `alpha` | Active development with players as testers. Progress may be reset at major changes — always announced, never as a surprise. | Until the project considers core systems stable enough that future wipes are unlikely. |
| `beta` | Stabilisation. Progress is kept. At most one announced wipe before 1.0, minimum 30 days notice. | Between "core stable" and the first real release. |
| `release` | 1.0+. Progress is not reset. Future work is patches, minor features, and expansions. | After the project ships 1.0. |

The stage is a separate signal from the version number. Do not encode the
stage into the version (no `0.x = alpha, 1.x = beta` schemes). Stage moves
rarely; the number moves continuously.

There is no `closed-beta` / `open-beta` split. Open versus closed
participation is handled with feature flags or invites, not with a new stage.

## Branch Strategy

Three long-lived branches plus short-lived ones, no exceptions:

```text
main              prod. Only fully prepared changes land here. Every merge tags a release.
develop           "next minor". All feature work, refactors, balance, content edits accumulate here.
hotfix/<topic>    short-lived; branched from main; back-merged into main AND develop.
release/wipe-<X>  carantine for code that will need a player-progress wipe; not merged into develop until announcement window has passed.
```

The decision flow for a new change:

1. **Is this a bug that needs to ship today?** -> `hotfix/<topic>` from `main`.
2. **Does this change require a wipe?** -> `release/wipe-<topic>` from `develop`. Do **not** merge into `develop` until announcement window is open and the wipe is approved.
3. **Otherwise?** -> feature branch from `develop`, PR into `develop`.

When a hotfix lands in `main`, immediately back-merge `main` into `develop`
so develop never trails on a fix that already shipped.

When a `release/wipe-*` branch is ready to ship, the merge order is:

```text
release/wipe-X -> develop -> main
```

Never merge `release/wipe-*` straight into `main`. The change must pass
through `develop` first so the next minor release contains it.

## Wipe-Risk Classification

Every PR description must carry a single line:

```text
Wipe-risk: NONE | DATA-MIGRATION | WIPE
```

| Label | Meaning | Examples |
|---|---|---|
| `NONE` | Pure content/balance/UI/fixes. Existing characters keep playing. | New monster, new item, new sprite, balance tuning, copy edits, refactors that do not touch persisted shapes. |
| `DATA-MIGRATION` | Persisted shape changes but a backward-compatible alembic/data backfill exists. Players keep their progress. | New nullable column with backfill, renamed field with compat alias, reorganised JSON section with one-time projection. |
| `WIPE` | Persisted shape changes are not safely migratable, or the design assumption behind existing data is gone. | Reworked attribute system, replaced inventory id scheme, restructured economy, switched skill progression formula, full rewrite (0.2 -> 0.3 style). |

Heuristic: if you cannot write a backward-compatible alembic migration with a
real `downgrade()` for the players you already have, it is `WIPE`. If you can
(however ugly), it is `DATA-MIGRATION`.

`NONE` may merge straight into `develop` or `hotfix/*` as usual.
`DATA-MIGRATION` requires an alembic revision and a working downgrade; check
the migration against a staging copy of prod data before merge.
`WIPE` may only land in `develop` after the announcement window has opened.

## Version Bumping Rules

Versions follow SemVer numerically but the meaning is fixed for this project:

| Change shape | Bump | Cadence | Source branch |
|---|---|---|---|
| Hotfix, security, regression, copy fix, single-flag rollout | `PATCH` (`0.3.0 -> 0.3.1`) | As needed, sometimes daily | `hotfix/*` -> `main` |
| New features, content, balance, refactors without persisted shape changes | `MINOR` (`0.3.x -> 0.4.0`) | Weekly train from `develop` -> `main` | `develop` -> `main` |
| Reworks that need a wipe, large architectural moves | `MINOR` with announcement | When announcement window closes | `release/wipe-*` -> `develop` -> `main` |
| Stage promotion (`alpha` -> `beta`, `beta` -> `release`) | Coincides with a `MINOR` or `MAJOR` tag | Once per stage | `develop` -> `main` |
| `1.0.0` itself | `MAJOR` | Once | `develop` -> `main` |

Stage label is bumped in `FrontendSettings.release_stage` (env override) at
the same time as the tag. It is not part of the version string.

Patch bumps do not need to wait for the weekly train.
