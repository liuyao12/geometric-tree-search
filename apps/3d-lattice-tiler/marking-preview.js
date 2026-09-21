import {markingDomain} from './marking-learning.js?v=20260921-marking-library';
// Shared inspection surface for the two engines. Data comes from the live
// worker, never from a recorded marking or an independent classifier.
export class MarkingPreview{
 constructor(host){
  this.host=host;host.hidden=true;host.innerHTML='<h3>GCTS · learn markings</h3><p class="marking-progress" role="status"></p><label>Marking orientation <select aria-label="Marking orientation"></select></label><canvas width="800" height="300" aria-label="Live pair corona and evolving point marking"></canvas><p class="marking-detail"></p>';
  this.canvas=host.querySelector('canvas');this.ctx=this.canvas.getContext('2d');this.status=host.querySelector('.marking-progress');this.detail=host.querySelector('.marking-detail');this.select=host.querySelector('select');this.select.onchange=()=>this.draw();this.model=null;this.snapshot=null;this.placements=[];this.hits=[];this.hover=null;this.changed=new Set();
  this.canvas.style.cssText='width:100%;height:auto;background:#fafbf7;border-radius:8px;';
  this.canvas.onmousemove=e=>{const r=this.canvas.getBoundingClientRect();this.hover={x:(e.clientX-r.left)*800/r.width,y:(e.clientY-r.top)*300/r.height};this.draw();};this.canvas.onmouseleave=()=>{this.hover=null;this.draw();};
 }
 reset(model){this.model=model;this.domainExtent=1;this.domains=markingDomain(model,1);this.snapshot=null;this.placements=[];this.changed.clear();this.select.replaceChildren(...model.orientations.map((o,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`Tile ${(o.type??0)+1} · orientation ${o.index??i}`;return option;}));this.host.hidden=false;this.status.textContent='Enumerating neighboring pairs…';this.detail.textContent='Unmarked one-corona checks; provisional values are not used to label samples.';this.draw();}
 accept(event){if(!this.model)return;
  if(event.type==='marking-learned'){
   this.snapshot=event.marking;
   this.status.textContent=event.marking.accepted?`${event.marking.saved?.persisted?'Saved':'Validated this visit'} · ${event.marking.saved?.name??'marking'} · starting marked tiling`:`Marking not activated · ${event.marking.reason}`;
  }else{
   this.placements=event.placements??this.placements;
   if(event.phase==='update'||event.phase==='refine'||event.phase==='replay'){
    const before=new Map((this.snapshot?.fields??[]).flatMap((f,oi)=>f.map(m=>[`${oi}:${m.pos}|${m.component}`,m.value]))),after=new Map(event.snapshot.fields.flatMap((f,oi)=>f.map(m=>[`${oi}:${m.pos}|${m.component}`,m.value])));
    this.changed=new Set([...new Set([...before.keys(),...after.keys()])].filter(k=>before.get(k)!==after.get(k)));this.snapshot=event.snapshot;
   }
   const c=event.counts??{};this.status.textContent=`${event.pairs??0} pairs · ${c.valid??0} valid · ${c.invalid??0} invalid · ${c.unresolved??0} unresolved · ${event.phase==='replay'?'checking saved pair evidence':event.phase==='pair'?'trying the next pair':event.phase==='refine'?'refining free values':event.phase==='update'?event.status: event.action??'filling the 1-corona'}`;
  }
  const s=this.snapshot;
  if(s&&s.extent!==this.domainExtent){this.domainExtent=s.extent;this.domains=markingDomain(this.model,s.extent);}
  this.detail.textContent=s?`${s.accepted?'Validated':'Provisional'} · accepts ${s.positivePassed??0}/${s.counts?.valid??0} valid · blocks ${s.negativeBlocked??0}/${s.counts?.invalid??0} invalid · ${s.points??0} points / ${s.values??0} values across orientations. Orange: changed. Hover for values; * is free.`:'Awaiting the first label.';
  this.draw();
 }
 project(p){return [(p[0]-p[2])*.8,p[1]*.8-(p[0]+p[2])*.35];}
 map(points,x,width){const qs=points.map(p=>this.project(p)),xs=qs.map(p=>p[0]),ys=qs.map(p=>p[1]),min=[Math.min(...xs),Math.min(...ys)],max=[Math.max(...xs),Math.max(...ys)],scale=Math.min((width-35)/Math.max(1,max[0]-min[0]),235/Math.max(1,max[1]-min[1]));return p=>{const q=this.project(p);return[x+width/2+(q[0]-(min[0]+max[0])/2)*scale,160-(q[1]-(min[1]+max[1])/2)*scale];};}
 geometry(o,t,map,core){const ctx=this.ctx;for(const face of o.faces??[]){ctx.beginPath();face.forEach((j,i)=>{const p=map(o.vertices[j].map((v,k)=>v+t[k]));i?ctx.lineTo(...p):ctx.moveTo(...p);});ctx.closePath();ctx.fillStyle=core?'#8bbfc13b':'#b5c9b52d';ctx.fill();ctx.strokeStyle=core?'#527d83':'#b6c5bb';ctx.lineWidth=core?1.3:.7;ctx.stroke();}}
 draw(){if(!this.model)return;const ctx=this.ctx;ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,800,300);ctx.fillStyle='#294d43';ctx.font='15px system-ui';ctx.fillText('Pair & one-corona attempt',14,22);ctx.fillText('Evolving marking',420,22);this.hits=[];
  const placements=this.placements.length?this.placements:[{oi:0,translation:[0,0,0]}],world=placements.flatMap(p=>this.model.orientations[p.oi].cells.map(c=>c.pos.map((v,i)=>v+p.translation[i]))),left=this.map(world,0,390);
  placements.forEach((p,i)=>this.geometry(this.model.orientations[p.oi],p.translation,left,i<2));
  const totals=new Map();for(const p of placements)for(const c of this.model.orientations[p.oi].cells){const pos=c.pos.map((v,i)=>v+p.translation[i]),key=pos.join();totals.set(key,(totals.get(key)??0)+c.weight);}
  for(const [key,n] of totals){const p=left(key.split(',').map(Number));ctx.beginPath();ctx.arc(...p,2.5,0,2*Math.PI);ctx.fillStyle=n===this.model.capacity?'#2d8b70':'#dfa22c';ctx.fill();}
  const oi=+this.select.value,o=this.model.orientations[oi],domain=this.domains[oi],right=this.map(domain.map(m=>m.pos),410,375),field=new Map((this.snapshot?.fields?.[oi]??[]).map(m=>[m.pos.join(),m.value]));this.geometry(o,[0,0,0],right,true);
  for(const m of domain){const [x,y]=right(m.pos),value=field.get(m.pos.join())??'*',changed=this.changed.has(`${oi}:${m.pos}|0`);ctx.beginPath();ctx.arc(x,y,changed?5:value==='*'?2:3.5,0,2*Math.PI);ctx.fillStyle=changed?'#e39931':value==='*'?'#9cafaa':`hsl(${value*137.5%360} 60% 40%)`;ctx.fill();this.hits.push({x,y,pos:m.pos,value});}
  ctx.strokeStyle='#d5e1d9';ctx.beginPath();ctx.moveTo(400,35);ctx.lineTo(400,286);ctx.stroke();
  if(this.hover){const hit=this.hits.filter(h=>Math.hypot(h.x-this.hover.x,h.y-this.hover.y)<9).sort((a,b)=>Math.hypot(a.x-this.hover.x,a.y-this.hover.y)-Math.hypot(b.x-this.hover.x,b.y-this.hover.y))[0];if(hit){const text=`(${hit.pos})  m=(${hit.value})`;ctx.font='13px system-ui';const width=ctx.measureText(text).width+14,x=Math.max(410,Math.min(hit.x+8,798-width)),y=Math.max(52,Math.min(hit.y-8,280));ctx.fillStyle='#fffdf1';ctx.fillRect(x,y-18,width,24);ctx.strokeStyle='#6a887b';ctx.strokeRect(x,y-18,width,24);ctx.fillStyle='#294d43';ctx.fillText(text,x+7,y);}}
 }
}
