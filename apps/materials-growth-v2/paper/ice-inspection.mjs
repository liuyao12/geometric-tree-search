import {readSourceFrame,coverage} from './ice-inspection-data.mjs';
const root=document.querySelector('#ice-inspection');
if(root) init().catch(error=>{root.querySelector('[data-ice-status]').textContent=`Figure unavailable: ${error.message}. The result table and evidence downloads remain available.`;});
async function init(){
  const q=s=>root.querySelector(s),response=await fetch(new URL('ice-inspection.json',import.meta.url));
  if(!response.ok)throw Error('Saved-state data unavailable');const data=await response.json();
  const config=q('[data-ice-config]'),policy=q('[data-ice-policy]'),color=q('[data-ice-color]'),reveal=q('[data-ice-reveal]'),status=q('[data-ice-status]'),picked=q('[data-ice-picked]');
  const names={baseline:'GCTS baseline · partial','support-rich':'GCTS ranked · partial','connected-oracle':'Separate solver · verified full witness'};
  const colors={baseline:'#447cbd','support-rich':'#b77928','connected-oracle':'#158579'};
  for(const c of data.configurations){
    const option=new Option(`Ice ${c.phase} · ${c.split}`,c.id);config.add(option);
    for(const s of Object.values(c.states)){const totals=coverage(s,c.atoms);if(JSON.stringify(totals)!==JSON.stringify(s.totals))throw Error('Saved coverage mismatch');}
    const chart=document.createElement('div');chart.className='ice-chart-case';const button=document.createElement('button');button.type='button';button.textContent=`${c.phase} · ${c.split==='training'?'train':'developmental'}`;button.dataset.configId=c.id;button.setAttribute('aria-pressed','false');button.onclick=()=>{config.value=c.id;loadConfig();};chart.append(button);
    for(const key of Object.keys(names)){const s=c.states[key],line=document.createElement('div');line.className='ice-bar-line';line.style.setProperty('--bar',colors[key]);line.setAttribute('aria-label',`${names[key]}: ${(s.massFraction*100).toFixed(1)} percent of required t mass`);const label=document.createElement('span');label.textContent=key==='baseline'?'Baseline':key==='support-rich'?'Ranked':'Separate';const track=document.createElement('span');track.className='ice-track';const bar=document.createElement('span');bar.style.width=`${s.massFraction*100}%`;track.append(bar);const value=document.createElement('span');value.textContent=`${(s.massFraction*100).toFixed(1)}%`;line.append(label,track,value);chart.append(line);}
    q('[data-ice-chart]').append(chart);
  }
  config.value='c01400';
  let THREE,OrbitControls,renderer,scene,camera,controls,mesh,cellLines,frame,current,totals,selected=null,loadVersion=0,setupPromise;
  const host=q('[data-ice-viewport]'),cache=new Map();
  async function setup(){
    if(!setupPromise)setupPromise=setupRenderer().catch(error=>{setupPromise=null;throw error;});
    return setupPromise;
  }
  async function setupRenderer(){
    THREE=await import('../../3d-lattice-tiler/vendor/three.module.min.js');
    ({OrbitControls}=await import('../../3d-lattice-tiler/vendor/OrbitControls.js'));
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor('#102b35');host.prepend(renderer.domElement);
    renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Rotatable 3D view of source atom positions, colored by geometric coverage. Use the Rotate view button as an alternative to dragging.');
    scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(40,1,.1,1000);controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.addEventListener('change',render);
    scene.add(new THREE.HemisphereLight(0xd5f2ff,0x344855,2.2));const light=new THREE.DirectionalLight(0xffffff,2.8);light.position.set(12,20,18);scene.add(light);
    new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}).observe(host);
    const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down;
    renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
    renderer.domElement.addEventListener('pointerup',e=>{if(!mesh||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);selected=ray.intersectObject(mesh)[0]?.instanceId??null;updateAtoms();});
  }
  function render(){if(renderer&&scene&&camera)renderer.render(scene,camera);}
  function viewHome(){if(!frame||!camera)return;const box=new THREE.Box3().setFromPoints(frame.atoms.map(a=>new THREE.Vector3(...a.position))),center=box.getCenter(new THREE.Vector3()),span=box.getSize(new THREE.Vector3()).length();camera.position.copy(center).add(new THREE.Vector3(1,.72,1.15).normalize().multiplyScalar(span*1.6));controls.target.copy(center);controls.update();render();}
  function buildAtoms(){
    if(mesh){scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}
    mesh=new THREE.InstancedMesh(new THREE.SphereGeometry(1,18,12),new THREE.MeshStandardMaterial({roughness:.4,metalness:.05}),frame.atoms.length);scene.add(mesh);
    if(cellLines){scene.remove(cellLines);cellLines.geometry.dispose();cellLines.material.dispose();}
    const vertices=[];for(let i=0;i<8;i++){const v=[0,0,0];for(let j=0;j<3;j++)if(i&(1<<j))for(let k=0;k<3;k++)v[k]+=frame.cell[j][k];vertices.push(v);}
    const edges=[];for(let i=0;i<8;i++)for(let j=0;j<3;j++)if(!(i&(1<<j)))edges.push(...vertices[i],...vertices[i|(1<<j)]);
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(edges,3));cellLines=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x62828d,transparent:true,opacity:.6}));scene.add(cellLines);viewHome();
  }
  function updateAtoms(){
    if(!frame||!mesh)return;const state=current.states[policy.value],count=Number(reveal.value);totals=coverage(state,current.atoms,count);const dummy=new THREE.Object3D(),tint=new THREE.Color();
    frame.atoms.forEach((a,i)=>{const t=totals[i];let radius=a.species==='H'?.19:.29;radius*=t===0?.6:1;if(i===selected)radius*=1.35;dummy.position.set(...a.position);dummy.scale.setScalar(radius);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);tint.set(i===selected?'#58c4ff':t===0?'#49636d':color.value==='element'?(a.species==='O'?'#f15461':'#f5f3e9'):t===1?'#f5b44a':'#4cdbc0');mesh.setColorAt(i,tint);});
    mesh.instanceMatrix.needsUpdate=true;mesh.instanceColor.needsUpdate=true;
    const full=totals.filter(t=>t===2).length,half=totals.filter(t=>t===1).length,empty=totals.filter(t=>t===0).length;
    q('[data-ice-count]').textContent=`${count} / ${state.supports.length} saved placements`;
    status.textContent=`${full} fully filled · ${half} half-filled · ${empty} untouched atom sites. ${count===state.supports.length?`${state.commonValues} verified common marking values in this saved final state.`:'Partial reveal only; common markings were verified for the saved final state.'}`;
    picked.textContent=selected===null?'Click an atom to inspect its t-value.':`Atom ${selected} · ${frame.atoms[selected].species} · t = ${totals[selected]/2} · ${totals[selected]} displayed motif contributions of ½.`;
    q('[data-ice-tag]').textContent=`Ice ${current.phase} · ${current.split} · ${names[policy.value]}`;
    q('[data-ice-color-legend]').textContent=color.value==='coverage'?'Teal: t = 1 · amber: t = ½ · small gray: t = 0':'O: red · H: ivory · small gray: t = 0';render();
  }
  function updateState(){if(!current)return;const state=current.states[policy.value];reveal.max=state.supports.length;reveal.value=state.supports.length;selected=null;updateAtoms();}
  async function loadConfig(){
    const version=++loadVersion;current=data.configurations.find(c=>c.id===config.value);frame=null;reveal.disabled=true;status.textContent='Loading and hash-checking the first frame from the authors’ source…';q('[data-ice-retry]').hidden=true;host.setAttribute('aria-busy','true');q('[data-ice-tag]').textContent='Loading source coordinates…';
    if(mesh)mesh.visible=false;if(cellLines)cellLines.visible=false;
    for(const button of root.querySelectorAll('[data-config-id]'))button.setAttribute('aria-pressed',String(button.dataset.configId===current.id));
    try{const c=current;await setup();if(!cache.has(c.id))cache.set(c.id,readSourceFrame(c));const loaded=await cache.get(c.id);if(version!==loadVersion)return;frame=loaded;buildAtoms();reveal.disabled=false;updateState();}
    catch(error){if(version!==loadVersion)return;cache.delete(current.id);status.textContent=`3D scene unavailable: ${error.message}. The comparison chart remains usable.`;q('[data-ice-tag]').textContent='Source or WebGL unavailable';q('[data-ice-retry]').hidden=false;}
    finally{if(version===loadVersion)host.setAttribute('aria-busy','false');}
  }
  config.onchange=loadConfig;policy.onchange=updateState;color.onchange=updateAtoms;reveal.oninput=updateAtoms;q('[data-ice-retry]').onclick=loadConfig;
  q('[data-ice-reset]').onclick=viewHome;q('[data-ice-rotate]').onclick=()=>{if(!camera||!frame)return;camera.position.sub(controls.target).applyAxisAngle(new THREE.Vector3(0,1,0),Math.PI/6).add(controls.target);controls.update();render();};
  await loadConfig();
}
