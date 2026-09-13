const canvas=document.querySelector('#prelim-canvas');
if(canvas){
 const live=document.querySelector('#prelim-live'),config=document.querySelector('#prelim-config'),focus=document.querySelector('#prelim-focus'),yaw=document.querySelector('#prelim-yaw');
 try{
  const response=await fetch(new URL('preliminary-report-data.json',import.meta.url));if(!response.ok)throw Error('Data unavailable');const data=await response.json();
  const old=new Set(data.prefix.map(p=>p.id)),blocked=new Set(data.triple.map(p=>p.id));
  function draw(){
   const prefix=config.value==='prefix';focus.disabled=prefix;if(prefix)focus.value='full';
   const points=config.value==='alternative'?data.alternative:prefix?data.prefix:data.union;
   const close=focus.value==='triple',shown=close?points.filter(p=>blocked.has(p.id)):points;
   const angle=Number(yaw.value)*Math.PI/180;document.querySelector('#prelim-yaw-value').textContent=yaw.value+'°';
   const center=[0,1,2].map(k=>shown.reduce((s,p)=>s+p.position[k],0)/shown.length);
   const projected=shown.map(p=>{const [x,y,z]=p.position.map((v,k)=>v-center[k]),a=x*Math.cos(angle)-z*Math.sin(angle),b=x*Math.sin(angle)+z*Math.cos(angle);return {...p,x:a,y:y*.91-b*.415,z:y*.415+b*.91};});
   const span=Math.max(1,...projected.flatMap(p=>[Math.abs(p.x),Math.abs(p.y)])),scale=Math.min(390,190)/span,ctx=canvas.getContext('2d');
   ctx.clearRect(0,0,960,510);ctx.fillStyle='#f1f5f2';ctx.fillRect(0,0,960,510);
   for(const p of projected){p.px=480+p.x*scale;p.py=255-p.y*scale;}
   const trio=projected.filter(p=>blocked.has(p.id));
   if(trio.length===3){ctx.strokeStyle='#c47622';ctx.lineWidth=2;ctx.setLineDash([6,5]);for(let i=0;i<3;i++){const a=trio[i],b=trio[(i+1)%3];ctx.beginPath();ctx.moveTo(a.px,a.py);ctx.lineTo(b.px,b.py);ctx.stroke();if(close){const d=Math.hypot(...a.position.map((v,k)=>v-b.position[k]));ctx.font='18px system-ui';ctx.fillStyle='#75480d';ctx.fillText(d.toFixed(3)+' Å',(a.px+b.px)/2+8,(a.py+b.py)/2-8);}}ctx.setLineDash([]);}
   projected.sort((a,b)=>a.z-b.z);for(const p of projected){const highlight=blocked.has(p.id)&&!prefix;ctx.beginPath();ctx.arc(p.px,p.py,highlight?11:8,0,2*Math.PI);ctx.fillStyle=highlight?'#c47622':old.has(p.id)?'#227d70':'#8a9ca7';ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=2;ctx.stroke();}
   ctx.fillStyle='#53696d';ctx.font='16px system-ui';ctx.fillText(close?'Three actual coordinates · distance constraints, not bonds':shown.length+' saved atoms · orthographic projection',22,32);
   live.textContent=prefix?'14 fixed atoms, with 4 centered supports and 10 remaining center obligations. This is a generated prefix.':config.value==='alternative'?'Second verified alternative: one added atom moves, but the blocked neighborhood is unchanged. Still 20 unsupported centers.':'34 distinct atoms pass the supplied-union checks. Only 14 are support centers; the other 20 still need continuation.';
  }
  for(const control of [config,focus,yaw])control.addEventListener('input',draw);draw();
 }catch(error){live.textContent='The saved-coordinate figure could not load. The report and downloadable evidence remain available.';}
}
const toc=document.querySelector('.toc');if(toc){const a=document.createElement('a');a.href='#preliminary-report';a.textContent='NEW / Preliminary report';toc.prepend(a);}
