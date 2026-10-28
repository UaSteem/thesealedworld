"""Retirement guards exercise isolated entry functions without starting storage."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[4]


def complete(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as finished:
        return finished.value
    raise AssertionError("Unexpected external suspension")


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def method(path, name, namespace):
    tree = ast.parse(source(path))
    node = next(node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef) and node.name == name)
    node.decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), path, "exec"), namespace)
    return namespace[name]


@pytest.mark.parametrize("name", ["publish_rift_entry_requested", "activate_prepared_rift_entry"])
def test_scenario_entry_rejected_before_any_side_effect(name):
    class RetiredError(RuntimeError):
        pass
    function = method("src/backend/features/scenario/integrations/system_integrator.py", name, {"LegacyRiftRetiredError": RetiredError})
    args = (object(), 1, object(), {}) if name.startswith("publish") else (object(), 1, object())
    with pytest.raises(RetiredError):
        complete(function(*args))


def test_scenario_show_does_not_prepare_legacy_run():
    function = method("src/backend/features/scenario/services/scenario_service.py", "_prepare_rift_entry_for_node", {})
    complete(function(object(), 1, object(), {"metadata": {"rift_entry": {"prepare_on_show": True}}}))


def test_dirty_sweeper_only_schedules_active_domains():
    namespace = {}
    async def inventory(*args, **kwargs):
        return [1]
    async def knowledge(*args, **kwargs):
        return [2]
    namespace.update(_enqueue_inventory=inventory, _enqueue_exploration_knowledge=knowledge, logger=SimpleNamespace(bind=lambda **kwargs: SimpleNamespace(info=lambda *args: None)))
    function = method("src/backend/features/system/workers/tasks/dirty_sweeper.py", "system_dirty_sweeper_task", namespace)
    result = complete(function({"redis_managers": SimpleNamespace(redis=object()), "system_arq": object()}))
    assert result["inventory_char_ids"] == [1]
    assert result["exploration_knowledge_char_ids"] == [2]
    assert not any("rift" in key for key in result)


@pytest.mark.parametrize("path", ["src/backend/core/containers/game.py", "src/backend/core/containers/redis.py", "src/backend/core/arq_container.py", "src/backend/core/lifespan.py", "src/backend/infrastructure/mongo/bootstrap.py", "src/backend/features/system/workers/arq.py"])
def test_startup_and_workers_do_not_import_legacy_rift(path):
    tree = ast.parse(source(path))
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any("features.rift" in name or "infrastructure.rift" in name for name in imports)
