from __future__ import annotations

import asyncio
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen


class PreviewServer:
    def __init__(self, *, preview_root: Path, static_root: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.preview_root = preview_root.resolve()
        self.static_root = static_root.resolve()
        self.host = host
        self.port = port

    def serve_forever(self) -> None:
        preview_root = self.preview_root
        static_root = self.static_root

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                request_path = unquote(parsed.path)
                if request_path.startswith("/preview/item-textures/"):
                    self._send_item_texture(request_path.removeprefix("/preview/item-textures/"))
                    return
                if request_path.startswith("/static/generated-assets/"):
                    self._send_generated_asset(request_path.removeprefix("/static/generated-assets/"))
                    return
                if request_path == "/game/catalog/bootstrap":
                    self._send_json(_catalog_bootstrap_payload())
                    return
                if request_path == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()
                    return
                if request_path.startswith("/static/"):
                    file_path = static_root / request_path.removeprefix("/static/")
                    self._send_file(file_path, static_root)
                    return
                if request_path in ("", "/"):
                    file_path = preview_root / "index.html"
                else:
                    file_path = preview_root / request_path.lstrip("/")
                self._send_file(file_path, preview_root)

            def log_message(self, message_format: str, *args: object) -> None:
                return

            def _send_item_texture(self, reference: str) -> None:
                from src.backend.features.items.resources.visuals import ITEM_VISUAL_CATALOG
                from src.frontend.config.settings import settings
                from src.frontend.integrations.generated_assets import (
                    LocalGeneratedAssetReader,
                    build_s3_generated_asset_reader,
                )

                variant_id, separator, kind = reference.partition("/")
                variant = ITEM_VISUAL_CATALOG.variants_by_id.get(variant_id)
                if not separator or kind not in {"image", "thumbnail"} or variant is None:
                    self.send_error(404)
                    return
                rendition = getattr(variant, kind)
                if rendition is None:
                    self.send_error(404)
                    return
                reader = (
                    build_s3_generated_asset_reader(settings)
                    if settings.asset_storage_backend == "s3"
                    else LocalGeneratedAssetReader(root=Path(settings.generated_assets_dir))
                )
                try:
                    asset = asyncio.run(reader.get_object(rendition.storage_key))
                    if asset is None:
                        self.send_error(404)
                        return
                    # Development-only relay: pinned catalog key, never an arbitrary upstream URL.
                    # WebGL requires CORS; the production S3 policy is deliberately left unchanged.
                    if asset.redirect_url:
                        with urlopen(asset.redirect_url, timeout=20) as upstream:
                            content = upstream.read()
                    else:
                        content = asset.content
                except Exception:
                    self.send_error(502, "Item preview texture unavailable")
                    return
                self.send_response(200)
                self.send_header("Content-Type", rendition.content_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                self.end_headers()
                self.wfile.write(content)

            def _send_generated_asset(self, storage_key: str) -> None:
                from src.frontend.config.settings import settings
                from src.frontend.integrations.generated_assets import (
                    LocalGeneratedAssetReader,
                    build_s3_generated_asset_reader,
                )

                # Exercise the same delivery adapter as frontend, including S3 redirects.
                reader = (
                    build_s3_generated_asset_reader(settings)
                    if settings.asset_storage_backend == "s3"
                    else LocalGeneratedAssetReader(root=Path(settings.generated_assets_dir))
                )
                try:
                    asset = asyncio.run(reader.get_object(storage_key))
                except ValueError:
                    self.send_error(404)
                    return
                if asset is None:
                    self.send_error(404)
                    return
                self.send_response(301 if asset.redirect_url else 200)
                self.send_header("Content-Type", asset.content_type)
                if asset.redirect_url:
                    self.send_header("Location", asset.redirect_url)
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                self.end_headers()
                if not asset.redirect_url:
                    self.wfile.write(asset.content)

            def _send_file(self, file_path: Path, allowed_root: Path) -> None:
                resolved = file_path.resolve()
                if not _is_within(resolved, allowed_root) or not resolved.is_file():
                    self.send_error(404)
                    return
                content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
                payload = resolved.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _send_json(self, payload: dict[str, object]) -> None:
                encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        print(f"Serving game preview at http://{self.host}:{self.port}/")
        print("Press Ctrl+C to stop.")
        server.serve_forever()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _catalog_bootstrap_payload() -> dict[str, object]:
    from src.backend.features.game_catalog.services.catalog_service import GameCatalogBootstrapService

    return GameCatalogBootstrapService().build_bootstrap().model_dump(mode="json")
