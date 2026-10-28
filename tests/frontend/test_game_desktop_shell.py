"""Desktop shell must not invoke the retired mobile viewport/storage policy."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("width,height", [(1366, 768), (2560, 1440)])
def test_shell_initialization_uses_desktop_state_without_mobile_queries(width, height):
    node = shutil.which("node")
    assert node, "Node.js is required for the actual game shell behavior check"
    source = Path("src/frontend/static/js/core/game_shell.js").resolve()
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const [source, width, height] = process.argv.slice(1);
const reads = [];
const window = {
  innerWidth: Number(width), innerHeight: Number(height),
  matchMedia: () => { throw new Error('Retired viewport policy queried'); },
  localStorage: {
    getItem: key => { reads.push(key); return null; },
    setItem: () => {},
    removeItem: () => { throw new Error('Desktop preferences deleted'); }
  }
};
vm.runInNewContext(fs.readFileSync(source, 'utf8'), {window, console});
const shell = window.gameShell({activeCharId: '101', domain: 'exploration'});
assert.equal(shell.leftOpen, true);
assert.equal(shell.rightOpen, true);
assert(reads.includes('tbmmorpg:shell:panels:exploration:101:desktop:v1'));
"""
    result = subprocess.run(
        [node, "-e", script, str(source), str(width), str(height)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
