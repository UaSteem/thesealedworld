/* Frozen combat presentation fixture; no chat data/service or combat calculations. */
(() => {
  const host=document.getElementById('combat-log'),shell=document.getElementById('chat');
  if(!host||!shell)return;
  const events=[
    ['Раунд 1','Бой начался: Ada Guard против Хранителя.'],
    ['Раунд 1','Ada Guard атакует. Хранитель теряет 18 HP.'],
    ['Раунд 1','Хранитель отвечает. Ada Guard блокирует часть удара: −6 HP.'],
    ['Раунд 2','Хранитель готовит тяжёлый удар.'],
    ['Раунд 2','Ada Guard использует защитную стойку.'],
    ['Раунд 2','Тяжёлый удар заблокирован. Ada Guard теряет 4 HP.'],
    ['Раунд 3','Ada Guard наносит критический удар: −27 HP.'],
    ['Раунд 3','Ожидание следующего действия…'],
  ];
  let timer=null,cursor=0;
  function append(){
    const [round,text]=events[cursor++],row=document.createElement('p');
    const label=document.createElement('b'),body=document.createElement('span');
    label.textContent=round;body.textContent=text;row.append(label,body);host.append(row);host.scrollTop=host.scrollHeight;
    if(cursor===events.length){clearInterval(timer);timer=null;}
  }
  function stop(){if(timer!==null)clearInterval(timer);timer=null;}
  shell.addEventListener('lab-combat-presence',event=>{
    stop();host.replaceChildren();cursor=0;
    if(event.detail.active){append();timer=setInterval(append,1800);}
  });
  window.addEventListener('pagehide',stop,{once:true});
})();
