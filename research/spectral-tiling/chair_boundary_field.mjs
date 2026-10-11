// Scalar smooth Neumann carrier for the given Chair44 arrow rule.
// This audits a fixed continuum encoding, not a GCTS search or a new theorem.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {BASE_MARKS,VARIANTS,ROTATIONS,IDENTITY,rotationId,chairLeaves,markPoint,key,apply,add} from '../../3d-reptiles/chair/chair44.js';

const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const sign=c=>c==='red'?1:c==='green'?-1:0;
export function carrier(mark){
  const polar=mark.direction.map(v=>sign(mark.color)*v);
  return {center:markPoint(mark).map(v=>v/2),normal:mark.direction,arrow:mark.arrow,
    color:mark.color,polar,cubic:cross(polar,mark.arrow)};
}
export const polynomialKey=m=>key([...m.arrow,...cross(m.direction.map(v=>sign(m.color)*v),m.arrow)]);
export function bump(z){return Math.abs(z)<1?Math.exp(1-1/(1-z*z)):0;}
export function trace(y,m){
  const radius2=dot(y,y);
  if(radius2>=1/16)return 0;
  return Math.exp(1-1/(1-16*radius2))*(dot(m.arrow,y)+16*radius2*dot(m.cubic,y));
}
export function field(x,panels){
  return panels.reduce((sum,m)=>{
    const displacement=x.map((v,i)=>v-m.center[i]);
    const normalDistance=dot(displacement,m.normal);
    const y=displacement.map((v,i)=>v-normalDistance*m.normal[i]);
    return sum+trace(y,m)*bump(4*normalDistance);
  },0);
}
const sha=url=>createHash('sha256').update(readFileSync(url)).digest('hex');
const near=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])))<1e-12;

function auditPair(first,second){
  const occupied=new Set(),marks=new Map();let contacts=0,compatible=true;
  for(const placement of [first,second]){
    const v=VARIANTS[placement.variantId];
    for(const cell of v.cells){const id=key(add(cell,placement.origin));if(occupied.has(id))return {overlap:true,contacts:0,compatible:false};occupied.add(id);}
    for(const m of v.marks){
      const point=markPoint(m).map((x,i)=>x+2*placement.origin[i]),id=key(point);
      if(marks.has(id)){
        const other=marks.get(id);contacts++;
        const expected=key(m.arrow)===key(other.arrow)&&['blue/blue','green/red'].includes([m.color,other.color].sort().join('/'));
        const encoded=polynomialKey(m)===polynomialKey(other);
        assert.equal(encoded,expected);compatible&&=encoded;
      }
      marks.set(id,m);
    }
  }
  return {overlap:false,contacts,compatible};
}

let panelCases=0;
for(const axis of [0,1,2])for(const direction of [-1,1]){
  const normal=[0,0,0];normal[axis]=direction;
  const tangent=[0,1,2].filter(i=>i!==axis);
  const arrows=[];
  for(const a of [-1,1])for(const b of [-1,1]){const v=[0,0,0];v[tangent[0]]=a;v[tangent[1]]=b;arrows.push(v);}
  for(const a of arrows)for(const A of arrows)for(const color of ['red','green','blue'])for(const otherColor of ['red','green','blue']){
    const first={direction:normal,arrow:a,color},second={direction:normal.map(v=>-v),arrow:A,color:otherColor};
    const expected=key(a)===key(A)&&['blue/blue','green/red'].includes([color,otherColor].sort().join('/'));
    assert.equal(polynomialKey(first)===polynomialKey(second),expected);panelCases++;
  }
}
assert.equal(panelCases,864);
const panels=BASE_MARKS.map(carrier);
assert.equal(panels.length,24);
const centerSeparationSquared=Math.min(...panels.flatMap((a,i)=>panels.slice(i+1).map(b=>dot(a.center.map((v,j)=>v-b.center[j]),a.center.map((v,j)=>v-b.center[j])))));
assert.equal(centerSeparationSquared,1/2);
let otherPanelDistanceSquared=Infinity;
for(const p of panels)for(const q of panels)if(p!==q){
  const axis=q.normal.findIndex(v=>v!==0),cell=BASE_MARKS[panels.indexOf(q)].cell;
  const distances=p.center.map((v,i)=>i===axis?Math.abs(v-q.center[i]):Math.max(cell[i]-v,0,v-cell[i]-1));
  otherPanelDistanceSquared=Math.min(otherPanelDistanceSquared,dot(distances,distances));
}
assert.equal(otherPanelDistanceSquared,1/4);
assert.ok(4*(1/16+1/16)<=centerSeparationSquared);
assert.ok(1/16+1/16<otherPanelDistanceSquared);
let rotationChecks=0,maxRotationSampleError=0;
for(const rotation of ROTATIONS)for(const panel of panels){
  const rotated={...panel,center:apply(rotation,panel.center.map(v=>v-1)).map(v=>v+1),normal:apply(rotation,panel.normal),arrow:apply(rotation,panel.arrow),polar:apply(rotation,panel.polar),cubic:apply(rotation,panel.cubic)};
  assert.ok(near(rotated.cubic,cross(rotated.polar,rotated.arrow)));
  for(const coordinates of [[.07,.13],[-.11,.05],[.19,-.06]]){
    const tangent=[0,1,2].filter(i=>panel.normal[i]===0),y=[0,0,0];tangent.forEach((axis,i)=>y[axis]=coordinates[i]);
    maxRotationSampleError=Math.max(maxRotationSampleError,Math.abs(trace(y,panel)-trace(apply(rotation,y),rotated)));
  }
  rotationChecks++;
}
const root={variantId:rotationId(IDENTITY),origin:[0,0,0]},neighbors=[];let tilePairs=0,facePairs=0;
for(const v of VARIANTS)for(let x=-2;x<=2;x++)for(let y=-2;y<=2;y++)for(let z=-2;z<=2;z++){
  const second={variantId:v.id,origin:[x,y,z]},result=auditPair(root,second);tilePairs++;
  if(result.contacts){facePairs++;if(result.compatible)neighbors.push({...second,contact_panels:result.contacts});}
}
assert.equal(neighbors.length,44);
const signatures=VARIANTS.map(v=>v.marks.map(m=>key(markPoint(m))+':'+polynomialKey(m)).sort().join(';'));
assert.equal(new Set(signatures).size,24);
const patches=[];
for(let level=0;level<=3;level++){
  const placements=chairLeaves(level),occupancy=new Set(),marks=new Map();let contacts=0;
  for(const p of placements){
    const v=VARIANTS[p.variantId];
    for(const c of v.cells){const id=key(add(c,p.origin));assert.ok(!occupancy.has(id));occupancy.add(id);}
    for(const m of v.marks){const id=key(markPoint(m).map((a,i)=>a+2*p.origin[i])),value=polynomialKey(m);if(marks.has(id)){assert.equal(marks.get(id),value);contacts++;}marks.set(id,value);}
  }
  assert.equal(occupancy.size,7*8**level);
  patches.push({level,tiles:placements.length,cubes:occupancy.size,shared_panels:contacts});
}
const result={date:'2026-10-11',status:'passed',script_sha256:sha(new URL(import.meta.url)),
  input_sha256:{'../../3d-reptiles/chair/chair44.js':sha(new URL('../../3d-reptiles/chair/chair44.js',import.meta.url))},
  source:'https://arxiv.org/html/2609.24779v1#S2',source_role:'Given Chair44 arrow rule and its infinite hierarchy/aperiodicity theorem; our scalar continuum transfer is independently checked.',
  geometry:{cells:VARIANTS[root.variantId].cells,volume:7,panels:24},panels,
  model:{prototype_fields:1,oriented_fields:24,translations:'Z^3',rotations:ROTATIONS,reflections:false,amplitude:'Fixed; no arbitrary mode coefficients or rescaling.',boundary_condition:'Homogeneous Neumann',modal_expansion:'Infinite'},
  carrier_certificate:{tangential_radius:'1/4',normal_half_width:'1/4',support_ball_radius_squared:'1/8',minimum_distinct_centers_squared:'1/2',minimum_center_to_other_panel_squared:'1/4',normal_derivative:'Exactly zero by the even normal bump; all other terms vanish nearby.'},
  contact_audit:{facing_panel_cases:panelCases,tile_pair_cases:tilePairs,capacity_legal_face_pairs:facePairs,legal_face_neighbors:neighbors.length,neighbors,proper_rotation_panel_checks:rotationChecks,maximum_rotation_trace_sample_error:maxRotationSampleError,patches},
  analytic_facts:{constant_coefficient:0,reason:'Every collar is symmetric tangentially, and its profile is odd under y -> -y.',finite_exact_representation:false,obstruction:'The nonzero field vanishes on an open interior set; a finite Laplacian eigenmode sum is analytic in the connected interior.'},
  limitations:'Infinite aperiodicity conclusion relies on the cited Chair44 theorem. No unrestricted placement-registration theorem, reflection transfer, exact finite-mode equality or certified numerical cutoff. Erasing fields is not claimed here to preserve aperiodicity.'};
writeFileSync(new URL('chair-boundary-field.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,prototype_fields:1,oriented_fields:24,panelCases,tilePairs,legal_face_neighbors:44,patches},null,2));
