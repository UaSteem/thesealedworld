"""Focused offline contracts for the isolated inventory server."""

import io
import unittest

from game_ui_lab.inventory_app import ART, PAYLOAD, Handler, render_inventory


class Request(Handler):
    def __init__(self, path):
        self.path = path
        self.wfile = io.BytesIO()
        self.status = None
        self.headers_sent = {}

    def send_response(self, code):
        self.status = code

    def send_error(self, code):
        self.status = code

    def send_header(self, key, value):
        self.headers_sent[key] = value

    def end_headers(self):
        pass


class InventoryContracts(unittest.TestCase):
    def test_frozen_data_and_shell(self):
        self.assertEqual([item["tier"] for item in PAYLOAD["items"]], list(range(6)))
        self.assertIsNone(PAYLOAD["selected_id"])
        html = render_inventory()
        for expected in ("inventory-stage", "character-panel", "chat-divider", "inventory-data"):
            self.assertIn(expected, html)
        self.assertNotIn("/ui-static/scene.js", html)

    def test_art_exact_map(self):
        self.assertEqual(len(ART), 12)
        for path, asset in ART.items():
            request = Request(path)
            request.do_GET()
            self.assertEqual(request.status, 200)
            self.assertEqual(request.headers_sent["Content-Type"], "image/webp")
            self.assertEqual(request.wfile.getvalue(), asset.read_bytes())

    def test_unknown_and_traversal_rejected(self):
        for path in (
            "/inventory-art/unknown/image",
            "/inventory-art/sword.basic.iron.t1/image/extra",
            "/inventory-art/%2e%2e/image",
            "/inventory-art/https://example.com/image",
            "/ui-static/%2e%2e/app.py",
            "/static/%252e%252e/app.py",
        ):
            request = Request(path)
            request.do_GET()
            self.assertEqual(request.status, 404, path)


if __name__ == "__main__":
    unittest.main()
