import * as THREE from './vendor/three.module.min.js';

export const vertices = [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]];
export const maxStage = 4;
export function stageWidth(stage) { return stage <= 1 ? 1 : 2 * stage - 1; }
export function canonicalQuaternion(q) {
  const r=q.clone().normalize();
  if(r.w<0 || (Math.abs(r.w)<1e-12 && [r.x,r.y,r.z].find(x=>Math.abs(x)>1e-12)<0))r.set(-r.x,-r.y,-r.z,-r.w);
  return r;
}
export const tetrahedralRotations = [];
for(const perm of [[0,1,2],[1,2,0],[2,0,1]])for(const signs of [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]) {
  const rows=Array.from({length:3},(_,i)=>Array.from({length:3},(_,j)=>perm[i]===j?signs[i]:0));
  const m=new THREE.Matrix4().set(...rows[0],0,...rows[1],0,...rows[2],0,0,0,0,1);
  tetrahedralRotations.push(canonicalQuaternion(new THREE.Quaternion().setFromRotationMatrix(m)));
}
export function orientationRepresentative(q, quotient=true) {
  const candidates=quotient?tetrahedralRotations.map(s=>canonicalQuaternion(q.clone().multiply(s))):[canonicalQuaternion(q)];
  return candidates.sort((a,b)=>b.w-a.w || a.x-b.x || a.y-b.y || a.z-b.z)[0];
}
export function orientationDistance(a,b,quotient=true) {
  let dot=0;
  for(const s of quotient?tetrahedralRotations:[new THREE.Quaternion()])dot=Math.max(dot,Math.abs(a.dot(b.clone().multiply(s))));
  return 2*Math.acos(Math.min(1,dot));
}
export function axisAnglePoint(q) {
  const r=canonicalQuaternion(q),angle=2*Math.acos(Math.min(1,r.w)),s=Math.sqrt(Math.max(0,1-r.w*r.w));
  return s<1e-9?new THREE.Vector3():new THREE.Vector3(r.x,r.y,r.z).multiplyScalar(angle/(Math.PI*s));
}
function v(p){return new THREE.Vector3(...p);}
function quaternionFor(points) {
  const basis=pts=>new THREE.Matrix4().makeBasis(v(pts[1]).sub(v(pts[0])),v(pts[2]).sub(v(pts[0])),v(pts[3]).sub(v(pts[0])));
  let target=points.map(p=>p.slice()),rotation=basis(target).multiply(basis(vertices).invert());
  if(rotation.determinant()<0){[target[1],target[2]]=[target[2],target[1]];rotation=basis(target).multiply(basis(vertices).invert());}
  return canonicalQuaternion(new THREE.Quaternion().setFromRotationMatrix(rotation));
}
export function dimerCell(progress=1) {
  // Equations (6), (7), (11), (13), Chen–Engel–Glotzer. A segment in the proved packing region.
  const u=progress*3/160,vv=progress*3/64,w=0;
  const a=v([27/10+u,21/20-vv,-3/20+2*u+vv]).multiplyScalar(2/3);
  const b=v([-3/10-u,51/20+vv,27/20-2*u-vv]).multiplyScalar(2/3);
  const c=v([129/160-u+2*vv+2*w,-237/320+u/2-vv+3*w,753/320+u/2-vv+w]).multiplyScalar(2/3);
  const d=v([1/10+u,-1/20+u+vv,-1/20+u-vv]).multiplyScalar(2/3);
  const basis=[a.clone().add(b),b.clone().add(c),c.clone().add(a)];
  const sets=[[[2,2,2],[2,-1,-1],[-1,2,-1],[-1,-1,2]],[[-2,-2,-2],[2,-1,-1],[-1,2,-1],[-1,-1,2]]];
  const particles=[];
  for(const sign of [1,-1])for(const points of sets){const ps=points.map(p=>v(p).multiplyScalar(sign*2/3));const center=ps.reduce((s,p)=>s.add(p),new THREE.Vector3()).multiplyScalar(.25);const local=ps.map(p=>p.clone().sub(center).toArray());const offset=sign===1?new THREE.Vector3():a.clone().add(d);particles.push({center:center.add(offset),quaternion:quaternionFor(local)});}
  const volume=Math.abs(new THREE.Matrix4().makeBasis(...basis).determinant());
  return {basis,particles,density:4*(8/3)/volume};
}
export function approximantCell(data) {
  return {basis:[v([data.box[0],0,0]),v([0,data.box[1],0]),v([0,0,data.box[2]])],particles:data.particles.map(row=>({center:v(row.slice(0,3)),quaternion:canonicalQuaternion(new THREE.Quaternion(row[4],row[5],row[6],row[3]))})),density:data.density};
}
export function compressionState(mode,progress,data) {
  const t=Math.max(0,Math.min(1,progress));
  // Expanded reference -> published endpoint. For dimers the second half follows the analytical family.
  const dilation=mode==='dimer'?1+.35*(1-Math.min(1,2*t)):1+.35*(1-t);
  const deformation=mode==='dimer'?Math.max(0,2*t-1):0;
  const cell=mode==='dimer'?dimerCell(deformation):approximantCell(data);
  return {...cell,dilation,deformation,density:cell.density/dilation**3};
}
export function anchoredPatch(cell,stage,assembly=cell.particles.length) {
  const radius=Math.max(0,stage-1),first=cell.particles[0],inverse=first.quaternion.clone().invert(),out=[];
  for(let i=-radius;i<=radius;i++)for(let j=-radius;j<=radius;j++)for(let k=-radius;k<=radius;k++) {
    const shell=Math.max(Math.abs(i),Math.abs(j),Math.abs(k));
    for(let index=0;index<cell.particles.length;index++){
      if(stage===0 && (i||j||k||index))continue;
      if(stage===1 && index>=assembly)continue;
      const p=cell.particles[index];
      const center=p.center.clone().addScaledVector(cell.basis[0],i).addScaledVector(cell.basis[1],j).addScaledVector(cell.basis[2],k).sub(first.center).multiplyScalar(cell.dilation).applyQuaternion(inverse);
      out.push({center,quaternion:inverse.clone().multiply(p.quaternion).normalize(),prototype:index,cell:[i,j,k],shell,anchor:!i&&!j&&!k&&!index});
    }
  }
  return {particles:out,inverse,anchorCenter:first.center};
}

// A bounded periodic display, not an inflation hierarchy or packing path.
export function periodicDisplay(cell, explosion=0, copies=0) {
  const inverse=cell.particles[0].quaternion.clone().invert();
  const center=cell.particles.reduce((v,p)=>v.add(p.center),new THREE.Vector3()).multiplyScalar(1/cell.particles.length);
  const offsets=[[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1],[0,1,1],[1,1,1]];
  const particles=[];
  for(let n=0;n<offsets.length;n++) {
    if(n>0 && copies<=n-1)continue;
    const t=n===0?1:Math.min(1,copies-(n-1));
    const offset=new THREE.Vector3();offsets[n].forEach((k,i)=>offset.addScaledVector(cell.basis[i],k));
    offset.multiplyScalar(1+1.3*(1-t));
    cell.particles.forEach((p,index)=>particles.push({center:p.center.clone().sub(center).multiplyScalar(1+explosion).add(offset).applyQuaternion(inverse),quaternion:inverse.clone().multiply(p.quaternion).normalize(),prototype:index,cell:offsets[n],shell:n,copyOffset:offset.clone(),anchor:n===0&&index===0}));
  }
  return {particles,inverse,anchorCenter:center};
}
