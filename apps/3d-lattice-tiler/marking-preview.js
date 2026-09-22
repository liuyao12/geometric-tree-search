import {markingVectors} from './marking-display.js?v=20260921-vector-learning';
import {markingDomain} from './marking-learning.js?v=20260921-vector-learning';
import {inspectPairMarking,pairInspectionText} from './marking-pair-display.js?v=20260921-vector-learning';

// Shared view for both engines. Values and witnesses come from the worker.
export class MarkingPreview {
 constructor(host,{compact=false,onInspect=()=>{}}={}) {
  this.compact=compact;this.onInspect=onInspect;
  this.host=host;host.hidden=true;
  host.innerHTML=`<h3>GCTS · learn markings</h3><p class="marking-progress" role="status"></p>
   <div class="marking-pair-controls" hidden>
    <label>Inspect pair <select class="marking-pair" aria-label="Inspect pair"></select></label>
    <button type="button" class="marking-previous" aria-label="Previous pair">←</button>
    <button type="button" class="marking-next" aria-label="Next pair">→</button>
    <label class="marking-witness-label"><input type="checkbox" class="marking-witness" checked> Show corona witness</label>
   </div>
   <p class="marking-pair-detail" role="status" hidden></p>
   <label>Marking orientation <select class="marking-orientation" aria-label="Marking orientation"></select></label>
   <canvas width="800" height="300" aria-label="Pair corona and learned point marking"></canvas>
   <p class="marking-detail"></p>`;
  if(compact){
   host.classList.add('marking-corner');host.querySelector('h3').textContent='Point marking';
   const details=document.createElement('details');details.className='marking-inspection';details.innerHTML='<summary>Samples & scores</summary>';
   for(const selector of ['.marking-progress','.marking-pair-controls','.marking-pair-detail','.marking-detail'])details.append(host.querySelector(selector));
   this.meta=document.createElement('p');this.meta.className='marking-meta';host.append(this.meta,details);
   host.querySelector('canvas').width=400;host.querySelector('canvas').setAttribute('aria-label','Evolving point marking');
  }
  this.canvas=host.querySelector('canvas');this.ctx=this.canvas.getContext('2d');
  this.status=host.querySelector('.marking-progress');this.detail=host.querySelector('.marking-detail');
  this.select=host.querySelector('.marking-orientation');this.select.onchange=()=>this.draw();
  this.pairControls=host.querySelector('.marking-pair-controls');this.pairSelect=host.querySelector('.marking-pair');
  this.pairDetail=host.querySelector('.marking-pair-detail');this.witness=host.querySelector('.marking-witness');
  this.previous=host.querySelector('.marking-previous');this.next=host.querySelector('.marking-next');
  this.pairSelect.onchange=()=>this.selectPair();this.witness.onchange=()=>this.selectPair();
  for(const [button,step] of [[this.previous,-1],[this.next,1]])button.onclick=()=>{this.pairSelect.selectedIndex+=step;this.selectPair();};
  this.model=null;this.snapshot=null;this.placements=[];this.pair=[];this.evidence=[];this.hits=[];this.hover=null;this.changed=new Set();
  this.canvas.style.cssText='width:100%;height:auto;background:#fafbf7;border-radius:8px;';
  this.canvas.onmousemove=e=>{const r=this.canvas.getBoundingClientRect();this.hover={x:(e.clientX-r.left)*this.canvas.width/r.width,y:(e.clientY-r.top)*300/r.height};this.draw();};
  this.canvas.onmouseleave=()=>{this.hover=null;this.draw();};
 }
 reset(model) {
  this.model=model;this.domainExtent=1;this.domains=markingDomain(model,1);this.snapshot=null;
  this.placements=[];this.pair=[];this.evidence=[];this.lastEvent=null;this.deadPoint=null;this.row=null;this.inspection=null;this.hover=null;this.changed.clear();
  this.pairSelect.replaceChildren();this.pairControls.hidden=true;this.pairDetail.hidden=true;this.witness.checked=true;
  this.select.replaceChildren(...model.orientations.map((o,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`Tile ${(o.type??0)+1} · orientation ${o.index??i}`;return option;}));
  this.host.hidden=false;this.status.textContent='Enumerating neighboring pairs…';
  if(this.meta)this.meta.textContent='Awaiting labels';
  this.detail.textContent='Unmarked one-corona checks; provisional values are not used to label samples.';this.draw();
 }
 selectPair(notify=true) {
  const index=this.pairSelect.selectedIndex,row=this.evidence[index];if(!row)return;
  this.row=row;this.pair=row.pair;this.deadPoint=null;
  this.witness.disabled=row.status!=='valid';
  this.placements=this.witness.checked&&row.status==='valid'?row.placements:row.pair;
  this.previous.disabled=index===0;this.next.disabled=index===this.evidence.length-1;
  this.select.value=row.pair[1].oi;
  this.updatePairDetail();this.draw();if(notify)this.onInspect({model:this.model,placements:this.placements,pair:this.pair,row:this.row,inspection:this.inspection});
 }
 updatePairDetail() {
  this.inspection=this.snapshot?.fields&&this.pair.length===2?inspectPairMarking(this.snapshot.fields,this.pair):null;
  this.pairDetail.hidden=!this.row||!this.inspection;
  if(!this.pairDetail.hidden)this.pairDetail.textContent=pairInspectionText(this.row,this.inspection);
 }
 accept(event) {
  if(!this.model||this.lastEvent===event)return;this.lastEvent=event;
  if(event.type==='marking-learned') {
   this.snapshot=event.marking;this.changed.clear();this.deadPoint=null;
   this.status.textContent=event.marking.accepted?`${event.marking.saved?.persisted?'Saved':'Validated this visit'} · ${event.marking.saved?.name??'marking'} · ${event.marking.totalPairs??event.marking.evidence?.length??0} pairs`:`Marking not activated · ${event.marking.reason}`;
   this.evidence=event.marking.evidence??[];
   this.pairSelect.replaceChildren(...this.evidence.map((row,i)=>{
    const option=document.createElement('option');option.value=i;
    const compatible=inspectPairMarking(event.marking.fields??[],row.pair).compatible;
    option.textContent=`${i+1} · ${row.status} · marking ${compatible?'accepts':'rejects'}`;return option;
   }));
   this.pairControls.hidden=!this.evidence.length;
   if(this.evidence.length)this.selectPair(false);
  } else {
   this.pairControls.hidden=true;this.row=event.phase==='update'?event:null;
   this.placements=event.placements??this.placements;
   this.pair=event.pair??this.placements.slice(0,2);
   this.deadPoint=event.action==='dead'?event.point:null;
   if(event.snapshot&&event.snapshot!==this.snapshot) {
    const before=new Map((this.snapshot?.fields??[]).flatMap((f,oi)=>f.map(m=>[`${oi}:${m.pos}|${m.component}`,m.value])));
    const after=new Map(event.snapshot.fields.flatMap((f,oi)=>f.map(m=>[`${oi}:${m.pos}|${m.component}`,m.value])));
    this.changed=new Set([...new Set([...before.keys(),...after.keys()])].filter(k=>before.get(k)!==after.get(k)));this.snapshot=event.snapshot;
   }
   const c=event.counts??{};
   const action=event.phase==='resume'?`continuing · ${event.retained} resolved labels retained · ${event.pairNodes} attempts per pair`
    :event.phase==='replay'?'checking saved pair evidence':event.phase==='pair'?'trying the next pair'
    :event.phase==='refine'?'refining free values':event.phase==='update'?event.status:event.action??'filling the 1-corona';
   this.status.textContent=`${event.totalPairs??event.pairs??0} pairs · ${c.valid??0} valid · ${c.invalid??0} invalid · ${c.unresolved??0} unresolved · ${action}`;
  }
  const s=this.snapshot;
  if(s&&s.extent!==this.domainExtent){this.domainExtent=s.extent;this.domains=markingDomain(this.model,s.extent);}
  this.detail.textContent=s?`${s.accepted?'Validated':'Provisional'} · accepts ${s.positivePassed??0}/${s.counts?.valid??0} valid · blocks ${s.negativeBlocked??0}/${s.counts?.invalid??0} invalid · ${s.points??0} points / ${s.values??0} values across orientations · ${s.componentCount??1} component${s.componentCount>1?'s':''}. Pair marks: blue rings agree, red rings conflict. Hover for values; * is free. Orange: changed values.`:'Awaiting the first label.';
  if(this.meta)this.meta.textContent=s?`${s.accepted?'Validated':'Provisional'} · ${s.points??0} points · ${s.values??0} values`:'Awaiting labels';
  this.updatePairDetail();this.draw();
 }
 project(p){return [(p[0]-p[2])*.8,p[1]*.8-(p[0]+p[2])*.35];}
 map(points,x,width) {
  const qs=(points.length?points:[[0,0,0]]).map(p=>this.project(p)),xs=qs.map(p=>p[0]),ys=qs.map(p=>p[1]);
  const min=[Math.min(...xs),Math.min(...ys)],max=[Math.max(...xs),Math.max(...ys)],scale=Math.min((width-35)/Math.max(1,max[0]-min[0]),220/Math.max(1,max[1]-min[1]));
  return p=>{const q=this.project(p);return[x+width/2+(q[0]-(min[0]+max[0])/2)*scale,155-(q[1]-(min[1]+max[1])/2)*scale];};
 }
 geometry(o,t,map,core) {
  const ctx=this.ctx;for(const face of o.faces??[]) {
   ctx.beginPath();face.forEach((j,i)=>{const p=map(o.vertices[j].map((v,k)=>v+t[k]));i?ctx.lineTo(...p):ctx.moveTo(...p);});
   ctx.closePath();ctx.fillStyle=core?'#8bbfc13b':'#b5c9b52d';ctx.fill();ctx.strokeStyle=core?'#527d83':'#b6c5bb';ctx.lineWidth=core?1.3:.7;ctx.stroke();
  }
 }
 draw() {
  if(!this.model)return;const ctx=this.ctx;
  ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,800,300);ctx.fillStyle='#294d43';ctx.font='15px system-ui';
  if(!this.compact){
  ctx.fillText(this.row?this.row.status==='valid'&&this.witness.checked?'Pair & unmarked corona witness':'Neighboring pair':'Pair & one-corona attempt',14,22);
  ctx.fillText(this.snapshot?.accepted?'Learned marking':'Evolving marking',420,22);this.hits=[];
  const placements=this.placements.length?this.placements:[{oi:0,translation:[0,0,0]}];
  const pairPoints=this.inspection?.points??[];
  const world=placements.flatMap(p=>this.model.orientations[p.oi].cells.map(c=>c.pos.map((v,i)=>v+p.translation[i])));
  const left=this.map([...world,...pairPoints.map(p=>p.pos)],0,390);
  placements.forEach((p,i)=>this.geometry(this.model.orientations[p.oi],p.translation,left,i<2));
  const totals=new Map();for(const p of placements)for(const c of this.model.orientations[p.oi].cells){const pos=c.pos.map((v,i)=>v+p.translation[i]),key=pos.join();totals.set(key,(totals.get(key)??0)+c.weight);}
  for(const [key,n] of totals){ctx.beginPath();ctx.arc(...left(key.split(',').map(Number)),2.5,0,2*Math.PI);ctx.fillStyle=n===this.model.capacity?'#2d8b70':'#dfa22c';ctx.fill();}
  // Only the two classified tiles receive markings. The extra corona tiles
  // witness unmarked extension; the learned field need not accept that patch.
  for(const p of [...pairPoints].sort((a,b)=>Number(a.conflict)-Number(b.conflict))) {
   const [x,y]=left(p.pos),value=p.assignments[0].value;
   ctx.beginPath();ctx.arc(x,y,p.overlap?5:2.7,0,2*Math.PI);
   ctx.strokeStyle=p.conflict?'#b5403d':'#327eae';ctx.lineWidth=p.conflict?2.5:1.5;
   if(p.overlap)ctx.stroke();else{ctx.fillStyle=`hsl(${value*137.5%360} 60% 40%)`;ctx.fill();}
   if(p.conflict){ctx.beginPath();ctx.moveTo(x-3,y-3);ctx.lineTo(x+3,y+3);ctx.moveTo(x-3,y+3);ctx.lineTo(x+3,y-3);ctx.stroke();}
   this.hits.push({x,y,pos:p.pos,side:'pair',conflict:p.conflict,text:`(${p.pos}) m[${p.component}]: ${p.assignments.map(a=>`tile ${a.tile+1} = ${a.value}`).join('; ')}`});
  }
  if(this.deadPoint){ctx.beginPath();ctx.arc(...left(this.deadPoint),8,0,2*Math.PI);ctx.strokeStyle='#b5403d';ctx.lineWidth=2;ctx.stroke();}
  if(pairPoints.length){ctx.fillStyle='#486656';ctx.font='11px system-ui';ctx.fillText('Markings shown on the two seed tiles only',14,290);}
  }
  this.hits=this.compact?[]:this.hits;
  const oi=+this.select.value,o=this.model.orientations[oi],domain=this.domains[oi];
  const right=this.map(domain.map(m=>m.pos),this.compact?10:410,this.compact?380:375),componentCount=this.snapshot?.componentCount??1,field=markingVectors(this.snapshot?.fields?.[oi]??[],componentCount);
  this.geometry(o,[0,0,0],right,true);
  for(const m of domain){const [x,y]=right(m.pos),values=field.get(m.pos.join())??Array(componentCount).fill('*'),value=values.find(v=>v!=='*')??'*',changed=values.some((_,c)=>this.changed.has(`${oi}:${m.pos}|${c}`));ctx.beginPath();ctx.arc(x,y,changed?5:value==='*'?2:3.5,0,2*Math.PI);ctx.fillStyle=changed?'#e39931':value==='*'?'#9cafaa':`hsl(${value*137.5%360} 60% 40%)`;ctx.fill();this.hits.push({x,y,pos:m.pos,value,values,side:'marking',text:`(${m.pos})  m=(${values.join(', ')})`});}
  if(!this.compact){ctx.strokeStyle='#d5e1d9';ctx.beginPath();ctx.moveTo(400,35);ctx.lineTo(400,286);ctx.stroke();}
  if(this.hover) {
   const hit=this.hits.filter(h=>Math.hypot(h.x-this.hover.x,h.y-this.hover.y)<9).sort((a,b)=>Number(b.conflict??false)-Number(a.conflict??false)||Math.hypot(a.x-this.hover.x,a.y-this.hover.y)-Math.hypot(b.x-this.hover.x,b.y-this.hover.y))[0];
   if(hit){ctx.font='12px system-ui';const width=ctx.measureText(hit.text).width+14,x=Math.max(2,Math.min(hit.x+8,this.canvas.width-2-width)),y=Math.max(52,Math.min(hit.y-8,275));ctx.fillStyle='#fffdf1';ctx.fillRect(x,y-18,width,24);ctx.strokeStyle=hit.conflict?'#b5403d':'#6a887b';ctx.strokeRect(x,y-18,width,24);ctx.fillStyle='#294d43';ctx.fillText(hit.text,x+7,y);}
  }
 }
}
