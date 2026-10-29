// Display only. One shared WebGL renderer copies into independent 2D canvases;
// every specimen keeps its own camera and controls, without exhausting contexts.
import * as THREE from 'three';
import {OrbitControls} from '../3d-lattice-tiler/vendor/OrbitControls.js';
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setClearColor(0x000000,0);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
const viewers=new Set();
const triangleGeometry=positions=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();return g;};
const clear=group=>{for(const c of [...group.children]){group.remove(c);c.geometry?.dispose();(Array.isArray(c.material)?c.material:[c.material]).forEach(m=>{m?.map?.dispose();m?.dispose();});}};
const visible=new IntersectionObserver(entries=>{for(const e of entries){const v=[...viewers].find(v=>v.canvas===e.target);if(v){v.visible=e.isIntersecting;v.dirty=true;}}});
function tick(){for(const v of viewers){if(!v.visible||!v.model)continue;v.controls.update();if(v.dirty)v.render();}requestAnimationFrame(tick);}requestAnimationFrame(tick);
export class TileViewer{
 constructor(canvas,{onFace=()=>{},color='#ddb475'}={}){
  this.canvas=canvas;this.context=canvas.getContext('2d');this.onFace=onFace;this.color=color;this.dirty=true;this.visible=true;this.enlarged=false;
  this.scene=new THREE.Scene();this.group=new THREE.Group();this.scene.add(this.group);this.camera=new THREE.PerspectiveCamera(35,1,0.01,100);
  this.scene.add(new THREE.HemisphereLight('#e6f4ed','#263941',2.8));for(const [pos,col,intensity]of [[[4,7,6],'#ffe0b7',3.1],[[-5,2,-4],'#86d8e1',2.3]]){const l=new THREE.DirectionalLight(col,intensity);l.position.set(...pos);this.scene.add(l);}
  this.controls=new OrbitControls(this.camera,canvas);this.controls.enablePan=false;this.controls.enableDamping=true;this.controls.minDistance=1.5;this.controls.maxDistance=12;this.controls.addEventListener('change',()=>this.dirty=true);
  this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(canvas);this.raycaster=new THREE.Raycaster();let down;
  canvas.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});canvas.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=canvas.getBoundingClientRect();this.raycaster.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),this.camera);const hit=this.raycaster.intersectObjects(this.group.children).find(h=>h.object.userData.faceIndices);if(hit)this.onFace(this.model,hit.object.userData.faceIndices[hit.faceIndex]);});
  viewers.add(this);visible.observe(canvas);this.reset();
 }
 resize(){const r=this.canvas.getBoundingClientRect();if(r.width<=0||r.height<=0)return;const ratio=Math.min(devicePixelRatio,2);this.width=Math.max(1,Math.round(r.width*ratio));this.height=Math.max(1,Math.round(r.height*ratio));this.canvas.width=this.width;this.canvas.height=this.height;this.camera.aspect=r.width/r.height;this.camera.updateProjectionMatrix();this.fit();this.dirty=true;}
 fit(){if(!this.fitPoints||!this.camera.aspect)return;for(let i=0;i<4;i++){this.camera.lookAt(this.controls.target);this.camera.updateMatrixWorld();const extent=this.fitPoints.reduce((m,p)=>{const x=p.clone().project(this.camera);return Math.max(m,Math.abs(x.x),Math.abs(x.y));},0);const distance=this.camera.position.length();this.camera.position.setLength(Math.max(1.8,Math.min(10,distance*extent/0.78)));}this.controls.update();}
 reset(){this.camera.position.set(1.2,0.85,1.7).setLength(3.8);this.controls.target.set(0,0,0);this.fit();this.controls.update();this.dirty=true;}
 turn(){this.camera.position.applyAxisAngle(new THREE.Vector3(0,1,0),Math.PI/6);this.controls.update();this.dirty=true;}
 setModel(model){this.model=model;this.build();this.reset();this.resize();}
 setEnlarged(value){this.enlarged=value;if(this.model)this.build();}
 build(){
  clear(this.group);const t=this.model;if(!t)return;const points=t.vertices.map(p=>new THREE.Vector3(...p));
  if(this.enlarged&&t.features){for(const feature of t.features){const base=feature.base.map(p=>new THREE.Vector3(...p)),center=base.reduce((s,p)=>s.add(p),new THREE.Vector3()).multiplyScalar(0.25);for(let i=0;i<points.length;i++){const original=new THREE.Vector3(...t.vertices[i]);const k=base.findIndex(p=>p.distanceToSquared(original)<1e-16);if(k>=0)points[i]=base[k].clone().sub(center).multiplyScalar(5).add(center);if(original.distanceToSquared(new THREE.Vector3(...feature.apex))<1e-16)points[i]=new THREE.Vector3(...feature.apex).sub(center).multiplyScalar(80).add(center);}}}
  const box=new THREE.Box3().setFromPoints(points),center=box.getCenter(new THREE.Vector3()),radius=box.getBoundingSphere(new THREE.Sphere()).radius||1;
  const local=p=>p.clone().sub(center).multiplyScalar(1/radius);const vertices=points.map(local);this.fitPoints=vertices;const positions=[],colors=[],faceIndices=[];
  for(const [fi,f]of t.faces.entries()){const col=new THREE.Color(t.faceColors?.[fi]||this.color);for(let i=1;i+1<f.length;i++){positions.push(...[f[0],f[i],f[i+1]].flatMap(j=>vertices[j].toArray()));for(let k=0;k<3;k++)colors.push(col.r,col.g,col.b);faceIndices.push(fi);}}
  const g=triangleGeometry(positions);g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));const mesh=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:0.52,metalness:0.1,side:THREE.DoubleSide}));mesh.userData.faceIndices=faceIndices;this.group.add(mesh);
  const edge=new THREE.LineSegments(new THREE.EdgesGeometry(g,20),new THREE.LineBasicMaterial({color:'#142c32',transparent:true,opacity:0.65}));this.group.add(edge);
  const disk=(p,n,color,r)=>{const disk=new THREE.Mesh(new THREE.CircleGeometry(r,20),new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide}));disk.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),n);disk.position.copy(p).addScaledVector(n,0.002);this.group.add(disk);};
  for(const d of t.dots||[]){const c=new THREE.Vector3(...d.center);const face=t.faces.find(f=>f.every(j=>Math.abs(new THREE.Plane().setFromCoplanarPoints(new THREE.Vector3(...t.vertices[f[0]]),new THREE.Vector3(...t.vertices[f[1]]),new THREE.Vector3(...t.vertices[f[2]])).distanceToPoint(c))<1e-6));if(!face)continue;const n=new THREE.Vector3(...t.vertices[face[1]]).sub(new THREE.Vector3(...t.vertices[face[0]])).cross(new THREE.Vector3(...t.vertices[face[2]]).sub(new THREE.Vector3(...t.vertices[face[0]]))).normalize();for(const key of ['black','red']){const p=local(new THREE.Vector3(...d[key]).multiplyScalar(0.75).addScaledVector(c,0.25));disk(p,n,'#ffefdc',0.026);disk(p.clone().addScaledVector(n,0.001),n,key==='black'?'#14222b':'#f34d48',0.019);}}
  for(const e of t.rightAngleEdges||[]){const p=e.flatMap(j=>vertices[j].toArray());this.group.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(p,3)),new THREE.LineBasicMaterial({color:'#4d9dff',linewidth:2})));}
  for(const a of t.arrows||[]){const f=t.faces[a.face],c=f.reduce((s,i)=>s.add(vertices[i]),new THREE.Vector3()).multiplyScalar(1/f.length),n=vertices[f[1]].clone().sub(vertices[f[0]]).cross(vertices[f[2]].clone().sub(vertices[f[0]])).normalize(),dir=new THREE.Vector3(...a.direction).normalize();c.addScaledVector(n,0.004);const len=0.28/radius;this.group.add(new THREE.ArrowHelper(dir,c.clone().addScaledVector(dir,-len/2),len,a.color,len*0.32,len*0.24));}
  if(t.features)for(const feature of t.features){const p=feature.base.map(x=>new THREE.Vector3(...x)),n=p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).normalize(),c=p.reduce((s,p)=>s.add(p),new THREE.Vector3()).multiplyScalar(0.25);disk(local(c),n,feature.coefficient>0?'#e8b373':'#64b7be',this.enlarged?0.018:0.009);}
  this.dirty=true;
 }
 render(){if(!this.width||!this.height)this.resize();if(!this.width)return;renderer.setSize(this.width,this.height,false);renderer.render(this.scene,this.camera);this.context.clearRect(0,0,this.width,this.height);this.context.drawImage(renderer.domElement,0,0);this.dirty=false;}
 save(){this.render();const a=document.createElement('a');a.download=`${this.model.id}-specimen.png`;a.href=this.canvas.toDataURL('image/png');a.click();}
 dispose(){viewers.delete(this);visible.unobserve(this.canvas);this.resizeObserver.disconnect();this.controls.dispose();clear(this.group);}
}
