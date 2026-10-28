"""One-handed sword artwork trials. Python definitions are independent of the workbench JSON."""

from src.backend.features.items.dto.visuals import ItemVisualRenditionDTO, ItemVisualSetDTO, ItemVisualVariantDTO

from .sword_renders import SWORD_RENDERS

SWORD_VISUAL_SET = ItemVisualSetDTO(
    visual_set_id="sword.basic",
    base_ids=("sword",),
    width_cells=1,
    height_cells=3,
    variants=(
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.scrap_metal.t0",
            material_id="mat_scrap_metal",
            material_tier=0,
            source_path="assets/item_art/variants/sword/sword__basic__scrap_metal__t0.svg",
            condition="worn",
            description_ru="Потёртый одноручный меч. Клинок, гарда и навершие покрыты ржавчиной, обмотка рукояти изношена.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.scrap_metal.t0"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.scrap_metal.t0"]["image"]),
        ),
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.iron.t1",
            material_id="mat_iron_ingot",
            material_tier=1,
            source_path="assets/item_art/variants/sword/sword__basic__iron__t1.svg",
            condition="clean",
            description_ru="Одноручный меч с прямым железным клинком, простой гардой и коричневой обмоткой рукояти.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.iron.t1"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.iron.t1"]["image"]),
        ),
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.cobalt.t2",
            material_id="mat_cobalt_ingot",
            material_tier=2,
            source_path="assets/item_art/variants/sword/sword__basic__cobalt__t2.svg",
            condition="clean",
            description_ru="Одноручный меч с холодным синим отливом кобальтового клинка и коричневой обмоткой рукояти.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.cobalt.t2"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.cobalt.t2"]["image"]),
        ),
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.mithril.t3",
            material_id="mat_mithril_ingot",
            material_tier=3,
            source_path="assets/item_art/variants/sword/sword__basic__mithril__t3.svg",
            condition="clean",
            description_ru="Одноручный меч со светлым серебристым мифриловым клинком, простой гардой и обмотанной рукоятью.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.mithril.t3"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.mithril.t3"]["image"]),
        ),
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.adamantite.t4",
            material_id="mat_adamantite_ingot",
            material_tier=4,
            source_path="assets/item_art/variants/sword/sword__basic__adamantite__t4.svg",
            condition="clean",
            description_ru="Одноручный меч с зеленоватым адамантитовым клинком и тёмными гранями металла. Рукоять обмотана кожей.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.adamantite.t4"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.adamantite.t4"]["image"]),
        ),
        ItemVisualVariantDTO(
            visual_variant_id="sword.basic.thorium.t5",
            material_id="mat_thorium_ingot",
            material_tier=5,
            source_path="assets/item_art/variants/sword/sword__basic__thorium__t5.svg",
            condition="clean",
            description_ru="Одноручный меч с бледным зеленовато-серебристым ториевым клинком и коричневой обмоткой рукояти.",
            thumbnail=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.thorium.t5"]["thumbnail"]),
            image=ItemVisualRenditionDTO.model_validate(SWORD_RENDERS["sword.basic.thorium.t5"]["image"]),
        ),
    ),
)
