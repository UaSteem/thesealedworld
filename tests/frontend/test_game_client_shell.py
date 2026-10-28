"""Persistent game-only host and transitional legacy rendering boundary."""
import shutil
import subprocess
from pathlib import Path


def test_persistent_canvas_host_belongs_to_base_not_session_fragment():
    base = Path('src/frontend/templates/game/base_game.html').read_text(encoding='utf-8')
    inner = Path('src/frontend/templates/game/session_content_inner.html').read_text(encoding='utf-8')
    fragment = Path('src/frontend/templates/game/session_content.html').read_text(encoding='utf-8')
    assert 'id="game-client-canvas-host"' in base
    assert 'id="game-client-canvas-host"' not in inner + fragment
    assert '/static/js/game/client/shell.js' in base
    assert 'id="game-client-scene-anchor"' in inner
    assert 'id="game-client-chat-anchor"' in inner
    assert 'include "game/includes/chat_overlay.html"' in base
    assert 'include "game/includes/chat_overlay.html"' not in fragment


def test_context_information_is_in_viewport_not_global_right_column():
    inner = Path('src/frontend/templates/game/session_content_inner.html').read_text(encoding='utf-8')
    assert 'id="game-client-context"' in inner
    assert inner.index('id="game-viewport"') < inner.index('id="game-client-context"')
    assert inner.index('id="game-client-context"') < inner.index('</main>')
    assert 'id="game-right-content"' in inner
    assert 'class="col-right"' not in inner


def test_runtime_shell_css_is_scoped_and_loaded_after_legacy_layout():
    bundle = Path('src/frontend/static/css/game_bundle.css').read_text(encoding='utf-8')
    assert bundle.index('shell/runtime_client.css') > bundle.index('shell/responsive/index.css')
    source = Path('src/frontend/static/css/game/shell/runtime_client.css').read_text(encoding='utf-8')
    assert '[data-game-client-shell]' in source
    assert '--client-chat-height' in source


def test_site_and_cabinet_do_not_import_game_client():
    for folder in ('site', 'account', 'admin'):
        for path in (Path('src/frontend/templates') / folder).rglob('*.html'):
            assert 'game/client/shell.js' not in path.read_text(encoding='utf-8'), path


def test_docked_shell_starts_chat_open_and_context_closed():
    node = shutil.which('node')
    assert node
    script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const window={innerWidth:1920,innerHeight:1080,localStorage:{getItem:()=>null,setItem:()=>{}}};
const container={hasAttribute:()=>true,style:{setProperty:()=>{}}};
const document={querySelector:s=>s==='.game-container'?container:{querySelectorAll:()=>[]},addEventListener:()=>{}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window,console});
const shell=window.gameShell({activeCharId:'101',domain:'exploration',docked:true});
assert.equal(shell.chatClosed,false);assert.equal(shell.chatStep,2);
assert.equal(shell.rightOpen,false);assert.equal(shell.leftOpen,true);
shell.startHudWindowDrag('chat',{},{});assert.equal(shell.windows.chat.dragging,false);
window.Alpine={$data:()=>shell};
vm.runInNewContext(fs.readFileSync('src/frontend/static/js/core/main.js','utf8'),{window,document,console});
shell.closeChatOverlay();assert.equal(shell.chatClosed,true);assert.equal(shell.chatStep,0);
shell.openChatOverlay();assert.equal(shell.chatClosed,false);assert.equal(shell.chatStep,2);
"""
    result = subprocess.run([node, '-e', script, 'src/frontend/static/js/core/game_shell.js'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
