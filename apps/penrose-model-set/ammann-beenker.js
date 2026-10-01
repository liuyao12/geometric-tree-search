import {xy,direction} from '../../assets/ammann-beenker.js?v=20261001-ab';
const $=id=>document.getElementById(id),canvas=$('abCanvas'),ctx=canvas.getContext('2d');
const colors={1:'#91c7b3',2:'#e7bb78'};
let worker,state,running=false,busy=false,target=20,hits=[],view=null,selectedPoint=null,lastPointText=null;
const typeset=element=>{if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([element]).catch(()=>{});};
function status(){
  $('abRun').textContent=running?'Pause':state?.paused?'Continue':'Run';
  $('abRun').disabled=!!state?.done||![1,2].some(k=>$('abTile'+k).checked);
  $('abStep').disabled=$('abRun').disabled;
  $('abStatus').textContent=state?.error||(!state?'Initializing':state.done?state.status:state.paused?'Consistent finite patch · target reached':running?'Searching':'Paused');
  if(!state?.tiles){$('abStats').textContent='';$('abGraph').textContent='';$('abMarkingInfo').textContent='';$('abEvent').textContent='';return;}
  const s=state.stats,g=state.graph,counts=[1,2].map(k=>state.tiles.filter(t=>t.kind===k).length);
  $('abStats').textContent=`${state.tiles.length} tiles (${counts.join(' / ')}) · peak ${s.peak} tiles · ${s.proposals} proposals · ${s.backtracks} backtracks · ${s.forcedMoves} forced moves · ${s.branches} branches · ${(state.computeMs/1000).toFixed(2)} s compute`;
  $('abGraph').textContent=`${g.points} frontier points · ${g.candidates} legal candidates · ${g.incidences} links · ${g.deadPoints} dead points · corona ${state.frontier.length?Math.min(...state.frontier.map(p=>p.depth)):'closed'}`;
  const m=state.marking,c=state.completion;
  $('abMarkingInfo').textContent=state.method==='gcts'?`Point marking: ${m.points} active points · ${m.values} assigned values · ${m.references} tile references. ${m.prunes.toLocaleString()} marking rejections.\nCorner propagation: ${c.prunes.toLocaleString()} rejections · ${c.cached.toLocaleString()} cached states · ${c.hits.toLocaleString()} cache hits.\nMarking source: ${state.rule==='full'?'published edge and vertex-house rules':state.rule==='edges'?'edge arrows only (weaker rules)':'none (unmarked comparison)'}. No new marking is being trained.`:'Baseline: pairwise geometry and point-marking checks. No corner-completion propagation or trained marking.';
  const event=state.event;
  $('abEvent').textContent=event?.type==='dead'?'Dead frontier detected; the next step backtracks.':event?.type==='remove'?'Backtracked: this decorated candidate is excluded in this parent state.':event?.type==='add'?`${event.forced?'Forced placement':'Branch placement'} · ${event.choices} decorated alternatives at the selected point.`:state.rule==='full'?'Ready. Matching candidates include every compatible house orientation.':'Ready. The frontier contains every legal selected placement.';

}
function pump(step=false){if(busy||!worker||state?.done||(!running&&!step))return;busy=true;worker.postMessage({type:'advance',target,step});}
function reset(){
  selectedPoint=null;lastPointText=null;running=false;worker?.terminate();worker=null;state=null;view=null;target=$('abRule').value==='full'?20:40;busy=false;
  const kinds=[1,2].filter(k=>$('abTile'+k).checked);
  $('abInfo').textContent='Click a vertex or edge midpoint to inspect its coordinate, total and marking.';
  const rule=$('abRule').value,method=$('abMethod').value;
  $('abRuleInfo').textContent=rule==='full'?'Full Ammann matching: edge directions agree, and vertex fragments form complete houses.':rule==='edges'?'Edge directions agree. These weaker rules permit periodic tilings.':'Unmarked squares and rhombs. Periodic tilings are possible.';
  if(!kinds.length){status();$('abStatus').textContent='Choose at least one tile.';draw();return;}
  worker=new Worker(new URL('./ammann-beenker-worker.js?v=20261001-ab',import.meta.url),{type:'module'});const current=worker;busy=true;
  worker.onmessage=({data})=>{if(worker!==current)return;busy=false;state=data;if(data.done||data.paused)running=false;status();draw();if(running)setTimeout(()=>pump(),0);};
  worker.onerror=e=>{if(worker!==current)return;busy=false;running=false;state={error:e.message,done:true};status();};
  worker.postMessage({type:'init',options:{kinds,rule,method,seed:Number($('abSeed').value)||1}});status();draw();
}
function draw(){
  const rect=canvas.getBoundingClientRect();if(!rect.width)return;
  const dpr=devicePixelRatio||1;canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,rect.width,rect.height);hits=[];
  if(!state?.tiles?.length)return;
  const points=state.tiles.flatMap(t=>t.loop),xs=points.map(p=>p.x),ys=points.map(p=>p.y),loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);
  view={x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min((rect.width-60)/Math.max(1,hiX-loX),(rect.height-60)/Math.max(1,hiY-loY))};
  const screen=p=>({x:rect.width/2+(p.x-view.x)*view.scale,y:rect.height/2-(p.y-view.y)*view.scale});
  const unique=new Map();
  for(const tile of state.tiles){
    ctx.beginPath();tile.loop.map(screen).forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=colors[tile.kind];ctx.fill();ctx.strokeStyle='#3f5653';ctx.lineWidth=1;ctx.stroke();
    tile.support.forEach((p,i)=>{if(!unique.has(p.key))unique.set(p.key,{point:p.exact,total:0,midpoint:i>=4,marks:new Map()});unique.get(p.key).total+=p.weight;});
    for(const m of tile.marks)unique.get(m.point.join(',')).marks.set(m.channel,m.value);
    if($('abMarks').checked)for(const m of tile.marks.filter(m=>m.channel==='edge')){
      const p=screen(xy(m.point.map(n=>n/2))),v=xy(direction(m.value)),length=Math.max(8,Math.min(24,view.scale*.45)),head=3,ux=v.x,uy=-v.y;
      ctx.strokeStyle='#34504a';ctx.lineWidth=1.3;ctx.beginPath();ctx.moveTo(p.x-ux*length/2,p.y-uy*length/2);ctx.lineTo(p.x+ux*length/2,p.y+uy*length/2);
      const x=p.x+ux*length/2,y=p.y+uy*length/2;ctx.moveTo(x-ux*head-uy*head*.7,y-uy*head+ux*head*.7);ctx.lineTo(x,y);ctx.lineTo(x-ux*head+uy*head*.7,y-uy*head-ux*head*.7);ctx.stroke();
    }
  }
  if($('abMarks').checked)for(const p of unique.values())if(p.marks.has('house')){
    const center=screen(xy(p.point.map(n=>n/2))),r=p.marks.get('house')*Math.PI/4,size=Math.max(2.5,Math.min(8,view.scale*.14));
    ctx.beginPath();[[Math.SQRT2,0],[0,Math.SQRT2],[-Math.SQRT2,0],[-1,0],[-1,-1],[1,-1],[1,0]].forEach(([x,y],i)=>{const X=center.x+size*(x*Math.cos(r)-y*Math.sin(r)),Y=center.y-size*(x*Math.sin(r)+y*Math.cos(r));i?ctx.lineTo(X,Y):ctx.moveTo(X,Y);});ctx.closePath();ctx.fillStyle='#284d6b99';ctx.fill();
  }
  for(const p of unique.values()){const q=screen(xy(p.point.map(n=>n/2)));hits.push({...p,...q});ctx.fillStyle=p.total===8?'#486052':'#a44832';if(p.midpoint){if(p.total<8)ctx.fillRect(q.x-1.5,q.y-1.5,3,3);}else{ctx.beginPath();ctx.arc(q.x,q.y,p.total===8?1.5:2.5,0,2*Math.PI);ctx.fill();}}
  if(selectedPoint){const p=unique.get(selectedPoint);if(p)showPoint(p);else{lastPointText=null;$('abInfo').textContent='The selected point was removed by backtracking.';}}
}
$('abRun').onclick=()=>{if(state?.paused)target+=state.rule==='full'?20:40;running=!running;status();pump();};
$('abStep').onclick=()=>{running=false;if(state?.paused)target+=state.rule==='full'?20:40;status();pump(true);};
$('abReset').onclick=reset;$('abMethod').onchange=reset;$('abRule').onchange=reset;$('abSeed').onchange=reset;
for(const k of [1,2])$('abTile'+k).onchange=reset;
$('abMarks').onchange=draw;
function showPoint(p){
  const integral=p.point.every(n=>n%2===0),coordinates=integral?p.point.map(n=>n/2):p.point;
  const terms=coordinates.map((n,i)=>!n?'':i===0?String(n):`${n===1?'':n===-1?'-':n}\\zeta_8${i===1?'':`^{${i}}`}`).filter(Boolean).join('+').replaceAll('+-','-')||'0';
  const coordinate=integral?terms:`\\frac{${terms}}{2}`,markText=[...p.marks].map(([channel,value])=>`\\(m_{\\mathrm{${channel}}}(p)=${value}\\)`).join(', ');
  const message=`${p.midpoint?'Edge midpoint':'Vertex'} \\(${coordinate}\\), \\(T(p)=\\frac{${p.total}}{8}\\). ${p.total===8?'Complete.':'Frontier obligation.'} ${markText||'No marking assigned here.'}`;
  if(message===lastPointText)return;lastPointText=message;window.MathJax?.typesetClear?.([$('abInfo')]);$('abInfo').textContent=message;typeset($('abInfo'));
}
canvas.onclick=e=>{
  const rect=canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
  const p=hits.reduce((a,b)=>Math.hypot(b.x-x,b.y-y)<Math.min(12,a?Math.hypot(a.x-x,a.y-y):Infinity)?b:a,null);if(!p)return;
  selectedPoint=p.point.join(',');showPoint(p);
};
new ResizeObserver(draw).observe(canvas);reset();
