const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
    const source = fs.readFileSync('src/frontend/static/js/game/client/components.js', 'utf8');
    const {fitAspect, createText, attachSemanticButton, createImageButton} = await import(
        'data:text/javascript;base64,' + Buffer.from(source).toString('base64')
    );
    const fitted=fitAspect(840,106,300,100);assert.equal(fitted.width,300);assert.ok(Math.abs(fitted.height-106*300/840)<1e-10);assert.ok(Math.abs(fitted.width/fitted.height-840/106)<1e-10);
    assert.deepEqual(fitAspect(840, 106, 500, 26.5), {width:210,height:26.5,scale:.25});
    for (const bad of [0,-1,NaN,Infinity]) assert.throws(() => fitAspect(bad,100,100,100), RangeError);
    let textCall;
    const fakeText = {destroy(){this.destroyed=true;}};
    const scene = {add:{text(...args){textCall=args;return fakeText;}}};
    assert.equal(createText(scene,7,11,'real name',{fontSize:14,renderScale:2,color:'#eee',fontFamily:'Arial'}),fakeText);
    assert.deepEqual(textCall.slice(0,3),[7,11,'real name']);
    assert.equal(textCall[3].fontSize,14);
    assert.equal(textCall[3].resolution,2);
    assert.equal(textCall[3].color,'#eee');
    assert.throws(() => createText(scene,0,0,'',{fontSize:0}),RangeError);
    let removed=0, activated=0;
    function element(){
        const handlers=new Map();
        return {style:{},attributes:{},disabled:false,hidden:false,
            setAttribute(k,v){this.attributes[k]=String(v);},
            addEventListener(k,fn){handlers.set(k,fn);},
            removeEventListener(k,fn){if(handlers.get(k)===fn)handlers.delete(k);},
            remove(){removed++;},
            dispatch(k){handlers.get(k)?.({type:k});}
        };
    }
    const document={createElement:()=>element()};
    const host={ownerDocument:document,append(b){this.button=b;}};
    let shutdown;const sceneHandlers=new Map();
    const events={once(name,fn){assert.equal(name,'shutdown');shutdown=fn;},on(name,fn){sceneHandlers.set(name,fn);},off(name,fn){if(shutdown===fn)shutdown=null;sceneHandlers.delete(name);}};
    const control=attachSemanticButton(host,{label:'Атака',rect:{x:10,y:20,width:120,height:28},onActivate:()=>activated++,scene:{events}});
    assert.equal(host.button.type,'button');
    assert.equal(host.button.attributes['aria-label'],'Атака');
    assert.equal(host.button.style.left,'10px');assert.equal(host.button.style.width,'120px');
    host.button.dispatch('click');assert.equal(activated,1);
    sceneHandlers.get('sleep')();host.button.dispatch('click');assert.equal(activated,1);assert.equal(host.button.hidden,true);
    sceneHandlers.get('wake')();assert.equal(host.button.hidden,false);
    control.update({disabled:true});host.button.dispatch('click');assert.equal(activated,1);
    control.update({disabled:false,label:'Финт',rect:{x:9,y:10,width:80,height:30}});
    assert.equal(host.button.attributes['aria-label'],'Финт');
    host.button.dispatch('focus');assert.notEqual(host.button.style.outline,'none');
    host.button.dispatch('blur');assert.equal(host.button.style.outline,'none');
    shutdown();assert.equal(removed,1);control.destroy();assert.equal(removed,1);
    assert.throws(()=>control.update({label:'late'}));
    assert.throws(()=>attachSemanticButton(host,{label:'',rect:{x:0,y:0,width:1,height:1}}));
    const image={setVisible(value){this.visible=value;return this;},setOrigin(){return this;},setDisplaySize(w,h){this.width=w;this.height=h;return this;},destroy(){this.destroyed=true;}};
    const buttonText={setVisible(value){this.visible=value;return this;},setOrigin(){return this;},destroy(){this.destroyed=true;}};
    const imageScene={add:{image(){return image;},text(){return buttonText;}}};
    const button=createImageButton(imageScene,host,{key:'ui',frame:'attack',sourceWidth:840,sourceHeight:116,rect:{x:0,y:0,width:300,height:50},label:'Удар',fontSize:14,color:'#eee',visible:false});
    assert.equal(image.visible,false);assert.equal(buttonText.visible,false);assert.equal(button.control.element.hidden,true);
    assert.equal(image.width,300);assert.ok(Math.abs(image.height-116*300/840)<1e-10);
    button.destroy();assert.equal(image.destroyed,true);assert.equal(buttonText.destroyed,true);
    let allocations=0;const noAllocationScene={add:{image(){allocations++;return image;}}};
    const invalidOptions={key:'ui',sourceWidth:840,sourceHeight:116,rect:{x:0,y:0,width:300,height:50},label:'Удар'};
    assert.throws(()=>createImageButton(noAllocationScene,null,invalidOptions),TypeError);
    assert.throws(()=>createImageButton(noAllocationScene,{ownerDocument:{}},invalidOptions),TypeError);
    assert.equal(allocations,0);
    console.log('PASS components: proportional images, sharp text, native controls, disabled state and cleanup');
})().catch(error=>{console.error(error);process.exitCode=1;});
