const $ = id => document.getElementById(id);
const info = {
 quasi: {kind:'TWELVEFOLD ORDER',name:'Dodecagonal quasicrystal',description:'A simulated packing with a nonrepeating square–triangle organization in its layers. Corrugated layers stack periodically; twelve-member tetrahedron rings form columns called “logs”.',density:'83.24%',periodicity:'Aperiodic in the layer plane',provenance:'Original research figures',caveat:'The sample is finite and simulated with periodic boundaries. Its twelvefold diffraction and nonrepeating layer organization identify quasicrystalline order. This is not a new simulation.',source:'https://arxiv.org/abs/1012.5138'},
 approx: {kind:'THE PERIODIC RELATIVE',name:'Square–triangle approximant',description:'Rotate the published 82-particle cell, repeat it, and cut through the stack. The same coordinates are copied into every cell.',density:'84.7866% in this model',periodicity:'Periodic in all three directions',provenance:'Published 82-particle coordinates',caveat:'The 85.03% card reports the separately compressed 656-particle result. This model shows the available 82-particle data at 84.7866%. Shrinking particles changes the display, not the reported packing fraction.',source:'https://arxiv.org/abs/1012.5138'},
 dimer: {kind:'THE DENSITY BENCHMARK',name:'Double-dimer crystal',description:'Two face-sharing pairs form a repeating cell of four tetrahedra. Opposite dimers are related by inversion. Explore the record construction as a contrast to the large, complex approximant.',density:'85.6348%',periodicity:'Periodic · triclinic cell',provenance:'Theorem 1 lattice and offset vectors',caveat:'Constructed from the published exact lattice parameters and rendered in floating point. Optimality is proved within the paper’s restricted dimer family; global optimality remains unproved.',source:'https://arxiv.org/abs/1001.0586'}
};
let mode='quasi',figure='packing',engine,creation;
function enlarge(src){$('large-figure').src=src;$('figure-dialog').showModal();}
$('figure-open').onclick=()=>enlarge($('main-figure').src);
$('close-dialog').onclick=()=>$('figure-dialog').close();
document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>enlarge(b.dataset.image));
$('figure-switch').onclick=()=>{figure=figure==='packing'?'structure':'packing';$('main-figure').src=`figures/${figure}.jpg`;$('main-figure').alt=figure==='packing'?'Published Figure 1: local motifs, perspective quasicrystal, side view and twelvefold-axis view.':'Published Figure 3: quasicrystal square–triangle network, tetrahedron logs, periodic approximant, underlying tiling and tetrahelices.';$('figure-switch').textContent=figure==='packing'?'Show tiling & logs':'Show packing views';};
async function select(next){mode=next;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));const item=info[mode];for(const key of ['kind','name','description','density','periodicity','provenance','caveat'])$(key).textContent=item[key];$('source-link').href=item.source;$('paper-view').hidden=mode!=='quasi';$('viewer').hidden=mode==='quasi';$('controls').hidden=mode==='quasi';$('data-link').hidden=mode!=='approx';$('visual-label').textContent=mode==='quasi'?'PUBLISHED QUASICRYSTAL':mode==='approx'?'PUBLISHED APPROXIMANT':'RECORD DIMER CONSTRUCTION';$('visual-tag').textContent=mode==='quasi'?'Source figure':'Interactive 3D';
 if(mode==='quasi'){if(engine)engine.active=false;return;}
 try{if(!creation)creation=createViewer();engine=await creation;engine.active=true;engine.rebuild();engine.view('oblique');$('load-error').hidden=true;}catch(error){$('load-error').hidden=false;$('load-error').textContent='The 3D viewer could not load. The published figures and source links remain available. '+error.message;}
}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>select(b.dataset.mode));
async function createViewer(){
 const [THREE,{OrbitControls},data]=await Promise.all([import('three'),import('./vendor/OrbitControls.js'),fetch('./data/approximant.json').then(r=>{if(!r.ok)throw Error('Coordinate file unavailable');return r.json();})]);
 const host=$('canvas-wrap'),scene=new THREE.Scene();scene.background=new THREE.Color('#08151d');
 const camera=new THREE.PerspectiveCamera(38,1,.01,1000);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.localClippingEnabled=true;host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','Interactive tetrahedron packing. Use the view buttons to change camera direction.');
 const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;
 scene.add(new THREE.HemisphereLight(0xd7faff,0x234254,2.5));let light=new THREE.DirectionalLight(0xffffff,3);light.position.set(8,15,12);scene.add(light);
 let group=new THREE.Group(),size=10;scene.add(group);let materials=[],planes=[];
 const api={active:true,rebuild,view};
 const v=p=>new THREE.Vector3(...p);
 function geometry(points){const g=new THREE.BufferGeometry();let arr=[];for(const face of [[0,2,1],[0,1,3],[0,3,2],[1,2,3]])for(const index of face)arr.push(...points[index]);g.setAttribute('position',new THREE.Float32BufferAttribute(arr,3));g.computeVertexNormals();return g;}
 function rebuild(){scene.remove(group);group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material)o.material.dispose();});group=new THREE.Group();scene.add(group);materials=[];
 const n=Number($('repeat').value),shrink=Number($('shrink').value),colour=$('colour').value;let particles=[],basis;
 if(mode==='approx'){
  basis=[v([data.box[0],0,0]),v([0,data.box[1],0]),v([0,0,data.box[2]])];
  for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(let k=0;k<n;k++){
   const offset=v([(i-(n-1)/2)*data.box[0],(j-(n-1)/2)*data.box[1],(k-(n-1)/2)*data.box[2]]);
   for(let p=0;p<data.particles.length;p++){const row=data.particles[p],center=v(row.slice(0,3)).add(offset),q=new THREE.Quaternion(row[4],row[5],row[6],row[3]).normalize();const points=[[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]].map(x=>v(x).applyQuaternion(q).toArray());particles.push({center,points,orientation:(Math.atan2(2*(row[3]*row[5]+row[4]*row[6]),1-2*(row[5]**2+row[6]**2))+Math.PI)/(2*Math.PI),cell:i*n*n+j*n+k});}
  }
 }else{
  const a=v([290,107,-7]).multiplyScalar(3/320/1.5),b=v([-34,277,135]).multiplyScalar(3/320/1.5),c=v([94,-83,247]).multiplyScalar(3/320/1.5),d=v([38,5,-25]).multiplyScalar(1/320/1.5);
  basis=[a.clone().add(b),b.clone().add(c),c.clone().add(a)];const sets=[[[2,2,2],[2,-1,-1],[-1,2,-1],[-1,-1,2]],[[-2,-2,-2],[2,-1,-1],[-1,2,-1],[-1,-1,2]]];
  for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(let k=0;k<n;k++){
   const off=basis[0].clone().multiplyScalar(i-(n-1)/2).addScaledVector(basis[1],j-(n-1)/2).addScaledVector(basis[2],k-(n-1)/2);
   for(let sign of [1,-1])for(let t=0;t<2;t++){const points=sets[t].map(p=>v(p).multiplyScalar(sign/1.5));const trans=off.clone();if(sign===-1)trans.add(a).add(d);const center=points.reduce((s,p)=>s.add(p),new THREE.Vector3()).multiplyScalar(.25);particles.push({center:center.clone().add(trans),points:points.map(p=>p.sub(center).toArray()),orientation:sign===1?.1:.6,cell:i*n*n+j*n+k});}
  }
 }
 // Center the patch without changing inter-particle displacement or orientation.
 const box=new THREE.Box3();for(const p of particles)for(const q of p.points)box.expandByPoint(v(q).add(p.center));const shift=box.getCenter(new THREE.Vector3());size=box.getSize(new THREE.Vector3()).length();
 const vertical=box.max.y-box.min.y,thickness=vertical*Number($('slice').value);planes=[new THREE.Plane(v([0,1,0]),thickness/2),new THREE.Plane(v([0,-1,0]),thickness/2)];
 const palette=[0x68dac4,0x6ba7de,0xd7b575,0xa990d4,0xe1927f,0x87ba93];
 const materialCache=new Map();
 for(const p of particles){const bin=colour==='cell'?p.cell%6:colour==='height'?Math.min(5,Math.floor((p.center.y-box.min.y)/Math.max(vertical,1e-9)*6)):Math.floor(p.orientation*6)%6;
  let mat=materialCache.get(bin);if(!mat){mat=new THREE.MeshStandardMaterial({color:palette[bin],roughness:.55,metalness:.12,side:THREE.DoubleSide,clippingPlanes:planes});materialCache.set(bin,mat);materials.push(mat);}
  const geom=geometry(p.points);const mesh=new THREE.Mesh(geom,mat);mesh.position.copy(p.center).sub(shift);mesh.scale.setScalar(shrink);group.add(mesh);
 }
 if($('cell').checked){const centralOffset=basis.reduce((s,p)=>s.addScaledVector(p,-.5),new THREE.Vector3()).sub(shift);if(n%2===0)for(const p of basis)centralOffset.addScaledVector(p,-.5);let corners=[];for(let z=0;z<8;z++)corners.push(centralOffset.clone().addScaledVector(basis[0],(z&1)?1:0).addScaledVector(basis[1],(z&2)?1:0).addScaledVector(basis[2],(z&4)?1:0));let points=[];for(let x=0;x<8;x++)for(let bit of [1,2,4])if(!(x&bit))points.push(corners[x],corners[x|bit]);group.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0xf0d093,transparent:true,opacity:.8})));}
 $('count').textContent=`${particles.length.toLocaleString()} tetrahedra · ${n**3} repeating ${n===1?'cell':'cells'}`;
 resize();
 }
 function view(name){const distance=size*1.25;orbit.target.set(0,0,0);camera.up.set(0,1,0);if(name==='top'){camera.up.set(0,0,-1);camera.position.set(0,distance,0);}else if(name==='side')camera.position.set(distance,0,0);else camera.position.set(distance*.65,distance*.6,distance*.8);orbit.update();}
 function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
 new ResizeObserver(resize).observe(host);
 for(const id of ['repeat','colour','cell'])$(id).onchange=()=>{rebuild();if(id==='repeat')view('oblique');};for(const id of ['shrink','slice'])$(id).oninput=rebuild;
 for(const id of ['oblique','top','side'])$(id).onclick=()=>view(id);$('reset').onclick=()=>{$('shrink').value=.92;$('slice').value=1;rebuild();view('oblique');};
 renderer.setAnimationLoop(()=>{if(api.active){orbit.update();renderer.render(scene,camera);}});return api;
}
