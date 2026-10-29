(() => {
  'use strict';
  const split = document.getElementById('scene-split');
  const divider = document.getElementById('chat-divider');
  const chat = document.getElementById('chat');
  const toggle = document.getElementById('chat-toggle');
  const reset = document.getElementById('chat-reset');
  const key = 'game-ui-lab-chat-ratio';
  let ratio = 0.175, collapsed = false, pointer = null;
  try {
    const stored = localStorage.getItem(key);
    if (stored !== null && Number.isFinite(Number(stored))) ratio = Math.max(0.15, Math.min(0.2, Number(stored)));
  } catch { /* Local size still works when storage is unavailable. */ }
  function bounds() {
    const available = Math.max(0, split.clientHeight - (collapsed ? 0 : 8));
    const max = Math.max(0, Math.min(available * 0.2, available - 410));
    return {available, min: Math.min(available * 0.15, max), max};
  }
  function sync() {
    const {available, min, max} = bounds();
    const height = collapsed ? 40 : Math.min(max, Math.max(min, available * ratio));
    split.style.setProperty('--chat-height', `${height}px`);
    const percent = value => available ? Math.round(value / available * 100) : 0;
    divider.hidden = collapsed;
    divider.setAttribute('aria-valuemin', String(percent(min)));
    divider.setAttribute('aria-valuemax', String(percent(max)));
    divider.setAttribute('aria-valuenow', String(percent(height)));
    divider.setAttribute('aria-valuetext', `${percent(height)}% игровой области и чата`);
  }
  function save() { try { localStorage.setItem(key, String(ratio)); } catch { /* Optional persistence. */ } }
  function setPixels(height) {
    const {available, min, max} = bounds();
    if (available) ratio = Math.min(max, Math.max(min, height)) / available;
    sync();
  }
  function expand(value) {
    collapsed = !value;
    chat.classList.toggle('is-collapsed', collapsed);
    split.classList.toggle('is-chat-collapsed', collapsed);
    toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.title = collapsed ? 'Развернуть чат' : 'Свернуть чат';
    toggle.textContent = collapsed ? 'Развернуть чат ⌃' : 'Свернуть ⌄';
    sync();
  }
  function finish(event) {
    if (pointer === null || (event.pointerId !== undefined && event.pointerId !== pointer)) return;
    const id = pointer;
    pointer = null;
    if (divider.hasPointerCapture(id)) divider.releasePointerCapture(id);
    document.body.classList.remove('is-chat-resizing');
    save();
  }
  divider.addEventListener('pointerdown', event => {
    if (event.button !== 0 || collapsed || pointer !== null) return;
    pointer = event.pointerId;
    divider.setPointerCapture(pointer);
    divider.focus();
    document.body.classList.add('is-chat-resizing');
    event.preventDefault();
  });
  divider.addEventListener('pointermove', event => {
    if (pointer !== event.pointerId) return;
    setPixels(split.getBoundingClientRect().bottom - event.clientY - 4);
  });
  ['pointerup','pointercancel','lostpointercapture'].forEach(type => divider.addEventListener(type, finish));
  divider.addEventListener('keydown', event => {
    const {available, min, max} = bounds();
    const step = event.shiftKey ? 0.1 : 0.02;
    const current = Math.min(max, Math.max(min, available * ratio));
    const next = {ArrowUp:current + available * step, ArrowDown:current - available * step, Home:min, End:max}[event.key];
    if (next === undefined) return;
    event.preventDefault();
    setPixels(next);save();
  });
  toggle.addEventListener('click', () => expand(collapsed));
  reset.addEventListener('click', () => {ratio = 0.175;expand(true);save();});
  new ResizeObserver(sync).observe(split);
  sync();
})();
