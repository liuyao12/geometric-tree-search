import * as THREE from 'three';
import {OrbitControls} from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';
const $=id=>document.getElementById(id),base='../../data/nonacube-search-replay/';
const fmt=n=>n.toLocaleString(),key=v=>v.join(','),offsets=[];
for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)offsets.push([x,y,z]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
let manifest,chunk,chunkIndex=-1,index=-1,selected=new Set(),count,playing=false,busy=false,token=0,clock=0,last=0;
const cache=new Map(),cellCache=new Map();
function cells(id){
  if(id===0)return manifest.root;
  if(!cellCache.has(id)){
    const [orientation,center]=manifest.placements[id-1],axes=[[0,1],[0,2],[1,2]][orientation],vs=[center];
    for(const axis of axes)for(const d of [-2,-1,1,2]){const v=[...center];v[axis]+=d;vs.push(v);}
    cellCache.set(id,vs);
  }return cellCache.get(id);
}
const host=$('scene'),scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
const camera=new THREE.PerspectiveCamera(40,1,.1,200);camera.position.set(22,19,25);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(.5,.5,.5);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xddeeff,0x465263,2.6));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(8,18,12);scene.add(light);
const grid=new THREE.GridHelper(24,24,0x415364,0x22313e);grid.position.y=-8.55;scene.add(grid);
const geometry=new THREE.BoxGeometry(.96,.96,.96),material=new THREE.MeshStandardMaterial({roughness:.65,metalness:0});
const cubes=new THREE.InstancedMesh(geometry,material,4000);cubes.instanceMatrix.setUsage(THREE.DynamicDrawUsage);cubes.count=0;scene.add(cubes);
const dummy=new THREE.Object3D(),color=new THREE.Color();
new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();drawDepth();}).observe(host);
let rootNear;
function geometryState(){
  const owners=new Map(),all=[0,...selected];
  for(const id of all)for(const v of cells(id)){const k=key(v);if(!owners.has(k))owners.set(k,[]);owners.get(k).push(id);}
  const component=new Set([0]),queue=[0],first=new Set();
  for(let n=0;n<queue.length;n++)for(const v of cells(queue[n]))for(const d of offsets)for(const other of owners.get(key(add(v,d)))??[]){
    if(queue[n]===0&&other!==0)first.add(other);
    if(!component.has(other)){component.add(other);queue.push(other);}
  }
  return {owners,component,first,covered:[...rootNear].filter(k=>owners.has(k)).length};
}
function renderPatch(){
  if(!manifest||!chunk||index<0)return;
  const f=chunk.frames[index-chunk.start],[op,a,b,,tileCount,overlaps]=f;
  const {owners,component,first,covered}=geometryState();let n=0;
  for(const id of [0,...selected]){
    if($('connected-only').checked&&!component.has(id))continue;
    for(const v of cells(id)){
      dummy.position.set(...v.map(x=>x+.5));dummy.updateMatrix();cubes.setMatrixAt(n,dummy.matrix);
      color.set(owners.get(key(v)).length>1?'#ec7276':id===0?'#f2e8cc':first.has(id)?'#64d6c3':'#e8a868');
      if(!component.has(id))color.multiplyScalar(.4);
      cubes.setColorAt(n++,color);
    }
  }
  cubes.count=n;cubes.instanceMatrix.needsUpdate=true;if(cubes.instanceColor)cubes.instanceColor.needsUpdate=true;cubes.computeBoundingSphere();
  $('tiles').textContent=fmt(tileCount);$('connected').textContent=fmt(component.size);$('coverage').textContent=`${covered} / ${rootNear.size}`;
  $('decisions').textContent=fmt(count.decisions);$('conflicts').textContent=fmt(count.conflicts);
  $('level').textContent=op===3?b:op===4||op===5?a:op===6?b:0;
  const labels={3:'Decision',4:'Conflict',5:'Backjump',6:a===1?'Start':'Restart',7:'UNSAT · proof complete'};
  $('event').textContent=labels[op];$('event').style.color=op===4?'#ec7276':'#68d9c7';
  if(op===3){
    const id=Math.abs(a);
    $('action').textContent=id>0&&id<=manifest.placements.length?`${a>0?'Select':'Exclude'} placement ${id}; its consequences appear at the next event.`:`Set auxiliary variable ${id} ${a<0?'false':'true'}.`;
  }else $('action').textContent=op===4?`A clause with ${b} literals is false. Learn from the conflict and backtrack.`:op===5?`Undo assignments above decision level ${a}.`:op===6?'Begin a search phase using all retained learned clauses.':'The final contradiction rules out every two-corona completion.';
  $('notice').textContent=overlaps?`${overlaps} overlapped cube positions in this conflicting assignment. Not a legal patch.`:op===3?'Nonoverlapping, propagation-complete state.':op===7?'The displayed remainder is the final failed assignment.':'Intermediate solver state; propagation may still be pending.';
  $('scrub').value=index;$('frame').textContent=`Event ${fmt(index+1)} / ${fmt(manifest.frames)}`;
  drawDepth();
  // Read-only audit surface for browser smoke tests and exact frame inspection.
  window.nonacubeReplay={index,event:op,selected:[...selected],tileCount,connected:component.size,covered,overlaps,counts:{...count},playing};
}
function drawDepth(){
  if(!chunk)return;const canvas=$('depth'),w=canvas.clientWidth,h=75;canvas.width=w*devicePixelRatio;canvas.height=h*devicePixelRatio;
  const ctx=canvas.getContext('2d');ctx.scale(devicePixelRatio,devicePixelRatio);ctx.clearRect(0,0,w,h);
  const levels=chunk.frames.map(f=>f[0]===3?f[2]:f[0]===4||f[0]===5?f[1]:0),max=Math.max(1,...levels);
  ctx.strokeStyle='#65d7c4';ctx.lineWidth=1;ctx.beginPath();levels.forEach((v,i)=>{const x=i*w/levels.length,y=h-5-v*(h-10)/max;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
  ctx.fillStyle='#c16975';chunk.frames.forEach((f,i)=>{if(f[0]===4)ctx.fillRect(i*w/levels.length,h-3,1,3);});
  ctx.strokeStyle='#f2e8cc';const x=(index-chunk.start)*w/levels.length;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();
}
async function loadChunk(ci){
  if(cache.has(ci))return cache.get(ci);
  const promise=(async()=>{const r=await fetch(base+manifest.chunks[ci].file);if(!r.ok)throw Error(`Recording segment failed: ${r.status}`);
    return JSON.parse(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text());})();
  cache.set(ci,promise);try{const data=await promise;while(cache.size>4)cache.delete(cache.keys().next().value);return data;}catch(e){cache.delete(ci);throw e;}
}
function apply(f){for(const d of f[3])d>0?selected.add(d):selected.delete(-d);const name={3:'decisions',4:'conflicts',5:'backtracks',6:'searchStarts'}[f[0]];if(name)count[name]++;}
async function seek(target,paint=true){
  target=Math.max(0,Math.min(manifest.frames-1,target));const mine=++token;busy=true;
  try{
    const ci=Math.floor(target/4096),loaded=await loadChunk(ci);if(mine!==token)return;
    if(ci!==chunkIndex||target<index){chunk=loaded;chunkIndex=ci;selected=new Set(chunk.initial);count={...chunk.counters};index=chunk.start-1;}
    while(index<target){index++;apply(chunk.frames[index-chunk.start]);}
    if(paint)renderPatch();
    if(ci+1<manifest.chunks.length)loadChunk(ci+1).catch(()=>{});
  }finally{if(mine===token)busy=false;}
}
function pause(){playing=false;$('play').textContent='Play';}
function fail(e){pause();$('error').textContent=`Playback error: ${e.message}`;console.error(e);}
async function manual(fn){pause();try{await fn();}catch(e){fail(e);}}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';clock=0;};
$('prev').onclick=()=>manual(()=>seek(index-1));$('next').onclick=()=>manual(()=>seek(index+1));
$('scrub').oninput=()=>manual(()=>seek(Number($('scrub').value)));
$('largest').onclick=()=>manual(async()=>{$('connected-only').checked=true;await seek(manifest.largestConnected.frame);});
$('finish').onclick=()=>manual(()=>seek(manifest.frames-1));$('connected-only').onchange=renderPatch;
$('conflict').onclick=()=>manual(async()=>{
  let p=index+1;
  while(p<manifest.frames){const ci=Math.floor(p/4096),c=await loadChunk(ci);const found=c.frames.findIndex((f,i)=>c.start+i>=p&&f[0]===4);
    if(found>=0){await seek(c.start+found);return;}p=c.start+c.frames.length;
  }await seek(manifest.frames-1);
});
async function tick(now){
  const dt=Math.min((now-last)/1000,.1);last=now;
  if(playing&&!busy&&manifest){clock+=dt*Number($('speed').value);const n=Math.floor(clock);
    if(n){clock-=n;try{
      // Do not skip segments at high speed: every chronological event is applied.
      const target=Math.min(index+n,chunk.start+chunk.frames.length-1);
      await seek(target>index?target:index+1);
      if(index===manifest.frames-1)pause();
    }catch(e){fail(e);}}
  }
  controls.update();renderer.render(scene,camera);requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
try{
  const r=await fetch(base+'manifest.json');if(!r.ok)throw Error(`Recording index failed: ${r.status}`);manifest=await r.json();
  const rootKeys=new Set(manifest.root.map(key));rootNear=new Set();for(const v of manifest.root)for(const d of offsets){const k=key(add(v,d));if(!rootKeys.has(k))rootNear.add(k);}
  $('total').textContent=`${fmt(manifest.counts.decisions)} decisions · ${fmt(manifest.counts.conflicts)} conflicts`;
  const best=manifest.largestConnected;
  $('largest-summary').textContent=`The largest root-connected patch has ${best.tileCount} tiles (${best.tileCount*9} unit cubes), including the root. At that event it covers ${best.rootHaloCovered} of ${best.rootHaloRequired} root-surround cells. The largest total nonoverlapping selection has ${manifest.largest.tileCount} tiles, counting detached pieces.`;
  $('scrub').max=manifest.frames-1;await seek(0);
  for(const el of document.querySelectorAll('button,input[type=range]'))el.disabled=false;
}catch(e){fail(e);}
