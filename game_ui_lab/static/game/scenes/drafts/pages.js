import {createArenaDraft} from './arena.js';
import {createDistrictDraft} from './districts.js';
import {createAftermathScenes} from './aftermath.js';
import {readTheme} from '../inventory/theme.js';

// Local composition studies. State is intentionally detached from game APIs.
export function createDraftScenes({host,renderScale=1}) {
  const controlKey='control-zone-low-wide-v3';
  class DraftPage extends Phaser.Scene {
    preload(){window.GameClientAssets.preload(this,'combat-controls');}
    create(){
      this.theme=readTheme();this.hits=[];
      const texture=this.textures.get(controlKey);
      if(!texture.has('draft-answer'))texture.add('draft-answer',0,92,1290,840,106);
      this.resizeHandler=()=>{if(this.sys.isActive())this.draw();};
      this.scale.on('resize',this.resizeHandler);
      this.events.on('wake',this.resizeHandler);
      this.events.once('shutdown',()=>{this.scale.off('resize',this.resizeHandler);this.events.off('wake',this.resizeHandler);});
      this.draw();
    }
    begin(){
      this.children.removeAll(true);this.hits=[];
      this.w=host.clientWidth;this.h=host.clientHeight;
      this.cameras.main.setViewport(0,0,this.w*renderScale,this.h*renderScale).setZoom(renderScale).centerOn(this.w/2,this.h/2);
      this.compact=this.w<1200;this.pad=this.compact?22:32;
      this.add.rectangle(0,0,this.w,this.h,this.theme.bg.number).setOrigin(0);
    }
    label(x,y,text,size=16,color=this.theme.text.css,width,style={}){
      return this.add.text(x,y,text,{fontFamily:this.theme.font,fontSize:`${size}px`,color,
        resolution:3,lineSpacing:8,...(width?{wordWrap:{width,useAdvancedWrap:true}}:{}),...style});
    }
    panel(x,y,w,h){
      this.add.rectangle(x,y,w,h,this.theme.panel.number).setOrigin(0).setStrokeStyle(1,this.theme.line.number);
      this.add.rectangle(x+4,y+4,w-8,h-8,0,0).setOrigin(0).setStrokeStyle(1,this.theme.line.number,.26);
    }
    line(x,y,w){this.add.rectangle(x,y,w,1,this.theme.line.number,.65).setOrigin(0);}
    button(id,x,y,w,h,label,fn,{active=false,answer=false}={}){
      const artWidth=Math.min(w,h*840/106),artHeight=artWidth*106/840;
      const surface=answer?this.add.image(x+w/2,y+h/2,controlKey,'draft-answer').setDisplaySize(artWidth,artHeight)
        :this.add.rectangle(x,y,w,h,active?this.theme.cell.number:this.theme.panel.number).setOrigin(0).setStrokeStyle(1,active?this.theme.accent.number:this.theme.line.number);
      const text=this.label(x+w/2,y+h/2,label,16,active?this.theme.accent.css:this.theme.text.css,undefined,{align:'center'}).setOrigin(.5);
      const zone=this.add.zone(x,y,w,h).setOrigin(0).setInteractive({useHandCursor:true});
      zone.on('pointerover',()=>text.setColor(this.theme.accent.css));
      zone.on('pointerout',()=>text.setColor(active?this.theme.accent.css:this.theme.text.css));
      zone.on('pointerdown',fn);this.hits.push({id,x,y,width:w,height:h});return surface;
    }
    heading(title,subtitle){
      this.label(this.pad,this.pad,title,30,this.theme.accent.css,undefined,{fontFamily:this.theme.display});
      this.label(this.pad,this.pad+45,subtitle,16,this.theme.dim.css);
    }
    inspect(){return{key:this.sys.settings.key,width:this.w,height:this.h,hits:this.hits,...this.state};}
  }

  class CharacterDraft extends DraftPage {
    constructor(){super({key:'CharacterDraft'});this.state={tab:'Характеристики'};this.skillScroll=0;this.openSkillGroups=new Set(['weapon_mastery','armor']);}
    create(){
      this.model=JSON.parse(document.getElementById('character-data').textContent);
      super.create();
      this.input.on('wheel',(pointer,_objects,_dx,dy)=>{
        const p=this.cameras.main.getWorldPoint(pointer.x,pointer.y);
        if(this.state.tab==='Характеристики'&&p.x>=this.skillsX&&p.x<=this.skillsRight){
          this.skillScroll=Phaser.Math.Clamp(this.skillScroll+dy,0,this.maxSkillScroll||0);this.draw();
        }
      });
    }
    draw(){
      this.begin();
      const m=this.model,p=this.pad;
      this.heading(this.state.tab,`${m.name} · ${m.title}`);
      const top=p+92,bottom=this.h-p,h=bottom-top;
      if(this.state.tab==='Билды'){
        this.panel(p,top,this.w-p*2,Math.min(h,190));
        this.label(p+26,top+28,'Билды не реализованы',26,this.theme.accent.css);
        this.label(p+26,top+78,'Концепция под вопросом. Настройка и переключение сборок пока отсутствуют.',17,this.theme.dim.css,this.w-p*2-52);
        return;
      }
      if(this.state.tab==='Настройки'){
        this.panel(p,top,this.w-p*2,160);
        this.label(p+26,top+28,'Настройки',26,this.theme.accent.css);
        this.label(p+26,top+78,'Состав настроек пока не определён.',17,this.theme.dim.css);
        return;
      }
      if(this.state.tab==='Квесты'){
        const quests=m.quests||[],selected=Math.min(this.state.quest||0,Math.max(0,quests.length-1));
        const narrow=Math.min(360,this.w*.27),right=p+narrow+20,wide=this.w-right-p;
        this.panel(p,top,narrow,h);this.panel(right,top,wide,h);
        quests.forEach((quest,i)=>{
          const y=top+22+i*104;
          this.button(`quest-${i}`,p+12,y,narrow-24,85,quest.title,()=>{this.state.quest=i;this.draw();},{active:i===selected});
          this.label(p+26,y+58,`В работе · ${quest.progress}`,13,this.theme.dim.css);
        });
        const quest=quests[selected];
        if(quest){
          this.label(right+28,top+28,quest.title,26,this.theme.accent.css,wide-56);
          this.label(right+28,top+78,`В работе · ${quest.progress}`,16,this.theme.dim.css);
          this.line(right+28,top+118,wide-56);
          this.label(right+28,top+146,'Описание',21,this.theme.accent.css);
          this.label(right+28,top+190,quest.description,17,this.theme.text.css,wide-56);
          this.label(right+28,top+290,'Диалоги',21,this.theme.accent.css);
          this.label(right+28,top+334,'В этом учебном слепке диалоги квеста не записаны.',16,this.theme.dim.css,wide-56);
        }return;
      }
      const gap=20,leftW=Math.round((this.w-p*2-gap)*.35),rightX=p+leftW+gap,rightW=this.w-rightX-p;
      const attrH=Math.min(370,Math.floor(h*.59));
      this.panel(p,top,leftW,attrH);
      this.label(p+22,top+18,'Атрибуты',23,this.theme.accent.css);
      const groups=[['Тело',[['strength','Сила'],['agility','Ловкость'],['endurance','Выносливость']]],['Разум',[['intellect','Интеллект'],['memory','Память'],['mental','Ментальность']]],['Чувства',[['perception','Восприятие'],['projection','Проекция'],['prediction','Предвидение']]]];
      const col=(leftW-44)/3;
      groups.forEach(([title,entries],i)=>{
        const x=p+22+i*col;this.label(x,top+65,title,16,this.theme.dim.css);
        entries.forEach(([key,label],j)=>{const y=top+107+j*66;this.label(x,y,label,14,this.theme.dim.css,col-8);this.label(x,y+24,m.attributes[key],24);});
      });
      const modTop=top+attrH+gap;
      this.panel(p,modTop,leftW,bottom-modTop);
      this.label(p+22,modTop+20,'Модификаторы',23,this.theme.accent.css);
      m.modifiers.forEach((entry,i)=>{
        const col=i%2,row=Math.floor(i/2),x=p+22+col*(leftW-44)/2,y=modTop+65+row*48;
        this.label(x,y,entry.name,13,this.theme.dim.css,(leftW-44)/2-12);
        this.label(x,y+21,entry.display,18,this.theme.text.css);
      });
      this.panel(rightX,top,rightW,h);
      const skills=m.skill_catalog,opened=skills.filter(skill=>skill.unlocked).length;
      this.label(rightX+22,top+18,'Навыки',23,this.theme.accent.css);
      this.label(rightX+rightW-22,top+24,`Открыто ${opened} / ${skills.length} · прокрутка`,14,this.theme.dim.css).setOrigin(1,0);
      this.skillsX=rightX;this.skillsRight=rightX+rightW;
      const listTop=top+67,listBottom=bottom-20,viewH=listBottom-listTop;
      const names={weapon_mastery:'Владение оружием',tactical:'Боевые стили',armor:'Броня',combat_support:'Боевая поддержка',crafting:'Ремёсла',gathering:'Сбор ресурсов',trade:'Торговля',leadership:'Лидерство',survival:'Выживание'};
      const skillGroups=Object.entries(names).map(([id,name])=>({id,name,items:skills.filter(skill=>skill.group===id)})).filter(group=>group.items.length);
      const entries=[];let total=0;
      for(const group of skillGroups){
        entries.push({group,offset:total,height:42});total+=48;
        if(this.openSkillGroups.has(group.id))for(const skill of group.items){entries.push({skill,offset:total,height:48});total+=52;}
      }
      this.maxSkillScroll=Math.max(0,total-viewH);this.skillScroll=Math.min(this.skillScroll,this.maxSkillScroll);
      const x=rightX+22,width=rightW-54;
      for(const entry of entries){
        const y=listTop+entry.offset-this.skillScroll;
        if(y<listTop||y+entry.height>listBottom)continue;
        if(entry.group){
          const group=entry.group,expanded=this.openSkillGroups.has(group.id),count=group.items.filter(skill=>skill.unlocked).length;
          this.button('skill-group-'+group.id,x,y,width,42,`${expanded?'−':'+'} ${group.name} · ${count} / ${group.items.length}`,()=>{
            expanded?this.openSkillGroups.delete(group.id):this.openSkillGroups.add(group.id);this.draw();
          },{active:expanded});continue;
        }
        const skill=entry.skill;
        if(!skill.unlocked){
          const lock=this.add.graphics();lock.lineStyle(1.5,this.theme.dim.number);lock.strokeRoundedRect(x+8,y+12,10,9,2);lock.strokeRoundedRect(x+10,y+6,6,9,3);
        }
        this.label(x+28,y,skill.name,15,skill.unlocked?this.theme.text.css:this.theme.dim.css,width-112);
        this.label(x+width-8,y,skill.unlocked?`${skill.progress}%`:'Закрыт',13,skill.unlocked?this.theme.accent.css:this.theme.dim.css).setOrigin(1,0);
        this.add.rectangle(x+28,y+32,width-36,4,this.theme.cell.number).setOrigin(0);
        if(skill.unlocked)this.add.rectangle(x+28,y+32,(width-36)*Math.min(1,skill.progress/100),4,this.theme.accent.number).setOrigin(0);
      }
      if(this.maxSkillScroll>0){
        const barH=Math.max(24,viewH*viewH/total);
        this.add.rectangle(rightX+rightW-12,listTop,3,viewH,this.theme.cell.number).setOrigin(0);
        this.add.rectangle(rightX+rightW-12,listTop+(viewH-barH)*this.skillScroll/this.maxSkillScroll,3,barH,this.theme.accent.number).setOrigin(0);
      }

    }
  }

  const ArenaDraft=createArenaDraft(DraftPage);
  return [CharacterDraft,ArenaDraft,createDistrictDraft(DraftPage),...createAftermathScenes(DraftPage)];
}
