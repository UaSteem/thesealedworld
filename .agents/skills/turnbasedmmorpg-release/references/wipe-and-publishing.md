## How to Route Work

When picking up a task, classify it once and route accordingly:

1. **What does the user want?** Phrase it as outcome, not diff. ("Add cooldown to shield bash" not "edit combat_resolver.py".)
2. **Is the bug in prod right now?** Yes -> `hotfix/*` from `main`. No -> step 3.
3. **Does it change persisted shapes?** No -> feature branch from `develop`. Yes -> step 4.
4. **Can backward-compat migration be written?** Yes -> `DATA-MIGRATION` on feature branch from `develop`. No -> `release/wipe-<topic>` from `develop`, plus a planned announcement (see below).

Record the choice in the PR description on the first line:

```text
Branch: hotfix | minor | wipe
Wipe-risk: NONE | DATA-MIGRATION | WIPE
Bump: patch | minor | major
```

## Wipe Announcement Protocol

When a `release/wipe-*` branch exists, before merging into `develop`:

1. Notice window opens. Minimum windows:
   - `alpha` stage: 7 days
   - `beta` stage: 30 days
   - `release` stage: wipes are not permitted; raise to the project owner.
2. Owner publishes a `/news` post titled e.g. `"Wipe on YYYY-MM-DD: <why>"`.
3. `release_progress_policy` on the landing remains unchanged (it is the standing rule); the news post is the specific instance.
4. After the wipe ships:
   - Add a footer entry to the affected `## [vX.Y.Z]` section in
     `docs/changelog/*.md`: `**Wipe.** <one sentence why>.`
   - Tag the commit with `v<X>.<Y>.<Z>` and a tag message that starts with `Wipe.`.

Do not skip the news post even if player count is low. The protocol is the
contract that makes the landing promise true.

## Git Tag and Image Convention

Production tags are exactly `v<X>.<Y>.<Z>`, no suffix. Pre-release builds may
use `v<X>.<Y>.<Z>-rc<N>` for explicit RCs but never appear in prod runtime.

`hatch-vcs` reads the tag at build time; no manual `version =` edit in
`pyproject.toml`.

`release_version` in `FrontendSettings` defaults to the latest released
version and is overridable per environment via `RELEASE_VERSION=`. Keep it in
sync with the tag at deploy time.

Image tags follow the deploy-management skill (release tag + commit SHA).

## Cross-Skill Contracts

When a change lands:

- The matching changelog gets an Unreleased line under .agents/skills/turnbasedmmorpg-release/references/changelog.md.
- Image-affecting deploys follow .agents/skills/turnbasedmmorpg-release/references/deployment.md.
- This skill owns the *branch and version decision*; the other two own *what to write and how to ship it*.

## Decision Self-Check

Before opening a PR, an agent must answer:

- What branch is this targeting and why?
- What is the wipe-risk label and the evidence for it?
- What version bump is implied?
- If `WIPE`, what is the announcement plan and which `/news` post covers it?
- Which changelog file received the `Unreleased` line?

Write the answers into the PR description verbatim. They are the audit trail.

## Common Mistakes

- Merging a `release/wipe-*` branch straight into `main` without going through `develop`.
- Treating any breaking-feeling change as `WIPE` when a migration is possible.
- Bumping `MAJOR` for an alpha or beta change. `1.0.0` is reserved for the release stage transition.
- Letting the stage drift on the landing while `release_version` stays the same after a stage promotion.
- Encoding the stage into the number (`0.x = alpha`). The stage is a separate signal.
- Forgetting the back-merge of `main` into `develop` after a hotfix.
- Shipping a wipe without a `/news` post, on the grounds that "no one will notice yet".
