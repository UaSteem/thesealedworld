from pathlib import Path

import pytest
from tools.validators.architecture import scan_source, validate_architecture


@pytest.mark.parametrize(
    "path,source",
    [
        ("src/frontend/client.py", "from src.backend.features.items import service"),
        ("src/frontend/client.py", "from src import backend"),
        ("src/frontend/pkg/client.py", "from ...backend import core"),
        ("src/shared/dto.py", "import src.frontend.features.auth"),
        ("src/backend/features/new/service.py", 'key = f"game:new_domain:{entity_id}"'),
        ("src/backend/features/rift/runtime.py", 'key = "game:rift:new"'),
        ("src/backend/features/new/service.py", 'key = "combat:" + actor_id'),
        ("src/backend/features/new/service.py", 'key = "loot:new"'),
        ("src/backend/features/new/service.py", "from redis.asyncio import Redis"),
    ],
)
def test_forbidden_source_is_detected(path, source):
    assert scan_source(source, Path(path))


@pytest.mark.parametrize(
    "path,source",
    [
        (
            "src/backend/infrastructure/new/manager.py",
            """from redis.asyncio import Redis
key="game:new:1"
""",
        ),
        (
            "src/backend/features/rift/integrations/runtime.py",
            "from src.backend.infrastructure.rift.managers import RiftInstanceStore",
        ),
        ("src/frontend/client.py", "from src.shared.schemas.user import UserDTO"),
        (
            "src/backend/features/new/service.py",
            '''"""Redis game:ac document is owned by infrastructure."""
# game:other key''',
        ),
        (
            "src/backend/features/combat/policy.py",
            'request = CombatDurabilityDamageRequest(idempotency_key=f"combat:{combat_id}:durability")',
        ),
    ],
)
def test_allowed_source_is_not_flagged(path, source):
    assert scan_source(source, Path(path)) == []


def test_actual_tree_scan_catches_rift_and_ignores_archive(tmp_path):
    path = tmp_path / "src/backend/features/rift/runtime.py"
    path.parent.mkdir(parents=True)
    path.write_text('key="game:unknown:1"', encoding="utf-8")
    archived = tmp_path / "archive/backend/features/service.py"
    archived.parent.mkdir(parents=True)
    archived.write_text('key="game:old"', encoding="utf-8")
    errors = validate_architecture(tmp_path)
    assert len(errors) == 1
    assert "rift/runtime.py:1" in errors[0]


@pytest.mark.parametrize(
    "source",
    [
        "import src.backend.core as hidden",
        "import importlib as loader; loader.import_module('src.backend.features.items')",
        "from importlib import import_module as load; load('src.backend.core')",
        "__import__('backend.features.items')",
    ],
)
def test_aliased_and_literal_dynamic_imports_are_detected(source):
    assert scan_source(source, Path("src/frontend/client.py"))


@pytest.mark.parametrize(
    "source",
    [
        'key="game" + ":new:" + entity_id',
        'redis.set("game:new:1",value)',
        'redis.set(idempotency_key="combat:still_storage")',
        'CombatDurabilityDamageRequest(idempotency_key=redis.set("combat:new", value))',
        'CombatDurabilityDamageRequest(idempotency_key="game:new")',
    ],
)
def test_split_or_storage_context_key_is_detected(source):
    assert scan_source(source, Path("src/backend/features/rift/runtime.py"))


def test_syntax_error_is_not_silently_skipped():
    errors = scan_source("def broken(", Path("src/frontend/client.py"))
    assert len(errors) == 1 and "syntax:" in errors[0]


def test_report_contains_rule_file_and_line_without_payload():
    errors = scan_source('value=1\nkey="game:new:private-id"', Path("src/backend/features/rift/runtime.py"))
    assert errors == ["src/backend/features/rift/runtime.py:2: redis-key-owner: game:"]


def test_ci_and_full_validator_include_source_gate():
    import ast

    import yaml

    root = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    command = next(
        step["run"]
        for step in workflow["jobs"]["develop-behavior"]["steps"]
        if step.get("name") == "Run behavioral tests"
    )
    assert "tests/backend/features/test_infrastructure_boundaries.py" in command.split()
    assert "tests/backend/core" in command.split()
    tree = ast.parse((root / "tools/validators/run.py").read_text(encoding="utf-8"))
    assert any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "validate_architecture"
        for node in ast.walk(tree)
    )
