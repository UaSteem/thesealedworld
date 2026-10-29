(() => {
  const viewport=document.getElementById('game-viewport');
  function fit(){
    const scale=Math.min(1,window.innerWidth/1920);
    viewport.style.setProperty('--game-ui-scale',scale);
    const configuredHeight=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--game-chrome-height'));
    const reservedHeight=Number.isFinite(configuredHeight)?configuredHeight:60;
    viewport.style.setProperty('--game-logical-height',`${Math.max(0,window.innerHeight-reservedHeight)/scale}px`);
    requestAnimationFrame(()=>window.gameUiLab?.game.scale.refresh());
  }
  fit();window.addEventListener('resize',fit);
})();
