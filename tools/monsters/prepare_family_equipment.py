"""Prepare editable, deterministic family equipment via ItemService, without persistence."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import pprint
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO  # noqa: E402
from src.backend.features.items.services.generation_service import ItemGenerationService  # noqa: E402
from src.backend.features.monsters.catalog.families.bandit_catalog.family import BANDIT_FAMILY  # noqa: E402
from src.backend.features.monsters.catalog.families.rat_catalog.family import RAT_FAMILY  # noqa: E402
from src.backend.features.monsters.catalog.nested_contracts import resolve_family  # noqa: E402
from src.backend.features.monsters.instances.integrations.item_generation import (  # noqa: E402
    build_monster_item_request,
    to_item_generation_request,
)

FAMILIES = {"rat_swarm": (RAT_FAMILY, "rat_catalog"), "bandit_gang": (BANDIT_FAMILY, "bandit_catalog")}


def item_kind(slot: str, base_id: str) -> str:
    """Classify the authored narrow loadout without changing its item bases."""
    if slot == "quiver" or base_id.startswith("quiver_"):
        return "ammo"
    if slot == "amulet":
        return "accessory"
    if base_id in {"shield", "buckler", "kite_shield"}:
        return "shield"
    return "weapon" if slot in {"main_hand", "off_hand", "two_hand"} else "armor"


def default_output(family_id: str) -> Path:
    return ROOT / "src/backend/features/monsters/catalog/families" / FAMILIES[family_id][1] / "equipment/prepared"


def seed_version(family_id: str) -> str:
    return f"{family_id}-prepared-equipment-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def prepare_payloads(family_id: str) -> tuple[dict[str, dict], list[dict]]:
    """Only the pure runtime-projection method is called; no DB or AI client exists."""
    service = ItemGenerationService(persistence=None, generation_ai=None)
    _, _, members = resolve_family(FAMILIES[family_id][0])
    payloads, provenance = {}, []
    for member in sorted(members, key=lambda m: m.id):
        for tier in range(member.min_tier, member.max_tier + 1):
            owner = f"{member.id}:tier:{tier}"
            requests = []
            for slot, base_id in sorted(member.fixed_loadout.items()):
                if not base_id:
                    continue
                seed = f"{seed_version(family_id)}:{owner}:{member.role}:{slot}"
                request = to_item_generation_request(
                    build_monster_item_request(
                        owner_key=owner,
                        family_id=member.family_id,
                        member_role=member.role,
                        member_tier=tier,
                        slot=slot,
                        **(
                            {"natural_key": base_id}
                            if family_id == "rat_swarm"
                            else {"base_id": base_id, "item_kind": item_kind(slot, base_id)}
                        ),
                        seed=seed,
                        source_context={"variant_id": member.variant_id, "slot": slot, "effective_tier": tier},
                    )
                )
                request.runtime_metadata["runtime_item_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
                requests.append(request)
            items = await service.generate_runtime_projections(requests)
            relative = f"{member.variant_id}/tier_{tier}.py"
            payloads[relative] = {
                "schema_version": 1,
                "family_id": member.family_id,
                "clan_id": member.clan_id,
                "variant_id": member.variant_id,
                "equipment_set_id": f"{member.family_id}.{member.base_id}",
                "role": member.role,
                "tier": tier,
                "seed_version": seed_version(family_id),
                "items": [item.model_dump(mode="json") for item in items],
            }
            provenance.append({"path": relative, "requests": [r.model_dump(mode="json") for r in requests]})
    return payloads, provenance


def read_data(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DATA" for target in node.targets)
    ]
    if len(values) != 1:
        raise ValueError(f"Expected one literal DATA assignment: {path}")
    return ast.literal_eval(values[0])


def validate(output: Path, family_id: str) -> dict[str, int]:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["family_id"] != family_id:
        raise ValueError("Manifest family mismatch")
    expected_paths = {
        f"{member.variant_id}/tier_{tier}.py"
        for member in resolve_family(FAMILIES[family_id][0])[2]
        for tier in range(member.min_tier, member.max_tier + 1)
    }
    if set(manifest["files"]) != expected_paths:
        raise ValueError("Manifest does not cover the authored catalog")
    inputs = {entry["path"]: entry["requests"] for entry in manifest["inputs"]}
    if len(inputs) != len(manifest["inputs"]) or set(inputs) != expected_paths:
        raise ValueError("Manifest input coverage mismatch")
    for relative, expected_hash in manifest["sources"].items():
        source = ROOT / relative
        if not source.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Unsafe source manifest path")
        if digest(source.read_bytes()) != expected_hash:
            raise ValueError(f"Generation source has changed: {relative}")
    item_count = 0
    for relative, expected_hash in manifest["files"].items():
        path = output / relative
        if not path.resolve().is_relative_to(output.resolve()):
            raise ValueError("Unsafe manifest path")
        data = read_data(path)
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError(f"Unsupported equipment data: {relative}")
        if data["family_id"] != family_id:
            raise ValueError("Payload family mismatch")
        items = [RuntimeItemProjectionDTO.model_validate(item) for item in data["items"]]
        if len({item.slot for item in items}) != len(items) or len({item.item_id for item in items}) != len(items):
            raise ValueError(f"Duplicate equipment slot or identity: {relative}")
        requests = inputs[relative]
        if {request["target_slot"] for request in requests} != {item.slot for item in items}:
            raise ValueError(f"Input slot mismatch: {relative}")
        for request in requests:
            item = next(item for item in items if item.slot == request["target_slot"])
            if request["base_id"] != item.base_id or request["runtime_metadata"]["runtime_item_id"] != item.item_id:
                raise ValueError(f"Input item identity mismatch: {relative}")
        owner = f"{data['clan_id']}.{data['variant_id']}:tier:{data['tier']}"
        if any(item.owner_key != owner or item.generation.rarity_tier != data["tier"] for item in items):
            raise ValueError(f"Equipment owner/tier mismatch: {relative}")
        if digest(path.read_bytes()) != expected_hash:
            raise ValueError(
                f"Manual changes detected in {relative}; review changes and explicitly refresh the manifest"
            )
        item_count += len(items)
    return {"sets": len(manifest["files"]), "items": item_count}


async def write_prepared(output: Path, family_id: str) -> dict[str, int]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}; use --validate-only or a new --output directory")
    payloads, provenance = await prepare_payloads(family_id)
    files = {}
    # Generate everything before creating output, so generation failures leave no partial artifact.
    for relative, payload in payloads.items():
        files[relative] = (
            '"""Prepared ItemService output. Edit deliberately; never regenerate over edits."""\n\n'
            + "DATA = "
            + pprint.pformat(payload, sort_dicts=False, width=110)
            + "\n"
        ).encode()
    output.mkdir(parents=True)
    (output / "__init__.py").write_text(
        '"""Prepared family equipment; no generation at import time."""\n', encoding="utf-8"
    )
    for relative, content in files.items():
        path = output / relative
        path.parent.mkdir(exist_ok=True)
        (path.parent / "__init__.py").touch(exist_ok=True)
        path.write_bytes(content)
    refs = tuple(path.removesuffix(".py").replace("/", ".") for path in sorted(files))
    (output / "index.py").write_text("DATA = " + pprint.pformat(refs, width=110) + "\n", encoding="utf-8")
    source_paths = {
        Path(__file__),
        ROOT / "src/backend/features/items/services/generation_service.py",
        ROOT / "src/backend/features/monsters/instances/integrations/item_generation.py",
        ROOT / "src/backend/features/monsters/catalog/resources/item_affix_profiles.py",
        ROOT / "src/backend/features/monsters/catalog/resources/equipment_mapping.py",
    }
    for relative in (
        "src/backend/features/items/resources",
        "src/backend/features/items/runtime",
        f"src/backend/features/monsters/catalog/families/{FAMILIES[family_id][1]}",
    ):
        source_paths.update(
            path
            for path in (ROOT / relative).rglob("*.py")
            if not path.is_relative_to(default_output(family_id)) and "__pycache__" not in path.parts
        )
    sources = sorted(source_paths)
    manifest = {
        "schema_version": 1,
        "family_id": family_id,
        "seed_version": seed_version(family_id),
        "files": {path: digest(content) for path, content in sorted(files.items())},
        "sources": {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path.read_bytes()) for path in sources},
        "inputs": provenance,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return validate(output, family_id)


def main():
    # Existing affix selection iterates sets. Pin Python's hash order as well as
    # per-item RNG seeds, without changing the shared ItemService implementation.
    if os.environ.get("PYTHONHASHSEED") != "0":
        environment = dict(os.environ, PYTHONHASHSEED="0")
        raise SystemExit(
            subprocess.call([sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], env=environment)
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-id", choices=tuple(FAMILIES), required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    output = args.output or default_output(args.family_id)
    result = (
        validate(output, args.family_id) if args.validate_only else asyncio.run(write_prepared(output, args.family_id))
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
