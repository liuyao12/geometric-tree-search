import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {dimensions as d,bodyMesh,rotorMesh,pinMesh} from './model.js';
const host=document.getElementById('scene'),section=document.getElementById('section'),slider=document.getElementById('fold');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#e9efe9');
const camera=new THREE.PerspectiveCamera(35,1,.1,600);camera.up.set(0,0,1);camera.position.set(74,-90,73);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(-12,20,-13);controls.enableDamping=true;controls.minDistance=40;controls.maxDistance=220;
scene.add(new THREE.HemisphereLight(0xffffff,0x70867a,2.6));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(25,-30,80);scene.add(light);
function geometry(positions){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();return g;}
const housingGeometry=geometry(bodyMesh()),colors=[];
for(let i=0;i<housingGeometry.attributes.position.count;i+=3){
 const pts=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(housingGeometry.attributes.position,i+j));
 const cavity=pts.every(p=>p.y>=d.cavityStart-1e-5&&p.y<=d.cavityEnd+1e-5&&Math.abs(Math.hypot(p.x,p.z)-d.cavityRadius)<1e-4);
 const green=pts.every(p=>Math.abs(p.z)<1e-5&&p.x<.001),red=pts.every(p=>Math.abs(p.x)<1e-5&&p.z<.001);
 const c=new THREE.Color(cavity?'#78a94f':green?'#b5c9a8':red?'#dcb6ab':'#b8c8bd');for(let j=0;j<3;j++)colors.push(c.r,c.g,c.b);
}
housingGeometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
const housingMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.83,transparent:true,opacity:.4,side:THREE.DoubleSide,depthWrite:false});
const housing=new THREE.Mesh(housingGeometry,housingMaterial);housing.renderOrder=1;scene.add(housing);
const outlines=new THREE.LineSegments(new THREE.EdgesGeometry(housingGeometry,25),new THREE.LineBasicMaterial({color:'#3c5a4d',transparent:true,opacity:.32}));scene.add(outlines);
const rotorGroup=new THREE.Group(),rotor=new THREE.Mesh(geometry(rotorMesh()),new THREE.MeshStandardMaterial({color:'#ce5c50',roughness:.68}));rotor.renderOrder=2;rotorGroup.add(rotor);scene.add(rotorGroup);
const pin=new THREE.Mesh(geometry(pinMesh()),new THREE.MeshStandardMaterial({color:'#c59a48',metalness:.4,roughness:.45}));pin.renderOrder=3;scene.add(pin);
let angle=45,playing=false,view='model',last=performance.now();
const play=document.getElementById('play'),name=document.getElementById('pose-name');
function setAngle(value){angle=value;slider.value=String(value);slider.setAttribute('aria-valuetext',`${Math.round(value)} degrees`);rotorGroup.rotation.y=-value*Math.PI/180;name.textContent=value<.1?'Seated':value>89.9?'Folded':Math.abs(value-45)<.1?'Halfway':'Turning';host.dataset.angle=String(value);drawSection();}
function stop(){playing=false;play.textContent='Play fold';}
slider.addEventListener('input',()=>{stop();setAngle(Number(slider.value));});
document.querySelectorAll('[data-angle]').forEach(b=>b.addEventListener('click',()=>{stop();setAngle(Number(b.dataset.angle));}));
play.addEventListener('click',()=>{if(playing){stop();return;}if(angle>=89.9)setAngle(0);playing=true;play.textContent='Pause';});
document.getElementById('transparent').addEventListener('change',e=>{housingMaterial.opacity=e.target.checked ? .4 : 1;housingMaterial.depthWrite=!e.target.checked;});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;host.hidden=view!=='model';section.hidden=view!=='section';document.querySelectorAll('[data-view]').forEach(v=>v.setAttribute('aria-pressed',String(v===b)));document.getElementById('view-caption').textContent=view==='model'?'Drag to orbit · scroll to zoom':'Through the rotor midplane · hardware omitted except axle';resize();}));
function drawSection(){
 const c=section.getContext('2d'),w=section.width,h=section.height;if(!w||!h)return;
 c.clearRect(0,0,w,h);const scale=Math.min(w,h)/36,cx=w*.49,cy=h*.45;
 const p=(x,z)=>[cx+x*scale,cy-z*scale];
 c.fillStyle='#bccdbf';c.fillRect(...p(-18,0),18*scale,18*scale);
 c.save();c.translate(cx,cy);c.scale(scale,-scale);c.beginPath();c.moveTo(0,0);c.arc(0,0,d.cavityRadius,Math.PI,1.5*Math.PI);c.closePath();c.fillStyle='#e9efe9';c.fill();
 c.beginPath();c.arc(0,0,d.cavityRadius,Math.PI,1.5*Math.PI);c.strokeStyle='#639243';c.lineWidth=.32;c.stroke();
 const a=angle*Math.PI/180;c.beginPath();c.arc(0,0,d.radius,Math.PI+a,1.5*Math.PI+a);c.arc(0,0,d.rotorBore,1.5*Math.PI+a,Math.PI+a,true);c.closePath();c.fillStyle='#cf6456';c.fill();
 c.beginPath();c.arc(0,0,d.pinRadius,0,Math.PI*2);c.fillStyle='#c59a48';c.fill();c.restore();
 c.font=`${Math.max(12,w/50)}px system-ui`;c.fillStyle='#476843';c.fillText('Green face',...p(-15,1.1));c.fillStyle='#9d4b43';c.fillText('Red face',...p(1,-14));
 c.fillStyle='#526b61';c.fillText('Clearance cavity',...p(-16,-13));
 c.strokeStyle='#738c7c';c.beginPath();c.moveTo(...p(-9,-11.9));c.lineTo(...p(-7.4,-7.4));c.stroke();
}
function resize(){const rect=document.querySelector('.stage').getBoundingClientRect();renderer.setSize(rect.width,rect.height);camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();section.width=Math.round(rect.width*devicePixelRatio);section.height=Math.round(rect.height*devicePixelRatio);drawSection();}
new ResizeObserver(resize).observe(document.querySelector('.stage'));setAngle(45);resize();
renderer.setAnimationLoop(time=>{const dt=Math.min(.05,(time-last)/1000);last=time;if(playing){setAngle(Math.min(90,angle+dt*22.5));if(angle>=90)stop();}controls.update();if(view==='model')renderer.render(scene,camera);});
