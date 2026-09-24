import {xy} from '../../assets/sevenfold-rhombs.js?v=20260924-sevenfold';
const $=id=>document.getElementById(id),canvas=$('sevenCanvas'),ctx=canvas.getContext('2d');
const colors={1:'#e7bb78',2:'#91c7b3',3:'#aaa6d8'};
let worker,state,running=false,busy=false,target=40,hits=[],view=null,initialized=false;
const typeset=element=>{if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([element]).catch(()=>{});};
function status(){
  $('sevenRun').textContent=running?'Pause':state?.paused?'Continue':'Run';
  $('sevenRun').disabled=!!state?.done||![1,2,3].some(k=>$('sevenTile'+k).checked);
  $('sevenStep').disabled=$('sevenRun').disabled;
  $('sevenStatus').textContent=state?.error||(!state?'Initializing':state.done?state.status:state.paused?'Consistent finite patch · target reached':running?'Searching':'Paused');
  if(!state?.tiles)return;
  const s=state.stats,g=state.graph,counts=[1,2,3].map(k=>state.tiles.filter(t=>t.kind===k).length);
  $('sevenStats').textContent=`${state.tiles.length} tiles (${counts.join(' / ')}) · ${s.proposals} proposals · ${s.backtracks} backtracks · ${s.forcedMoves} forced moves · ${s.branches} branches · ${(state.computeMs/1000).toFixed(2)} s compute`;
  $('sevenGraph').textContent=`${g.points} frontier points · ${g.candidates} legal candidates · ${g.incidences} links · ${g.deadPoints} dead points · corona ${state.frontier.length?Math.min(...state.frontier.map(p=>p.depth)):'closed'}`;
}
function pump(step=false){if(busy||!worker||state?.done||(!running&&!step))return;busy=true;worker.postMessage({type:'advance',target,step});}
function reset(){
  running=false;worker?.terminate();worker=null;state=null;view=null;target=40;busy=false;
  const kinds=[1,2,3].filter(k=>$('sevenTile'+k).checked);
  $('sevenInfo').textContent='Click a vertex to inspect its exact coordinate and corner total.';
  const forbidden=$('sevenRule').value==='forbidden';
  $('sevenRuleInfo').textContent=forbidden?'Experimental restriction: equal-shaped rhombs cannot share an edge. This rule has no claimed infinite extension or aperiodicity theorem.':'Unmarked rhombs: all geometrically legal edge-to-edge contacts are allowed. Periodic tilings are possible.';
  if(!kinds.length){status();$('sevenStatus').textContent='Choose at least one rhomb.';draw();return;}
  worker=new Worker(new URL('./sevenfold-worker.js?v=20260924-sevenfold',import.meta.url),{type:'module'});const current=worker;busy=true;
  worker.onmessage=({data})=>{if(worker!==current)return;busy=false;state=data;if(data.done||data.paused)running=false;status();draw();if(running)setTimeout(()=>pump(),0);};
  worker.onerror=e=>{if(worker!==current)return;busy=false;running=false;state={error:e.message,done:true};status();};
  worker.postMessage({type:'init',options:{kinds,forbidden,seed:Number($('sevenSeed').value)||1}});status();draw();
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
    tile.vertices.forEach((v,i)=>{if(!unique.has(v))unique.set(v,{point:tile.points[i],total:0});unique.get(v).total+=tile.weights[i];});
    if(state.forbidden&&$('sevenMarks').checked)for(const m of tile.marks){const p=screen(xy(m.point.map(n=>n/2)));ctx.beginPath();ctx.arc(p.x,p.y,3,0,2*Math.PI);ctx.fillStyle=m.value?'#734996':'#fffdf7';ctx.fill();ctx.strokeStyle='#734996';ctx.stroke();}
  }
  for(const p of unique.values()){const q=screen(xy(p.point));hits.push({...p,...q});ctx.beginPath();ctx.arc(q.x,q.y,p.total===14?1.5:2.5,0,2*Math.PI);ctx.fillStyle=p.total===14?'#486052':'#a44832';ctx.fill();}
}
function setSystem(seven){
  if(seven&&$('runLearning').textContent==='Pause')$('runLearning').click();
  if(!seven){running=false;status();}
  $('penrosePane').hidden=seven;$('sevenPane').hidden=!seven;
  $('systemFive').setAttribute('aria-pressed',String(!seven));$('systemSeven').setAttribute('aria-pressed',String(seven));
  const url=new URL(location.href);if(seven)url.searchParams.set('ring','7');else url.searchParams.delete('ring');history.replaceState(null,'',url);
  if(seven&&!initialized){initialized=true;reset();}else if(seven)draw();
}
$('systemFive').onclick=()=>setSystem(false);$('systemSeven').onclick=()=>setSystem(true);
$('sevenRun').onclick=()=>{if(state?.paused)target+=40;running=!running;status();pump();};
$('sevenStep').onclick=()=>{running=false;if(state?.paused)target+=40;status();pump(true);};
$('sevenReset').onclick=reset;$('sevenRule').onchange=reset;$('sevenSeed').onchange=reset;
for(const k of [1,2,3])$('sevenTile'+k).onchange=reset;
$('sevenMarks').onchange=draw;
canvas.onclick=e=>{
  const rect=canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
  const p=hits.reduce((a,b)=>Math.hypot(b.x-x,b.y-y)<Math.min(12,a?Math.hypot(a.x-x,a.y-y):Infinity)?b:a,null);if(!p)return;
  const terms=p.point.map((n,i)=>!n?'':i===0?String(n):`${n===1?'':n===-1?'-':n}\\zeta_7${i===1?'':`^{${i}}`}`).filter(Boolean).join('+').replaceAll('+-','-')||'0';
  window.MathJax?.typesetClear?.([$('sevenInfo')]);$('sevenInfo').textContent=`\\(${terms}\\), \\(T(p)=\\frac{${p.total}}{14}\\). ${p.total===14?'Full corner.':'Frontier obligation.'}`;typeset($('sevenInfo'));
};
new ResizeObserver(draw).observe(canvas);setSystem(new URL(location.href).searchParams.get('ring')==='7');
