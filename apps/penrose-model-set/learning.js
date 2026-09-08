import {createDisplayCache} from './learning-display.js?v=20260908-speed';
import {TILE_KINDS,TILE_PRESETS} from '../../assets/penrose-selection-problem.js?v=20260908-speed';
import {createLaneRunner,LANE_IDS} from './lanes.js?v=20260908-speed';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js?v=20260908-speed';
import {embedding,cycloAdd,latticeKey} from '../../assets/cyclotomic-five.js?v=20260908-speed';
import {activityText} from './search-status.js?v=20260908-speed';
const $=id=>document.getElementById(id),canvas=$('learningCanvas'),ctx=canvas.getContext('2d');
let state,view=null,hits=[],selected='learned',tileKinds=[...TILE_PRESETS.P3],latest,runner,drawPending=false;
const known=knownPenroseBenchmark({});let displays={};const names={learned:'Learned points',plain:'Local matching',known:'Ammann bars'};
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
 if(mem.pairCaches?.length)lines.push(`Geometry/matching cache: ${count(mem.pairCaches.reduce((n,c)=>n+c.entries,0))} pair results (bounded)`);
 if(m)lines.push(`Learning: ${count(m.rules)} certificates · ${count(m.proofSource?.cachedMasks)} cached masks · ${count(m.localTeacher?.cached)} cached local checks`);
 $('memoryCost').textContent=lines.join('\n');
}
function draw(){const bounds=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1;canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,bounds.width,bounds.height);if(!state?.tiles?.length){hits=[];return;}
 const display=displays[selected]||(displays[selected]=createDisplayCache()),showBars=selected==='known'&&$('showPoints').checked;
 const input=showBars?state.tiles.map(t=>t.bars?t:known.decorate(t)):state.tiles;
 const frame=display.frame(input,state.learning?.tables,$('showPoints').checked,showBars),points=frame.points,all=points.map(p=>p.xy);if(!view){const xs=all.map(p=>p.x),ys=all.map(p=>p.y),loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);view={x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min((bounds.width-70)/Math.max(1,hiX-loX),(bounds.height-70)/Math.max(1,hiY-loY))};}
 const screen=p=>({x:bounds.width/2+(p.x-view.x)*view.scale,y:bounds.height/2-(p.y-view.y)*view.scale});
 for(const tile of frame.tiles){const loop=tile.loop.map(screen);ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=({thick:'#b7d8c8',thin:'#ecc888',kite:'#b8dce8',dart:'#e8b5c4',p5:'#c8c2e5',p3:'#ddcae9',p2:'#e8bad5',diamond:'#efcf92',boat:'#9fcdb5',star:'#e6b194'})[tile.kind];ctx.fill();ctx.strokeStyle='#3f5653';ctx.lineWidth=1;ctx.stroke();}
 if(showBars)for(const tile of frame.tiles)for(const bar of tile.bars){const a=screen(bar.from),b=screen(bar.to);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle='#733bd266';ctx.lineWidth=1;ctx.stroke();}
 hits=points.map(p=>({...p,...screen(p.xy)}));for(const p of hits){ctx.beginPath();ctx.arc(p.x,p.y,p.marked?3:1.5,0,Math.PI*2);ctx.fillStyle=p.marked?'#733bd2':'#51645d';ctx.fill();}}
runner=createLaneRunner({makeWorker:()=>new Worker(new URL('./learning-worker.js?v=20260908-speed',import.meta.url),{type:'module'}),notify:render,options:()=>({tileKinds:[...tileKinds],compact:true})});
$('runLearning').onclick=()=>runner.toggle();$('stepLearning').onclick=()=>runner.step();$('resetLearning').onclick=()=>resetSelection();
for(const id of LANE_IDS)$('lane_'+id).onclick=()=>{selected=id;render(latest);};
$('fitLearning').onclick=()=>{view=null;queueDraw();};$('showPoints').onchange=queueDraw;
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const p=hits.reduce((best,p)=>Math.hypot(p.x-x,p.y-y)<Math.min(9,best?Math.hypot(best.x-x,best.y-y):Infinity)?p:best,null);$('pointInfo').textContent=p?`${coordinate(p.point)}\n t = ${p.total}/10; m = ${p.values.size?[...p.values].sort((a,b)=>a[0]-b[0]).map(([c,v])=>`${c}:${v}`).join(', '):'undefined'}${p.values.size?' (unlisted channels undefined)':''}`:'';};
function resetSelection(){
 displays={};
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
