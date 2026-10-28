"""Archived node endpoints fail explicitly; Hex remains dev-only."""

from fastapi import APIRouter, HTTPException

from src.backend.features.rift.retirement import LEGACY_RIFT_RETIRED_DETAIL


async def legacy_rift_retired(legacy_path: str = "") -> None:
    raise HTTPException(status_code=410, detail=LEGACY_RIFT_RETIRED_DETAIL)


def build_rift_router(*, enable_dev_routes: bool = True) -> APIRouter:
    router = APIRouter()
    for prefix in ("/api/game/rift",):
        router.add_api_route(prefix, legacy_rift_retired, methods=["GET", "POST"])
        router.add_api_route(prefix + "/{legacy_path:path}", legacy_rift_retired, methods=["GET", "POST"])
    if enable_dev_routes:
        from src.backend.features.rift.api.hex_test_router import router as hex_router

        router.include_router(hex_router)
        router.add_api_route("/api/dev/rift", legacy_rift_retired, methods=["GET", "POST"])
        router.add_api_route("/api/dev/rift/{legacy_path:path}", legacy_rift_retired, methods=["GET", "POST"])
    return router
