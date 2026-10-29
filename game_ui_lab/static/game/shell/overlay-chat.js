/* Persistent HTML chat over the shared gameplay canvas, no reserved layout row. */
(() => {
  const chat=document.getElementById('chat'),toggle=document.getElementById('chat-toggle');
  if(!chat||!toggle)return;
  toggle.addEventListener('click',()=>{
    const collapsed=chat.classList.toggle('is-collapsed');
    toggle.setAttribute('aria-expanded',String(!collapsed));
    toggle.textContent=collapsed?'Развернуть ⌃':'Свернуть ⌄';
  });
})();
