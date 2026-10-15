"""Approved neutral base rats; legacy numerical mechanics remain unchanged."""

from copy import deepcopy

from src.backend.features.monsters.catalog.families.rats import RATS_FAMILY
from src.backend.features.monsters.catalog.presentation import MEMBER_PRESENTATION

RAT_LEGACY_VARIANTS = {
    "burrow_guard": "plague_rat",
    "ironfang": "rotfang",
    "heavy_rat": "blight_carrier",
}

PREPARED_RATS_FAMILY = deepcopy(RATS_FAMILY)
PREPARED_RATS_FAMILY["default_tags"] = ["beast", "rat", "swarm"]
for bucket, variants in PREPARED_RATS_FAMILY["hierarchy"].items():
    PREPARED_RATS_FAMILY["hierarchy"][bucket] = [
        next((new for new, old in RAT_LEGACY_VARIANTS.items() if old == variant), variant) for variant in variants
    ]
for new_id, old_id in RAT_LEGACY_VARIANTS.items():
    variant = PREPARED_RATS_FAMILY["variants"].pop(old_id)
    variant["id"] = new_id
    PREPARED_RATS_FAMILY["variants"][new_id] = variant

_DETAILS = {
    "sewer_rat": (
        "Молодая небольшая крыса с мягкой серо-коричневой шерстью и осторожным любопытным взглядом.",
        ["young", "weak"],
    ),
    "scavenger_rat": (
        "Молодая крыса-собиратель, защищающая найденный лоскут ткани.",
        ["young", "scavenger", "hoarder"],
    ),
    "swarm_rat": ("Маленькая юркая крыса, опасная вместе с остальной стаей.", ["young", "swarm"]),
    "tunnel_rat": (
        "Опытная крыса-землекоп с крупными передними когтями и старым шрамом на морде.",
        ["digger", "stealth"],
    ),
    "pack_rat": (
        "Поджарая опытная крыса, обходящая добычу с фланга и действующая вместе со стаей.",
        ["pack_tactics", "flanker"],
    ),
    "screecher": (
        "Матёрая крыса с мощным горловым мешком, предупреждающая стаю пронзительным криком.",
        ["support", "alarm"],
    ),
    "burrow_guard": (
        "Коренастый страж норы с мощными плечами, старым шрамом и простой серьгой в ухе.",
        ["guardian", "defender"],
    ),
    "ironfang": (
        "Поджарая крыса с длинной мордой, сильной челюстью и особенно крупными естественными резцами.",
        ["fangs", "fighter"],
    ),
    "heavy_rat": ("Здоровая тяжёлая крыса с широким низким телом и короткими сильными лапами.", ["heavy", "strong"]),
    "rat_brute": (
        "Огромная крыса с высокими плечами, мощными передними лапами и боевыми шрамами.",
        ["brute", "strong"],
    ),
    "brood_alpha": (
        "Опытный умный вожак выводка с надорванным ухом, направляющий остальных крыс.",
        ["leader", "alpha", "tactician"],
    ),
    "rat_king": (
        "Живой клубок крыс с переплетёнными хвостами; из него выбираются новые крысы, присоединяясь к стае.",
        ["king", "hive_mind", "summoner"],
    ),
}
for variant_id, (description, tags) in _DETAILS.items():
    variant = PREPARED_RATS_FAMILY["variants"][variant_id]
    variant["narrative_hint"] = description
    variant["extra_tags"] = tags

# Keep the agreed minion/veteran/elite/boss order after replacing legacy IDs.
PREPARED_RATS_FAMILY["variants"] = {variant_id: PREPARED_RATS_FAMILY["variants"][variant_id] for variant_id in _DETAILS}
RAT_PRESENTATION = {
    variant_id: deepcopy(MEMBER_PRESENTATION["rat_swarm"][RAT_LEGACY_VARIANTS.get(variant_id, variant_id)])
    for variant_id in _DETAILS
}
