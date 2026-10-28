from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.backend.features.items.dto.visuals import ItemVisualPublicDTO


class GameCatalogManifestDTO(BaseModel):
    version: str
    catalogs: dict[str, str] = Field(default_factory=dict)


class GameCatalogBootstrapDTO(BaseModel):
    version: str
    catalogs: dict[str, dict[str, dict[str, Any]]] = Field(default_factory=dict)
    manifest: GameCatalogManifestDTO

    @field_validator("catalogs")
    @classmethod
    def validate_item_visuals(
        cls, catalogs: dict[str, dict[str, dict[str, Any]]]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        if "item_visuals" in catalogs:
            catalogs["item_visuals"] = {
                key: ItemVisualPublicDTO.model_validate(value).model_dump(mode="json")
                for key, value in catalogs["item_visuals"].items()
            }
        return catalogs
