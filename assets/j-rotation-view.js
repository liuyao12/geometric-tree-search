import{TILE,EDGE_FAMILY,PROJECTIONS,projectPose,projectedShape,radius}from'./j-rotation-model.js';
const $=id=>document.getElementById(id),canvas=$('rotation'),ctx=canvas.getContext('2d');
let applications=0,displayStep=0,previousStep=null,pending=0,animating=false,frame=0,dimensions=[1,1];
const selected=()=>{const value=$('projection-choice').value;return value==='all'?PROJECTIONS:PROJECTIONS.filter(p=>p.id===value);};
function draw(){const dpr=devicePixelRatio||1,[width,height]=dimensions;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);ctx.fillStyle='#f6f6ee';ctx.fillRect(0,0,width,height);
 const views=selected(),cell=width/views.length,commonRadius=Math.max(...views.map(p=>radius(p.theta))),scale=Math.max(1,Math.min(cell-24,height-65)/(2*commonRadius));
 views.forEach((view,i)=>{const cx=(i+.5)*cell,cy=(height+22)/2,toScreen=p=>[cx+p[0]*scale,cy-p[1]*scale];
  if(i){ctx.strokeStyle='#dce2d8';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(i*cell,12);ctx.lineTo(i*cell,height-12);ctx.stroke();}
  ctx.textAlign='center';ctx.textBaseline='top';ctx.fillStyle='#3d5e55';ctx.font='600 12px system-ui';ctx.fillText(view.name,cx,12);ctx.font='10px system-ui';ctx.fillStyle='#7a8b80';ctx.fillText(animating?'Rotating in 4D…':projectedShape(view.id,applications),cx,30);
  ctx.strokeStyle='#b6c4b9';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(cx-4,cy);ctx.lineTo(cx+4,cy);ctx.moveTo(cx,cy-4);ctx.lineTo(cx,cy+4);ctx.stroke();
  const path=step=>TILE.map(v=>toScreen(projectPose(v,step,view.theta)));
  if(previousStep!==null){const ghost=path(previousStep);ctx.beginPath();ghost.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.strokeStyle='#9eafa4';ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.stroke();ctx.setLineDash([]);}
  const points=path(displayStep);ctx.beginPath();points.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fillStyle='#c7ddd144';ctx.fill();
  for(let j=0;j<points.length;j++){ctx.beginPath();ctx.moveTo(...points[j]);ctx.lineTo(...points[(j+1)%points.length]);ctx.strokeStyle=EDGE_FAMILY[j]?'#d09140':'#2d8a7c';ctx.lineWidth=Math.min(3,Math.max(1.6,scale/12));ctx.stroke();}
  ctx.beginPath();ctx.arc(...points[0],3.5,0,Math.PI*2);ctx.fillStyle='#c96051';ctx.fill();ctx.strokeStyle='#fbfaf7';ctx.lineWidth=1;ctx.stroke();
 });
 canvas.setAttribute('aria-label',`${$('projection-choice').value==='all'?'Hat, Turtle and Spectre projections':views[0].name}, orientation ${applications%12} of 12`);
}
function status(){const n=applications%12;$('step-status').textContent=animating?`Applying J${pending>1?` · ${pending-1} more queued`:''}…`:n===0?`${applications?'Back at the original orientation':'Original orientation'} · ${applications} applications`:`Orientation ${n} of 12 · ${applications} application${applications===1?'':'s'}`;$('apply-j').classList.toggle('busy',animating);}
function next(){if(!pending)return;animating=true;previousStep=applications;const start=performance.now(),from=applications,duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:850;status();
 const tick=now=>{const t=duration?Math.min(1,(now-start)/duration):1,eased=t*t*(3-2*t);displayStep=from+eased;draw();if(t<1){frame=requestAnimationFrame(tick);return;}applications++;displayStep=applications;pending--;animating=false;status();draw();if(pending)next();};frame=requestAnimationFrame(tick);
}
$('apply-j').onclick=()=>{pending++;if(!animating)next();else status();};
$('reset').onclick=()=>{cancelAnimationFrame(frame);applications=0;displayStep=0;pending=0;animating=false;previousStep=null;status();draw();};
$('projection-choice').onchange=draw;
new ResizeObserver(()=>{const r=canvas.getBoundingClientRect();dimensions=[r.width,r.height];canvas.width=Math.round(r.width*(devicePixelRatio||1));canvas.height=Math.round(r.height*(devicePixelRatio||1));draw();}).observe(canvas);
status();draw();
