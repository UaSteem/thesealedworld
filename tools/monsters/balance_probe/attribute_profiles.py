"""Canonical starter allocations with an offline uniform experimental control."""

from src.backend.features.character.resources.starting_imprints import ATTRIBUTE_KEYS, STARTING_IMPRINTS

KEYS = ATTRIBUTE_KEYS
VALUES = {
    key: tuple(dict(imprint.attribute_values)[attribute] for attribute in KEYS)
    for key, imprint in STARTING_IMPRINTS.items()
}
ALLOCATIONS = {key: dict(zip(KEYS, values, strict=True)) for key, values in VALUES.items()}
