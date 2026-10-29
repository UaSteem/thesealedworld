// Design briefs only. No simulated claim, rewards, death loss or respawn.
export function createAftermathScenes(DraftPage){
  const make=(key,id)=>class extends DraftPage{
    constructor(){super({key});}
    draw(){
      this.begin();
      const brief=JSON.parse(document.getElementById('page-briefs').textContent)[id];
      this.heading(brief.title,'Описание будущей страницы · макет ещё не выбран');
      const p=this.pad,top=p+94,w=this.w-p*2;
      this.label(p,top,brief.purpose,21,this.theme.text.css,w);
      const gap=20,col=(w-gap*2)/3,y=top+78;
      brief.sections.forEach(([title,text],i)=>{
        const x=p+i*(col+gap);this.panel(x,y,col,Math.max(160,this.h-y-p));
        this.label(x+24,y+24,title,22,this.theme.accent.css,col-48);
        this.label(x+24,y+88,text,17,this.theme.text.css,col-48);
      });
    }
  };
  return [make('LootDraft','loot'),make('DeathDraft','death'),make('CityDraft','city'),make('ScenarioDraft','dialogues')];
}
