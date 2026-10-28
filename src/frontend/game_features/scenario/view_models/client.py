"""Public scenario presentation, independent from scenario execution or persistence."""

from collections.abc import Mapping
from html.parser import HTMLParser
from math import isfinite
from typing import Any

from src.shared.schemas.scenario import ScenarioPayloadDTO

_MISSING = object()
_WIDGET_TYPES = frozenset({"key_value", "list", "meter_list", "text"})
_ITEM_FIELDS = ("key", "label", "value", "display_value", "percent", "catalog", "catalog_key")
_BLOCK_TAGS = frozenset({"div", "p", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6"})


class _ScenarioTextParser(HTMLParser):
    """Decode known formatter HTML as text; never emit an HTML node or attribute."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.blocked: list[str] = []

    def _line_break(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.blocked.append(tag)
        elif not self.blocked:
            if tag == "br":
                self.parts.append("\n")
            elif tag in _BLOCK_TAGS:
                self._line_break()

    def handle_endtag(self, tag: str) -> None:
        if self.blocked:
            if tag == self.blocked[-1]:
                self.blocked.pop()
        elif tag in _BLOCK_TAGS:
            self._line_break()

    def handle_data(self, data: str) -> None:
        if not self.blocked:
            self.parts.append(data)


def scenario_plain_text(value: str) -> str:
    """The canvas receives literal text, including decoded entities and line breaks."""
    parser = _ScenarioTextParser()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts).replace("\r\n", "\n").strip()


def _scalar(value: Any) -> Any:
    if isinstance(value, str):
        return scenario_plain_text(value)
    if isinstance(value, bool | int):
        return value
    if isinstance(value, float) and isfinite(value):
        return value
    return _MISSING


def _selected_scalars(source: Mapping, fields: tuple[str, ...]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for field in fields:
        value = _scalar(source.get(field))
        if value is not _MISSING:
            selected[field] = value
    return selected


def _right_panel(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    widgets = value.get("widgets")
    if not isinstance(widgets, list):
        return None
    output = []
    for widget in widgets:
        if not isinstance(widget, Mapping) or widget.get("type") not in _WIDGET_TYPES:
            continue
        item: dict[str, Any] = {"type": widget["type"]}
        if isinstance(widget.get("title"), str):
            item["title"] = scenario_plain_text(widget["title"])
        if isinstance(widget.get("visible"), bool):
            item["visible"] = widget["visible"]
        if isinstance(widget.get("items"), list):
            item["items"] = [
                selected
                for row in widget["items"]
                if isinstance(row, Mapping)
                if (selected := _selected_scalars(row, _ITEM_FIELDS))
            ]
        data = widget.get("data")
        if isinstance(data, Mapping) and isinstance(data.get("text"), str):
            item["data"] = {"text": scenario_plain_text(data["text"])}
        output.append(item)
    return {"widgets": output}


def _public_extra(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    result = _selected_scalars(value, ("quest_title", "background_url", "npc_reputation", "npc_affinity"))
    reputation = value.get("reputation")
    if isinstance(reputation, Mapping):
        result["reputation"] = _selected_scalars(reputation, ("npc", "faction"))
    if isinstance(value.get("rewards"), list):
        rewards = []
        for reward in value["rewards"]:
            if isinstance(reward, Mapping):
                selected = _selected_scalars(reward, ("label", "value"))
                if selected:
                    rewards.append(selected)
            elif isinstance(reward, str):
                rewards.append(scenario_plain_text(reward))
        result["rewards"] = rewards
    if (panel := _right_panel(value.get("right_panel"))) is not None:
        result["right_panel"] = panel
    return result


def build_scenario_client_payload(scenario: ScenarioPayloadDTO, char_id: int) -> dict[str, Any]:
    """Project existing authoritative fields without exposing flattened runtime context."""
    return {
        "char_id": char_id,
        "node_key": scenario.node_key,
        "node_type": scenario.node_type,
        "phase": scenario.phase,
        "speaker": scenario_plain_text(scenario.speaker) if scenario.speaker is not None else None,
        "display_name": scenario_plain_text(scenario.display_name) if scenario.display_name is not None else None,
        "icon": scenario.icon,
        "avatar": scenario.avatar,
        "text": scenario_plain_text(scenario.text),
        "system_messages": [scenario_plain_text(message) for message in scenario.system_messages],
        "status_bar": [scenario_plain_text(message) for message in scenario.status_bar],
        "buttons": [
            {"action_id": button.action_id, "label": scenario_plain_text(button.label), "icon": button.icon}
            for button in scenario.buttons
        ],
        "is_terminal": scenario.is_terminal,
        "extra_data": _public_extra(scenario.extra_data),
    }
