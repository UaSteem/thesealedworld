(() => {
  const viewport=document.getElementById('game-viewport');
  function fit(){
    if(!viewport)return;
    const width=window.innerWidth;
    const scale=Math.min(1,width/1920);
    viewport.style.setProperty('--game-ui-scale',scale);
    viewport.style.setProperty('--game-viewport-width',`${width}px`);
    const configuredHeight=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--game-chrome-height'));
    const reservedHeight=Number.isFinite(configuredHeight)?configuredHeight:0;
    viewport.style.setProperty('--game-logical-height',`${Math.max(0,window.innerHeight-reservedHeight)}px`);
    requestAnimationFrame(()=>window.gameUiLab?.game?.scale?.refresh());
  }
  fit();
  window.addEventListener('resize',fit);
  window.addEventListener('orientationchange',fit);
})();
