import ast
from pathlib import Path


def test_monster_responsibilities_own_implementation():
    root = Path("src/backend/features/monsters")
    for responsibility in ("catalog", "encounters", "instances", "inspection"):
        assert (root / responsibility / "__init__.py").is_file()
    for legacy in ("services", "runtime", "resources", "repositories"):
        assert not any((root / legacy).glob("*.py"))
    assert (root / "catalog/registry.py").is_file()
    assert (root / "public.py").is_file()


def test_integrations_only_adapt_shared_pool_cache():
    root = Path("src/backend/features/monsters/integrations")
    assert {path.name for path in root.glob("*.py")} == {"encounter_pool_cache.py"}
    tree = ast.parse((root / "encounter_pool_cache.py").read_text(encoding="utf8"))
    imports = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    # The adapter may serialize the pool contract, never own admission or composition.
    assert {name for name in imports if name.startswith("src.backend.features.monsters")} == {
        "src.backend.features.monsters.encounters.services.variant_pool"
    }
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    assert classes == ["MonsterEncounterPoolCache"]
