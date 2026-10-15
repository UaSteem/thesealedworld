# Check Commands

From the repository root, choose commands relevant to the change:

```powershell
uv run pytest path/to/relevant_tests.py
uv run ruff check path/to/changed_code
uv run mypy path/to/changed_package
```

For broad code changes, commit readiness, or a required full gate:

```powershell
uv run python tools/dev/check.py
```

The local `tools/dev/check.py` adds `tools/validators/run.py` and `uv run --group docs mkdocs build --clean` to a base runner imported from `codex_core`. Inspect the installed base runner before naming its steps or supported flags. The current script's machine-specific library path may make the full gate unavailable on another checkout. The project's configured coverage threshold is in `pyproject.toml`; do not change it as part of routine verification.

For skill or documentation edits, validate paths, frontmatter, Markdown links, and diff whitespace. Runtime tests are warranted when behavior changed.
