import {materialize,project} from './j-tiling-model.js';
const $=id=>document.getElementById(id),canvas=$('projection'),ctx=canvas.getContext('2d');
let specs=[],tiles=[],worker=null,running=false,paused=false,currentSource='saved',scale=20,offset=[0,0],manualView=false,size=[1,1],lastStats=null;
const theta=()=>Math.PI/3-Number($('morph').value)/1000*Math.PI/12;
function fit(){if(!tiles.length)return;let xs=[],ys=[];for(let n=0;n<=20;n++){const a=Math.PI/3-n/20*Math.PI/12;for(const t of tiles)for(const v of t.vertices){const p=project(v,a);xs.push(p[0]);ys.push(p[1]);}}
 const lo=[Math.min(...xs),Math.min(...ys)],hi=[Math.max(...xs),Math.max(...ys)];scale=Math.min((size[0]-38)/(hi[0]-lo[0]),(size[1]-48)/(hi[1]-lo[1]));offset=[size[0]/2-(hi[0]+lo[0])/2*scale,size[1]/2+(hi[1]+lo[1])/2*scale];manualView=false;draw();}
function draw(){const dpr=devicePixelRatio||1;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,...size);ctx.fillStyle='#f7f6ee';ctx.fillRect(0,0,...size);
 for(const t of tiles){const ps=t.vertices.map(v=>{const p=project(v,theta());return[p[0]*scale+offset[0],-p[1]*scale+offset[1]];});ctx.beginPath();ps.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fillStyle=t.orientation%2?'#eed5ae':'#b9d9d1';ctx.fill();ctx.strokeStyle='#53645e';ctx.lineWidth=Math.max(.7,Math.min(1.25,scale/22));ctx.stroke();}
 const ev=specs.filter(p=>p.orientation%2===0).length,odd=specs.length-ev,m=+$('morph').value;
 $('even-label').textContent=(m===0?'Hats':'Even orientations')+` (${ev})`;$('odd-label').textContent=(m===0?'Turtles':'Odd orientations')+` (${odd})`;
 $('projection-name').textContent=m===0?'Hats in turtles':m===1000?'Equilateral Spectre polygon':`Morph ${Math.round(m/10)}%`;
 canvas.setAttribute('aria-label',`${specs.length}-tile ${$('projection-name').textContent} projection`);
}
function setPatch(p){specs=p;tiles=specs.map(p=>materialize(p.orientation,p.translation));if(!manualView)fit();else draw();}
function controls(){running?$('run').disabled=true:$('run').disabled=false;$('pause').disabled=!running;$('pause').textContent=paused?'Resume':'Pause';}
function stop(){worker?.terminate();worker=null;running=false;paused=false;controls();}
async function saved(){stop();currentSource='saved';const response=await fetch('assets/j-search-patch-30.json?v=20261101-j30');if(!response.ok)throw Error('Saved patch could not load');const data=await response.json();manualView=false;setPatch(data.placements);lastStats=data.stats;
 $('status').textContent='Saved search result: 30 tiles. Sector constraints and 21 morph projections independently checked.';$('counts').textContent=`From one tile · ${data.stats.attempts} attempts · ${data.stats.backtracks} backtracks · open boundary`;}
function run(){stop();currentSource='live';running=true;paused=false;manualView=false;setPatch([{orientation:0,translation:[0,0,0,0],generation:0}]);controls();$('status').textContent='Searching from one tile with the J rule…';$('counts').textContent='';
 worker=new Worker(new URL('./j-tiling-worker.js',import.meta.url),{type:'module'});
 worker.onerror=event=>{$('status').textContent='Search stopped: '+event.message;stop();};
 worker.onmessage=({data})=>{lastStats=data.stats;if(data.placements.length)setPatch(data.placements);$('counts').textContent=`${data.placements.length} tiles · ${data.stats.attempts} attempts · ${data.stats.forced} forced · ${data.stats.backtracks} backtracks · ${(data.elapsedMs/1000).toFixed(1)} s`;
  if(data.type==='finished'){running=false;paused=false;controls();$('status').textContent=data.status==='consistent finite patch'?`${data.placements.length}-tile checkpoint reached. Finite sector-consistent patch; no infinite-extension claim.`:`Budget reached: best viable 4D prefix has ${data.placements.length} tiles. Extension is unknown.`;}else $('status').textContent=`Searching from one tile · best sector-consistent prefix: ${data.bestTiles} tiles`;
 };
 worker.postMessage({type:'start',target:+$('target').value});
}
$('run').onclick=run;$('saved').onclick=()=>saved().catch(e=>{$('status').textContent=e.message;});$('pause').onclick=()=>{paused=!paused;worker?.postMessage({type:paused?'pause':'resume'});controls();};$('fit').onclick=fit;
$('morph').oninput=draw;$('mixed').onclick=()=>{$('morph').value='0';draw();};$('equilateral').onclick=()=>{$('morph').value='1000';draw();};
let drag=null;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,...offset];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;manualView=true;offset=[drag[2]+e.clientX-drag[0],drag[3]+e.clientY-drag[1]];draw();};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;
canvas.addEventListener('wheel',e=>{e.preventDefault();manualView=true;const box=canvas.getBoundingClientRect(),p=[e.clientX-box.left,e.clientY-box.top],factor=Math.exp(-e.deltaY*.001);scale*=factor;offset=p.map((v,i)=>v+(offset[i]-v)*factor);draw();},{passive:false});
new ResizeObserver(()=>{const box=canvas.getBoundingClientRect();size=[box.width,box.height];canvas.width=Math.round(box.width*(devicePixelRatio||1));canvas.height=Math.round(box.height*(devicePixelRatio||1));if(!manualView)fit();else draw();}).observe(canvas);
addEventListener('message',({data,origin})=>{if(origin!==location.origin)return;if(data?.type==='j-pause'&&running&&!paused){paused=true;worker?.postMessage({type:'pause'});controls();}});
saved().catch(e=>{$('status').textContent=e.message;});
