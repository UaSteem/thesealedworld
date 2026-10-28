"""Exercise actual shared chat controls without retired mobile viewport policy."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("width,height", [(1366, 768), (2560, 1440)])
def test_chat_controls_keep_desktop_minimum_without_mobile_queries(width, height):
    node = shutil.which("node")
    assert node, "Node.js is required for actual chat control behavior checks"
    source = Path("src/frontend/static/js/core/main.js").resolve()
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const [source, width, height] = process.argv.slice(1);
const state = {chatStep: 2, chatClosed: false, chatUnread: true, windows: {chat: {height: 300}}};
const classes = new Set(['game-chat-row']);
const label = {textContent: ''};
const chat = {
  style: {removeProperty: () => {}},
  classList: {
    remove: (...names) => names.forEach(name => classes.delete(name)),
    add: name => classes.add(name),
    contains: name => classes.has(name),
    toggle: (name, active) => active ? classes.add(name) : classes.delete(name)
  },
  querySelectorAll: () => [label]
};
const properties = {};
const container = {style: {setProperty: (key,value) => {properties[key] = value;}}};
let gamePresent = true;
const document = {
  querySelector: selector => !gamePresent ? null : selector === '.game-container' ? container : chat,
  addEventListener: () => {},
  querySelectorAll: () => []
};
const Alpine = {$data: () => state};
const window = {
  innerWidth: Number(width), innerHeight: Number(height), Alpine,
  getComputedStyle: () => ({getPropertyValue: () => '30px'}),
  matchMedia: () => {throw new Error('Retired mobile policy queried');}
};
vm.runInNewContext(fs.readFileSync(source, 'utf8'), {window, document, Alpine, console});
window.stepChatSize('min');
assert.equal(state.chatStep, 1);
assert.equal(state.chatMinimized, false);
assert.equal(label.textContent, 'MAX');
assert.equal(properties['--chat-height'], Math.round((Number(height)-80)*0.25)+'px');
window.setChatStep(0);
assert.equal(state.chatStep, 1);
window.stepChatSize(-1);
assert.equal(state.chatStep, 1);
window.toggleChatMinMax();
assert.equal(state.chatStep, 3);
assert.equal(label.textContent, 'MIN');
window.toggleChatMinMax();
assert.equal(state.chatStep, 1);
window.stepChatSize('max');
assert.equal(state.chatStep, 3);
assert.equal(state.chatClosed, false);
assert.equal(state.chatUnread, true);
assert.equal(state.windows.chat.height, Math.round((Number(height)-80)*0.75));
gamePresent = false;
const before = JSON.stringify(state);
window.stepChatSize('min');
window.setChatStep(0);
window.toggleChatMinMax();
assert.equal(JSON.stringify(state), before, 'Shared site code must be a no-op without game shell');
"""
    result = subprocess.run(
        [node, "-e", script, str(source), str(width), str(height)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
