"""Author reusable monster equipment once. Read paths never invoke this tool.

The ItemFactory supplies scaled base mechanics. Explicit monster profiles then
receive existing catalog affix rolls/compilation, not random player loot pools.
No persistence, external inference or combat simulation is involved.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pprint
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO  # noqa: E402
from src.backend.features.items.resources.affixes.catalog import AFFIX_CATALOG  # noqa: E402
from src.backend.features.items.runtime.item_factory import ItemFactory  # noqa: E402
from src.backend.features.monsters.catalog import get_catalog  # noqa: E402
from src.backend.features.monsters.catalog.equipment_library.contracts import EquipmentItemDefinitionDTO  # noqa: E402
from src.backend.features.monsters.catalog.equipment_library.profiles import PROFILES  # noqa: E402
from src.backend.features.monsters.catalog.families.goblin_catalog.equipment.references import (  # noqa: E402
    profile_for,
    references_for,
)
from src.backend.features.monsters.catalog.resources.item_affix_profiles import (  # noqa: E402
    get_monster_affix_step_count,
)

SEED_VERSION = "shared-monster-equipment-v1"
DEFAULT_OUTPUT = ROOT / "src/backend/features/monsters/catalog/equipment_library"


def read_data(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DATA" for target in node.targets)
    ]
    if len(values) != 1:
        raise ValueError("Expected one literal DATA assignment")
    return ast.literal_eval(values[0])


def build_definitions() -> dict:
    factory = ItemFactory()
    definitions = {}
    for member in get_catalog().members.values():
        if member.family_id != "goblin_tribe":
            continue
        for tier in range(member.min_tier, member.max_tier + 1):
            for reference in references_for(member, tier):
                if reference.item_id in definitions:
                    continue
                base_id = member.fixed_loadout[reference.slot]
                profile_id = profile_for(member, reference.slot, base_id)
                seed = f"{SEED_VERSION}:{base_id}:{reference.slot}:{profile_id}"
                item = factory.generate_runtime_item(
                    ItemGenerationRequestDTO(
                        base_id=base_id,
                        target_slot=reference.slot,
                        rarity_tier=tier,
                        affix_count=0,
                        request_ai_text=False,
                        origin_ref=ItemOriginRefDTO(seed=seed),
                        source_context={"authoring_profile": profile_id, "seed_version": SEED_VERSION},
                    )
                )
                material = factory.catalog.get_material(item.material_id)
                steps = get_monster_affix_step_count(tier)

                # A fixed middle roll is deliberately authored, using the same
                # existing roll formula, rounding and step policy as ItemService.
                class MiddleRoll(random.Random):
                    def uniform(self, a, b):
                        return (a + b) / 2

                rng = MiddleRoll(seed)
                affixes = []
                for key in PROFILES[profile_id]:
                    entry = AFFIX_CATALOG[key]
                    if entry.technical.min_item_tier > tier:
                        continue
                    rolled = factory._roll_affix(entry, material.tier_mult, rng, item_tier=tier, affix_step_count=steps)
                    if float(rolled["value"]) <= 0:
                        continue
                    rolled["source"] = f"authored:{profile_id}"
                    affixes.append(rolled)
                item.mechanics["affixes"] = affixes
                item.bonuses = factory._compile_affix_bonuses(affixes)
                item.metadata["affix_profile"] = f"authored_monster:{profile_id}"
                item.instance_id = reference.item_id
                projection = factory.project_runtime_item(item)
                record = EquipmentItemDefinitionDTO(
                    id=reference.item_id, tier=tier, profile_id=profile_id, item=projection
                )
                definitions[reference.item_id] = record.model_dump(mode="json")
    return dict(sorted(definitions.items()))


def validate(output: Path) -> dict[str, int]:
    index = read_data(output / "prepared/index.py")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        path = output / relative
        if not path.resolve().is_relative_to(output.resolve()):
            raise ValueError("Unsafe manifest path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Manual changes detected; review before refreshing manifest")
    for key, module in index.items():
        raw = read_data(output / "prepared" / (module.replace(".", "/") + ".py"))
        item = EquipmentItemDefinitionDTO.model_validate(raw)
        if item.id != key:
            raise ValueError("Catalog item identity differs from key")
    sets = assignments = 0
    for member in get_catalog().members.values():
        if member.family_id != "goblin_tribe":
            continue
        for tier in range(member.min_tier, member.max_tier + 1):
            refs = references_for(member, tier)
            if any(ref.item_id not in index for ref in refs):
                raise ValueError("Missing shared item reference")
            sets += 1
            assignments += len(refs)
    return {"definitions": len(index), "sets": sets, "assignments": assignments}


def write_prepared(output: Path) -> dict[str, int]:
    if (output / "prepared").exists():
        raise FileExistsError(f"Refusing to overwrite prepared items: {output}")
    data = build_definitions()
    files = {}
    index = {}
    for key, definition in data.items():
        base_id, slot, profile, tier = key.split(".")
        module = f"{profile}.{base_id}_{slot}.tier_{tier.removeprefix('t')}"
        index[key] = module
        relative = "prepared/" + module.replace(".", "/") + ".py"
        files[relative] = (
            '"""Authored shared mechanics. Edit deliberately."""\n\nDATA = '
            + pprint.pformat(definition, sort_dicts=False, width=110)
            + "\n"
        ).encode()
    files["prepared/index.py"] = ("DATA = " + pprint.pformat(index, sort_dicts=True, width=110) + "\n").encode()
    output.mkdir(parents=True, exist_ok=True)
    for relative, content in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        for parent in path.parents:
            if parent == output:
                break
            (parent / "__init__.py").touch(exist_ok=True)
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "seed_version": SEED_VERSION,
                "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
                "definition_count": len(data),
                "authoring": "Shared authored monster profiles, median rolls; existing tier/tick rules.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return validate(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(args.output) if args.validate_only else write_prepared(args.output)))


if __name__ == "__main__":
    main()
