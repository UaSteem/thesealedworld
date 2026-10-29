"""Standalone frozen inventory mock; stdlib and Jinja only at runtime."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

from game_ui_lab.app import LAB_ROOT, resolve_asset
from game_ui_lab.fixtures.inventory import ART, PAYLOAD


def render_inventory() -> str:
    env = Environment(loader=FileSystemLoader(LAB_ROOT / "templates"), autoescape=select_autoescape(("html",)))
    character = json.loads((LAB_ROOT / "data/starter_guard_01.json").read_text(encoding="utf-8"))
    return env.get_template("inventory.html").render(character=character, inventory=PAYLOAD)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/":
            content, mime = render_inventory().encode(), "text/html; charset=utf-8"
        else:
            asset = ART.get(path) if path.startswith("/inventory-art/") else resolve_asset(self.path)
            if asset is None:
                self.send_error(404)
                return
            content = asset.read_bytes()
            mime = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8880)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Inventory Lab: http://127.0.0.1:{args.port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
