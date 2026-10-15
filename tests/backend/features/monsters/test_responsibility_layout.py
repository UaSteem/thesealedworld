from pathlib import Path


def test_monster_responsibilities_own_implementation():
    root = Path("src/backend/features/monsters")
    for responsibility in ("catalog", "encounters", "instances", "inspection"):
        assert (root / responsibility / "__init__.py").is_file()
    for legacy in ("services", "runtime", "resources", "repositories", "integrations"):
        assert not any((root / legacy).glob("*.py"))
    assert (root / "catalog/registry.py").is_file()
    assert (root / "public.py").is_file()
