import {circularArcs,drawCircularArcs} from '../../assets/penrose-circular-arcs.js?v=20260928-arcs';
import {createDisplayCache} from './learning-display.js?v=20260908-lines';
import {TILE_KINDS,TILE_PRESETS} from '../../assets/penrose-selection-problem.js?v=20260928-space';
import {createLaneRunner,LANE_IDS} from './lanes.js?v=20260908-solo';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js?v=20260908-lines';
import {activityText} from './search-status.js?v=20260908-speed';
const $=id=>document.getElementById(id),canvas=$('learningCanvas'),ctx=canvas.getContext('2d');
let state,view=null,hits=[],selected='learned',tileKinds=[...TILE_PRESETS.P3],latest,runner,drawPending=false;
const known=knownPenroseBenchmark({});let displays={};const names={learned:'Marking space',plain:'Local matching',known:'Ammann bars'};
const count=n=>(n||0).toLocaleString();
function queueDraw(){if(drawPending)return;drawPending=true;requestAnimationFrame(()=>{drawPending=false;draw();});}
function render(update){latest=update;const {lanes,running,target}=update;
 const lane=lanes[selected],complete=lane?.state?.pausedCorona===target;
 $('runLearning').textContent=running?'Pause':complete||lane?.state?.stats?.proposals?'Continue':'Run';
 $('runLearning').disabled=!tileKinds.length||lane?.state?.done;$('stepLearning').disabled=!tileKinds.length;
 for(const id of LANE_IDS){const s=lanes[id]?.state,card=$('lane_'+id);card.setAttribute('aria-pressed',String(id===selected));
  $('laneStatus_'+id).textContent=s?.error?'Error':!s?(lanes[id]?.worker?'Initializing':'Ready'):s.pausedCorona?`Paused at corona ${s.pausedCorona}`:s.done?s.status:`Corona ${s.minimumFrontierGeneration??'closed'} · ${count(s.tiles.length)} tiles`;
  $('laneMemory_'+id).textContent=s?.learning?`${count(s.learning.dimension)} / ${count(s.learning.variables)} free values`:id==='known'?'Infinite line geometry':'No marking table';
 }
 const next=lanes[selected]?.state;if(state!==next){state=next;view=null;hovered=null;clearTimeout(hoverTimer);window.MathJax?.typesetClear?.([$('pointInfo')]);$('pointInfo').textContent='';queueDraw();}
 $('modeInfo').textContent=selected==='learned'?'Starts with independent symbolic values. Tile contacts cut down the marking space; backtracking restores it.':selected==='plain'?($('boundaryRule')?.value==='none'?'Bare tile geometry and corner capacity.':'Geometry, corner capacity, and the supplied boundary rule.'):'Infinite Ammann lines enforce matching directly.';
 if(!state||state.error){if($('spaceSummary'))$('spaceSummary').hidden=true;$('learningStatus').textContent=state?.error||'Initializing';$('learningStats').textContent='';$('memoryCost').textContent='';$('coronaStatus').textContent='';return;}
 const activity=activityText(state.activity,()=> 'frontier point').replace(' at [frontier point]',' at the frontier');
 $('learningStatus').textContent=state.pausedCorona?`Pausing at corona ${state.pausedCorona} · ${activity}`:state.done?state.status:!running?`Paused · ${activity}`:activity;
 $('coronaStatus').textContent=`${names[selected]} · corona ${state.minimumFrontierGeneration??'closed'}`;
 $('learningStats').textContent=`${count(state.tiles.length)} tiles · ${count(state.stats.proposals)} proposals · ${count(state.stats.backtracks)} backtracks`;
 const m=state.learning,mem=state.memory,g=state.graph;
 if($('spaceSummary')){$('spaceSummary').hidden=!m;if(m){$('spaceDimension').textContent=count(m.dimension);$('spaceInitial').textContent=count(m.variables);$('spaceRank').textContent=count(m.rank);$('spaceContacts').textContent=count(m.contacts);$('spaceProgress').max=m.variables;$('spaceProgress').value=m.dimension;}}
 const lines=m?[`Marking space: ${count(m.dimension)} dimensions remaining of ${count(m.variables)}`, `Independent equalities: ${count(m.rank)} · contact equations: ${count(m.contacts)}`, `Template support: ${count(m.addresses)} points across all rigid orientations`, `Active marking: ${count(mem.activeMarking.points)} points · ${count(mem.activeMarking.values)} defined values`]:selected==='known'?[`Infinite lines: ${count(mem.bars.segments)} tile-line records`,`${count(mem.bars.endpointReferences)} defining-point references · ${count(mem.bars.familyValues)} family labels; no discrete point-value table`]:['Marking: 0 points · 0 values'];
 lines.push(`Active t field: ${count(mem.tPoints)} points · ${count(mem.tValues)} values`,`Search graph: ${count(g.points)} frontier points · ${count(g.retainedCandidates)} candidate records · ${count(g.incidences)} legal links`);
 if(mem.pairCaches?.length)lines.push(`Geometry/matching cache: ${count(mem.pairCaches.reduce((n,c)=>n+c.entries,0))} pair results (bounded)`);
 if(m)lines.push(`Rotations/reflections: ${count(m.symmetryOrder)} actions · vertex and edge-midpoint support`, 'Patch-compatible space; provisional values do not prune the search.');
 $('memoryCost').textContent=lines.join('\n');
}
function draw(){const bounds=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1;canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,bounds.width,bounds.height);if(!state?.tiles?.length){hits=[];return;}
 const display=displays[selected]||(displays[selected]=createDisplayCache()),showBars=selected==='known'&&$('showPoints').checked;
 const input=showBars?state.tiles.map(t=>t.bars?t:known.decorate(t)):state.tiles;
 const frame=display.frame(input,state.learning?.tables,$('showPoints').checked,showBars),points=frame.points,all=points.map(p=>p.xy);if(!view){const xs=all.map(p=>p.x),ys=all.map(p=>p.y),loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);view={x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min((bounds.width-70)/Math.max(1,hiX-loX),(bounds.height-70)/Math.max(1,hiY-loY))};}
 const screen=p=>({x:bounds.width/2+(p.x-view.x)*view.scale,y:bounds.height/2-(p.y-view.y)*view.scale});
 for(const tile of frame.tiles){const loop=tile.loop.map(screen);ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=({thick:'#b7d8c8',thin:'#ecc888',kite:'#b8dce8',dart:'#e8b5c4',p5:'#c8c2e5',p3:'#ddcae9',p2:'#e8bad5',diamond:'#efcf92',boat:'#9fcdb5',star:'#e6b194'})[tile.kind];ctx.fill();ctx.strokeStyle='#3f5653';ctx.lineWidth=1;ctx.stroke();}
 if($('showCircularArcs')?.checked)for(const tile of frame.tiles)drawCircularArcs(ctx,circularArcs(tile.kind,tile.loop),screen,view.scale,Math.min(3,Math.max(1.4,view.scale*.025)));
 if(showBars)for(const tile of frame.tiles)for(const bar of tile.bars){const a=screen(bar.from),b=screen(bar.to),dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy);if(!len)continue;const reach=2*(Math.hypot(bounds.width,bounds.height)+Math.hypot(a.x,a.y)),ux=dx/len*reach,uy=dy/len*reach;ctx.beginPath();ctx.moveTo(a.x-ux,a.y-uy);ctx.lineTo(a.x+ux,a.y+uy);ctx.strokeStyle='#733bd266';ctx.lineWidth=1;ctx.stroke();}
 hits=points.map(p=>({...p,...screen(p.xy)}));for(const p of hits){ctx.beginPath();ctx.arc(p.x,p.y,p.marked?3:1.5,0,Math.PI*2);const symbol=p.values.get(0);ctx.fillStyle=p.marked&&/^u\d+$/.test(symbol)?`hsl(${Number(symbol.slice(1))*137.508%360} 65% 32%)`:p.marked?'#733bd2':'#51645d';ctx.fill();}}
runner=createLaneRunner({makeWorker:()=>new Worker(new URL('./learning-worker.js?v=20260928-space',import.meta.url),{type:'module'}),notify:render,options:()=>({tileKinds:[...tileKinds],compact:true,boundaryRule:$('boundaryRule')?.value||'supplied'})});
$('runLearning').onclick=()=>runner.toggle();$('stepLearning').onclick=()=>runner.step();$('resetLearning').onclick=()=>{delete displays[selected];runner.resetCurrent();};
for(const id of LANE_IDS)$('lane_'+id).onclick=()=>{selected=id;runner.select(id);render(latest);};
$('fitLearning').onclick=()=>{view=null;queueDraw();};$('showPoints').onchange=queueDraw;
if($('showCircularArcs'))$('showCircularArcs').onchange=queueDraw;
const latexCoordinate=p=>{const terms=p.coeff.map((v,i)=>v?`${v}${i?`\\zeta_5${i===1?'':`^{${i}}`}`:''}`:null).filter(Boolean).join(' + ').replaceAll('+ -','- ')||'0';return p.denominator===1?terms:`\\frac{${terms}}{${p.denominator}}`;};
let hovered=null,hoverTimer;
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const p=hits.reduce((best,p)=>Math.hypot(p.x-x,p.y-y)<Math.min(9,best?Math.hypot(best.x-x,best.y-y):Infinity)?p:best,null);
 const content=p?`\\(p=${latexCoordinate(p.point)},\\quad t=\\frac{${p.total}}{10}\\)`+(p.values.size?'\n'+[...p.values].sort((a,b)=>a[0]-b[0]).map(([c,v])=>/^u\d+$/.test(v)?`\\(m(p)=u_{${v.slice(1)}}\\)`:`Channel ${c}: ${v}`).join(', ')+'\nIndependent symbols may take arbitrary values; equal symbols must agree.':'\nMarking unassigned.'):'';
 if(hovered===content)return;hovered=content;clearTimeout(hoverTimer);hoverTimer=setTimeout(()=>{const info=$('pointInfo');window.MathJax?.typesetClear?.([info]);info.textContent=content;if(content)window.MathJax?.typesetPromise?.([info]);},80);
};
canvas.onclick=canvas.onpointermove;
function resetSelection(){
 displays={};
 tileKinds=TILE_KINDS.filter(k=>$('tile_'+k).checked);
 const preset=Object.entries(TILE_PRESETS).find(([,ks])=>ks.length===tileKinds.length&&ks.every(k=>tileKinds.includes(k)));$('tileSet').value=preset?.[0]||'custom';
 const hasP2=tileKinds.some(k=>k==='kite'||k==='dart');
 if($('showCircularArcs')){$('showCircularArcs').disabled=!hasP2;$('circularArcHint').textContent=hasP2?'Two-colour arcs on kite and dart tiles. Illustration only; the search uses its existing rules.':'Choose P2 · kite & dart to see arcs on the tiling. Illustration only.';}
 const bare=$('boundaryRule')?.value==='none';
 const p3=tileKinds.length&&tileKinds.every(k=>['thick','thin'].includes(k));
 $('lane_plain').querySelector('strong').textContent=bare?'Bare geometry':p3?'Edge arrows':'Local matching';names.plain=bare?'Bare geometry':p3?'Edge arrows':'Local matching';
 $('selectionInfo').textContent=bare?'Marking space and geometry use bare tiles. Ammann lines remain a separate known-rule control.':p3?'Marking space and local matching use supplied edge arrows.':'Marking space and local matching use supplied boundary ports.';
 const mixed=new Set(tileKinds.map(k=>TILE_PRESETS.P3.includes(k)?'P3':TILE_PRESETS.P2.includes(k)?'P2':'P1')).size>1;
 $('tileHint').textContent=!tileKinds.length?'Choose at least one tile.':mixed?'Experimental mix. Selected tiles are allowed, not required. P1 cannot share whole edges with P2/P3 at this scale.':'Selected tiles are allowed, not required.';
 runner.reset();
}
if($('boundaryRule'))$('boundaryRule').onchange=resetSelection;
$('tileSet').onchange=()=>{const ks=TILE_PRESETS[$('tileSet').value];if(!ks)return;for(const k of TILE_KINDS)$('tile_'+k).checked=ks.includes(k);resetSelection();};
for(const k of TILE_KINDS)$('tile_'+k).onchange=resetSelection;
function updateTimer(){for(const id of LANE_IDS){const l=latest?.lanes[id];$('laneTimer_'+id).textContent=`${((runner?.elapsed(id)||0)/1000).toFixed(2)} s${l?.busy?' · working':l?.state?' · paused':''}`;}}
setInterval(updateTimer,100);
new ResizeObserver(queueDraw).observe(canvas);resetSelection();
