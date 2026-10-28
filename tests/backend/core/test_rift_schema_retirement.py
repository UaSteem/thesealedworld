"""The new game schema must not recreate archived node Rift tables."""

from src.backend.core.database import Base, model_imports


def test_new_game_metadata_excludes_legacy_rift_models() -> None:
    retired = {"rift_settings", "rift_node_pool_records", "rift_memberships"}
    assert not retired.intersection(Base.metadata.tables)
    assert not {"RiftSetting", "RiftNodePoolRecord", "RiftMembership"}.intersection(model_imports.__all__)
    assert {"characters", "item_instances"} <= set(Base.metadata.tables)
    assert not any(
        foreign_key.target_fullname.split(".")[0] in retired
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
