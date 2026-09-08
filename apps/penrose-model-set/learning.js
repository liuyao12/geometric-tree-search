import {TILE_KINDS,TILE_PRESETS} from '../../assets/penrose-selection-problem.js?v=20260908-sets';
import {createLaneRunner,LANE_IDS} from './lanes.js?v=20260908-sets';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js?v=20260908-sets';
import {extendedBars} from '../../assets/penrose-mixed-markings.js';
import {embedding,cycloAdd,latticeKey} from '../../assets/cyclotomic-five.js';
import {activityText} from './search-status.js';
const $=id=>document.getElementById(id),canvas=$('learningCanvas'),ctx=canvas.getContext('2d');
let state,view=null,hits=[],selected='learned',tileKinds=[...TILE_PRESETS.P3],latest,runner,drawPending=false;
const known=knownPenroseBenchmark({}),names={learned:'Learned points',plain:'Local matching',known:'Ammann bars'};
const coordinate=p=>{const terms=p.coeff.map((v,i)=>v?`${v}${i?`ζ${i===1?'':`^${i}`}`:''}`:null).filter(Boolean);return `(${terms.join(' + ').replaceAll('+ -','− ')||'0'})${p.denominator===1?'':`/${p.denominator}`}`;};
const keyCoordinate=key=>{if(!key)return'?';const [s,d]=key.split('/');return coordinate({coeff:s.split(',').map(Number),denominator:Number(d)});};
const count=n=>(n||0).toLocaleString();
function queueDraw(){if(drawPending)return;drawPending=true;requestAnimationFrame(()=>{drawPending=false;draw();});}
function render(update){latest=update;const {lanes,running,target}=update;
 const complete=LANE_IDS.every(id=>lanes[id]?.state?.done||lanes[id]?.state?.pausedCorona===target);
 $('runLearning').textContent=running?'Pause all':complete?'Continue all':'Run all';
 $('runLearning').disabled=!tileKinds.length||LANE_IDS.every(id=>lanes[id]?.state?.done);$('stepLearning').disabled=!tileKinds.length;
 for(const id of LANE_IDS){const s=lanes[id]?.state,card=$('lane_'+id);card.setAttribute('aria-pressed',String(id===selected));
  $('laneStatus_'+id).textContent=s?.error?'Error':!s?'Initializing':s.pausedCorona?`Paused at corona ${s.pausedCorona}`:s.done?s.status:`Corona ${s.minimumFrontierGeneration??'closed'} · ${count(s.tiles.length)} tiles`;
  $('laneMemory_'+id).textContent=s?.learning?`${count(s.learning.addresses)} marking points · ${count(s.learning.entries)} values`:id==='known'?'Continuous bar geometry':'No marking table';
 }
 const next=lanes[selected]?.state;if(state!==next){state=next;view=null;$('pointInfo').textContent='';queueDraw();}
 $('modeInfo').textContent=selected==='learned'?'Starts empty. Learns point constraints from certified impossible pairs.':selected==='plain'?'Geometry, corner capacity, and the selected tiles’ local matching rule.':'Continuous Ammann checks at extent 2, in addition to the base rules.';
 if(!state||state.error){$('learningStatus').textContent=state?.error||'Initializing';$('learningStats').textContent='';$('memoryCost').textContent='';$('coronaStatus').textContent='';return;}
 const activity=activityText(state.activity,keyCoordinate);
 $('learningStatus').textContent=state.pausedCorona?`Pausing at corona ${state.pausedCorona} · ${activity}`:state.done?state.status:!running?`Paused · ${activity}`:activity;
 $('coronaStatus').textContent=`${names[selected]} · corona ${state.minimumFrontierGeneration??'closed'}`;
 $('learningStats').textContent=`${count(state.tiles.length)} tiles · ${count(state.stats.proposals)} proposals · ${count(state.stats.backtracks)} backtracks · ${(state.computeMs/1000).toFixed(2)} s worker time`;
 const m=state.learning,mem=state.memory,g=state.graph;
 const lines=m?[`Template marking: ${count(m.addresses)} points · ${count(m.entries)} defined values`, `Active marking: ${count(mem.activeMarking.points)} points · ${count(mem.activeMarking.values)} defined values`]:selected==='known'?[`Continuous bars: ${count(mem.bars.points)} distinct endpoints · ${count(mem.bars.segments)} segments`,`${count(mem.bars.endpointReferences)} endpoint references · ${count(mem.bars.familyValues)} family labels; no discrete point-value table`]:['Marking: 0 points · 0 values'];
 lines.push(`Active t field: ${count(mem.tPoints)} points · ${count(mem.tValues)} values`,`Search graph: ${count(g.points)} frontier points · ${count(g.retainedCandidates)} candidate records · ${count(g.incidences)} legal links`);
 if(m)lines.push(`Learning: ${count(m.rules)} certificates · ${count(m.proofSource?.cachedMasks)} cached masks · ${count(m.localTeacher?.cached)} cached local checks`);
 $('memoryCost').textContent=lines.join('\n');
}
function pointData(){const points=new Map(),tables=new Map((state.learning?.tables||[]).map(t=>[t.type,t.rows]));
 const get=p=>{const key=latticeKey(p);if(!points.has(key))points.set(key,{point:p,total:0,values:new Map(),marked:false});return points.get(key);};
 for(const tile of state.tiles){tile.exactPoints.forEach((p,i)=>get(p).total+=tile.weights[i]);if($('showPoints').checked)for(const r of tables.get(tile.type)||[]){const p=get(cycloAdd(tile.origin,r.offset));p.marked=true;const old=p.values.get(r.channel);p.values.set(r.channel,old!==undefined&&old!==r.value?'conflict':r.value);}}
 return [...points.values()];}
function draw(){const bounds=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1;canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,bounds.width,bounds.height);if(!state?.tiles?.length){hits=[];return;}
 const points=pointData(),all=points.map(p=>embedding(p.point));if(!view){const xs=all.map(p=>p.x),ys=all.map(p=>p.y),loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);view={x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min((bounds.width-70)/Math.max(1,hiX-loX),(bounds.height-70)/Math.max(1,hiY-loY))};}
 const screen=p=>({x:bounds.width/2+(p.x-view.x)*view.scale,y:bounds.height/2-(p.y-view.y)*view.scale});
 for(const tile of state.tiles){const loop=tile.exactPoints.map(p=>screen(embedding(p)));ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=({thick:'#b7d8c8',thin:'#ecc888',kite:'#b8dce8',dart:'#e8b5c4',p5:'#c8c2e5',p3:'#ddcae9',p2:'#e8bad5',diamond:'#efcf92',boat:'#9fcdb5',star:'#e6b194'})[tile.kind];ctx.fill();ctx.strokeStyle='#3f5653';ctx.lineWidth=1;ctx.stroke();}
 if(selected==='known'&&$('showPoints').checked)for(const tile of state.tiles)for(const bar of extendedBars(known.decorate(tile),2)){const a=screen(embedding(bar.from)),b=screen(embedding(bar.to));ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle='#733bd266';ctx.lineWidth=1;ctx.stroke();}
 hits=points.map(p=>({...p,...screen(embedding(p.point))}));for(const p of hits){ctx.beginPath();ctx.arc(p.x,p.y,p.marked?3:1.5,0,Math.PI*2);ctx.fillStyle=p.marked?'#733bd2':'#51645d';ctx.fill();}}
runner=createLaneRunner({makeWorker:()=>new Worker(new URL('./learning-worker.js?v=20260908-sets',import.meta.url),{type:'module'}),notify:render,options:()=>({tileKinds:[...tileKinds]})});
$('runLearning').onclick=()=>runner.toggle();$('stepLearning').onclick=()=>runner.step();$('resetLearning').onclick=()=>resetSelection();
for(const id of LANE_IDS)$('lane_'+id).onclick=()=>{selected=id;render(latest);};
$('fitLearning').onclick=()=>{view=null;queueDraw();};$('showPoints').onchange=queueDraw;
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const p=hits.reduce((best,p)=>Math.hypot(p.x-x,p.y-y)<Math.min(9,best?Math.hypot(best.x-x,best.y-y):Infinity)?p:best,null);$('pointInfo').textContent=p?`${coordinate(p.point)}\n t = ${p.total}/10; m = ${p.values.size?[...p.values].sort((a,b)=>a[0]-b[0]).map(([c,v])=>`${c}:${v}`).join(', '):'undefined'}${p.values.size?' (unlisted channels undefined)':''}`:'';};
function resetSelection(){
 tileKinds=TILE_KINDS.filter(k=>$('tile_'+k).checked);
 const preset=Object.entries(TILE_PRESETS).find(([,ks])=>ks.length===tileKinds.length&&ks.every(k=>tileKinds.includes(k)));$('tileSet').value=preset?.[0]||'custom';
 const p3=tileKinds.length&&tileKinds.every(k=>['thick','thin'].includes(k));
 $('lane_plain').querySelector('strong').textContent=p3?'Edge arrows':'Local matching';names.plain=p3?'Edge arrows':'Local matching';
 $('selectionInfo').textContent=p3?'All lanes enforce the same independent Penrose edge arrows.':'All lanes enforce the same supplied boundary-port matching rules.';
 const mixed=new Set(tileKinds.map(k=>TILE_PRESETS.P3.includes(k)?'P3':TILE_PRESETS.P2.includes(k)?'P2':'P1')).size>1;
 $('tileHint').textContent=!tileKinds.length?'Choose at least one tile.':mixed?'Experimental mix. Selected tiles are allowed, not required. P1 cannot share whole edges with P2/P3 at this scale.':'Selected tiles are allowed, not required.';
 runner.reset();
}
$('tileSet').onchange=()=>{const ks=TILE_PRESETS[$('tileSet').value];if(!ks)return;for(const k of TILE_KINDS)$('tile_'+k).checked=ks.includes(k);resetSelection();};
for(const k of TILE_KINDS)$('tile_'+k).onchange=resetSelection;
new ResizeObserver(queueDraw).observe(canvas);resetSelection();
