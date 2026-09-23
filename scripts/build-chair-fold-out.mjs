import {writeFileSync,mkdirSync} from 'node:fs';
import {dimensions,bodyMesh,rotorMesh,pinMesh,foldPoint} from '../3d-reptiles/chair/fold-out/model.js';
import assert from 'node:assert/strict';
const out='3d-reptiles/chair/fold-out';mkdirSync(out,{recursive:true});
function inspect(name,positions){
 const edges=new Map();let volume=0,triangles=positions.length/9;
 const key=p=>p.map(v=>Math.round(v*1e7)).join(',');
 for(let i=0;i<positions.length;i+=9){
  const [a,b,c]=[0,3,6].map(j=>positions.slice(i+j,i+j+3));
  volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
  for(const [u,v] of [[a,b],[b,c],[c,a]]){
   const x=key(u),y=key(v);assert.notEqual(x,y);const k=[x,y].sort().join('|'),e=edges.get(k)??[0,0];
   e[0]++;e[1]+=x<y?1:-1;edges.set(k,e);
  }
 }
 assert.ok([...edges.values()].every(([n,b])=>n===2&&b===0),`${name}: watertight, consistently oriented mesh`);
 assert.ok(volume>0,`${name}: positive volume`);return {name,triangles,volumeMM3:volume};
}
function stl(positions){
 const b=Buffer.alloc(84+positions.length/9*50);b.write('Chair44 fold-out mechanism coupon; millimetres');b.writeUInt32LE(positions.length/9,80);
 for(let i=0;i<positions.length;i+=9){
  const o=84+i/9*50,a=positions.slice(i,i+3),u=positions.slice(i+3,i+6).map((v,j)=>v-a[j]),v=positions.slice(i+6,i+9).map((v,j)=>v-a[j]);
  const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],l=Math.hypot(...n);assert.ok(l>1e-10);
  n.forEach((v,j)=>b.writeFloatLE(v/l,o+4*j));for(let j=0;j<9;j++)b.writeFloatLE(positions[i+j],o+12+4*j);
 }return b;
}
const bodies={body:bodyMesh(),rotor:rotorMesh(),pin:pinMesh()},checks=[];
for(const [name,positions] of Object.entries(bodies)){
 checks.push(inspect(name,positions));
 // Put each individual print on the bed with its pin axis vertical (printer Z).
 const bed=positions.reduce((m,_,i)=>i%3===1?Math.min(m,positions[i]):m,Infinity);
 const printed=[];for(let i=0;i<positions.length;i+=3)printed.push(...[positions[i],-positions[i+2],positions[i+1]-bed].map(v=>Math.abs(v)<1e-10?0:v));
 const binary=stl(printed),decoded=[];
 for(let triangle=0;triangle<printed.length/9;triangle++)for(let j=0;j<9;j++)decoded.push(binary.readFloatLE(84+triangle*50+12+j*4));
 inspect(`${name} exported STL`,decoded);
 writeFileSync(`${out}/${name}.stl`,binary);
}
// Exact design inequalities provide an all-angle clearance bound. The faceted
// cavity's inradius remains larger than the rotor's circumradius.
const d=dimensions;
assert.ok(d.cavityRadius*Math.cos(Math.PI/d.angularSegments)>d.radius);
assert.ok(d.rotorStart>d.cavityStart&&d.rotorEnd<d.cavityEnd);
assert.ok(d.rotorBore*Math.cos(Math.PI/d.angularSegments)>d.pinRadius);
assert.ok(d.bodyBore*Math.cos(Math.PI/d.angularSegments)>d.pinRadius);
// Numerical sweep additionally exercises the actual mesh vertices and transform.
let samples=0,minRadial=Infinity;
for(let degrees=0;degrees<=90;degrees+=.25)for(let i=0;i<bodies.rotor.length;i+=3){
 const p=foldPoint(bodies.rotor.slice(i,i+3),degrees*Math.PI/180);
 assert.ok(p[1]>=d.rotorStart-1e-9&&p[1]<=d.rotorEnd+1e-9);
 const r=Math.hypot(p[0],p[2]);assert.ok(r<=d.radius+1e-9);minRadial=Math.min(minRadial,r);samples++;
}
assert.ok(minRadial>=d.rotorBore-1e-9);
const result={scope:'Single convex-corner mechanical prototype; not a tiling certificate',dimensions:d,meshes:checks,
 motion:{degrees:[0,90],samples,allAnglesBound:true,minimumBodyRadialClearance:d.cavityRadius*Math.cos(Math.PI/d.angularSegments)-d.radius,
 axialClearance:d.rotorStart-d.cavityStart,minimumBodyPinRadialClearance:d.bodyBore*Math.cos(Math.PI/d.angularSegments)-d.pinRadius,
 minimumRotorPinRadialClearance:d.rotorBore*Math.cos(Math.PI/d.angularSegments)-d.pinRadius}};
writeFileSync(`${out}/verification.json`,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
