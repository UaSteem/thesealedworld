"""Ingress contracts for the GitHub webhook, independent of develop deploy tests."""

import re
from pathlib import Path

import yaml


def _blocks(text: str, prefix: str) -> list[str]:
    blocks = []
    for match in re.finditer(prefix + r"\s*\{", text):
        opening = match.end() - 1
        depth = 1
        cursor = opening + 1
        while depth and cursor < len(text):
            depth += (text[cursor] == "{") - (text[cursor] == "}")
            cursor += 1
        assert depth == 0, "Unbalanced nginx config block"
        blocks.append(text[opening + 1 : cursor - 1])
    return blocks


def _https_server(text: str, domain_variable: str) -> str:
    matching = [
        block
        for block in _blocks(text, r"\bserver")
        if "listen 443 ssl;" in block and f"server_name ${{{domain_variable}}}" in block
    ]
    assert len(matching) == 1
    return matching[0]


def test_signed_webhook_has_exact_main_host_route_and_bounded_upstream() -> None:
    template = Path("deploy/nginx/site.conf.template").read_text(encoding="utf-8")
    main = _https_server(template, "DOMAIN_NAME")
    locations = _blocks(main, r"\blocation\s+=\s+/webhooks/github")
    assert len(locations) == 1
    location = locations[0]
    assert "set $tg_bot_upstream http://tg-bot:8091;" in main
    assert "proxy_pass $tg_bot_upstream;" in location
    assert "client_max_body_size 1m;" in location
    assert "proxy_connect_timeout 3s;" in location
    assert "proxy_read_timeout 15s;" in location
    assert "proxy_next_upstream off;" in location
    # Forward the original request body and signing headers; nginx must not
    # replace signature or delivery headers before HMAC validation in the bot.
    assert "proxy_pass_request_body off" not in location
    assert "proxy_pass_request_headers off" not in location
    assert not re.search(r"proxy_set_header\s+(X-Hub-Signature-256|X-GitHub-Delivery)\b", location, re.I)


def test_webhook_is_not_exposed_on_game_host() -> None:
    template = Path("deploy/nginx/site.conf.template").read_text(encoding="utf-8")
    play = _https_server(template, "PLAY_DOMAIN_NAME")
    locations = _blocks(play, r"\blocation\s+=\s+/webhooks/github")
    assert len(locations) == 1
    assert "return 404;" in locations[0]
    assert "proxy_pass" not in locations[0]
    assert "$tg_bot_upstream" not in play


def test_compose_webhook_is_opt_in_and_internal_only() -> None:
    compose = yaml.safe_load(Path("deploy/compose.tg-bot.yml").read_text(encoding="utf-8"))
    bot = compose["services"]["tg-bot"]
    env = bot["environment"]
    assert env["GITHUB_WEBHOOK_ENABLED"] == "${GITHUB_WEBHOOK_ENABLED:-False}"
    assert env["GITHUB_WEBHOOK_SECRET"] == "${GITHUB_WEBHOOK_SECRET:-}"
    assert env["GITHUB_WEBHOOK_REPOSITORIES"] == "${GITHUB_WEBHOOK_REPOSITORIES:-CodexDLC/thesealedworld}"
    assert env["GITHUB_WEBHOOK_BRANCHES"] == "${GITHUB_WEBHOOK_BRANCHES:-develop,main}"
    assert env["TELEGRAM_DEV_CHAT_ID"] == "${TELEGRAM_DEV_CHAT_ID:--1004387822347}"
    assert env["GITHUB_WEBHOOK_HOST"] == "0.0.0.0"
    assert env["GITHUB_WEBHOOK_PORT"] == "8091"
    assert [str(port) for port in bot["expose"]] == ["8091"]
    assert not bot.get("ports")


def test_production_example_disables_webhook_without_secret() -> None:
    example = dict(
        line.split("=", 1)
        for line in Path(".env.prod.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    assert example["GITHUB_WEBHOOK_ENABLED"] == "False"
    assert example["GITHUB_WEBHOOK_SECRET"] == ""
    assert example["GITHUB_WEBHOOK_REPOSITORIES"] == "CodexDLC/thesealedworld"
    assert example["GITHUB_WEBHOOK_BRANCHES"] == "develop,main"
    assert example["TELEGRAM_DEV_CHAT_ID"] == "-1004387822347"
