"""Compatibility import for analytical callers of the accepted physical GS model."""

from src.backend.features.character.runtime.gear_score_model import (
    GearScoreConfig as ExperimentalGearScoreConfig,
)
from src.backend.features.character.runtime.gear_score_model import (
    GearScoreModel as ExperimentalGearScoreCalculator,
)

__all__ = ["ExperimentalGearScoreCalculator", "ExperimentalGearScoreConfig"]
