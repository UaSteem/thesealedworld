"""Run presentation primitives without a game server or a Phaser runtime."""

import shutil
import subprocess
from pathlib import Path


def test_game_client_components_behavior():
    node = shutil.which("node")
    assert node, "Node.js is required for presentation primitive checks"
    result = subprocess.run(
        [node, str(Path(__file__).with_name("game_client_components.cjs"))],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
