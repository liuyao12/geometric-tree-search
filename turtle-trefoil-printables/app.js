import {loops,stripes,project} from './search/model.js';
export function mount(THREE,data){
 const $=id=>document.getElementById(id),palette=['#4b9b64','#9bd4b2','#1763cb','#d8c8a9','#c58a45','#f1ce91'].map(v=>new THREE.Color(v));
 function load(encoded,type){
  const bytes=typeof encoded==='string'?Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)):new Uint8Array(encoded),v=new DataView(bytes.buffer),count=v.getUint32(80,true),p=new Float32Array(count*9),c=new Float32Array(count*9);
  for(let i=0;i<count;i++){
   for(let j=0;j<9;j++)p[9*i+j]=v.getFloat32(84+50*i+12+4*j,true);
   let x=0,y=0,z=0;for(let j=0;j<3;j++){x+=p[9*i+j*3]/3;y+=p[9*i+j*3+1]/3;z+=p[9*i+j*3+2]/3;}
   let color=type==='board'?3:type==='connector'?2:z<-.0001||z>4.0001?2:z>2?1:0;
   if((type==='turtle'||type==='trefoil')&&z>4.0001&&Math.hypot(x,y)<10)color=1;
   if(type==='trefoil'&&color<2)color+=4;
   for(let j=0;j<3;j++)palette[color].toArray(c,9*i+3*j);
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p,3));g.setAttribute('color',new THREE.BufferAttribute(c,3));g.computeVertexNormals();g.computeBoundingBox();return g;
 }
 const geometry=Object.fromEntries(Object.entries(data).map(([k,v])=>[k,load(v,k)]));geometry.connector.translate(0,0,-1.3);
 const opaque=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.57,side:THREE.DoubleSide});
 const transparent=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.57,side:THREE.DoubleSide,transparent:true,opacity:.5,depthWrite:false});
 const edges=Object.fromEntries(['turtle','trefoil'].map(k=>[k,new THREE.EdgesGeometry(geometry[k],35)]));
 const edgeMaterial=new THREE.LineBasicMaterial({color:'#504832',transparent:true,opacity:.25});
 const viewport=$('viewport'),renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor('#f4f1eb');viewport.append(renderer.domElement);$('loading')?.remove();
 const scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xffffff,0x73867c,2));for(const [x,y,z,p] of [[-80,-80,180,2.5],[100,30,100,1]]){const l=new THREE.DirectionalLight(0xffffff,p);l.position.set(x,y,z);scene.add(l);}
 const camera=new THREE.PerspectiveCamera(34,1,.1,5000),root=new THREE.Group(),content=new THREE.Group();root.add(content);scene.add(root);
 let distance=500,initialDistance=500,live=false,worker=null,queue=[],batchPending=false,running=false,stepping=false,finished=false,inFlight=null,requestId=0,randomSeed=10,lastTime=0;
 let tileObjects=new Map(),boardObjects=[],connectorObjects=[],placed=[],nodes=0,backtracks=0,lastAction='Ready',autoZoom=true,moveMode=false,moveCount=0,moveTotal=0;
 const matrix=a=>new THREE.Matrix4().set(...a.flat());
 // Turn the entire patch over about the middle of its 4 mm bodies.
 const faceFlip=matrix([[1,0,0,0],[0,-1,0,0],[0,0,-1,4],[0,0,0,1]]);
 function object(type,m){const o=new THREE.Mesh(geometry[type],opaque);if(m)o.applyMatrix4(matrix(m));if(type!=='board')o.applyMatrix4(faceFlip);if(edges[type])o.add(new THREE.LineSegments(edges[type],edgeMaterial));content.add(o);return o;}
 function render(){camera.position.set(0,-distance*.48,distance*.88);camera.lookAt(0,0,0);renderer.render(scene,camera);}
 function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}
 function boards(centers){for(const o of boardObjects)content.remove(o);boardObjects=centers.map(c=>{const o=object('board');o.position.set(c[0],-c[1],c[2]);o.scale.y=-1;o.material=$('boardTransparent').checked?transparent:opaque;return o;});}
 function clearConnectors(){for(const o of connectorObjects)content.remove(o);connectorObjects=[];}
 function drawConnectors(matrices){clearConnectors();connectorObjects=matrices.map(m=>object('connector',m));}
 // Display only upper-face connections. Endpoint matching here is a drawing
 // operation; all placement legality comes from the worker's point graph.
 function connectorsFor(tiles){
  const groups=new Map(),result=[];
  for(const t of tiles){const m=matrix(t.matrix);
   for(const [a,b,side] of stripes[t.tile]){
    const normal=side*t.matrix[2][2];if(normal>0)continue;
    const ends=[a,b].map(i=>new THREE.Vector3(...project(loops[t.tile][i]),side>0?4:0).applyMatrix4(m));
    const dir=ends[1].clone().sub(ends[0]).normalize();
    for(let i=0;i<2;i++){const p=ends[i],d=dir.clone().multiplyScalar(i?-1:1),key=[p.x,p.y,p.z].map(n=>n.toFixed(4)).join(',');
     const prior=groups.get(key)||[];
     for(const other of prior)if(other.id!==t.id&&other.d.dot(d)<-.999999){const n=new THREE.Vector3(-d.y*normal,d.x*normal,0);result.push([[d.x,n.x,0,p.x],[d.y,n.y,0,p.y],[0,0,normal,p.z],[0,0,0,1]]);}
     prior.push({id:t.id,d});groups.set(key,prior);
    }
   }
  }return result;
 }
 function fitView(minimum=0){
  const box=new THREE.Box3();for(const o of tileObjects.values()){o.updateMatrix();box.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrix));}
  if(box.isEmpty())return;
  if(!live){const center=box.getCenter(new THREE.Vector3());content.position.copy(center).multiplyScalar(-1);}else content.position.set(0,0,0);
  const center=live?new THREE.Vector3():box.getCenter(new THREE.Vector3()),tangent=Math.tan(camera.fov*Math.PI/360);let needed=0;
  for(const x0 of [box.min.x,box.max.x])for(const y0 of [box.min.y,box.max.y])for(const z0 of [box.min.z,box.max.z]){const x=x0-center.x,y=y0-center.y,z=z0-center.z;needed=Math.max(needed,-.479*y+.878*z+Math.max(Math.abs(x)/(tangent*camera.aspect),Math.abs(.878*y+.479*z)/tangent));}
  distance=Math.max(minimum,needed*1.18);initialDistance=distance;render();
 }
 function controls(){
  for(const id of ['run','step','restart','speed'])$(id).hidden=!live;
  $('run').textContent=running?'Pause':'Run';$('run').disabled=finished;
  $('step').disabled=running||stepping||finished;
  $('caption').textContent=moveMode?`${placed.length} tiles · ${moveCount} / ${moveTotal} moves · ${lastAction}`:`${placed.length} ${placed.length===1?'tile':'tiles'} · ${backtracks} backtracks · ${lastAction}`;
  $('scope').textContent=moveMode?'Paired flips and half-turns preserve the outline and point markings. The lifting motion is illustrative.':'Live stripe-matching search. The board is a visual guide; physical board fit is not checked.';
 }
 function sync(tiles){
  const ids=new Set(tiles.map(t=>t.id));for(const [id,o] of tileObjects)if(!ids.has(id)){content.remove(o);tileObjects.delete(id);}
  for(const t of tiles){if(!tileObjects.has(t.id))tileObjects.set(t.id,object(t.tile,t.matrix));else faceFlip.clone().multiply(matrix(t.matrix)).decompose(tileObjects.get(t.id).position,tileObjects.get(t.id).quaternion,tileObjects.get(t.id).scale);}
  placed=tiles;
 }
 function ensureBoardCoverage(){
  const extent=Math.max(0,...placed.flatMap(t=>[Math.abs(t.matrix[0][3]),Math.abs(t.matrix[1][3])]));
  if(extent>105&&boardObjects.length===1){const a=[285.7883832488647,15,0],b=[129.9038105676658,255,0];boards([[0,0,0],a,b,[-a[0],-a[1],0],[-b[0],-b[1],0],[a[0]-b[0],a[1]-b[1],0],[b[0]-a[0],b[1]-a[1],0]]);}
 }
 function event(e){
  nodes=e.nodes;backtracks=e.backtracks;if(e.moveTotal!==undefined)moveTotal=e.moveTotal;
  if(e.type==='finished'){finished=true;running=false;sync(e.placements);lastAction=e.result==='sequence'?'Sequence complete':e.result==='no-moves'?'No paired moves found in this patch':e.result==='yes'?'Growth checkpoint reached':e.result==='no'?'This seed cannot extend under these markings':'Search budget reached';controls();render();return;}
  if(e.type==='start'){moveCount=0;sync(e.placements);lastAction=moveMode&&!moveTotal?'No paired moves found in this patch':'Ready';if(moveMode&&!moveTotal)finished=true;drawConnectors(connectorsFor(placed));ensureBoardCoverage();fitView(260);controls();return;}
  if(e.type==='flip'){
   const objects=e.ids.map(id=>tileObjects.get(id)),axis=new THREE.Vector3(...e.axis),center=new THREE.Vector3(...e.axisPoint);
   const starts=objects.map(o=>{o.updateMatrix();return o.matrix.clone();});let lift=12;
   for(const o of objects){const box=o.geometry.boundingBox;for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){const v=new THREE.Vector3(x,y,z).applyMatrix4(o.matrix).sub(center);v.addScaledVector(axis,-v.dot(axis));lift=Math.max(lift,v.length()+8);}}
   drawConnectors(connectorsFor(placed.filter(t=>!e.ids.includes(t.id))));
   inFlight={objects,starts,axis,center,lift,elapsed:0,kind:'pair',e};lastAction=e.kind==='flip'?'Flipping the pair':'Turning the pair';controls();return;
  }
  const next=new Set(e.placements.map(t=>t.id)),added=e.placements.find(t=>!tileObjects.has(t.id)),removed=placed.find(t=>!next.has(t.id));
  if(removed)drawConnectors(connectorsFor(placed.filter(t=>t.id!==removed.id)));
  if(e.type==='placement'&&added){const o=object(added.tile,added.matrix);tileObjects.set(added.id,o);const target=o.position.clone();inFlight={o,target,elapsed:0,kind:'in',e};o.position.z+=75;lastAction=e.forced?'Forced placement':'Trying a branch';}
  else if(e.type==='backtrack'&&removed){const o=tileObjects.get(removed.id);inFlight={o,target:o.position.clone(),elapsed:0,kind:'out',e};lastAction='Backtracking';}
  else{sync(e.placements);lastAction=e.type;stepping=false;}
  controls();
 }
 function pump(){
  if(inFlight||(!running&&!stepping)||finished)return;
  if(queue.length){event(queue.shift());return;}
  if(batchPending){batchPending=false;worker?.postMessage({type:'next'});}
 }
 function tick(time){
  const dt=Math.min(80,time-lastTime||0);lastTime=time;
  if(inFlight&&(running||stepping)){
   const f=inFlight;f.elapsed+=dt;const t=Math.min(1,f.elapsed/(Number($('speed').value)*(f.kind==='pair'?4.8:1)));
   if(f.kind==='pair'){
    const ease=v=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v);},rise=ease(t/.2),fall=ease((1-t)/.2),angle=Math.PI*ease((t-.2)/.6);
    const transform=new THREE.Matrix4().makeTranslation(f.center.x,f.center.y,f.center.z+f.lift*Math.min(rise,fall)).multiply(new THREE.Matrix4().makeRotationAxis(f.axis,angle)).multiply(new THREE.Matrix4().makeTranslation(-f.center.x,-f.center.y,-f.center.z));
    f.objects.forEach((o,i)=>transform.clone().multiply(f.starts[i]).decompose(o.position,o.quaternion,o.scale));
   }else{f.o.position.copy(f.target);
   if(f.kind==='in')f.o.position.z+=75*Math.pow(1-t,3);
   else{const eased=t*t*(3-2*t);f.o.position.z+=75*eased;f.o.position.x+=18*eased;}}
   render();
   if(t===1){if(f.kind==='pair'){running=false;moveCount=f.e.moveCount;lastAction=f.e.kind==='flip'?'Pair flipped':'Pair turned';if(moveCount===moveTotal){finished=true;running=false;lastAction='Sequence complete';}}sync(f.e.placements);inFlight=null;drawConnectors(connectorsFor(placed));ensureBoardCoverage();if(autoZoom)fitView(Math.max(260,distance));stepping=false;controls();render();}
  }
  pump();requestId=requestAnimationFrame(tick);
 }
 function stop(){worker?.terminate();worker=null;queue=[];batchPending=false;running=false;stepping=false;finished=false;inFlight=null;}
 function show(){
  stop();content.clear();tileObjects=new Map();boardObjects=[];connectorObjects=[];placed=[];backtracks=0;nodes=0;autoZoom=true;root.rotation.set(0,0,0);content.position.set(0,0,0);
  live=true;moveMode=$('sample').value==='live-moves';moveCount=0;moveTotal=0;lastAction=moveMode?'Growing a patch and finding moves…':'Preparing seed';
  if(live){boards([[0,0,0]]);distance=initialDistance=300;worker=new Worker(new URL(moveMode?'./search/flip-worker.js':'./search/worker.js',import.meta.url),{type:'module'});
   const activeWorker=worker;worker.onmessage=({data})=>{if(worker!==activeWorker)return;if(data.type==='error'){finished=true;running=false;lastAction=data.message;controls();return;}queue.push(...data.events);batchPending=true;if(queue[0]?.type==='start')event(queue.shift());pump();};
   worker.onerror=e=>{if(worker!==activeWorker)return;finished=true;running=false;lastAction='Search could not start. Reload to retry.';controls();};
   worker.postMessage({type:'start',mode:$('sample').value.slice(5),seed:randomSeed});
  }
  controls();resize();
 }
 const liveGroup=document.createElement('optgroup');liveGroup.label='Live tiling';for(const [id,label] of [['turtles','Turtles · live'],['trefoil','One trefoil surrounded by turtles · live'],['mixed','Turtles and trefoils · live'],['moves','Trefoil walk · live moves']]){const o=new Option(label,'live-'+id);liveGroup.append(o);}$('sample').append(liveGroup);
 $('sample').value='live-trefoil';
 $('sample').onchange=show;$('run').onclick=()=>{running=!running;stepping=false;controls();pump();};$('step').onclick=()=>{stepping=true;controls();pump();};$('restart').onclick=()=>{randomSeed++;show();};
 $('boardTransparent').onchange=()=>{for(const o of boardObjects)o.material=$('boardTransparent').checked?transparent:opaque;render();};
 $('reset').onclick=()=>{root.rotation.set(0,0,0);autoZoom=true;fitView(260);};
 addEventListener('resize',resize);let dragging=false,last;
 renderer.domElement.onpointerdown=e=>{dragging=true;last=[e.clientX,e.clientY];renderer.domElement.setPointerCapture(e.pointerId);};
 renderer.domElement.onpointermove=e=>{if(!dragging)return;root.rotation.z+=(e.clientX-last[0])*.008;root.rotation.x+=(e.clientY-last[1])*.008;last=[e.clientX,e.clientY];render();};
 renderer.domElement.onpointerup=renderer.domElement.onpointercancel=()=>{dragging=false;};
 renderer.domElement.onwheel=e=>{e.preventDefault();autoZoom=false;distance=Math.max(80,Math.min(3000,distance*Math.exp(e.deltaY*.001)));render();};
 addEventListener('pagehide',()=>{stop();cancelAnimationFrame(requestId);});show();requestId=requestAnimationFrame(tick);
}
