"""Game fragments and dynamic risk frames consume the selected UI theme."""

import shutil
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def test_world_art_theme_does_not_override_selected_interface_palette():
    env = Environment(loader=FileSystemLoader("src/frontend/templates"))
    html = env.get_template("game/includes/world_theme_vars.html").render(
        world_theme={"css_vars": {"--world-accent": "#123456"}},
        oob=False,
    )
    assert "--world-accent: #123456" in html
    assert "--col-accent:" not in html
    assert "--col-border:" not in html


def test_avatar_fallbacks_use_theme_tokens():
    for name in ("components/panel/widgets/avatar.html", "components/status/fragments/avatar.html"):
        text = Path("src/frontend/templates/game", name).read_text(encoding="utf-8")
        assert "var(--game-avatar-fallback-light)" in text
        assert "var(--game-avatar-fallback-dark)" in text
        assert "#1a1a20" not in text
        assert "font-size: 9px" not in text


def test_risk_frame_preserves_state_and_uses_live_theme_roles():
    node = shutil.which("node")
    assert node, "Node.js is required to exercise the real risk frame"
    source = Path("src/frontend/static/js/core/exploration_cooldown.js").resolve()
    script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const window={},document={addEventListener:()=>{}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window,document,console});
function apply(dataset){
 const props={},classes={};
 window.ExplorationRiskFrame.apply({dataset,style:{setProperty:(k,v)=>props[k]=v},classList:{toggle:(k,v)=>classes[k]=v}});
 return {props,classes};
}
const encounter=apply({encounter:'true',safeZone:'true',threat:'0'});
assert.equal(encounter.classes['is-danger'],true);
assert.equal(encounter.classes['is-safe'],false);
assert(encounter.props['--danger-color'].includes('var(--game-risk-danger)'));
assert(encounter.props['--danger-glow-color'].includes('36%'));
const safe=apply({safeZone:'true',threat:'1'});
assert.equal(safe.classes['is-safe'],true);
assert(safe.props['--danger-color'].includes('var(--game-risk-safe)'));
const middle=apply({threat:'0.25'});
assert(middle.props['--danger-color'].includes('var(--game-risk-low)'));
assert(middle.props['--danger-color'].includes('var(--game-risk-medium)'));
assert(middle.props['--danger-color'].includes('50%'));
const high=apply({threat:'0.9'});
assert.equal(high.classes['is-danger'],true);
assert(high.props['--danger-color'].includes('var(--game-risk-danger)'));
"""
    result = subprocess.run([node, "-e", script, str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
