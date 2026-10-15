# TurnBasedMMORPG Testing Strategy

Read `docs/ru/management/testing_strategy.md` for the project test layout, fixtures, doubles, and coverage goals. The configured global coverage threshold is in `pyproject.toml`; do not lower it to pass a change.

For new or changed behavior, write tests that exercise observable contracts and meaningful edge cases. For a tested refactor or contract migration, follow the global `refactor-test-first` workflow. Add integration tests when the change crosses a real database, Redis, API, event, or other external boundary. Prefer simple in-memory fakes for stateful dependencies when they make behavior clearer than large mock setups.

Choose focused tests first and broaden validation according to risk and required gates. The project targets strong coverage, especially at auth, config, and state-transition boundaries; no fixed patch percentage or unrelated surrounding coverage expansion is required for every change. Avoid tests that merely mirror implementation details or inflate line coverage.
