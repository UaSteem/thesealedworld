"""Static, non-importing checks for explicit source ownership boundaries.

This is not data-flow analysis: computed import names, arbitrary key factories,
and domain semantics require additional checks/review, not a claim of enforcement.
"""

from __future__ import annotations

import ast
from pathlib import Path

REDIS_ROOTS = ("game:", "combat:", "loot:")


def _under(module: str, root: str) -> bool:
    return module == root or module.startswith(root + ".")


def _prefix(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        pieces = []
        for item in node.values:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                break
            pieces.append(item.value)
        return "".join(pieces)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _prefix(node.left) + _prefix(node.right)
    return ""


def scan_source(source: str, path: Path) -> list[str]:
    name = path.as_posix()
    frontend = name.startswith("src/frontend/")
    shared = name.startswith("src/shared/")
    feature = name.startswith("src/backend/features/")
    if not (frontend or shared or feature):
        return []
    try:
        tree = ast.parse(source, filename=name)
    except SyntaxError as exc:
        return [f"{name}:{exc.lineno}: syntax: {exc.msg}"]
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    errors: set[tuple[int, str, str]] = set()
    importlib_aliases = {"importlib"}
    loaders = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            loaders.update(a.asname or a.name for a in node.names if a.name == "import_module")

    def check_import(module: str, line: int) -> None:
        if frontend and any(_under(module, root) for root in ("src.backend", "backend")):
            errors.add((line, "frontend-import", module))
        if shared and any(_under(module, root) for root in ("src.backend", "backend", "src.frontend", "frontend")):
            errors.add((line, "shared-import", module))
        if feature and _under(module, "redis"):
            errors.add((line, "feature-redis-client", module))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_import(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = list(path.parent.parts)
                module = ".".join(package[: len(package) - node.level + 1] + ([module] if module else []))
            check_import(module, node.lineno)
            for alias in node.names:
                check_import(f"{module}.{alias.name}", node.lineno)
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            dynamic = (
                isinstance(func, ast.Name)
                and func.id in loaders
                or isinstance(func, ast.Attribute)
                and func.attr == "import_module"
                and isinstance(func.value, ast.Name)
                and func.value.id in importlib_aliases
            )
            if dynamic and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                check_import(node.args[0].value, node.lineno)

        if not isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            continue
        parent = parents.get(node)
        if isinstance(parent, (ast.Expr, ast.JoinedStr, ast.BinOp)):
            continue
        prefix = _prefix(node)
        if not prefix.startswith(REDIS_ROOTS):
            continue
        # Explicit domain-operation identity, not Redis storage ownership. This
        # exception is one DTO field, never a file, feature or storage call.
        ancestor = parent
        while ancestor is not None and not isinstance(ancestor, (ast.keyword, ast.stmt, ast.Call)):
            ancestor = parents.get(ancestor)
        if (
            feature
            and prefix.startswith("combat:")
            and isinstance(ancestor, ast.keyword)
            and ancestor.arg == "idempotency_key"
        ):
            call = parents.get(ancestor)
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "CombatDurabilityDamageRequest"
            ):
                continue
        errors.add((node.lineno, "redis-key-owner", prefix.split(":", 1)[0] + ":"))
    return [f"{name}:{line}: {rule}: {detail}" for line, rule, detail in sorted(errors)]


def validate_architecture(root: Path) -> list[str]:
    errors = []
    for path in sorted((root / "src").rglob("*.py")):
        errors.extend(scan_source(path.read_text(encoding="utf-8-sig"), path.relative_to(root)))
    return errors
