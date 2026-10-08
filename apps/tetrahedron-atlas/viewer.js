import * as THREE from './vendor/three.module.min.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {vertices,maxStage,stageWidth,canonicalQuaternion,orientationRepresentative,orientationDistance,axisAnglePoint,compressionState,anchoredPatch} from './model.js';

const $=id=>document.getElementById(id);
const colours=[0x68dac4,0x6ba7de,0xd7b575,0xa990d4,0xe1927f,0x87ba93];
export function createPackingViewer(data,getMode) {
  const host=$('canvas-wrap'),plot=$('orientation-plot');
  const scene=new THREE.Scene();scene.background=new THREE.Color('#08151d');
  scene.add(new THREE.HemisphereLight(0xd7faff,0x234254,2.0));
  const light=new THREE.DirectionalLight(0xffffff,2.0);light.position.set(8,15,12);scene.add(light);
  const camera=new THREE.PerspectiveCamera(38,1,.002,4000);
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.localClippingEnabled=true;
  renderer.domElement.setAttribute('aria-label','Packing growing around a fixed tetrahedron. Camera controls are below the scene.');host.appendChild(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.1;controls.maxDistance=2000;
  const orientationScene=new THREE.Scene(),orientationCamera=new THREE.PerspectiveCamera(34,1,.01,20);
  orientationCamera.position.set(2.7,1.9,2.5);
  const orientationRenderer=new THREE.WebGLRenderer({antialias:true,alpha:true});orientationRenderer.setPixelRatio(Math.min(devicePixelRatio,2));orientationRenderer.setClearColor(0,0);plot.appendChild(orientationRenderer.domElement);
  const orientationControls=new OrbitControls(orientationCamera,orientationRenderer.domElement);orientationControls.enableDamping=true;orientationControls.enablePan=false;orientationControls.minDistance=2.5;orientationControls.maxDistance=7;
  const sphere=new THREE.Mesh(new THREE.SphereGeometry(1,32,20),new THREE.MeshBasicMaterial({color:0xb9ded7,wireframe:true,transparent:true,opacity:.11}));orientationScene.add(sphere);
  for(const [dir,col] of [[new THREE.Vector3(1,0,0),0xe1927f],[new THREE.Vector3(0,1,0),0x68dac4],[new THREE.Vector3(0,0,1),0x6ba7de]])orientationScene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([dir.clone().negate(),dir]),new THREE.LineBasicMaterial({color:col,transparent:true,opacity:.4})));
  const dotCanvas=document.createElement('canvas');dotCanvas.width=32;dotCanvas.height=32;const dotContext=dotCanvas.getContext('2d');dotContext.fillStyle='white';dotContext.beginPath();dotContext.arc(16,16,14,0,2*Math.PI);dotContext.fill();
  const pointGeometry=new THREE.BufferGeometry(),pointMaterial=new THREE.PointsMaterial({size:6,sizeAttenuation:false,vertexColors:true,depthTest:false,map:new THREE.CanvasTexture(dotCanvas),transparent:true,alphaTest:.2});
  const points=new THREE.Points(pointGeometry,pointMaterial);orientationScene.add(points);
  const selectionMarker=new THREE.Mesh(new THREE.SphereGeometry(.09,12,8),new THREE.MeshBasicMaterial({color:0xf0d093,wireframe:true,depthTest:false}));selectionMarker.visible=false;orientationScene.add(selectionMarker);
  const flat=[];for(const face of [[0,2,1],[0,1,3],[0,3,2],[1,2,3]])for(const index of face)flat.push(...vertices[index]);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(flat,3));geometry.computeVertexNormals();
  const outlineGeometry=new THREE.EdgesGeometry(geometry);
  const anchorOutline=new THREE.LineSegments(outlineGeometry,new THREE.LineBasicMaterial({color:0xf5d086,depthTest:false}));anchorOutline.renderOrder=2;scene.add(anchorOutline);
  const patchGroup=new THREE.Group();scene.add(patchGroup);
  const cellOutline=new THREE.LineSegments(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:0xf0d093,transparent:true,opacity:.55}));scene.add(cellOutline);
  const clip=[new THREE.Plane(new THREE.Vector3(0,1,0),1000),new THREE.Plane(new THREE.Vector3(0,-1,0),1000)];
  let active=false,mode,stage=1,assembly=82,progress=1,patch,cell,meshes=[],classes=[],prototypeClasses=[],hidden=new Set(),selected=null,pointKeys=[],counts=[],animation=null,paused=false,cameraAnimation=null,lastTick=0,radius=10;
  const matrix=new THREE.Matrix4(),pos=new THREE.Vector3(),scale=new THREE.Vector3(),tempColour=new THREE.Color();
  const quotient=()=>$('orientation-convention').value==='tetra';
  const degreeRadius=()=>Number($('angular-radius').value)*Math.PI/180;
  const api={activate,pause};

  function createClasses(){
    const endpoint=compressionState(mode,1,data),inverse=endpoint.particles[0].quaternion.clone().invert();classes=[];prototypeClasses=[];hidden.clear();selected=null;
    for(const p of endpoint.particles){const q=canonicalQuaternion(inverse.clone().multiply(p.quaternion));let index=classes.findIndex(c=>orientationDistance(q,c.quaternion,quotient())<1e-7);if(index<0){index=classes.length;const rep=orientationRepresentative(q,quotient());const colour=new THREE.Color().setHSL((.48+rep.x*.17+rep.y*.31+rep.z*.23)%1,.52,.62);classes.push({quaternion:q,point:axisAnglePoint(rep),colour});}prototypeClasses.push(index);}
    $('orientation-select').replaceChildren(new Option('Select a dot or orientation',''),...classes.map((_,i)=>new Option(`Orientation ${i+1}`,String(i))));
    $('orientation-note').textContent=quotient()?'Representatives modulo the 12 proper tetrahedral symmetries. Small differences in the published poses are retained.':'Rotations of labelled vertex frames in the full axis–angle ball. Vertex labels distinguish physically equivalent tetrahedra.';
  }
  function selectedSet(){if(selected===null)return new Set();return new Set(classes.map((c,i)=>orientationDistance(classes[selected].quaternion,c.quaternion,quotient())<=degreeRadius()+1e-7?i:-1).filter(i=>i>=0));}
  function updateOrientationPlot(){
    counts=classes.map(()=>0);for(const p of patch.particles)counts[prototypeClasses[p.prototype]]++;
    const selectedIds=selectedSet(),positions=[],cs=[];pointKeys=[];
    for(let i=0;i<classes.length;i++){if(!counts[i])continue;pointKeys.push(i);positions.push(...classes[i].point.toArray());const col=hidden.has(i)?new THREE.Color('#415059'):classes[i].colour.clone();if(selectedIds.has(i))col.set('#ffe3a4');cs.push(...col.toArray());}
    pointGeometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));pointGeometry.setAttribute('color',new THREE.Float32BufferAttribute(cs,3));pointGeometry.computeBoundingSphere();
    selectionMarker.visible=selected!==null && counts[selected]>0;if(selectionMarker.visible)selectionMarker.position.copy(classes[selected].point);
    let visible=counts.reduce((n,c,i)=>n+(hidden.has(i)?0:c),0);let match=[...selectedIds].reduce((n,i)=>n+counts[i],0);
    const angular=Number($('angular-radius').value);$('angular-value').textContent=`${angular} degrees`;
    $('orientation-readout').textContent=`${counts.filter(Boolean).length} ${counts.filter(Boolean).length===1?'orientation':'orientations'} present · ${visible.toLocaleString()} / ${patch.particles.length.toLocaleString()} tetrahedra enabled${selected===null?'':` · selected neighborhood: ${match.toLocaleString()}`}. Counts precede slicing.`;
    for(let i=0;i<classes.length;i++)$('orientation-select').options[i+1].textContent=`Orientation ${i+1} · ${counts[i].toLocaleString()}${hidden.has(i)?' · hidden':''}`;
    for(const id of ['isolate-orientation','hide-orientation','show-orientation'])$(id).disabled=selected===null;
    plot.setAttribute('aria-label',`Axis–angle orientation ball with ${counts.filter(Boolean).length} orientations present. Click a dot or use the selected orientation menu.`);
  }
  function disposePatch(){for(const mesh of meshes){patchGroup.remove(mesh);mesh.material.dispose();mesh.dispose();}meshes=[];}
  function rebuild(){
    cell=compressionState(mode,progress,data);patch=anchoredPatch(cell,stage,assembly);disposePatch();
    const byShell=new Map();for(const p of patch.particles){if(!byShell.has(p.shell))byShell.set(p.shell,[]);byShell.get(p.shell).push(p);}
    for(const [shell,particles] of byShell){const transparent=$('transparent').checked;const material=new THREE.MeshStandardMaterial({roughness:.6,metalness:.03,side:THREE.DoubleSide,clippingPlanes:clip,transparent,opacity:transparent?.16:1,depthWrite:!transparent});const mesh=new THREE.InstancedMesh(geometry,material,particles.length);mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);mesh.userData.particles=particles;mesh.userData.shell=shell;mesh.frustumCulled=false;patchGroup.add(mesh);meshes.push(mesh);}
    updateMatrices();updateOrientationPlot();updateReadouts();resize();
  }
  function updateMatrices(){
    cell=compressionState(mode,progress,data);const inverse=cell.particles[0].quaternion.clone().invert(),first=cell.particles[0].center;
    const stackAxis=cell.basis[1].clone().applyQuaternion(inverse).normalize();clip[0].normal.copy(stackAxis);clip[1].normal.copy(stackAxis).negate();
    const uniform=Number($('shrink').value),selectedIds=selectedSet();radius=Math.sqrt(3);
    let minY=Infinity,maxY=-Infinity;
    for(const mesh of meshes){let index=0;for(const p of mesh.userData.particles){const proto=cell.particles[p.prototype];pos.copy(proto.center).addScaledVector(cell.basis[0],p.cell[0]).addScaledVector(cell.basis[1],p.cell[1]).addScaledVector(cell.basis[2],p.cell[2]).sub(first).multiplyScalar(cell.dilation).applyQuaternion(inverse);radius=Math.max(radius,pos.length()+Math.sqrt(3));const height=pos.dot(stackAxis);minY=Math.min(minY,height-Math.sqrt(3));maxY=Math.max(maxY,height+Math.sqrt(3));
      const cls=prototypeClasses[p.prototype],size=hidden.has(cls)?0:uniform;scale.setScalar(size);matrix.compose(pos,p.quaternion,scale);mesh.setMatrixAt(index,matrix);
      if($('colour').value==='shell')tempColour.setHex(colours[p.shell%colours.length]);else if($('colour').value==='height')tempColour.setHSL((.5+height/(stageWidth(stage)*cell.basis[1].length()*cell.dilation)*.3+1)%1,.55,.62);else tempColour.copy(classes[cls].colour);
      if(selectedIds.has(cls))tempColour.lerp(new THREE.Color('#fff2cc'),.5);mesh.setColorAt(index++,tempColour);
    }mesh.instanceMatrix.needsUpdate=true;if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;}
    const half=Math.max(Math.abs(minY),Math.abs(maxY))*Number($('slice').value);clip[0].constant=half;clip[1].constant=half;
    anchorOutline.scale.setScalar(uniform);updateCellOutline(inverse,first);updateCompressionReadout();
  }
  function updateCellOutline(inverse,first){
    cellOutline.visible=$('cell').checked && stage>0;const corners=[];
    for(let z=0;z<8;z++){const p=new THREE.Vector3();for(let bit=0;bit<3;bit++)p.addScaledVector(cell.basis[bit],(z&(1<<bit))?.5:-.5);corners.push(p.sub(first).multiplyScalar(cell.dilation).applyQuaternion(inverse));}
    const arr=[];for(let x=0;x<8;x++)for(const bit of [1,2,4])if(!(x&bit))arr.push(...corners[x].toArray(),...corners[x|bit].toArray());cellOutline.geometry.dispose();cellOutline.geometry=new THREE.BufferGeometry();cellOutline.geometry.setAttribute('position',new THREE.Float32BufferAttribute(arr,3));
  }
  function updateCompressionReadout(){
    $('compression').value=(progress*100).toFixed(1);$('compression-value').textContent=`${(progress*100).toFixed(1)}%`;
    $('path-density').textContent=`${(cell.density*100).toFixed(4)}% full periodic packing fraction`;
    $('density').textContent=mode==='approx'?`${(cell.density*100).toFixed(4)}% along displayed path`:`${(cell.density*100).toFixed(4)}% along displayed path`;
  }
  function updateReadouts(){
    $('stage-number').textContent=String(stage);$('patch-count').textContent=`${patch.particles.length.toLocaleString()} ${patch.particles.length===1?'tetrahedron':'tetrahedra'}`;
    const n=stageWidth(stage),full=mode==='approx'?82:4;
    $('count').textContent=stage===0?'One fixed reference tetrahedron':`${patch.particles.length.toLocaleString()} tetrahedra · ${n**3} ${n===1?'cell':'cells'}`;
    $('assembly').max=String(full);$('assembly').value=String(assembly);$('assembly').disabled=stage!==1;$('assembly-value').textContent=`${stage===0?1:assembly} / ${full}`;
    $('build-back').disabled=stage===0;$('build-next').disabled=stage===maxStage;
    $('build-next').textContent=stage===0?'Build the primitive cell ↗':stage===maxStage?'Largest patch shown':stage===1 && assembly<full?'Complete primitive cell ↗':'Expand one shell ↗';
    $('growth-description').textContent=stage===0?'A single tetrahedron, pinned at the origin. Build its primitive cell next.':stage===1?'Reveal the primitive cell particle by particle. Source row order is an assembly illustration, not a physical growth sequence.':`Cell shell ${stage-1}: ${n} cells along each basis direction. The reference tetrahedron keeps its position, size and orientation.`;
  }
  function cameraDistance(){const angle=THREE.MathUtils.degToRad(camera.fov/2);return radius/Math.sin(angle)*1.08/Math.min(1,camera.aspect);}
  function fit(animated=false){const distance=cameraDistance();const dir=camera.position.clone().sub(controls.target).normalize();if(!dir.lengthSq())dir.set(.65,.6,.8).normalize();const target=dir.multiplyScalar(distance);controls.target.set(0,0,0);if(animated&&!matchMedia('(prefers-reduced-motion: reduce)').matches)cameraAnimation={from:camera.position.clone(),to:target,start:performance.now()};else {camera.position.copy(target);cameraAnimation=null;}controls.update();}
  function view(name){camera.up.set(0,1,0);const distance=cameraDistance();controls.target.set(0,0,0);if(name==='top'){const axis=cell.basis[1].clone().applyQuaternion(cell.particles[0].quaternion.clone().invert()).normalize();camera.up.set(0,0,-1);camera.position.copy(axis.multiplyScalar(distance));}else if(name==='side')camera.position.set(distance,0,0);else camera.position.set(.65,.6,.8).normalize().multiplyScalar(distance);cameraAnimation=null;controls.update();}
  function stopAnimation(){animation=null;paused=false;$('play-compression').textContent='▶ Animate compression';}
  function pause(){active=false;stopAnimation();cameraAnimation=null;}
  function activate(){
    const next=getMode();if(mode!==next){mode=next;stage=1;assembly=mode==='approx'?82:4;progress=1;stopAnimation();createClasses();}
    active=true;rebuild();view('oblique');
    $('family-start').hidden=mode!=='dimer';$('top').textContent=mode==='approx'?'Along stack':'Along cell axis';$('colour').options[2].textContent=mode==='approx'?'Height along stack':'Height along cell axis';
    $('path-name').textContent=mode==='approx'?'Expanded reference → published endpoint':'Expanded reference → earlier dimer → record';
    $('compression-note').textContent=mode==='approx'?'Illustrative uniform motion of particle centres; tetrahedra keep their size and orientation. This is not the original ideal construction or a Monte Carlo replay. Endpoint: published 82-particle coordinates.':'First half: close added spacing around the earlier dimer packing. Second half: continuous deformation inside the paper’s proved packing family, from 85.4701% to 85.6348%. Particle orientations stay fixed; no recorded simulation is implied.';
    if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise().catch(()=>{});
  }
  function setStage(next){stopAnimation();if(next<0||next>maxStage)return;stage=next;assembly=mode==='approx'?82:4;rebuild();fit(true);}
  $('build-back').onclick=()=>setStage(stage-1);
  $('build-next').onclick=()=>{if(stage===1 && assembly<cell.particles.length){assembly=cell.particles.length;rebuild();return;}setStage(stage+1);};
  $('seed').onclick=()=>setStage(0);
  $('assembly').oninput=()=>{stopAnimation();assembly=Number($('assembly').value);rebuild();};
  $('compression').oninput=()=>{stopAnimation();progress=Number($('compression').value)/100;updateMatrices();};
  $('play-compression').onclick=()=>{if(animation){animation=null;paused=true;$('play-compression').textContent='▶ Resume compression';return;}if(!paused){progress=0;updateMatrices();fit();}paused=false;animation={start:performance.now(),from:progress};$('play-compression').textContent='Ⅱ Pause compression';};
  $('family-start').onclick=()=>{stopAnimation();progress=.5;updateMatrices();fit(true);};
  $('raw').onclick=()=>{stopAnimation();progress=0;updateMatrices();fit(true);};$('packed').onclick=()=>{stopAnimation();progress=1;updateMatrices();fit(true);};
  $('orientation-convention').onchange=()=>{createClasses();rebuild();};
  function selectClass(index){selected=index;$('orientation-select').value=index===null?'':String(index);updateOrientationPlot();updateMatrices();}
  $('orientation-select').onchange=()=>selectClass($('orientation-select').value===''?null:Number($('orientation-select').value));
  $('angular-radius').oninput=()=>{updateOrientationPlot();updateMatrices();};
  $('isolate-orientation').onclick=()=>{const ids=selectedSet();hidden=new Set(classes.map((_,i)=>i).filter(i=>!ids.has(i)));updateMatrices();updateOrientationPlot();};
  $('hide-orientation').onclick=()=>{for(const i of selectedSet())hidden.add(i);updateMatrices();updateOrientationPlot();};
  $('show-orientation').onclick=()=>{for(const i of selectedSet())hidden.delete(i);updateMatrices();updateOrientationPlot();};
  $('show-all').onclick=()=>{hidden.clear();selected=null;$('orientation-select').value='';updateMatrices();updateOrientationPlot();};
  const raycaster=new THREE.Raycaster();raycaster.params.Points.threshold=.09;let down=null;
  orientationRenderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
  orientationRenderer.domElement.addEventListener('pointerup',e=>{if(!down)return;const d=Math.hypot(e.clientX-down[0],e.clientY-down[1]);down=null;if(d>5)return;const r=orientationRenderer.domElement.getBoundingClientRect();raycaster.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),orientationCamera);const hit=raycaster.intersectObject(points)[0];selectClass(hit?pointKeys[hit.index]:null);});
  for(const id of ['colour','cell'])$(id).onchange=updateMatrices;for(const id of ['shrink','slice'])$(id).oninput=updateMatrices;$('transparent').onchange=rebuild;
  for(const id of ['oblique','top','side'])$(id).onclick=()=>view(id);$('reset').onclick=()=>fit(true);
  function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();const pw=plot.clientWidth,ph=plot.clientHeight;if(pw&&ph){orientationRenderer.setSize(pw,ph,false);orientationCamera.aspect=pw/ph;orientationCamera.updateProjectionMatrix();}}
  new ResizeObserver(resize).observe(host);new ResizeObserver(resize).observe(plot);
  renderer.setAnimationLoop(time=>{
    if(!active)return;
    if(animation && time-lastTick>30){lastTick=time;progress=Math.min(1,animation.from+(performance.now()-animation.start)/6500);updateMatrices();if(progress===1)stopAnimation();}
    if(cameraAnimation){const t=Math.min(1,(performance.now()-cameraAnimation.start)/750),s=t*t*(3-2*t);camera.position.lerpVectors(cameraAnimation.from,cameraAnimation.to,s);if(t===1)cameraAnimation=null;}
    controls.update();orientationControls.update();renderer.render(scene,camera);orientationRenderer.render(orientationScene,orientationCamera);
  });
  return api;
}
