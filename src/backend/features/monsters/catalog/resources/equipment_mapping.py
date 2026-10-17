from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MonsterEquipmentKind = Literal["weapon", "armor", "shield", "ammo", "accessory"]


@dataclass(frozen=True, slots=True)
class MonsterNaturalEquipmentMapping:
    natural_key: str
    base_id: str
    item_kind: MonsterEquipmentKind
    default_slot: str
    name_ru: str | None = None
    material_id: str | None = None
    item_grade: str = "common"
    tags: tuple[str, ...] = ()
    description_ru: str | None = None


NATURAL_EQUIPMENT_MAPPINGS: dict[str, MonsterNaturalEquipmentMapping] = {
    # ── КРЫСЫ: оружие (прогрессия по ролям) ──────────────────────────
    "rat_bite_claws": MonsterNaturalEquipmentMapping(
        natural_key="rat_bite_claws",
        base_id="knife",
        name_ru="Крысиные клыки и когти",
        description_ru="Мелкие острые зубы и цепкие когти крысы. Зверёк вцепляется в добычу, чередуя короткие укусы с ударами лап.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "claws", "rat"),
    ),
    "rat_veteran_claws": MonsterNaturalEquipmentMapping(
        natural_key="rat_veteran_claws",
        base_id="dagger",
        name_ru="Острые когти крысы",
        description_ru="Длинные когти опытной крысы со сточенными кончиками. Они цепляются за шкуру добычи и помогают удерживаться в тесной схватке.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "claws", "rat"),
    ),
    "rat_elite_claws": MonsterNaturalEquipmentMapping(
        natural_key="rat_elite_claws",
        base_id="katar",
        name_ru="Мощные когти крысы",
        description_ru="Толстые загнутые когти крупной крысы. Сильные передние лапы оставляют глубокие борозды и подтягивают добычу ближе к пасти.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "claws", "rat"),
    ),
    "rat_boss_claws": MonsterNaturalEquipmentMapping(
        natural_key="rat_boss_claws",
        base_id="rapier",
        name_ru="Огромные клыки крысиного короля",
        description_ru="Крупные резцы крысиного короля с широкими основаниями и неровными краями. Сильные челюсти смыкаются на добыче тяжёлым хватательным укусом.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "claws", "rat"),
    ),
    "rat_left_claws": MonsterNaturalEquipmentMapping(
        natural_key="rat_left_claws",
        base_id="dagger",
        name_ru="Левая лапа крысы",
        description_ru="Подвижная передняя лапа с цепкими когтями. Крыса придерживает ею добычу и наносит короткие боковые удары.",
        item_kind="weapon",
        default_slot="off_hand",
        tags=("natural_weapon", "rat", "claws", "offhand"),
    ),
    "rat_offhand_bite": MonsterNaturalEquipmentMapping(
        natural_key="rat_offhand_bite",
        base_id="dagger",
        name_ru="Крысиный укус",
        description_ru="Быстрый боковой укус острыми резцами. Крыса ловит открытый участок тела, пока лапы удерживают добычу рядом.",
        item_kind="weapon",
        default_slot="off_hand",
        tags=("natural_weapon", "rat", "bite", "fangs", "offhand"),
    ),
    "rat_bone_growth": MonsterNaturalEquipmentMapping(
        natural_key="rat_bone_growth",
        base_id="buckler",
        name_ru="Костяные наросты крысы",
        description_ru="Неровные костяные выступы под огрубевшей кожей плеч. Крыса разворачивает корпус и подставляет их под встречный удар.",
        item_kind="shield",
        default_slot="off_hand",
        tags=("natural_shield", "rat", "bone_growth", "block"),
    ),
    "rat_spiked_growth": MonsterNaturalEquipmentMapping(
        natural_key="rat_spiked_growth",
        base_id="shield",
        name_ru="Шипастые наросты крысы",
        description_ru="Толстые костяные шипы на плечах и спине крупной крысы. Прижавшись к земле, зверь прикрывает ими шею и бока.",
        item_kind="shield",
        default_slot="off_hand",
        tags=("natural_shield", "rat", "spikes", "block", "counter"),
    ),
    "rat_poison_spit": MonsterNaturalEquipmentMapping(
        natural_key="rat_poison_spit",
        base_id="shortbow",
        name_ru="Ядовитый плевок крысы",
        description_ru="Сгусток едкой слюны, который крыса выбрасывает резким движением пасти. Такой плевок позволяет достать добычу на расстоянии.",
        item_kind="weapon",
        default_slot="two_hand",
        tags=("natural_weapon", "rat", "poison", "spit", "ranged"),
    ),
    "rat_poison_glands": MonsterNaturalEquipmentMapping(
        natural_key="rat_poison_glands",
        base_id="quiver_training",
        name_ru="Ядовитые железы крысы",
        description_ru="Развитые железы у основания челюстей. В них скапливается густой секрет, который крыса расходует на дальние плевки.",
        item_kind="ammo",
        default_slot="quiver",
        tags=("natural_ammo", "rat", "poison", "glands"),
    ),
    "rat_crushing_bite": MonsterNaturalEquipmentMapping(
        natural_key="rat_crushing_bite",
        base_id="warhammer",
        name_ru="Давящий крысиный укус",
        description_ru="Массивные челюсти с широкими резцами. Крыса наваливается на добычу всем телом и сжимает её тяжёлым укусом.",
        item_kind="weapon",
        default_slot="two_hand",
        tags=("natural_weapon", "rat", "bite", "crushing", "two_handed"),
    ),
    # ── КРЫСЫ: броня ─────────────────────────────────────────────────
    "rat_light_hide": MonsterNaturalEquipmentMapping(
        natural_key="rat_light_hide",
        base_id="leather_armor",
        name_ru="Лёгкая звериная шкура",
        description_ru="Тонкая гибкая шкура под короткой шерстью крысы. Она прикрывает тело, сохраняя подвижность в узких проходах.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "rat", "hide", "light"),
    ),
    "rat_medium_hide": MonsterNaturalEquipmentMapping(
        natural_key="rat_medium_hide",
        base_id="jerkin",
        name_ru="Плотная шкура крысы",
        description_ru="Огрубевшая шкура взрослой крысы со старыми рубцами и редкой жёсткой шерстью. Плотные складки прикрывают бока и плечи.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "rat", "hide", "medium"),
    ),
    "rat_heavy_hide": MonsterNaturalEquipmentMapping(
        natural_key="rat_heavy_hide",
        base_id="plate_chest",
        name_ru="Толстая шкура крупной крысы",
        description_ru="Толстая складчатая шкура тяжёлой крысы. На груди и загривке она огрубела от старых укусов и постоянного трения о камень.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "rat", "hide", "heavy"),
    ),
    # ── КРЫСЫ: бижутерия / природный фокус ──────────────────────────
    "rat_plague_gland": MonsterNaturalEquipmentMapping(
        natural_key="rat_plague_gland",
        base_id="amulet",
        name_ru="Заражённая железа крысы",
        description_ru="Плотный узел железистой ткани под кожей крысы. Сквозь тонкую оболочку проступает мутный секрет с резким звериным запахом.",
        item_kind="accessory",
        default_slot="amulet",
        tags=("natural_jewelry", "rat", "plague_gland", "magic_armor"),
    ),
    # ── ВОЛКИ: оружие ────────────────────────────────────────────────
    "wolf_young_fangs": MonsterNaturalEquipmentMapping(
        natural_key="wolf_young_fangs",
        base_id="dagger",
        name_ru="Молодые волчьи клыки",
        description_ru="Короткие острые клыки молодого волка. Быстрый укус цепляет добычу и помогает удержаться рядом с ней.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "wolf"),
    ),
    "wolf_bite_claws": MonsterNaturalEquipmentMapping(
        natural_key="wolf_bite_claws",
        base_id="rapier",
        name_ru="Волчьи клыки и когти",
        description_ru="Крепкие клыки и загнутые когти взрослого волка. Хищник вцепляется в добычу и рвёт её короткими рывками.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "claws", "wolf"),
    ),
    "wolf_elite_fangs": MonsterNaturalEquipmentMapping(
        natural_key="wolf_elite_fangs",
        base_id="rapier",
        name_ru="Мощные клыки хищника",
        description_ru="Длинные клыки матёрого хищника с широкими основаниями. Глубокий укус позволяет удерживать сопротивляющуюся добычу.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "wolf"),
    ),
    "wolf_alpha_fangs": MonsterNaturalEquipmentMapping(
        natural_key="wolf_alpha_fangs",
        base_id="rapier",
        name_ru="Клыки Альфы",
        description_ru="Крупные клыки вожака, потемневшие у корней и отмеченные сколами. Альфа впивается в добычу и тянет её на себя всей тяжестью тела.",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("natural_weapon", "fangs", "claws", "wolf"),
    ),
    "wolf_young_claws": MonsterNaturalEquipmentMapping(
        natural_key="wolf_young_claws",
        base_id="knife",
        name_ru="Молодые волчьи когти",
        description_ru="Тонкие когти на подвижных лапах молодого волка. Они цепляют землю при броске и царапают добычу в ближней схватке.",
        item_kind="weapon",
        default_slot="off_hand",
        tags=("natural_weapon", "claws", "wolf", "offhand", "swift"),
    ),
    "wolf_raking_claws": MonsterNaturalEquipmentMapping(
        natural_key="wolf_raking_claws",
        base_id="katar",
        name_ru="Раздирающие волчьи когти",
        description_ru="Толстые загнутые когти с неровными краями. Волк впивается ими в добычу и оставляет глубокие рваные борозды.",
        item_kind="weapon",
        default_slot="off_hand",
        tags=("natural_weapon", "claws", "wolf", "offhand", "piercing"),
    ),
    "wolf_locking_fangs": MonsterNaturalEquipmentMapping(
        natural_key="wolf_locking_fangs",
        base_id="main_gauche",
        name_ru="Удерживающий волчий захват",
        description_ru="Плотно смыкающиеся клыки и сильные челюсти. Волк цепляется за конечность или шкуру добычи, сдерживая её движения.",
        item_kind="weapon",
        default_slot="off_hand",
        tags=("natural_weapon", "fangs", "wolf", "offhand", "control"),
    ),
    "wolf_braced_mane": MonsterNaturalEquipmentMapping(
        natural_key="wolf_braced_mane",
        base_id="buckler",
        name_ru="Жёсткий волчий загривок",
        description_ru="Плотная складка шкуры и жёсткая шерсть на загривке. Волк подставляет крепкую шею под удар, прикрывая более уязвимые участки тела.",
        item_kind="shield",
        default_slot="off_hand",
        tags=("natural_shield", "wolf", "mane", "block", "counter"),
    ),
    "wolf_bone_shoulders": MonsterNaturalEquipmentMapping(
        natural_key="wolf_bone_shoulders",
        base_id="shield",
        name_ru="Костистые плечи волка",
        description_ru="Массивные плечи с плотной кожей над выступающими костями. Разворачивая корпус, волк встречает удар самой крепкой частью тела.",
        item_kind="shield",
        default_slot="off_hand",
        tags=("natural_shield", "wolf", "shoulders", "block", "guard"),
    ),
    # ── ВОЛКИ: броня ─────────────────────────────────────────────────
    "wolf_hide": MonsterNaturalEquipmentMapping(
        natural_key="wolf_hide",
        base_id="leather_armor",
        name_ru="Лёгкая волчья шкура",
        description_ru="Гибкая шкура под коротким плотным мехом. Она прикрывает тело молодого волка, не сковывая его резких движений.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "wolf", "hide", "light"),
    ),
    "wolf_medium_hide": MonsterNaturalEquipmentMapping(
        natural_key="wolf_medium_hide",
        base_id="jerkin",
        name_ru="Плотная волчья шкура",
        description_ru="Огрубевшая шкура взрослого волка под густой шерстью. На боках и спине видны старые следы укусов и зажившие рубцы.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "wolf", "hide", "medium"),
    ),
    "wolf_heavy_hide": MonsterNaturalEquipmentMapping(
        natural_key="wolf_heavy_hide",
        base_id="plate_chest",
        name_ru="Толстая шкура матёрого волка",
        description_ru="Толстая рубцовая шкура с густым слежавшимся мехом. Плотные складки прикрывают шею, грудь и бока тяжёлого хищника.",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("natural_armor", "wolf", "hide", "heavy"),
    ),
    "wolf_pack_mark": MonsterNaturalEquipmentMapping(
        natural_key="wolf_pack_mark",
        base_id="amulet",
        name_ru="Метка волчьей стаи",
        description_ru="Слабый природный отпечаток стаи в запахе и поведении волка. Он узнаётся сородичами и связывает хищника с его сворой.",
        item_kind="accessory",
        default_slot="amulet",
        tags=("natural_jewelry", "wolf", "pack_mark", "magic_armor"),
    ),
    # ── ЯКОРНЫЕ БОССЫ: оружие ────────────────────────────────────────
    "anchor_stasis_crown_blade": MonsterNaturalEquipmentMapping(
        natural_key="anchor_stasis_crown_blade",
        base_id="rapier",
        name_ru="Лезвие Северного Стазиса",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("anchor", "stasis", "frost", "boss_weapon", "one_handed"),
    ),
    "anchor_entropy_cinder_maul": MonsterNaturalEquipmentMapping(
        natural_key="anchor_entropy_cinder_maul",
        base_id="warhammer",
        name_ru="Пепельный Молот Южной Энтропии",
        item_kind="weapon",
        default_slot="two_hand",
        tags=("anchor", "entropy", "ash_storm", "boss_weapon", "two_handed"),
    ),
    "anchor_gravity_storm_lance": MonsterNaturalEquipmentMapping(
        natural_key="anchor_gravity_storm_lance",
        base_id="rapier",
        name_ru="Штормовое Копьё Западной Гравитации",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("anchor", "gravity", "lightning", "boss_weapon", "one_handed"),
    ),
    "anchor_evolution_bloom_talons": MonsterNaturalEquipmentMapping(
        natural_key="anchor_evolution_bloom_talons",
        base_id="katar",
        name_ru="Когти Восточной Эволюции",
        item_kind="weapon",
        default_slot="main_hand",
        tags=("anchor", "evolution", "living_jungle", "boss_weapon", "dual_wield"),
    ),
    # ── ЯКОРНЫЕ БОССЫ: броня ─────────────────────────────────────────
    "anchor_projection_aegis": MonsterNaturalEquipmentMapping(
        natural_key="anchor_projection_aegis",
        base_id="plate_chest",
        name_ru="Оболочка Анкорной Проекции",
        item_kind="armor",
        default_slot="chest_armor",
        tags=("anchor", "projection", "natural_armor", "raid_boss"),
    ),
}


def get_natural_equipment_mapping(natural_key: str) -> MonsterNaturalEquipmentMapping:
    mapping = NATURAL_EQUIPMENT_MAPPINGS.get(natural_key)
    if mapping is None:
        raise ValueError(f"Unknown monster natural equipment key: {natural_key}")
    return mapping
