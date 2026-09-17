const canvas=document.querySelector('#prelim-canvas');
if(canvas){
 const live=document.querySelector('#prelim-live'),config=document.querySelector('#prelim-config'),focus=document.querySelector('#prelim-focus');
 let yaw=25*Math.PI/180,pitch=.43,panX=0,panY=0,zoom=1,panMode=false;
 try{
  const response=await fetch(new URL('preliminary-report-data.json',import.meta.url));if(!response.ok)throw Error('Data unavailable');const data=await response.json();
  const old=new Set(data.prefix.map(p=>p.id)),blocked=new Set(data.triple.map(p=>p.id));
  function draw(){
   const prefix=config.value==='prefix';focus.disabled=prefix;if(prefix)focus.value='full';
   const points=config.value==='alternative'?data.alternative:prefix?data.prefix:data.union;
   const close=focus.value==='triple',shown=close?points.filter(p=>blocked.has(p.id)):points;
   const angle=yaw;
   const center=[0,1,2].map(k=>shown.reduce((s,p)=>s+p.position[k],0)/shown.length);
   const projected=shown.map(p=>{const [x,y,z]=p.position.map((v,k)=>v-center[k]),a=x*Math.cos(angle)-z*Math.sin(angle),b=x*Math.sin(angle)+z*Math.cos(angle);return {...p,x:a,y:y*Math.cos(pitch)-b*Math.sin(pitch),z:y*Math.sin(pitch)+b*Math.cos(pitch)};});
   const span=Math.max(1,...shown.map(p=>Math.hypot(...p.position.map((v,k)=>v-center[k])))),scale=190/span*zoom,ctx=canvas.getContext('2d');
   ctx.clearRect(0,0,960,510);ctx.fillStyle='#f1f5f2';ctx.fillRect(0,0,960,510);
   for(const p of projected){p.px=480+panX+p.x*scale;p.py=255+panY-p.y*scale;}
   const trio=projected.filter(p=>blocked.has(p.id));
   if(trio.length===3){ctx.strokeStyle='#c47622';ctx.lineWidth=2;ctx.setLineDash([6,5]);for(let i=0;i<3;i++){const a=trio[i],b=trio[(i+1)%3];ctx.beginPath();ctx.moveTo(a.px,a.py);ctx.lineTo(b.px,b.py);ctx.stroke();if(close){const d=Math.hypot(...a.position.map((v,k)=>v-b.position[k]));ctx.font='18px system-ui';ctx.fillStyle='#75480d';ctx.fillText(d.toFixed(3)+' Å',(a.px+b.px)/2+8,(a.py+b.py)/2-8);}}ctx.setLineDash([]);}
   projected.sort((a,b)=>a.z-b.z);for(const p of projected){const highlight=blocked.has(p.id)&&!prefix;ctx.beginPath();ctx.arc(p.px,p.py,highlight?11:8,0,2*Math.PI);ctx.fillStyle=highlight?'#c47622':old.has(p.id)?'#227d70':'#8a9ca7';ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=2;ctx.stroke();}
   ctx.fillStyle='#53696d';ctx.font='16px system-ui';ctx.fillText(close?'Three actual coordinates · distance constraints, not bonds':shown.length+' saved atoms · orthographic projection',22,32);
   live.textContent=prefix?'14 fixed atoms, with 4 centered supports and 10 remaining center obligations. This is a generated prefix.':config.value==='alternative'?'Second verified alternative: one added atom moves, but the blocked neighborhood is unchanged. Still 20 unsupported centers.':'34 distinct atoms pass the supplied-union checks. Only 14 are support centers; the other 20 still need continuation.';
  }
  function reset(){yaw=25*Math.PI/180;pitch=.43;panX=panY=0;zoom=1;draw();}
  const points=new Map();canvas.tabIndex=0;canvas.setAttribute('aria-label','Saved silicon geometry. Drag to orbit, Shift-drag to pan, scroll to zoom. Arrow keys orbit, Shift and arrows pan, R resets.');
  const pair=()=>{const [a,b]=[...points.values()];return b?{x:(a.x+b.x)/2,y:(a.y+b.y)/2,d:Math.hypot(a.x-b.x,a.y-b.y)}:null;};
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);points.set(e.pointerId,{x:e.clientX,y:e.clientY});});
  canvas.addEventListener('pointermove',e=>{if(!points.has(e.pointerId))return;const old=points.get(e.pointerId),before=pair();points.set(e.pointerId,{x:e.clientX,y:e.clientY});const after=pair(),rect=canvas.getBoundingClientRect();if(before&&after){panX+=(after.x-before.x)*960/rect.width;panY+=(after.y-before.y)*510/rect.height;if(before.d>0)zoom=Math.max(.2,Math.min(8,zoom*after.d/before.d));}else if(panMode||e.shiftKey||e.buttons===2){panX+=(e.clientX-old.x)*960/rect.width;panY+=(e.clientY-old.y)*510/rect.height;}else{yaw+=(e.clientX-old.x)*.008;pitch=Math.max(-1.55,Math.min(1.55,pitch+(e.clientY-old.y)*.008));}draw();});
  for(const name of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(name,e=>points.delete(e.pointerId));
  canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.2,Math.min(8,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
  canvas.addEventListener('keydown',e=>{if(e.key.toLowerCase()==='r'){reset();return;}if(!e.key.startsWith('Arrow'))return;e.preventDefault();const x=e.key==='ArrowLeft'?-1:e.key==='ArrowRight'?1:0,y=e.key==='ArrowUp'?-1:e.key==='ArrowDown'?1:0;if(e.shiftKey){panX+=x*20;panY+=y*20;}else{yaw+=x*.1;pitch=Math.max(-1.55,Math.min(1.55,pitch+y*.1));}draw();});
  document.querySelector('#prelim-pan').onclick=e=>{panMode=!panMode;e.currentTarget.setAttribute('aria-pressed',String(panMode));};document.querySelector('#prelim-reset').onclick=reset;
  for(const control of [config,focus])control.addEventListener('input',reset);draw();
 }catch(error){live.textContent='The saved-coordinate figure could not load. The report and downloadable evidence remain available.';}
}
const toc=document.querySelector('.toc');if(toc){const a=document.createElement('a');a.href='#preliminary-report';a.textContent='NEW / Preliminary report';toc.prepend(a);}
