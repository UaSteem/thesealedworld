"""Keep executable workflow and deploy image references immutable."""

import ast
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTION = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}")
IMAGE = re.compile(r"[^\s@$]+@sha256:[0-9a-f]{64}")
PROJECT_IMAGE = re.compile(r"\$\{DOCKER_IMAGE_(SITE|GAME|CHAT|WORKER|TG_BOT|NGINX):\?[^}]+\}")


def _values(value, key):
    if isinstance(value, dict):
        for name, item in value.items():
            if name == key:
                yield item
            yield from _values(item, key)
    elif isinstance(value, list):
        for item in value:
            yield from _values(item, key)


@pytest.mark.parametrize("path", sorted((ROOT / ".github/workflows").glob("*.y*ml")), ids=lambda p: p.name)
def test_workflow_actions_use_full_commit_sha(path):
    for reference in _values(yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader), "uses"):
        assert ACTION.fullmatch(reference), f"{path.name}: mutable or unsupported Action: {reference}"


@pytest.mark.parametrize("path", sorted((ROOT / "deploy").glob("*.y*ml")), ids=lambda p: p.name)
def test_compose_images_use_digests_or_verified_project_outputs(path):
    for reference in _values(yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader), "image"):
        assert IMAGE.fullmatch(reference) or PROJECT_IMAGE.fullmatch(reference), (
            f"{path.name}: mutable or unverified image: {reference}"
        )


@pytest.mark.parametrize("path", sorted((ROOT / "deploy").rglob("Dockerfile*")), ids=lambda p: str(p.relative_to(ROOT)))
def test_dockerfile_base_and_frontend_images_use_digests(path):
    stages = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        syntax = re.match(r"#\s*syntax\s*=\s*(\S+)", line)
        if syntax:
            assert IMAGE.fullmatch(syntax[1]), f"{path}: mutable Dockerfile frontend: {syntax[1]}"
        fields = line.split()
        if not fields or fields[0].upper() != "FROM":
            continue
        fields = fields[1:]
        if fields[0].startswith("--platform="):
            fields = fields[1:]
        image = fields[0]
        assert image in stages or image == "scratch" or IMAGE.fullmatch(image), f"{path}: mutable base image: {image}"
        if len(fields) == 3 and fields[1].upper() == "AS":
            stages.add(fields[2])


@pytest.mark.parametrize("path", sorted((ROOT / ".github/workflows").glob("*.y*ml")), ids=lambda p: p.name)
def test_buildkit_driver_image_and_buildx_version_are_explicit(path):
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if not step.get("uses", "").startswith("docker/setup-buildx-action@"):
                continue
            settings = step.get("with", {})
            assert re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", settings.get("version", "")), "Mutable Buildx release"
            options = settings.get("driver-opts", "").splitlines()
            images = [option.removeprefix("image=") for option in options if option.startswith("image=")]
            assert len(images) == 1 and IMAGE.fullmatch(images[0]), "Mutable BuildKit driver image"


def test_hadolint_ci_image_uses_digest():
    tree = ast.parse((ROOT / "tools/dev/hadolint_docker.py").read_text(encoding="utf-8"))
    references = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("hadolint/hadolint:")
    ]
    assert len(references) == 1 and IMAGE.fullmatch(references[0]), "Mutable hadolint CI image"
