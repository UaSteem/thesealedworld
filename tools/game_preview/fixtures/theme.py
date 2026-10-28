"""Explicit offline theme previews; these DTOs are not live gameplay state."""

from tools.game_preview.fixtures import PreviewFixture

from src.backend.features.arena.resources import ArenaResources
from src.shared.schemas.arena import ArenaScreenEnum, ArenaUIPayloadDTO
from src.shared.schemas.city_services import CityServiceScreenEnum, CityServiceUIPayloadDTO
from src.shared.schemas.exploration import (
    DetectionStatus,
    EncounterDTO,
    EncounterOptionDTO,
    EncounterType,
    EnemyPreviewDTO,
)


def build_fixture(name: str, params: dict[str, str]) -> PreviewFixture:
    context = {"char_id": 101, "status_seed": {"symbiote_name": "PREVIEW"}, "oob_panels": False}
    if name == "arena":
        context.update(
            domain="arena",
            arena=ArenaUIPayloadDTO(
                screen=ArenaScreenEnum.MODE_MENU,
                mode="one_vs_one",
                title="Схватка [1x1]",
                description="Предпросмотр очереди и доступных действий арены.",
                buttons=ArenaResources.get_mode_buttons("one_vs_one"),
                metadata={"queue_waiting_count": 2, "max_wait_limit_sec": 300},
            ),
        )
        template = "game/domains/arena/viewport/main.html"
    elif name == "services":
        context.update(
            domain="city_services",
            city_service=CityServiceUIPayloadDTO(
                service_id="preview_portal",
                service_type="portal",
                location_id="52_52",
                screen=CityServiceScreenEnum.MAIN,
                title="Площадь Рунного Круга",
                description="Предпросмотр городской службы и контакта с персонажем.",
                metadata={
                    "npc": {
                        "id": "preview_contact",
                        "name": "Оценщик",
                        "role": "PREVIEW CONTACT",
                        "stage_position": "bottom-right",
                        "dialogue_quest_key": "preview_dialogue",
                    }
                },
            ),
        )
        template = "game/domains/city_services/viewport/main.html"
    elif name == "scenario":
        context.update(
            domain="scenario",
            scenario={
                "extra_data": {"char_id": 101, "quest_title": "Предпросмотр диалога"},
                "display_name": "Рунный круг [52:52]",
                "speaker": "Проводник",
                "avatar": None,
                "text": "Рядом с каменными воротами мерцает знакомая руна. Проводник ожидает ответа.",
                "system_messages": ["PREVIEW: варианты ответа и описание сцены."],
                "is_terminal": False,
                "buttons": [
                    {
                        "action_id": "preview_listen",
                        "label": "Выслушать проводника",
                        "icon": "default",
                        "hint": "Узнать подробности.",
                    },
                    {
                        "action_id": "preview_leave",
                        "label": "Отойти от ворот",
                        "icon": "warning",
                        "hint": "Закончить разговор.",
                    },
                ],
            },
        )
        template = "game/domains/scenario/viewport/main.html"
    elif name == "exploration":
        encounter = EncounterDTO(
            id="preview_encounter",
            type=EncounterType.COMBAT,
            status=DetectionStatus.DETECTED,
            title="След у ворот",
            description="Предпросмотр обнаруженной группы и доступных решений.",
            enemies=[EnemyPreviewDTO(name="Дозорный", member_tier=1, image=None)],
            options=[EncounterOptionDTO(id="attack", label="Вступить в бой", style="danger")],
        )
        encounter.grid = {"services": []}
        context.update(
            domain="exploration",
            payload_type="exploration_encounter",
            exploration=encounter,
            encounter=encounter,
            location_view={"grid": True},
            city_map=None,
            symbiote_name="PREVIEW",
        )
        template = "game/domains/exploration/viewport/main.html"
    else:
        raise ValueError("Theme fixtures: arena, scenario, services, exploration.")
    return PreviewFixture(
        context=context,
        template=template,
        title=f"Theme PREVIEW: {name}",
        description="PREVIEW: explicit local fixture, no backend requests or live game state.",
        body_class=f"game-preview-body game-preview-body--{name}",
    )
