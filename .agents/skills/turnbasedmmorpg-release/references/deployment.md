# TurnBasedMMORPG Deployment Management

## Read First

Read:

- `.agents/skills/turnbasedmmorpg-project/references/repository-operations.md`
- `.agents/skills/turnbasedmmorpg-release/references/stage-branches-and-versions.md` for branch strategy, version bumping, and wipe-risk classification that picks the source branch for the deploy.
- `docs/ru/management/deployment.md`
- `docs/ru/management/deployment-contract.md`

Use .agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md when site/frontend containers or routes change.
Use .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md for backend containers and .agents/skills/turnbasedmmorpg-backend/references/event-bus.md for Redis Streams.

## Ownership

Deployment management owns the operational split, not runtime business logic:

- Docker Compose file layout under `deploy/`.
- CI/CD jobs and manual deployment gates.
- Image tag and version policy.
- Documentation build as a release artifact/check.
- Service restart boundaries for infra, site, and game runtime.

## Compose Strategy

Local development may keep a single convenient compose file until the split is ready.

Production should be designed as three layers:

```text
infra: postgres, redis, networks, volumes, reverse proxy
site: frontend/site service and site migrations
game: backend/game API, chat/ws, arq workers, game/chat migrations
```

Do not couple site deployment to game runtime restart. Site must be deployable while game is in maintenance.

## CI/CD Rules

- On pull request or push, run quality checks for the whole repository because contracts are shared.
- Build documentation in CI together with tests.
- Build immutable container images after tests pass.
- Tag images by release tag/version and commit SHA; do not deploy mutable-only `latest`.
- Deployment to production should be a manual approval step.
- Manual deploy should allow selecting the target layer: `site`, `game`, or full stack.

## Do Not

- Do not make game runtime deployment automatically restart site unless explicitly required.
- Do not make chat/ws start only after a character login; chat service belongs to game runtime, browser connections are conditional.
- Do not add cross-database assumptions to deployment scripts.
- Do not make production deploy depend on local-only compose behavior.

## Verification

For deploy-management changes, prefer:

```powershell
docker compose -f <file> config
```

For release pipeline changes, verify:

- tests and lint jobs still cover frontend, backend, and shared code;
- docs build is included;
- image tags include release tag/version and commit SHA;
- deploy jobs are manual and layer-specific.
