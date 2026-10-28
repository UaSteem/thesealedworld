"""Public labels for carried retired items; never an active generation catalog.

Frozen public text only. No stats, valid slots, generated names or private lore.
Source definitions are archived in archive/equipment_slots_2026_10_25/.
Historical IDs here resolve presentation only; generation/equip still reject them.
"""

from types import MappingProxyType

RETIRED_ITEM_PRESENTATIONS = MappingProxyType(
    {
        "apron": ("Фартук", "Рабочий фартук с карманами для мелких инструментов и расходников."),
        "shirt": ("Рубаха", "Рубаха закрывает корпус и надевается отдельным слоем под броню."),
        "tunic": ("Туника", "Туника свободного кроя закрывает корпус и надевается отдельным слоем под броню."),
        "pants": ("Штаны", "Штаны закрывают ноги и надеваются отдельным слоем под поножи."),
        "linen_shirt": ("Рубаха", "Рубаха закрывает корпус и надевается отдельным слоем под броню."),
        "wool_tunic": ("Туника", "Туника свободного кроя закрывает корпус и надевается отдельным слоем под броню."),
        "fur_pants": ("Штаны", "Штаны закрывают ноги и надеваются отдельным слоем под поножи."),
    }
)
