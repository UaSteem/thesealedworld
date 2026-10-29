/* Presentation shell only: chat and battle journal retain separate data owners. */
(() => {
  const shell=document.querySelector('.game-lab-workspace'),chat=document.getElementById('chat');
  if(!shell||!chat)return;
  const battleTab=document.getElementById('combat-log-tab'),battle=document.getElementById('combat-log');
  const messages=document.getElementById('chat-messages'),form=document.getElementById('chat-form');
  const channels=[...chat.querySelectorAll('[data-chat]')];
  let selected=channels[0];
  function select(tab){
    selected=tab;
    const isBattle=tab===battleTab;
    messages.hidden=isBattle;form.hidden=isBattle;battle.hidden=!isBattle;
    for(const button of [...channels,battleTab]){
      button.classList.toggle('is-active',button===tab);
      button.setAttribute('aria-pressed',String(button===tab));
    }
  }
  channels.forEach(tab=>tab.addEventListener('click',()=>select(tab)));
  battleTab.addEventListener('click',()=>select(battleTab));
  function sync(){
    const inBattle=shell.dataset.gameScreen==='combat';
    battleTab.hidden=!inBattle;
    if(!inBattle&&selected===battleTab)channels[0].click();
    chat.dispatchEvent(new CustomEvent('lab-combat-presence',{detail:{active:inBattle}}));
  }
  const observer=new MutationObserver(sync);
  observer.observe(shell,{attributes:true,attributeFilter:['data-game-screen']});
  window.addEventListener('pagehide',()=>observer.disconnect(),{once:true});
  sync();
})();
