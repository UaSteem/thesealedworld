"""The common shell must not dispatch into archived node Rift templates."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from jinja2 import BaseLoader, Environment


def test_shell_does_not_render_retired_node_rift() -> None:
    requested: list[str] = []

    class ComponentLoader(BaseLoader):
        def get_source(self, environment, template):
            requested.append(template)
            return "", None, lambda: True

    root = Path(__file__).resolve().parents[2]
    source = (root / "src/frontend/templates/game/session_content_inner.html").read_text(encoding="utf-8")
    environment = Environment(loader=ComponentLoader(), autoescape=True)
    html = environment.from_string(source).render(domain="rift", static_version="test", background_url=None)

    assert "game-session-root" in html
    assert not any(name.startswith("game/domains/rift/") for name in requested)


def _session_route(name, namespace):
    root = Path(__file__).resolve().parents[2]
    path = root / "src/frontend/game_features/session/routes/pages.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(item for item in tree.body if isinstance(item, ast.AsyncFunctionDef) and item.name == name)
    node.decorator_list = []
    module = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[name]


def test_retired_reset_control_does_not_query_backend():
    function = _session_route("_attach_dev_status_context", {"get_game_access_token_from_context": lambda context: ""})
    context = {"dev_status_controls": {"starter_rift_reset": {}}}
    with pytest.raises(StopIteration):
        function(context, user=object(), game_session_api=object()).send(None)
    assert "dev_status_controls" not in context


def test_retired_reset_route_rejects_without_context_builder():
    from starlette import status

    class Auth:
        async def require_current_user(self, request):
            return SimpleNamespace(is_superuser=True)

    function = _session_route(
        "game_dev_starter_rift_reset",
        {"settings": SimpleNamespace(debug=True), "HTTPException": HTTPException, "status": status},
    )
    with pytest.raises(HTTPException) as error:
        function(object(), object(), Auth(), object(), 1, "test").send(None)
    assert error.value.status_code == 410
