/* Persistent HTML chat over the shared gameplay canvas, no reserved layout row. */
(() => {
  const chat=document.getElementById('chat'),toggle=document.getElementById('chat-toggle');
  if(!chat||!toggle)return;
  function label(collapsed){
    toggle.textContent=collapsed?'⌃':'⌄';
    toggle.setAttribute('aria-label',collapsed?'Развернуть чат':'Свернуть чат');
    toggle.title=collapsed?'Развернуть чат':'Свернуть чат';
  }
  label(chat.classList.contains('is-collapsed'));
  toggle.addEventListener('click',()=>{
    const collapsed=chat.classList.toggle('is-collapsed');
    toggle.setAttribute('aria-expanded',String(!collapsed));
    label(collapsed);
  });
})();
