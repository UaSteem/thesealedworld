GARMENT_DB = {
    "basic": {
        "boots": {
            "id": "boots",
            "name_ru": "Ботинки",
            "slot": "feetwear",
            "type": "garment",
            "allowed_materials": ["leathers"],
            "base_power": 0,
            "base_durability": 30,
            "damage_spread": 0.0,
            "narrative_description": "Ботинки закрывают ступни и защищают их при ходьбе.",
            "narrative_tags": ["boots", "garment", "travel", "feetwear"],
            "implicit_bonuses": {"stamina": 10.0, "stamina_regen": 1.5},
        },
        "gloves": {
            "id": "gloves",
            "name_ru": "Перчатки",
            "slot": "gloves_garment",
            "type": "garment",
            "allowed_materials": ["cloths", "leathers"],
            "base_power": 0,
            "base_durability": 25,
            "damage_spread": 0.0,
            "narrative_description": "Перчатки закрывают кисти и пальцы, сохраняя удобный хват.",
            "narrative_tags": ["gloves", "garment", "grip"],
            "implicit_bonuses": {"anti_dodge_chance": 0.04, "physical_crit_chance": 0.01},
        },
        "cloak": {
            "id": "cloak",
            "name_ru": "Плащ",
            "slot": "outer_garment",
            "type": "garment",
            "allowed_materials": ["cloths", "leathers"],
            "base_power": 0,
            "base_durability": 45,
            "damage_spread": 0.0,
            "narrative_description": "Плащ накидывается поверх одежды и брони, прикрывая плечи и спину.",
            "narrative_tags": ["cloak", "garment", "outerwear"],
            "implicit_bonuses": {"hp_regen": 0.5},
        },
    }
}

__all__ = ["GARMENT_DB"]
