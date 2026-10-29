// Scenario presentation study: shared shell, two-column responses, local data only.
export function createScenarioDraft(DraftPage) {
  return class ScenarioDraft extends DraftPage {
    constructor(){
      super({key:'ScenarioDraft'});
      this.state={mode:'quest',count:4,longText:false,step:0,scroll:0};
    }
    create(){
      super.create();
      this.wheelHandler=(pointer,objects,dx,dy)=>{
        if(!this.sys.isActive()||!this.storyBounds)return;
        const point=this.cameras.main.getWorldPoint(pointer.x,pointer.y);
        const b=this.storyBounds;
        if(point.x<b.x||point.x>b.x+b.width||point.y<b.y||point.y>b.y+b.height)return;
        this.state.scroll=Phaser.Math.Clamp(this.state.scroll+dy*.65,0,this.storyMaxScroll);
        this.placeStory();
      };
      this.input.on('wheel',this.wheelHandler);
      this.events.once('shutdown',()=>{
        this.input.off('wheel',this.wheelHandler);
        this.storyMask?.destroy();this.storyMask=null;
      });
    }
    setDemo(change){Object.assign(this.state,change,{scroll:0});this.draw();}
    framedChoice(id,x,y,w,h,label,index){
      const g=this.add.graphics(),cut=8;
      const paint=hover=>{
        g.clear();g.fillStyle(hover?this.theme.panel.number:this.theme.cell.number,1);
        const points=[{x:x+cut,y},{x:x+w-cut,y},{x:x+w,y:y+cut},{x:x+w,y:y+h-cut},
          {x:x+w-cut,y:y+h},{x:x+cut,y:y+h},{x,y:y+h-cut},{x,y:y+cut}];
        g.fillPoints(points,true);g.lineStyle(1,hover?this.theme.accent.number:this.theme.line.number,1);g.strokePoints(points,true);
        g.lineStyle(1,this.theme.accent.number,hover?.65:.24);g.strokeRect(x+4,y+4,w-8,h-8);
      };
      paint(false);
      const number=this.label(x+15,y+h/2,String(index+1).padStart(2,'0'),13,this.theme.accent.css).setOrigin(0,.5);
      const text=this.label(x+47,y+h/2,label,17,this.theme.text.css,w-66,{lineSpacing:4}).setOrigin(0,.5);
      const zone=this.add.zone(x,y,w,h).setOrigin(0).setInteractive({useHandCursor:true});
      zone.on('pointerover',()=>{paint(true);text.setColor(this.theme.accent.css);});
      zone.on('pointerout',()=>{paint(false);text.setColor(this.theme.text.css);});
      zone.on('pointerdown',()=>{this.state.step++;this.state.lastChoice=label;this.draw();});
      this.hits.push({id,x,y,width:w,height:h});
      return {id,x,y,width:w,height:h,textHeight:text.height,textWidth:text.width};
    }
    placeStory(){
      this.storyText?.setY(this.storyBounds.y-this.state.scroll);
      if(this.scrollHint)this.scrollHint.setText(this.storyMaxScroll>0?`${Math.round(this.state.scroll/this.storyMaxScroll*100)}% · прокрутка колёсиком`:'');
    }
    draw(){
      this.storyMask?.destroy();this.storyMask=null;
      this.begin();const p=this.pad,bottom=this.h-p;
      this.heading(this.state.mode==='quest'?'Переправа в тумане':'Разговор у старого тракта',
        this.state.mode==='quest'?'Текстовый квест · глава I':'Лиора · проводник');
      const toolbarY=p+78;
      this.button('mode-quest',p,toolbarY,164,36,'Текстовый квест',()=>this.setDemo({mode:'quest',step:0}),{active:this.state.mode==='quest'});
      this.button('mode-dialogue',p+172,toolbarY,122,36,'Диалог',()=>this.setDemo({mode:'dialogue',step:0}),{active:this.state.mode==='dialogue'});
      this.button('long-text',p+310,toolbarY,205,36,this.state.longText?'Длинный текст: вкл.':'Длинный текст',()=>this.setDemo({longText:!this.state.longText}),{active:this.state.longText});
      const countX=this.w-p-294;
      this.label(countX-94,toolbarY+9,'Ответов',15,this.theme.dim.css);
      for(let i=1;i<=6;i++)this.button(`count-${i}`,countX+(i-1)*49,toolbarY,42,36,String(i),()=>this.setDemo({count:i}),{active:this.state.count===i});
      const top=p+132,side=Math.min(290,this.w*.24),right=this.w-p-side,mainW=right-p-22;
      this.panel(p,top,mainW,bottom-top);this.panel(right,top,side,bottom-top);
      const sx=right+22,sw=side-44;
      this.label(sx,top+22,this.state.mode==='quest'?'Переправа':'Лиора',24,this.theme.accent.css);
      this.label(sx,top+60,this.state.mode==='quest'?'Параметры ситуации':'Проводник',15,this.theme.dim.css,sw);
      this.line(sx,top+94,sw);
      const data=this.state.mode==='quest'?[['Время','6 часов'],['Припасы','8 / 12'],['Состояние моста','Ненадёжное'],['Риск','Средний']]
        :[['Отношение','Доверие +12'],['Настроение','Насторожена'],['Известность','Знакомы'],['Тема','Пропавший караван']];
      const shortPanel=bottom-top<450,rhythm=shortPanel?42:Math.min(61,(bottom-top-220)/4);
      data.forEach(([name,value],i)=>{
        if(shortPanel){this.label(sx,top+112+i*rhythm,name,14,this.theme.dim.css);this.label(sx+sw,top+130+i*rhythm,value,15,this.theme.accent.css).setOrigin(1,0);}
        else{this.label(sx,top+112+i*rhythm,name,15,this.theme.dim.css);this.label(sx,top+133+i*rhythm,value,17,this.theme.accent.css,sw);}
      });
      const goalY=top+(shortPanel?110:122)+4*rhythm;
      this.line(sx,goalY,sw);if(!shortPanel)this.label(sx,goalY+19,'Текущая цель',15,this.theme.dim.css);
      this.label(sx,goalY+(shortPanel?12:47),this.state.mode==='quest'?'Найти безопасный путь через реку.':'Узнать, куда ушёл караван.',shortPanel?16:17,undefined,sw);
      const contentX=p+24,contentW=mainW-48,gap=10,bw=(contentW-gap)/2;
      const short=this.state.mode==='quest'?['Осмотреть опоры моста','Поговорить с лодочником','Искать брод','Переждать туман','Проверить припасы','Вернуться к тракту']
        :['Спросить о караване','Предложить помощь','Уточнить путь','Завершить разговор','Спросить о разломе','Узнать о награде'];
      const long=this.state.mode==='quest'?[
        'Спуститься к воде и осмотреть опоры моста, прежде чем вести по нему весь отряд.',
        'Расспросить лодочника о течении и договориться о переправе для людей и припасов.',
        'Пройти вдоль берега и поискать брод, даже если это займёт несколько часов.',
        'Остаться у переправы до рассвета: в темноте идти по незнакомому мосту слишком опасно.',
        'Пересчитать припасы и решить, хватит ли еды на обходной путь через перевал.',
        'Вернуться к старому тракту и предупредить остальных о состоянии переправы.'
      ]:[
        'Попросить Лиору вспомнить, кто сопровождал караван и как были вооружены эти люди.',
        'Предложить помощь в поисках, но сначала узнать, какую опасность она скрывает.',
        'Попросить отметить безопасную дорогу к перевалу и места, где стоит разбить лагерь.',
        'Поблагодарить за сведения и закончить разговор, чтобы подготовиться к дороге.',
        'Спросить, связаны ли огни за рекой с разломом и пропажей путешественников.',
        'Уточнить, кто обещал награду за караван и какие доказательства нужно принести.'
      ];
      const choices=(this.state.longText?long:short).slice(0,this.state.count);
      const heights=choices.map(label=>{const probe=this.label(-5000,-5000,label,17,undefined,bw-66,{lineSpacing:4});const height=Math.max(58,probe.height+28);probe.destroy();return height;});
      const rowHeights=Array.from({length:Math.ceil(choices.length/2)},(_,i)=>Math.max(...heights.slice(i*2,i*2+2)));
      const choiceH=rowHeights.reduce((sum,h)=>sum+h,0)+(rowHeights.length-1)*gap;
      const choiceY=bottom-22-choiceH;
      this.label(contentX,top+21,this.state.mode==='quest'?'На другом берегу':'Лиора',20,this.theme.accent.css);
      this.line(contentX,choiceY-17,contentW);
      this.storyBounds={x:contentX,y:top+61,width:contentW,height:Math.max(50,choiceY-top-111)};
      const paragraphs=this.state.mode==='quest'?[
        'Из тумана проступают остатки старой переправы. Вода скрывает нижние опоры, а на мокрых досках видны свежие следы. У причала покачивается лодка. Её хозяин молча наблюдает за вами.',
        'До наступления темноты остаётся несколько часов. За рекой начинается короткая дорога к перевалу; обход по старому тракту отнимет ещё день. Проводник опускается на колено и проверяет землю у разрушенного ограждения.',
        'Следы оставлены недавно: несколько человек прошли к мосту с тяжёлой поклажей, но обратно никто не возвращался. На верёвке у причала висит клочок синей ткани. Лодочник замечает ваш взгляд и отворачивается.',
        'Ветер приносит запах мокрого дерева. Где-то за пеленой тумана звенит металл, затем снова становится тихо. Нужно выбрать путь, пока у отряда ещё достаточно времени и припасов.'
      ]:[
        '«Караван прошёл здесь на рассвете. Но к перевалу никто не вышел». Лиора опускает голос и смотрит на лес. «Если собираешься искать их, не сворачивай к огням за рекой».',
        'Она раскладывает на столе грубую карту. Несколько троп отмечены углём; у переправы стоит вопросительный знак. «Сначала нужно понять, кто оставил эти следы. Я видела не только людей».',
        'Лиора замолкает, давая вам время рассмотреть карту. На её рукаве заметен свежий порез. Она явно знает больше, но пока не решила, можно ли вам доверять.'
      ];
      const story=(this.state.longText?[...paragraphs,...paragraphs]:paragraphs.slice(0,2)).join('\n\n');
      this.storyText=this.label(contentX,this.storyBounds.y,story,19,undefined,contentW,{lineSpacing:9});
      this.storyMaxScroll=Math.max(0,this.storyText.height-this.storyBounds.height);
      this.state.scroll=Phaser.Math.Clamp(this.state.scroll,0,this.storyMaxScroll);
      const maskGraphic=this.make.graphics({x:0,y:0,add:false});maskGraphic.fillStyle(0xffffff).fillRect(this.storyBounds.x,this.storyBounds.y,this.storyBounds.width,this.storyBounds.height);
      this.storyMask=maskGraphic.createGeometryMask();this.storyMask.geometryMask=maskGraphic;
      this.storyText.setMask(this.storyMask);
      // Mask graphics are not in the display list; destroy them together with the mask.
      const mask=this.storyMask,originalDestroy=mask.destroy.bind(mask);
      mask.destroy=()=>{maskGraphic.destroy();originalDestroy();};
      this.scrollHint=this.label(contentX,this.storyBounds.y+this.storyBounds.height+7,'',13,this.theme.dim.css);
      this.placeStory();
      this.choiceBounds=[];let rowY=choiceY;
      choices.forEach((label,i)=>{const row=Math.floor(i/2);if(i>0&&i%2===0)rowY+=rowHeights[row-1]+gap;
        this.choiceBounds.push(this.framedChoice(`choice-${i}`,contentX+(i%2)*(bw+gap),rowY,bw,rowHeights[row],label,i));});
      if(this.state.step){
        this.scrollHint.setText(`Ответ принят · шаг ${this.state.step}${this.storyMaxScroll>0?' · текст прокручивается колёсиком':''}`);
      }
    }
    inspect(){return {...super.inspect(),layout:'two-columns',choices:this.choiceBounds,storyBounds:this.storyBounds,storyMaxScroll:this.storyMaxScroll,storyHeight:this.storyText?.height};}
  };
}
