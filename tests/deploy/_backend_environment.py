"""Inspect declared API/runtime env names without importing either settings singleton."""

import ast
from pathlib import Path


def backend_environment_names(root: Path) -> set[str]:
    fields: set[str] = set()
    for name in ("settings.py", "runtime.py"):
        tree = ast.parse((root / "src/backend/config" / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                fields.add(node.target.id.upper())
    return fields | {"REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_MAX_CONNECTIONS", "REDIS_TIMEOUT"}
