"""Local-only interface shell; no accounts, persistence or game services."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

from game_ui_lab.fixtures.inventory import ART as INVENTORY_ART
from game_ui_lab.fixtures.inventory import PAYLOAD as INVENTORY_PAYLOAD

LAB_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = LAB_ROOT.parent / "src/frontend/static"


def render_index(scene: str = "hex") -> str:
    environment = Environment(loader=FileSystemLoader(LAB_ROOT / "templates"), autoescape=select_autoescape(("html",)))
    character = json.loads((LAB_ROOT / "data/starter_guard_01.json").read_text(encoding="utf-8"))
    scene = "hex"
    scripts = [
        "game/shared/hex-layout.js",
        "game/ui/combat-controls.js",
        "game/ui/target-inspector.js",
        "game/scenes/combat/scene.js",
    ]
    return environment.get_template("index.html").render(
        character=character,
        scene_version=scene,
        scene_scripts=scripts,
        inventory=INVENTORY_PAYLOAD,
        page_briefs=json.loads((LAB_ROOT / "data/page-briefs.json").read_text(encoding="utf-8")),
    )


def resolve_asset(request_path: str) -> Path | None:
    """Resolve public files, rejecting encoded traversal and Windows separators."""
    path = urlsplit(request_path).path
    for _ in range(4):
        decoded = unquote(path)
        if decoded == path:
            break
        path = decoded
    if "\\" in path or "\x00" in path or "%" in path:
        return None
    if path.startswith("/inventory-art/"):
        return INVENTORY_ART.get(path)
    for prefix, root in (
        ("/ui-static/", LAB_ROOT / "static"),
        ("/ui-data/", LAB_ROOT / "data"),
        ("/static/", STATIC_ROOT),
    ):
        if not path.startswith(prefix):
            continue
        relative = path.removeprefix(prefix)
        if not relative or any(part in ("", ".", "..") for part in relative.split("/")):
            return None
        target = (root / relative).resolve()
        if target.is_relative_to(root.resolve()) and target.is_file():
            return target
    return None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/":
            scene = parse_qs(urlsplit(self.path).query).get("scene", ["hex"])[0]
            content, content_type = render_index(scene).encode("utf-8"), "text/html; charset=utf-8"
        else:
            asset = resolve_asset(self.path)
            if asset is None:
                self.send_error(404)
                return
            content = asset.read_bytes()
            content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8879)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Game UI Lab: http://127.0.0.1:{args.port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
