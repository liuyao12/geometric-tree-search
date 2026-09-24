import * as THREE from 'three';
import {OrbitControls} from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';
import {POINT_GROUP,transform,transformedPlacement,compilePatchConstraints,ConstraintSection} from '../../apps/3d-lattice-tiler/patch-constraint-markings.js';
const $=id=>document.getElementById(id),colors=['#6dd5c1','#eba85f','#b493eb'];
window.addEventListener('error',event=>{$('error').textContent=`The interactive view could not load: ${event.message}`;});
window.addEventListener('unhandledrejection',event=>{$('error').textContent=`The interactive view could not load: ${event.reason?.message||event.reason}`;});
const data=await fetch('../../data/nonacube-patch-constraints/study.json').then(r=>{if(!r.ok)throw Error(`Study data: ${r.status}`);return r.json();});
const marking=compilePatchConstraints(data.fixed,data.deadPoint,data.marking);
function cells([oi,t]){const result=[t];for(const axis of [[0,1],[0,2],[1,2]][oi])for(const d of [-2,-1,1,2]){const p=[...t];p[axis]+=d;result.push(p);}return result;}
const host=$('scene'),scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(40,1,.1,200);camera.position.set(12,10,14);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(-1,-1,-.5);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xe3f3ff,0x435366,2.7));const light=new THREE.DirectionalLight(0xffffff,2.5);light.position.set(8,15,10);scene.add(light);
const group=new THREE.Group();scene.add(group);const box=new THREE.BoxGeometry(.95,.95,.95);
const baseMaterials=colors.map(c=>new THREE.MeshStandardMaterial({color:c,roughness:.7}));
const ghost=new THREE.MeshStandardMaterial({color:'#bcc9d7',transparent:true,opacity:.2,depthWrite:false});
const trial=new THREE.MeshStandardMaterial({color:'#ee8795',transparent:true,opacity:.38,depthWrite:false});
const gap=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1.05,1.05,1.05)),new THREE.LineBasicMaterial({color:'#ff9aa9',depthTest:false}));gap.renderOrder=2;scene.add(gap);
const signName=g=>{let inversions=0;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)inversions+=g.perm[i]>g.perm[j];return ((-1)**inversions*g.sign.reduce((a,b)=>a*b,1))>0?'Rotation':'Reflection';};
POINT_GROUP.forEach((g,i)=>{const opt=document.createElement('option');opt.value=i;opt.textContent=`${i+1} · ${signName(g)}${i===0?' (identity)':''}`;$('symmetry').append(opt);});
data.coverBlockers.forEach((c,i)=>{const opt=document.createElement('option');opt.value=i;opt.textContent=`Candidate ${i+1} · blocked by ${c.roles.map(r=>'ABC'[r]).join(', ')}`;$('candidate').append(opt);});
function mask(){return [0,1,2].reduce((s,i)=>s|($(`role-${i}`).checked?1<<i:0),0);}
function setMask(s){for(let i=0;i<3;i++)$(`role-${i}`).checked=!!(s&(1<<i));render();}
function addTile(s,material,g){for(const p of cells(transformedPlacement(g,s))){const mesh=new THREE.Mesh(box,material);mesh.position.set(...p);group.add(mesh);}}
function render(){
  group.clear();const chosen=mask(),gi=Number($('symmetry').value),g=POINT_GROUP[gi],section=new ConstraintSection(marking);
  let common=marking.full;data.fixed.forEach((s,i)=>{if(chosen&(1<<i)){common&=data.marking.allowedMasks[i];section.push(transformedPlacement(g,s));addTile(s,baseMaterials[i],g);}});
  const conflicts=section.conflicts();gap.position.set(...transform(g,data.deadPoint));
  for(let i=0;i<3;i++)$(`state-${i}`).classList.toggle('excluded',!(common&(1<<i)));
  $('marking-state').textContent=conflicts.length?'Contradiction':'Compatible';$('marking-state').style.color=conflicts.length?'#f3919d':'#7bdcc1';
  $('marking-detail').textContent=conflicts.length?'No common fiber value remains. The full triple is flagged.':`${[0,1,2].filter(i=>common&(1<<i)).length} shared state(s) remain. This proper subset passes.`;
  const available=data.coverBlockers.filter(c=>!c.roles.some(r=>chosen&(1<<r))).length;
  $('geometry-state').textContent=`${available} of 27 placements covering the outlined cell avoid the selected tiles.`;
  const candidate=Number($('candidate').value);
  if(candidate>=0){const c=data.coverBlockers[candidate];addTile(c.placement,trial,g);const blockers=c.roles.filter(r=>chosen&(1<<r));$('candidate-state').textContent=blockers.length?`Candidate ${candidate+1} overlaps ${blockers.map(r=>'ABC'[r]).join(', ')}.`:`Candidate ${candidate+1} avoids the selected core. Further completion still needs checking.`;}
  else $('candidate-state').textContent='';
  const roles=[0,1,2].filter(i=>chosen&(1<<i));$('witness').disabled=roles.length!==2;
  if(roles.length!==2)$('witness').checked=false;
  if($('witness').checked){const pair=data.pairs.find(p=>p.roles.every(r=>chosen&(1<<r)));for(const s of pair.outer)addTile(s,ghost,g);}
  window.nonacubePatchConstraints={mask:chosen,symmetry:gi,contradiction:!!conflicts.length,available,common,witness:$('witness').checked};
}
for(let s=0;s<8;s++){
  const row=document.createElement('tr'),roles=[0,1,2].filter(i=>s&(1<<i)),label=roles.map(i=>'ABC'[i]).join(' + ')||'Empty';
  const values=[label,s===7?'Rejected':'Accepted',s===7?'All 27 covers blocked':roles.length===2?'Verified full surround':roles.length===1?'Surround inherited from a pair witness':'No fixed obstruction'];
  values.forEach((v,i)=>{const cell=document.createElement('td');cell.textContent=v;if(i===1)cell.className=s===7?'bad':'ok';row.append(cell);});
  const cell=document.createElement('td'),button=document.createElement('button');button.textContent='View';button.setAttribute('aria-label',`View ${label}`);button.onclick=()=>setMask(s);cell.append(button);row.append(cell);$('subset-table').querySelector('tbody').append(row);
}
for(const id of ['role-0','role-1','role-2','symmetry','candidate','witness'])$(id).addEventListener('change',render);
$('all').onclick=()=>setMask(7);$('none').onclick=()=>setMask(0);
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);
function animate(){controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}render();animate();
