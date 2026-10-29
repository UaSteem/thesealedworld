// Canvas consumes the existing semantic theme; CSS normalizes rgb/color-mix/fonts.
export function readTheme() {
  const styles = getComputedStyle(document.documentElement);
  const css = key => styles.getPropertyValue(key).trim();
  const probe = document.createElement('span');
  document.body.append(probe);
  const color = key => {
    probe.style.color = `var(${key})`;
    const channels = getComputedStyle(probe).color.match(/[\d.]+/g).slice(0, 3).map(Number);
    return { css: `rgb(${channels.join(',')})`, number: (channels[0] << 16) + (channels[1] << 8) + channels[2] };
  };
  const theme = {font:css('--font-ui'), display:css('--font-world')};
  for (const [key, token] of Object.entries({bg:'--col-bg-base',panel:'--col-bg-surface',cell:'--col-bg-darker',line:'--col-border',accent:'--col-accent',text:'--col-text-primary',dim:'--col-text-dim',success:'--col-success'})) theme[key]=color(token);
  theme.tiers=Array.from({length:6},(_,i)=>color(`--r${i}`));
  probe.remove();
  return theme;
}
