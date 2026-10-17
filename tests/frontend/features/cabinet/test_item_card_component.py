from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.frontend.integrations.backend_api.item_presentation import ItemCard


def render_card(**overrides):
    card = ItemCard(
        title="Мифриловый кинжал", description="Лёгкий клинок.",
        material_label="Мифрил", rarity_label="Редкий", slot_label="Правая рука",
        power_label="Сила оружия", power_value="6,6", **overrides,
    )
    environment = Environment(
        loader=FileSystemLoader(Path("src/fastapi_cabinet/templates")),
        autoescape=select_autoescape(),
    )
    return environment.get_template("components/items/card.html").render(card=card)


def test_card_shows_readable_values_and_closed_technical_panel():
    html = render_card(
        bonuses=[{"label": "Точность", "value": "+3,33%"}],
        technical={"base_id": "knife"},
    )
    assert "Мифриловый кинжал" in html
    assert "Точность" in html and "+3,33%" in html
    assert '<details class="item-card__technical">' in html
    assert '<details open' not in html
    assert html.index("knife") > html.index("Технические данные")


def test_card_can_be_reused_without_debug_data():
    html = render_card()
    assert "Мифриловый кинжал" in html
    assert "Технические данные" not in html
