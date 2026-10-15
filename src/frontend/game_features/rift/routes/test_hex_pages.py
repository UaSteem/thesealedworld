from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from src.frontend.config.settings import settings
from src.frontend.core.renderer import UIRenderer, get_ui_renderer

router = APIRouter(tags=["Rift-Hex-Test"])
RANDOM_LAYOUT_SCHEME_KEY = "__random__"
HEX_RIFT_BACKEND_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


@router.get("/rifttest", name="test_hex_rift")
async def test_hex_rift(
    request: Request,
    ui: Annotated[UIRenderer, Depends(get_ui_renderer)],
    instance_id: Annotated[str | None, Query()] = None,
    seed: Annotated[str | None, Query()] = None,
    scale_key: Annotated[str, Query()] = "solo",
    scheme_key: Annotated[str | None, Query()] = None,
    pattern_key: Annotated[str | None, Query()] = None,
    show_all_map: Annotated[bool, Query()] = False,
):
    if not settings.enable_dev_rift_routes:
        raise HTTPException(status_code=404)

    async with httpx.AsyncClient(base_url=settings.backend_base_url, timeout=HEX_RIFT_BACKEND_TIMEOUT) as client:
        if not instance_id:
            # Start new hex rift
            params = {}
            if seed:
                params["seed"] = seed
            if scale_key:
                params["scale_key"] = scale_key
            if scheme_key:
                params["scheme_key"] = scheme_key
            if pattern_key:
                params["pattern_key"] = pattern_key
            if show_all_map:
                params["show_all_map"] = "true"
            response = await client.post("/api/dev/rift/hex-test/start", params=params)
            response.raise_for_status()
            state = response.json()
            instance_id = state["instance_id"]
            scale_query = f"&scale_key={scale_key}" if scale_key else ""
            scheme_query = f"&scheme_key={scheme_key}" if scheme_key else ""
            pattern_query = f"&pattern_key={pattern_key}" if pattern_key else ""
            show_all_query = "&show_all_map=true" if show_all_map else ""
            return RedirectResponse(
                url=f"/rifttest?instance_id={instance_id}{scale_query}{scheme_query}{pattern_query}{show_all_query}",
                status_code=303,
            )
        else:
            response = await client.get(
                f"/api/dev/rift/hex-test/{instance_id}/state",
                params={"show_all_map": show_all_map},
            )
            response.raise_for_status()
            state = response.json()

    context = {
        "char_id": 0,
        "domain": "rift",
        "rift": state,
        "instance_id": instance_id,
        "selected_scale_key": scale_key or state.get("scale_key"),
        "selected_scheme_key": scheme_key or state.get("scheme_key"),
        "selected_pattern_key": pattern_key
        or state.get("pattern_key")
        or state.get("layout_template_debug", {}).get("geometry_pattern"),
        "show_all_map": show_all_map,
        "random_scheme_key": RANDOM_LAYOUT_SCHEME_KEY,
        "status_seed": {
            "character_id": 0,
            "name": "Rift tester",
            "symbiote_name": "SYSTEM",
            "hp": 1,
            "max_hp": 1,
            "energy": 1,
            "max_energy": 1,
            "stamina": 1,
            "max_stamina": 1,
            "avatar_url": None,
            "gear_score": 0,
        },
        "character_status": {
            "char_id": 0,
            "bio": {"name": "Rift tester", "avatar": None},
            "vitals": {
                "hp": {"cur": 1, "max": 1},
                "energy": {"cur": 1, "max": 1},
                "stamina": {"cur": 1, "max": 1},
            },
            "attributes": {
                "strength": 10,
                "agility": 10,
                "endurance": 10,
                "intellect": 10,
                "memory": 10,
                "mental": 10,
                "perception": 10,
                "projection": 10,
                "prediction": 10,
            },
            "skills": {},
            "metrics": {"gear_score": 0},
        },
    }
    return await ui.render("game/test_hex_rift.html", context=context)


@router.post("/game/rift/hex-test/move", name="game_rift_hex_move")
async def game_rift_hex_move(
    instance_id: Annotated[str, Form()],
    target_x: Annotated[int, Form()],
    target_y: Annotated[int, Form()],
):
    async with httpx.AsyncClient(base_url=settings.backend_base_url, timeout=HEX_RIFT_BACKEND_TIMEOUT) as client:
        response = await client.post(
            f"/api/dev/rift/hex-test/{instance_id}/move", json={"target_x": target_x, "target_y": target_y}
        )
        response.raise_for_status()

    return RedirectResponse(url=f"/rifttest?instance_id={instance_id}", status_code=303)


@router.post("/game/rift/hex-test/resolve-combat", name="game_rift_hex_resolve_combat")
async def game_rift_hex_resolve_combat(
    instance_id: Annotated[str, Form()],
    action: Annotated[str, Form()],
):
    async with httpx.AsyncClient(base_url=settings.backend_base_url, timeout=HEX_RIFT_BACKEND_TIMEOUT) as client:
        response = await client.post(f"/api/dev/rift/hex-test/{instance_id}/resolve-combat", json={"action": action})
        response.raise_for_status()

    return RedirectResponse(url=f"/rifttest?instance_id={instance_id}", status_code=303)


@router.post("/game/rift/hex-test/next-floor", name="game_rift_hex_next_floor")
async def game_rift_hex_next_floor(
    instance_id: Annotated[str, Form()],
):
    async with httpx.AsyncClient(base_url=settings.backend_base_url, timeout=HEX_RIFT_BACKEND_TIMEOUT) as client:
        response = await client.post(f"/api/dev/rift/hex-test/{instance_id}/next-floor")
        response.raise_for_status()

    return RedirectResponse(url=f"/rifttest?instance_id={instance_id}", status_code=303)
