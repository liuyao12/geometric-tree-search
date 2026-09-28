import * as THREE from 'three';
import {OrbitControls} from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';
const $=id=>document.getElementById(id);
window.addEventListener('error',e=>{$('error').textContent=e.message;});
window.addEventListener('unhandledrejection',e=>{$('error').textContent=e.reason?.message??String(e.reason);});
const [tile,receipt]=await Promise.all(['tile.json','verification.json'].map(async name=>{
 const r=await fetch('../../data/bent-six-arm/'+name);if(!r.ok)throw Error(`${name}: ${r.status}`);return r.json();
}));
$('shape-facts').textContent=`${tile.voxels.length} cubes · six congruent arms`;
$('proof-time').textContent=`Verified in ${receipt.proofCheckSeconds.toFixed(2)} seconds`;
const host=$('scene'),scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
const camera=new THREE.PerspectiveCamera(40,1,.1,100),renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xf0f8ff,0x465568,2.6));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(5,9,7);scene.add(light);
const cube=new THREE.BoxGeometry(.98,.98,.98),edge=new THREE.EdgesGeometry(cube),line=new THREE.LineBasicMaterial({color:0x182739});
const blue=new THREE.MeshStandardMaterial({color:0x669fe5,roughness:.65}),gold=new THREE.MeshStandardMaterial({color:0xf1c264,roughness:.65});
for(const v of tile.voxels){const root=v.every(x=>x===0),mesh=new THREE.Mesh(cube,root?gold:blue);mesh.position.set(...v);mesh.add(new THREE.LineSegments(edge,line));scene.add(mesh);}
function reset(){camera.position.set(9,7,11);controls.target.set(0,0,0);controls.update();}
$('reset').onclick=reset;reset();
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
window.bentSixArm={voxelCount:tile.voxels.length,orientations:receipt.properOrientations,proofVerified:receipt.proofVerified};
