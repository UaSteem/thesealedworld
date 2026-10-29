// Latest-size resize scheduling, isolated from Phaser and browser observer wiring.
export function createResizeCoordinator({readSize,readCurrent,resize,isDragging,requestFrame,cancelFrame}) {
  let frame=null,disposed=false;
  function schedule(){
    if(disposed||frame!==null)return;
    frame=requestFrame(()=>{
      frame=null;
      if(disposed||isDragging())return;
      const {width,height}=readSize(),current=readCurrent();
      if(width>0&&height>0&&(width!==current.width||height!==current.height))resize(width,height);
    });
  }
  function dispose(){disposed=true;if(frame!==null)cancelFrame(frame);frame=null;}
  return {schedule,dispose};
}
