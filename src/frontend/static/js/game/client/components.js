/* Presentation only: callers provide authoritative labels, state and actions. */
function positive(value, name) {
    if (!Number.isFinite(value) || value <= 0) throw new RangeError(`${name} must be positive and finite`);
    return value;
}
function bounds(value) {
    if (!value || !Number.isFinite(value.x) || !Number.isFinite(value.y)) throw new RangeError('Invalid control position');
    return {x:value.x, y:value.y, width:positive(value.width,'width'), height:positive(value.height,'height')};
}

/** Fit without distortion; callers decide whether upscaling source art is acceptable. */
export function fitAspect(sourceWidth, sourceHeight, maxWidth, maxHeight) {
    [sourceWidth,sourceHeight,maxWidth,maxHeight].forEach(value => positive(value,'dimension'));
    const scale = Math.min(maxWidth / sourceWidth, maxHeight / sourceHeight);
    return {width:sourceWidth * scale, height:sourceHeight * scale, scale};
}

/** Coordinates/fontSize use scene units. renderScale changes raster resolution only. */
export function createText(scene, x, y, label, options = {}) {
    const fontSize = positive(options.fontSize ?? 14,'fontSize');
    const resolution = Math.max(1,Math.min(3, positive(options.renderScale ?? 1,'renderScale')));
    const host = options.themeHost ?? globalThis.document?.querySelector('[data-game-client-shell]');
    const theme = host && globalThis.getComputedStyle?.(host);
    const style = {fontSize, resolution};
    const fontFamily = options.fontFamily ?? theme?.getPropertyValue('--font-ui').trim();
    const color = options.color ?? theme?.getPropertyValue('--col-text-primary').trim();
    if (fontFamily) style.fontFamily = fontFamily;
    if (color) style.color = color;
    if (options.align) style.align = options.align;
    if (options.wordWrap) style.wordWrap = options.wordWrap;
    return scene.add.text(x,y,String(label ?? ''),style);
}

/**
 * Native keyboard/pointer control above canvas. Host must be positioned; rect is
 * relative to its padding box in CSS pixels, not Phaser backing-store pixels.
 * Canvas artwork is not separately interactive: one activation path per action.
 */
export function attachSemanticButton(host, options) {
    if (typeof host?.ownerDocument?.createElement !== 'function' || typeof host?.append !== 'function' || typeof options?.label !== 'string' || !options.label.trim()) throw new TypeError('A host and accessible label are required');
    let state = {...options,rect:bounds(options.rect)}, destroyed = false, sleeping = false;
    const button = host.ownerDocument.createElement('button');
    button.type = 'button';
    Object.assign(button.style,{position:'absolute',padding:'0',margin:'0',border:'0',
        background:'transparent',color:'transparent',outline:'none',cursor:'pointer',boxSizing:'border-box'});
    function render() {
        button.setAttribute('aria-label',state.label);
        button.disabled = Boolean(state.disabled);
        button.hidden = sleeping || state.visible === false;
        button.style.pointerEvents = button.hidden ? 'none' : 'auto';
        for (const [key,value] of Object.entries({left:state.rect.x,top:state.rect.y,width:state.rect.width,height:state.rect.height})) button.style[key] = `${value}px`;
    }
    function click(event) {
        if (!destroyed && !button.disabled && !button.hidden) state.onActivate?.(event);
    }
    function focus() {button.style.outline = '2px solid var(--col-accent)';button.style.outlineOffset = '2px';}
    function blur() {button.style.outline = 'none';}
    function sleep() {sleeping = true;render();}
    function wake() {sleeping = false;render();}
    function destroy() {
        if (destroyed) return;
        destroyed = true;
        button.removeEventListener('click',click);button.removeEventListener('focus',focus);button.removeEventListener('blur',blur);
        options.scene?.events?.off('shutdown',destroy);
        options.scene?.events?.off('sleep',sleep);options.scene?.events?.off('wake',wake);
        button.remove();
    }
    button.addEventListener('click',click);button.addEventListener('focus',focus);button.addEventListener('blur',blur);
    render();host.append(button);
    options.scene?.events?.once('shutdown',destroy);
    options.scene?.events?.on?.('sleep',sleep);options.scene?.events?.on?.('wake',wake);
    return {element:button, update(next) {
        if (destroyed) throw new Error('Control already destroyed');
        const candidate = {...state,...next,rect:next.rect ? bounds(next.rect) : state.rect};
        if (typeof candidate.label !== 'string' || !candidate.label.trim()) throw new TypeError('Accessible label must not be empty');
        state = candidate;render();
    },destroy};
}

/** Proportional image+caption with one semantic control; no gameplay behavior. */
export function createImageButton(scene, host, options) {
    if (typeof host?.ownerDocument?.createElement !== 'function' || typeof host?.append !== 'function' || typeof options?.label !== 'string' || !options.label.trim()) throw new TypeError('A host and accessible label are required');
    positive(options.fontSize ?? 14,'fontSize');positive(options.renderScale ?? 1,'renderScale');
    const rect = bounds(options.rect), sceneRect = bounds(options.sceneRect ?? rect);
    const fit = fitAspect(options.sourceWidth,options.sourceHeight,sceneRect.width,sceneRect.height);
    const image = scene.add.image(sceneRect.x + (sceneRect.width-fit.width)/2,
        sceneRect.y + (sceneRect.height-fit.height)/2,options.key,options.frame)
        .setOrigin(0).setDisplaySize(fit.width,fit.height);
    const text = createText(scene,sceneRect.x+sceneRect.width/2,sceneRect.y+sceneRect.height/2,options.label,options).setOrigin(.5);
    image.setVisible(options.visible !== false);text.setVisible(options.visible !== false);
    // Own the whole component on shutdown rather than removing only its input.
    const control = attachSemanticButton(host,{label:options.label,rect,onActivate:options.onActivate,disabled:options.disabled,visible:options.visible,scene});
    let destroyed = false;
    function destroy() {
        if (destroyed) return;
        destroyed = true;scene.events?.off('shutdown',destroy);
        control.destroy();image.destroy();text.destroy();
    }
    scene.events?.once('shutdown',destroy);
    return {image,text,control,destroy};
}
