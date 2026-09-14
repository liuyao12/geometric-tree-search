/* UI and rendering. Every solver event advances the animation by one visible step. */
'use strict';
const H=window.Hyperbolic,$=id=>document.getElementById(id);
const params=new URLSearchParams(location.search);
if(['2','3','4'].includes(params.get('m'))) $('tile').value=params.get('m');
if(params.has('seed'))$('seed').value=Math.max(0,Math.min(4294967295,Number(params.get('seed'))||1));
if(params.has('radius'))$('radius').value=Math.max(.6,Math.min(3,Number(params.get('radius'))||1.8));
if(params.get('prune')==='1')$('prune').checked=true;
let spec=H.family(+$('tile').value),mode=params.get('mode')==='search'?'search':'known';
let solver=null,known=[],visible=0,playing=false,event=null,events=[],nodes=new Map(),messages=[];
let ghost=null,selectedEdge=null,zoom=1,lastTick=0,dirty=true,traceFull=false;
const identity=()=>[[1,0],[0,0],[0,0],[1,0]];let camera=identity();
const view=$('view'),tree=$('tree'),preview=$('preview');
const transform=(z,M=camera)=>H.div(H.add(H.mul(M[0],z),M[1]),H.add(H.mul(M[2],z),M[3]));
const inverse=z=>transform(z,[camera[3],H.scale(camera[1],-1),H.scale(camera[2],-1),camera[0]]);
function compose(a,b){const r=[H.add(H.mul(a[0],b[0]),H.mul(a[1],b[2])),H.add(H.mul(a[0],b[1]),H.mul(a[1],b[3])),H.add(H.mul(a[2],b[0]),H.mul(a[3],b[2])),H.add(H.mul(a[2],b[1]),H.mul(a[3],b[3]))];const s=Math.max(...r.map(H.norm));return r.map(z=>H.scale(z,1/s));}
function moveMap(a,b){return [H.sub([1,0],H.mul(b,H.conj(a))),H.sub(b,a),H.sub(H.conj(b),H.conj(a)),H.sub([1,0],H.mul(H.conj(b),a))];}
function canvasSize(c){const r=c.getBoundingClientRect(),d=Math.min(2,devicePixelRatio||1);if(c.width!==Math.round(r.width*d)||c.height!==Math.round(r.height*d)){c.width=Math.round(r.width*d);c.height=Math.round(r.height*d);}const g=c.getContext('2d');g.setTransform(d,0,0,d,0,0);return {g,w:r.width,h:r.height};}
function project(p,w,h){
  const z=transform(p),model=$('model').value;
  if(model==='upper'){const q=H.diskToUpper(z,spec.cx,spec.cy),s=Math.min(w/6,h/4.2)*zoom;return [w/2+(q[0]-spec.cx)*s,h-38-q[1]*s];}
  const q=model==='klein'?H.klein(z):z,s=Math.min(w,h)*.435*zoom;return [w/2+q[0]*s,h/2-q[1]*s];
}
function unproject(x,y,w,h){
  const model=$('model').value;
  if(model==='upper'){const s=Math.min(w/6,h/4.2)*zoom;return H.upperToDisk([(x-w/2)/s+spec.cx,(h-38-y)/s],spec.cx,spec.cy);}
  const s=Math.min(w,h)*.435*zoom,p=[(x-w/2)/s,(h/2-y)/s];return model==='klein'?H.fromKlein(p):p;
}
function edgePath(g,a,b,projector,depth=0){
  const pa=projector(a),pb=projector(b),mid=H.fromKlein(H.scale(H.add(H.klein(a),H.klein(b)),.5)),pm=projector(mid);
  const dx=pb[0]-pa[0],dy=pb[1]-pa[1],error=Math.abs((pm[0]-pa[0])*dy-(pm[1]-pa[1])*dx)/(Math.hypot(dx,dy)||1);
  if(error>.28&&depth<10){edgePath(g,a,mid,projector,depth+1);edgePath(g,mid,b,projector,depth+1);}else g.lineTo(...pb);
}
function polygon(g,t,fill,stroke,w,h,width=.7){
  const p=z=>project(z,w,h);g.beginPath();g.moveTo(...p(t.v[0]));
  for(let i=0;i<t.v.length;i++)edgePath(g,t.v[i],t.v[(i+1)%t.v.length],p);
  g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}
}
function drawScene(){
  const {g,w,h}=canvasSize(view);g.clearRect(0,0,w,h);g.fillStyle='#091827';g.fillRect(0,0,w,h);
  g.save();g.beginPath();if($('model').value==='upper')g.rect(0,0,w,h-38);else g.arc(w/2,h/2,Math.min(w,h)*.435*zoom,0,H.TAU);g.clip();
  g.fillStyle='#102639';g.fillRect(0,0,w,h);
  const tiles=mode==='known'?known.slice(0,visible):solver.tiles;
  for(let i=0;i<tiles.length;i++){
    const t=tiles[i],hue=mode==='known'?175+((t.row%5+5)%5)*14:177+(t.node%9)*7;
    const color=`hsl(${hue} 42% ${mode==='known'?40+(Math.abs(t.column)%3)*4:41+(t.node%3)*5}%)`;
    polygon(g,t,color,'#10283b',w,h,.75);
  }
  if(mode==='search'&&$('show-edges').checked){
    g.setLineDash([5,5]);g.strokeStyle='#d0e0ed99';g.lineWidth=1;g.beginPath();
    for(let i=0;i<=180;i++){const a=H.TAU*i/180,p=project([Math.tanh(+$('radius').value/2)*Math.cos(a),Math.tanh(+$('radius').value/2)*Math.sin(a)],w,h);i?g.lineTo(...p):g.moveTo(...p);}g.stroke();g.setLineDash([]);
    g.strokeStyle='#85dfd48a';g.lineWidth=1.2;g.beginPath();for(const e of H.frontier(solver.tiles)){g.moveTo(...project(e.a,w,h));edgePath(g,e.a,e.b,p=>project(p,w,h));}g.stroke();
  }
  if(ghost){const bad=event?.type==='reject',back=event?.type==='backtrack';polygon(g,ghost,bad?'#f675884d':back?'#ffcf7840':'#ffdc8b54',bad?'#ff7b92':back?'#f5be65':'#ffdf9c',w,h,2);}
  if(selectedEdge&&mode==='search'){g.beginPath();g.moveTo(...project(selectedEdge[0],w,h));edgePath(g,...selectedEdge,p=>project(p,w,h));g.strokeStyle='#ffe5ab';g.lineWidth=3;g.stroke();}
  if(mode==='search'&&solver.tiles.length){polygon(g,solver.tiles[0],null,'#eaf6f5c0',w,h,1.7);}
  g.restore();g.strokeStyle='#637b8c';g.lineWidth=1;
  g.beginPath();if($('model').value==='upper'){g.moveTo(0,h-38);g.lineTo(w,h-38);}else g.arc(w/2,h/2,Math.min(w,h)*.435*zoom,0,H.TAU);g.stroke();
  $('zoom-label').textContent=Math.round(zoom*100)+'%';
}
function drawPreview(){
  const {g,w,h}=canvasSize(preview);g.clearRect(0,0,w,h);
  const s=Math.min((w-55)/spec.m,(h-42)/(spec.m*Math.sqrt(1.25))),proj=p=>{const q=H.diskToUpper(p,spec.cx,spec.cy);return [w/2+(q[0]-spec.m/2)*s,h-20-q[1]*s];};
  g.beginPath();g.moveTo(...proj(spec.v[0]));for(let i=0;i<spec.v.length;i++)edgePath(g,spec.v[i],spec.v[(i+1)%spec.v.length],proj);g.closePath();g.fillStyle='#d8eceb';g.fill();g.strokeStyle='#22878c';g.lineWidth=1.5;g.stroke();
  spec.v.forEach((v,i)=>{const p=proj(v);g.beginPath();g.arc(...p,2.5,0,H.TAU);g.fillStyle='#20777d';g.fill();g.fillStyle='#506a77';g.font='10px system-ui';g.textAlign='center';g.fillText(String.fromCharCode(65+i),p[0],p[1]+(i<=spec.m?14:-9));});
  if(event?.type==='try'&&ghost){const i=ghost.edge;g.beginPath();g.moveTo(...proj(spec.v[i]));edgePath(g,spec.v[i],spec.v[(i+1)%spec.v.length],proj);g.strokeStyle='#b27e21';g.lineWidth=3;g.stroke();}
}
function drawTree(){
  const {g,w,h}=canvasSize(tree);g.clearRect(0,0,w,h);
  if(mode!=='search'||nodes.size<2){g.fillStyle='#79909b';g.font='12px system-ui';g.fillText(mode==='known'?'Explicit construction — no search tree.':'The root is the initial tile. Press Play or Step.',8,h/2);return;}
  const ns=[...nodes.values()].slice(-180),lo=ns[0].id,hi=ns.at(-1).id,depthMax=Math.max(...ns.map(n=>n.depth),1);
  const pos=n=>[30+(n.id-lo)/Math.max(1,hi-lo)*(w-44),16+n.depth/depthMax*(h-35)];
  g.font='9px system-ui';g.fillStyle='#80929c';g.fillText('depth',2,10);g.fillText('0',7,20);g.fillText(String(depthMax),4,h-18);
  g.save();g.beginPath();g.rect(27,0,w-27,h);g.clip();
  for(const n of ns){const p=nodes.get(n.parent);if(!p)continue;g.beginPath();g.moveTo(...pos(p));g.lineTo(...pos(n));g.strokeStyle=n.status==='backtrack'?'#d6b57a99':'#adc2ca88';g.lineWidth=1;g.stroke();}
  for(const n of ns){const p=pos(n);g.beginPath();g.arc(...p,n.id===event?.node?3.5:2.3,0,H.TAU);g.fillStyle=n.status==='reject'?'#d06375':n.status==='backtrack'?'#c69444':n.status==='try'?'#465e72':'#168c8d';g.fill();}g.restore();
  $('tree-caption').textContent=`${nodes.size-1} attempted placements · showing ${ns.length} most recent nodes · full history in Export trace`;
}
const descriptions={seed:['Seed','One initial tile; no prescribed neighboring placements.'],choose:['Choose frontier','Try all equal-length sides on the highlighted edge.'],try:['Try candidate','A congruent tile placed by a hyperbolic isometry.'],place:['Accept','No detected overlap or forbidden contact.'],reject:['Reject',''],backtrack:['Backtrack','An exhausted branch has been removed.'],'dead-end':['Dead end','Every candidate on this frontier side failed.'],solved:['Disk covered','No exposed edge meets the interior of the target disk.'],exhausted:['Search exhausted','No completion in the explored edge-to-edge search.'],limit:['Safety limit','600 tiles reached. This is not an impossibility result.']};
function record(e){
  event=e;events.push(e);ghost=['try','reject','backtrack'].includes(e.type)?e.tile:null;
  if(e.edge)selectedEdge=e.edge;if(['solved','exhausted','limit'].includes(e.type))selectedEdge=null;
  if(e.type==='seed')nodes.set(0,{id:0,parent:null,depth:0,status:'place'});
  if(e.type==='try')nodes.set(e.node,{id:e.node,parent:e.parent,depth:e.depth,status:'try'});
  if(['place','reject','backtrack'].includes(e.type)&&nodes.has(e.node))nodes.get(e.node).status=e.type;
  const [title,detail]=descriptions[e.type]||[e.type,''];$('event-title').textContent=title;$('event-detail').textContent=e.reason||detail;
  $('event-dot').style.background=e.type==='reject'?'#d06375':e.type==='backtrack'?'#c69444':'#109b9e';
  const text=`${String(e.event).padStart(5,' ')}  ${e.type.padEnd(10,' ')} depth ${e.depth}${e.node!==undefined?'  #'+e.node:''}${e.reason?'  '+e.reason:''}`;
  messages.unshift({type:e.type,text});messages=messages.slice(0,35);$('log').replaceChildren(...messages.map(m=>{const d=document.createElement('div');d.textContent=m.text;d.className='log-'+m.type;return d;}));
  if(['solved','exhausted','limit'].includes(e.type)){playing=false;$('play').textContent='Finished';$('play').disabled=true;$('step').disabled=true;}
  if(events.length>=50000){playing=false;traceFull=true;$('play').disabled=true;$('step').disabled=true;$('play').textContent='Paused';$('event-title').textContent='Trace buffer full';$('event-detail').textContent='Export the trace, then reset. No events have been discarded.';}
  dirty=true;updateStats();
}
function updateStats(){
  $('s-tiles').textContent=mode==='known'?visible:solver.tiles.length;
  for(const [id,k] of [['tries','attempts'],['rejects','rejected'],['backs','backtracks'],['depth','maxDepth']])$('s-'+id).textContent=mode==='known'?'—':solver.stats[k];
}
function reset(home=false){
  playing=false;event=null;ghost=null;selectedEdge=null;events=[];messages=[];nodes.clear();traceFull=false;
  if(home){camera=identity();zoom=1;}spec=H.family(+$('tile').value);
  $('radius-value').textContent=(+$('radius').value).toFixed(1);$('extent-value').textContent=(+$('extent').value).toFixed(1);
  $('known-tab').classList.toggle('active',mode==='known');$('search-tab').classList.toggle('active',mode==='search');
  $('search-controls').hidden=mode!=='search';$('known-controls').hidden=mode!=='known';
  $('mode-badge').textContent=mode==='known'?'EXPLICIT CONSTRUCTION':'LIVE GEOMETRIC DFS';
  $('mode-help').textContent=mode==='known'?'A finite window of the known infinite tiling. Animate reveals the formula; there is no branching.':'Depth-first search from one tile, with every trial, rejection and rollback shown as it happens.';
  $('stage-caption').textContent=mode==='known'?'All tiles are congruent in the hyperbolic metric.':'Dashed curve: target disk. Gold: selected frontier side.';
  $('tile-meta').textContent=`${spec.v.length} geodesic sides · area ${spec.area.toFixed(6)} · curvature −1`;
  $('play').disabled=false;$('step').disabled=false;$('play').textContent=mode==='known'?'Animate':'Play';
  $('export-trace').disabled=mode!=='search';$('log').replaceChildren();$('tree-caption').textContent='Each node is an attempted placement; links follow recursive parent states.';
  if(mode==='known'){known=H.construction(spec,+$('extent').value);visible=known.length;$('event-title').textContent='Known tiling';$('event-detail').textContent=`${known.length} tiles in the displayed window · z ↦ ${spec.m}ᵏ(z + ${spec.m}j)`;}
  else {solver=new H.Search(spec,{radius:+$('radius').value,seed:Number($('seed').value)>>>0,anglePrune:$('prune').checked});record(solver.next());}
  updateStats();dirty=true;
}
function advance(){
  if(mode==='known'){if(visible>=known.length)visible=0;visible++;$('event-title').textContent='Reveal tile';$('event-detail').textContent=`${visible} / ${known.length} · construction only`;if(visible===known.length){playing=false;$('play').textContent='Animate';}updateStats();dirty=true;}
  else if(!traceFull){const e=solver.next();if(e)record(e);else playing=false;}
}
function togglePlay(){if($('play').disabled||traceFull)return;playing=!playing;if(mode==='known'&&playing&&visible===known.length)visible=0;$('play').textContent=playing?'Pause':mode==='known'?'Animate':'Play';lastTick=0;dirty=true;}
$('play').onclick=togglePlay;$('step').onclick=()=>{playing=false;$('play').textContent=mode==='known'?'Animate':'Play';advance();};$('reset').onclick=()=>reset();
$('known-tab').onclick=()=>{mode='known';reset(true);};$('search-tab').onclick=()=>{mode='search';reset(true);};
for(const id of ['tile','radius','seed','prune','extent'])$(id).onchange=()=>reset(id==='tile');
$('radius').oninput=()=>{$('radius-value').textContent=(+$('radius').value).toFixed(1);};$('extent').oninput=()=>{$('extent-value').textContent=(+$('extent').value).toFixed(1);};
$('speed').oninput=()=>{$('speed-value').textContent=$('speed').value+' events/s';};
$('model').onchange=()=>{camera=identity();zoom=1;$('model-badge').textContent=$('model').selectedOptions[0].textContent.toUpperCase();dirty=true;};
$('home').onclick=()=>{camera=identity();zoom=1;dirty=true;};$('show-edges').onchange=()=>dirty=true;
function download(name,data){const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
$('export-patch').onclick=()=>download(`hyperbolic-m${spec.m}-patch.json`,{format:'gcts-hyperbolic-patch-v1',model:'Poincare disk',curvature:-1,upperHalfPlaneOrigin:[spec.cx,spec.cy],prototile:spec.upper,mode,numerical:true,options:mode==='search'?solver.options:{radius:+$('extent').value},tiles:(mode==='known'?known.slice(0,visible):solver.tiles).map(t=>({vertices:t.v,node:t.node,row:t.row,column:t.column}))});
$('export-trace').onclick=()=>download(`hyperbolic-m${spec.m}-trace.json`,{format:'gcts-hyperbolic-trace-v1',prototile:spec.upper,options:solver.options,stats:solver.stats,complete:solver.done||['solved','exhausted'].includes(event?.type),events});
let drag=null;
view.addEventListener('pointerdown',e=>{const r=view.getBoundingClientRect(),p=unproject(e.clientX-r.left,e.clientY-r.top,r.width,r.height);if(H.norm(p)>.98)return;drag={p,camera:camera.map(z=>z.slice())};view.setPointerCapture(e.pointerId);});
view.addEventListener('pointermove',e=>{if(!drag)return;const r=view.getBoundingClientRect(),p=unproject(e.clientX-r.left,e.clientY-r.top,r.width,r.height);if(H.norm(p)>.98)return;camera=compose(moveMap(drag.p,p),drag.camera);dirty=true;});
view.addEventListener('pointerup',()=>drag=null);view.addEventListener('pointercancel',()=>drag=null);
view.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.55,Math.min(3,zoom*Math.exp(-e.deltaY*.001)));dirty=true;},{passive:false});
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(e.target.tagName))return;if(e.code==='Space'){e.preventDefault();togglePlay();}if(e.key.toLowerCase()==='n'&&!$('step').disabled)$('step').click();if(e.key.toLowerCase()==='r')reset();});
new ResizeObserver(()=>dirty=true).observe(view);window.addEventListener('resize',()=>dirty=true);
function frame(now){if(playing&&now-lastTick>=1000/(+$('speed').value)){lastTick=now;advance();}if(dirty){drawScene();drawPreview();drawTree();dirty=false;}requestAnimationFrame(frame);}
reset(true);requestAnimationFrame(frame);
// Read-only diagnostic access for reproducible browser tests and inspection.
window.hyperbolicLab={get spec(){return spec;},get mode(){return mode;},get solver(){return solver;},get events(){return events;},get known(){return known;}};
