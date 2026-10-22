import {BASE,TRIANGLES,materialize,H,T,cartesian,MODEL_INFO} from './model.js';
const $=id=>document.getElementById(id),colors=['#a7c5c1','#ecd8ae','#c4d3b7','#e3b99d','#b8cbd0','#d7c5ac'];
let worker=null,snapshot={placements:[{orientation:0,translation:[0,0,0,0],generation:0}],stats:{frontierPoints:28}},paused=false,morph=0,height='r',yaw=-.65,pitch=.75,drag=null;
let tiles=[],pending=false;
function schedule(){if(!pending){pending=true;requestAnimationFrame(()=>{pending=false;draw();});}}
function load(s){snapshot=s;tiles=s.placements.map(p=>materialize(p.orientation,p.translation));
 for(const id of ['tiles','attempts','forced','branches','backtracks','frontier']){
  const value=id==='tiles'?tiles.length:id==='frontier'?(s.verification?.openVertexObligations??s.stats.frontierPoints):s.stats[id];$(id).textContent=(value||0).toLocaleString();
 }
 if(s.choice)$('choice').textContent=`${s.choice.kind==='forced'?'Forced point':s.choice.kind==='dead'?'Dead point':'Branch point'} · generation ${s.choice.generation??'—'} · ${s.choice.degree??0} candidate placements`;
 $('export').disabled=!tiles.length;schedule();
}
function context(id){const c=$(id),rect=c.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);c.width=Math.round(rect.width*dpr);c.height=Math.round(rect.height*dpr);const ctx=c.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#f7f5ee';ctx.fillRect(0,0,rect.width,rect.height);return {ctx,w:rect.width,h:rect.height};}
function fit(points,w,h,pad=22){const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),sc=Math.min((w-2*pad)/Math.max(x1-x0,1),(h-2*pad)/Math.max(y1-y0,1));return p=>[w/2+(p[0]-(x0+x1)/2)*sc,h/2-(p[1]-(y0+y1)/2)*sc];}
function poly(ctx,ps,fill,stroke,width=1){ctx.beginPath();ps.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.lineJoin='round';ctx.stroke();}
function color(tile){return tile.orientation>=6?'#355e69':colors[tile.orientation%6];}
function draw(){if(!tiles.length)return;
 const a=Math.PI/3-morph*Math.PI/6,c=Math.cos(a),s=Math.sin(a),{ctx,w,h}=context('plane');
 const all=tiles.map(tile=>tile.vertices.map(p=>{const q=cartesian(p);return [c*q[0]+s*q[2],c*q[1]+s*q[3]];})),project=fit(all.flat(),w,h);
 all.forEach((ps,i)=>poly(ctx,ps.map(project),color(tiles[i]),'#647f75',.8));
 poly(ctx,all[0].map(project),'#00000000','#c45430',2);
 const surf=context('surface'),cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const world=tiles.map(tile=>tile.vertices.map(p=>{const [x,y]=H(p),px=x+y/2,py=Math.sqrt(3)*y/2,z=height==='r'?p[2]:p[3],rx=cy*px-sy*py,ry=sy*px+cy*py;return [rx,cp*ry-sp*z,sp*ry+cp*z];}));
 const surfaceProject=fit(world.flat(),surf.w,surf.h,28);
 const faces=[];world.forEach((ps,i)=>TRIANGLES.forEach(t=>faces.push({tile:i,tri:t,depth:t.reduce((sum,j)=>sum+ps[j][2]/3,0)})));faces.sort((a,b)=>a.depth-b.depth);
 faces.forEach(face=>poly(surf.ctx,face.tri.map(i=>surfaceProject(world[face.tile][i])),color(tiles[face.tile]),'#5a786e88',.55));
 world.forEach((ps,i)=>{const screen=ps.map(surfaceProject);surf.ctx.beginPath();screen.forEach((p,j)=>j?surf.ctx.lineTo(...p):surf.ctx.moveTo(...p));surf.ctx.closePath();surf.ctx.strokeStyle=i===0?'#c45430':'#365650a0';surf.ctx.lineWidth=i===0?1.8:.8;surf.ctx.stroke();});
}
$('start').onclick=()=>{
 worker?.terminate();worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});paused=false;$('pause').textContent='Pause';$('start').disabled=true;$('pause').disabled=false;$('stop').disabled=false;
 $('status').textContent='Searching from one lifted tile. Both projections and shared vertex coordinates are checked.';$('verification').textContent='Search in progress. Current trial patches may still lead to dead ends.';
 worker.onmessage=e=>{if(e.data.type==='error'){$('status').textContent=`Search stopped: ${e.data.message}`;finish();return;}const s=e.data.snapshot;load(s);
  if(e.data.type==='done'){
   const v=s.verification;$('status').textContent=s.status==='consistent finite patch'?`Checkpoint reached: ${s.placements.length} tiles. Both projections and shared lifts verified.`:`${s.status==='unknown'?'Budget or stop limit: unknown.':'Rooted search exhausted.'} Showing the best frontier-viable patch (${s.placements.length} tiles).`;
   $('verification').textContent=`Independent replay passed · ${v.sharedEdges} shared lifted edges · ${v.openVertexObligations} open vertex obligations. This is a consistent finite patch, not an infinite-tiling certificate.`;finish();
  }else if(paused)$('status').textContent='Paused with the search stack intact.';else $('status').textContent=`Searching · ${s.placements.length} current tiles · ${(s.elapsedMs/1000).toFixed(1)} seconds${s.choice?.kind==='dead'?' · backtracking from a dead frontier':''}`;
 };
 worker.postMessage({type:'start',options:{target:Math.max(2,Math.min(80,Math.round(+$('target').value)||12)),nodeLimit:+$('budget').value,seed:+$('seed').value||1}});
};
function finish(){$('start').disabled=false;$('pause').disabled=true;$('stop').disabled=true;}
$('pause').onclick=()=>{paused=!paused;worker?.postMessage({type:'pause',value:paused});$('pause').textContent=paused?'Resume':'Pause';if(paused)$('status').textContent='Paused with the search stack intact.';};
$('stop').onclick=()=>{worker?.postMessage({type:'stop'});$('status').textContent='Stopping and restoring the current search branch…';};
$('morph').oninput=e=>{morph=+e.target.value/1000;$('shape').textContent=morph===0?'Hat':morph===1?'Turtle':'Intermediate projection';schedule();};
$('height').onchange=e=>{height=e.target.value;schedule();};
$('surface').onpointerdown=e=>{drag={x:e.clientX,y:e.clientY};$('surface').setPointerCapture(e.pointerId);};
$('surface').onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.012;pitch=Math.max(-1.4,Math.min(1.4,pitch+(e.clientY-drag.y)*.012));drag={x:e.clientX,y:e.clientY};schedule();};
$('surface').onpointerup=()=>{drag=null;};$('surface').onpointercancel=()=>{drag=null;};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({model:MODEL_INFO,...snapshot},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='lifted-hat-turtle-search.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
new ResizeObserver(schedule).observe($('plane'));new ResizeObserver(schedule).observe($('surface'));load(snapshot);
