import {alignmentSamples} from './perspectives.js?v=4';
export function createParameterMap(canvas,onChange){
 const samples=alignmentSamples();let current={m:1/3,phi:0},dots=[],rect,drag=null;
 function draw(value=current){current=value;rect=canvas.getBoundingClientRect();const dpr=Math.min(devicePixelRatio||1,2),w=rect.width,h=rect.height;canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#f7f5ee';ctx.fillRect(0,0,w,h);
  const box={x:42,y:18,w:w-60,h:h-48},at=p=>[box.x+p.m*box.w,box.y+(Math.PI-p.phi)/(2*Math.PI)*box.h];
  ctx.strokeStyle='#d7ded3';ctx.lineWidth=1;for(const phi of [-Math.PI,-Math.PI/2,0,Math.PI/2,Math.PI]){const y=at({m:0,phi})[1];ctx.beginPath();ctx.moveTo(box.x,y);ctx.lineTo(box.x+box.w,y);ctx.stroke();}
  const bins=new Set();dots=[];ctx.fillStyle='#557d7880';
  for(const p of samples){const [x,y]=at(p),bin=`${Math.round(x/7)},${Math.round(y/7)}`;if(bins.has(bin))continue;bins.add(bin);dots.push({...p,x,y});ctx.beginPath();ctx.arc(x,y,1.8,0,2*Math.PI);ctx.fill();}
  ctx.strokeStyle='#c45430';ctx.lineWidth=2;const y=at({m:0,phi:0})[1];ctx.beginPath();ctx.moveTo(box.x,y);ctx.lineTo(box.x+box.w,y);ctx.stroke();
  for(const m of [0,1]){const x=at({m,phi:0})[0];ctx.strokeStyle='#557d78';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x,box.y);ctx.lineTo(x,box.y+box.h);ctx.stroke();}
  ctx.font='10px ui-sans-serif,system-ui';ctx.fillStyle='#687873';ctx.textAlign='right';ctx.fillText('+180',box.x-7,box.y+4);ctx.fillText('0',box.x-7,y+3);ctx.fillText('−180',box.x-7,box.y+box.h+3);ctx.textAlign='left';ctx.fillText('Chevron',box.x,h-8);ctx.textAlign='right';ctx.fillText('Comet',box.x+box.w,h-8);
  for(const [m,label] of [[1/3,'Hat'],[2/3,'Turtle']]){const x=at({m,phi:0})[0];ctx.fillStyle='#c45430';ctx.beginPath();ctx.arc(x,y,4,0,2*Math.PI);ctx.fill();ctx.textAlign='center';ctx.fillStyle='#294c48';ctx.fillText(label,x,y-10);}
  const [x,yy]=at(current);ctx.strokeStyle='#294c48';ctx.lineWidth=2;ctx.fillStyle='#fffaf0';ctx.beginPath();ctx.arc(x,yy,5,0,2*Math.PI);ctx.fill();ctx.stroke();
  canvas._mapBox=box;
 }
 function fromEvent(e){const b=canvas._mapBox,r=canvas.getBoundingClientRect();return {m:Math.max(0,Math.min(1,(e.clientX-r.left-b.x)/b.w)),phi:Math.max(-Math.PI,Math.min(Math.PI,Math.PI-(e.clientY-r.top-b.y)/b.h*2*Math.PI)),exact:null};}
 canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY};});
 canvas.addEventListener('pointermove',e=>{if(drag)onChange(fromEvent(e));});
 canvas.addEventListener('pointerup',e=>{if(!drag)return;const moved=Math.hypot(e.clientX-drag.x,e.clientY-drag.y);drag=null;if(moved>5){onChange(fromEvent(e));return;}const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let best=null,d=10;
  for(const p of dots){const distance=Math.hypot(p.x-x,p.y-y);if(distance<d){best=p;d=distance;}}
  onChange(best?{m:best.m,phi:best.phi,exact:best.exact}:fromEvent(e));
 });canvas.addEventListener('pointercancel',()=>{drag=null;});
 new ResizeObserver(()=>draw()).observe(canvas);return {draw};
}
