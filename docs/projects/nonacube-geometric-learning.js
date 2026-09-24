import * as THREE from 'three';
import {OrbitControls} from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';
const $=id=>document.getElementById(id);
window.addEventListener('error',e=>{$('error').textContent=e.message;});
window.addEventListener('unhandledrejection',e=>{$('error').textContent=e.reason?.message||String(e.reason);});
const response=await fetch('../../data/nonacube-geometric-learning/examples.json');if(!response.ok)throw Error(`Patterns: ${response.status}`);
const examples=(await response.json()).sort((a,b)=>a.roles-b.roles);
const host=$('scene'),scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(42,1,.1,200);camera.position.set(17,14,18);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xe3f3ff,0x435366,2.7));const light=new THREE.DirectionalLight(0xffffff,2.5);light.position.set(8,15,10);scene.add(light);
const group=new THREE.Group();scene.add(group);const box=new THREE.BoxGeometry(.94,.94,.94),gray=new THREE.MeshStandardMaterial({color:'#8d9da8',transparent:true,opacity:.42});
const colors=Array.from({length:43},(_,i)=>new THREE.Color().setHSL((.43+i*.6180339)%1,.58,.65));
const materials=colors.map(color=>new THREE.MeshStandardMaterial({color,roughness:.7}));
const anchor=new THREE.Mesh(new THREE.SphereGeometry(.2,14,12),new THREE.MeshBasicMaterial({color:'#ff90b6',depthTest:false}));anchor.renderOrder=4;scene.add(anchor);
let current,selected=[];
function tile([oi,c],material){const axes=[[0,1],[0,2],[1,2]][oi],voxels=[[0,0,0]];for(const axis of axes)for(const n of [-2,-1,1,2]){const v=[0,0,0];v[axis]=n;voxels.push(v);}for(const v of voxels){const mesh=new THREE.Mesh(box,material);mesh.position.set(...v.map((x,i)=>x+c[i]));group.add(mesh);}}
function render(){group.clear();tile([0,[0,0,0]],gray);current.placements.forEach((s,i)=>{if(selected[i])tile(s,materials[i]);});
 const count=selected.filter(Boolean).length,missing=selected.indexOf(false),conflict=missing<0;
 $('status').textContent=conflict?'This channel contradicts':'This channel is compatible';$('status').style.color=conflict?'#ed9eaa':'#7edbc3';
 $('equation').textContent=`${count} of ${current.roles} coordinates forced to zero.`;
 $('witness').textContent=conflict?'All coordinates are zero, but their sum must be one.':`Set coordinate ${missing+1} to one and every other coordinate to zero.`;
 $('pattern-info').textContent=`Learned pattern ${current.learnedIndex.toLocaleString()}. The gray root remains fixed. Toggle any subset of the colored roles.`;
 for(let i=0;i<selected.length;i++)$(`role-${i}`).checked=selected[i];
 window.nonacubeGeometricLearning={roles:current.roles,selected:count,conflict,learnedIndex:current.learnedIndex};
}
function choose(){current=examples[Number($('pattern').value)];selected=current.placements.map(()=>true);$('roles').replaceChildren();selected.forEach((_,i)=>{const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.id=`role-${i}`;input.checked=true;input.onchange=()=>{selected[i]=input.checked;render();};label.style.borderColor=`#${colors[i].getHexString()}`;label.append(input,document.createTextNode(String(i+1)));$('roles').append(label);});
 const bounds=new THREE.Box3();for(const [,c] of current.placements)bounds.expandByPoint(new THREE.Vector3(...c));bounds.expandByPoint(new THREE.Vector3());const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3()).length();controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,.8,1.1).normalize().multiplyScalar(Math.max(18,size*1.7)));render();}
examples.forEach((p,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${p.roles} roles · pattern ${p.learnedIndex.toLocaleString()}`;$('pattern').append(option);});
$('pattern').value=String(examples.findIndex(p=>p.roles===5));$('pattern').onchange=choose;
$('all').onclick=()=>{selected.fill(true);render();};$('none').onclick=()=>{selected.fill(false);render();};$('remove').onclick=()=>{selected.fill(true);selected[selected.length-1]=false;render();};
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);
function animate(){controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}choose();animate();
