"""Production edge isolation without starting the production stack."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
LAYERS = ("compose.infra.yml", "compose.site.yml", "compose.game.yml", "compose.tg-bot.yml")
UPSTREAMS = {"frontend", "frontend-play", "backend", "chat"}
STORES = {"postgres", "redis", "mongo"}


def _assert_topology(config):
    services = config["services"]
    declared = config["networks"]
    assert set(declared) == {"tbmmorpg-network", "tbmmorpg-edge"}
    # Data clients still need outbound provider/S3/Telegram access.
    assert not declared["tbmmorpg-network"].get("internal", False)
    for name, service in services.items():
        networks = set(service.get("networks", []))
        if service.get("network_mode") == "none":
            assert name in {"generated-assets-init", "redisinsight-data-init"}
            assert not networks
            continue
        assert networks and networks <= set(declared), name
        expected = {"tbmmorpg-network"}
        if name in {"nginx", "certbot"}:
            expected = {"tbmmorpg-edge"}
        elif name in UPSTREAMS:
            expected.add("tbmmorpg-edge")
        assert networks == expected, name
        assert service.get("network_mode") != "host"
        if name in STORES:
            assert not service.get("ports"), name
    proxy = set(services["nginx"]["networks"])
    for name in STORES:
        assert not proxy.intersection(services[name]["networks"]), name
    for name in UPSTREAMS.intersection(services):
        assert proxy.intersection(services[name]["networks"]), name
        for store in STORES:
            assert set(services[name]["networks"]).intersection(services[store]["networks"])


def _source_config():
    result = {"services": {}, "networks": {}}
    for filename in LAYERS:
        layer = yaml.safe_load((ROOT / "deploy" / filename).read_text())
        for key in result:
            result[key].update(layer.get(key, {}))
    return result


def test_production_edge_storage_boundary():
    _assert_topology(_source_config())


@pytest.mark.parametrize("mutation", ["proxy_data", "store_edge", "upstream_missing", "implicit_default"])
def test_topology_rejects_network_regressions(mutation):
    config = _source_config()
    if mutation == "proxy_data":
        config["services"]["nginx"]["networks"].append("tbmmorpg-network")
    elif mutation == "store_edge":
        config["services"]["redis"]["networks"].append("tbmmorpg-edge")
    elif mutation == "upstream_missing":
        config["services"]["chat"]["networks"].remove("tbmmorpg-edge")
    else:
        del config["services"]["backend"]["networks"]
    with pytest.raises(AssertionError):
        _assert_topology(config)


def test_certbot_renewal_uses_edge_network():
    helper = (ROOT / "deploy/certbot/tbmmorpg-certbot-renew.sh").read_text()
    assert "COMPOSE_NETWORK:-tbmmorpg-edge" in helper
    assert '--network "${COMPOSE_NETWORK}"' in helper
    assert "tbmmorpg-network" not in helper
    unit = (ROOT / "deploy/certbot/tbmmorpg-certbot-renew.service").read_text()
    assert "tbmmorpg-network" not in unit


@pytest.mark.external
@pytest.mark.parametrize(
    "filenames",
    [
        ("compose.prod.yml",),
        ("compose.infra.yml", "compose.site.yml"),
        ("compose.infra.yml", "compose.game.yml"),
        ("compose.infra.yml", "compose.site.yml", "compose.game.yml", "compose.tg-bot.yml"),
        ("compose.infra.yml", "compose.site.yml", "compose.game.yml", "compose.tg-bot.yml", "compose.tools.yml"),
    ],
)
def test_resolved_production_network_boundary(tmp_path, filenames):
    docker = shutil.which("docker")
    if not docker:
        pytest.skip("Docker Compose CLI required")
    empty = tmp_path / "empty.env"
    empty.write_text("")
    environment = os.environ.copy()
    for file in (ROOT / "deploy").glob("*.yml"):
        for name in re.findall(r"\$\{([A-Z][A-Z0-9_]*)", file.read_text()):
            environment[name] = "contract-test"
    environment.update(
        DEPLOY_ENV_FILE=str(empty),
        DOMAIN_NAME="example.test",
        PLAY_DOMAIN_NAME="play.example.test",
        COMPOSE_PROFILES="",
    )
    command = [docker, "compose", "--env-file", str(empty), "--profile", "*"]
    for filename in filenames:
        command.extend(["-f", str(ROOT / "deploy" / filename)])
    command.extend(["config", "--no-env-resolution", "--format", "json"])
    completed = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, "Sanitized Compose config failed"
    _assert_topology(json.loads(completed.stdout))
