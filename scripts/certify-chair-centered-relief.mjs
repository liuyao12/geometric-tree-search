// Certify that every centered-relief neighbor excluded by the original arrows
// has a finite forced contradiction. Replay uses independent geometric domains.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {VARIANTS,FACE_DIRECTIONS,worldMarks,markPoint,key,verifyPatch} from '../3d-reptiles/chair/chair44.js';
import {reliefFeatures} from '../3d-reptiles/chair/relief-profile.js';
import {createReliefPointModel} from './lib/chair-relief-points.mjs';
const out=resolve(process.env.CHAIR_RELIEF_OUT??'output/chair44-centered-relief-search');
const report=JSON.parse(readFileSync(resolve(out,'results.json'),'utf8'));
assert.equal(report.centered,true);
const model=createReliefPointModel({centered:true}),root={variantId:0,origin:[0,0,0],generation:0};
const pose=p=>({variantId:p.variantId,origin:[...p.origin],generation:p.generation??0});
const id=p=>`${p.variantId}@${key(p.origin)}`;
const certificates=[];
for(const pair of report.pairs.filter(p=>p.extra)) {
 const patch=[root,pose(pair)],steps=[];
 for(let limit=0;limit<8;limit++) {
  const g=model.graphFor(patch);
  if(g.dead){steps.push({point:g.dead,candidate:null});break;}
  assert.ok(g.forced,'This certificate format permits forced steps only');
  const candidate=g.choices[0];
  const point=[...g.frontier.values()].find(p=>p.candidates.size===1&&p.candidates.has(candidate.id));
  assert.ok(point);steps.push({point:point.id,candidate:pose(candidate)});patch.push(pose(candidate));
 }
 assert.equal(steps.at(-1).candidate,null,'A certificate must end at a dead obligation');
 certificates.push({pair:id(pair),seed:[root,pose(pair)],steps});
}

// Independent continuous-interface verifier. Heights are exact integers in
// units of 1/400, evaluated at every vertex of the linear profile subdivision.
const features=Object.fromEntries(['red','green','blue'].map(color=>[color,reliefFeatures(color,true).map(f=>({
 u:Math.round(f.u*100),v:Math.round(f.v*100),r:Math.round(f.radius*100),h:Math.round(f.height*400)}))]));
const lines=new Map(),put=(a,b,c)=>lines.set(`${a},${b},${c}`,[a,b,c]);
for(const a of [-1,1])for(const b of [-1,1])for(const fs of Object.values(features))for(const {u,v,r} of fs) {
 for(const d of [-r,0,r]){put(b,-a,u+d);put(a,b,v+d);}put(b-a,-a-b,u-v);put(b+a,-a+b,u+v);
}
for(const c of [-50,50]){put(1,0,c);put(0,1,c);}
const vertices=new Map();
for(const [a,b,c] of lines.values())for(const [d,e,f] of lines.values()) {
 const det=a*e-b*d;if(!det)continue;const x=(c*e-b*f)/det,y=(a*f-c*d)/det;
 assert.ok(Number.isInteger(x)&&Number.isInteger(y));if(Math.abs(x)<=50&&Math.abs(y)<=50)vertices.set(`${x},${y}`,[x,y]);
}
function height(mark,x,y) {
 const [i,j]=[0,1,2].filter(i=>!mark.direction[i]),a=mark.arrow,n=mark.direction;
 const s=[a[1]*n[2]-a[2]*n[1],a[2]*n[0]-a[0]*n[2],a[0]*n[1]-a[1]*n[0]];
 const U=s[i]*x+s[j]*y,V=a[i]*x+a[j]*y;
 return features[mark.color].reduce((sum,f)=>sum+(f.h/f.r)*Math.max(0,f.r-Math.max(Math.abs(U-f.u),Math.abs(V-f.v))),0);
}
const overlapCache=new Map(),type=m=>[...m.direction,...m.arrow,m.color].join(',');
function interfacesOverlap(a,b) {
 const k=`${type(a)}|${type(b)}`;
 if(!overlapCache.has(k))overlapCache.set(k,[...vertices.values()].some(([x,y])=>height(a,x,y)+height(b,x,y)>0));
 return overlapCache.get(k);
}
const cache=new Map();
function tile(p) {
 if(!cache.has(id(p)))cache.set(id(p),{pose:p,cells:new Set(VARIANTS[p.variantId].cells.map(c=>key(c.map((v,i)=>v+p.origin[i])))),
  faces:new Map(worldMarks(p).map(m=>[key(markPoint(m)),m]))});
 return cache.get(id(p));
}
function legal(t,patch) {
 for(const other of patch) {
  if([...t.cells].some(c=>other.cells.has(c)))return false;
  for(const [face,mark] of t.faces)if(other.faces.has(face)&&interfacesOverlap(mark,other.faces.get(face)))return false;
 }
 return true;
}
function obligation(point) {
 if(point.startsWith('c:'))return {cells:[point.slice(2).split(',').map(Number)]};
 const [,axisText,cellText,probeText]=point.split(':'),axis=Number(axisText),a=cellText.split(',').map(Number),b=[...a];b[axis]++;
 const face=a.map((v,i)=>2*v+(i===axis?2:1));
 return {cells:[a,b],axis,face:key(face),probe:model.PROBES[Number(probeText)]};
}
function covers(t,q) {
 const owners=q.cells.filter(c=>t.cells.has(key(c)));
 if(!q.probe)return owners.length>0;
 if(owners.length===2)return true;if(!owners.length)return false;
 const mark=t.faces.get(q.face);assert.ok(mark);
 return mark.direction[q.axis]*q.probe.h < height(mark,q.probe.x,q.probe.y);
}
function domain(point,placements) {
 const q=obligation(point),patch=placements.map(tile);
 assert.ok(patch.some(t=>q.cells.some(c=>t.cells.has(key(c)))||(!q.probe&&q.cells.some(c=>FACE_DIRECTIONS.some(d=>t.cells.has(key(c.map((v,i)=>v+d[i]))))))),'Obligation is active');
 assert.ok(patch.every(t=>!covers(t,q)),'Obligation is unfilled');
 const found=new Set(),seen=new Set();
 for(const cell of q.cells)for(const variant of VARIANTS)for(const c of variant.cells) {
  const p={variantId:variant.id,origin:cell.map((v,i)=>v-c[i])},k=id(p);if(seen.has(k))continue;seen.add(k);
  const candidate=tile(p);if(covers(candidate,q)&&legal(candidate,patch))found.add(k);
 }
 return found;
}
// Enumerate all possible face-adjacent translations independently of graphFor.
const neighbors=new Set(),base=tile(root);
for(const v of VARIANTS)for(let x=-2;x<=2;x++)for(let y=-2;y<=2;y++)for(let z=-2;z<=2;z++) {
 const p={variantId:v.id,origin:[x,y,z]},t=tile(p);
 if(!legal(t,[base]))continue;
 if([...t.cells].some(c=>FACE_DIRECTIONS.some(d=>base.cells.has(key(c.split(',').map((a,i)=>Number(a)+d[i]))))))neighbors.add(id(p));
}
assert.deepEqual(neighbors,new Set(report.pairs.map(id)),'Complete geometric neighbor catalog');
const expected=new Set(report.pairs.filter(p=>!verifyPatch([root,p]).valid).map(id));
assert.deepEqual(expected,new Set(certificates.map(c=>c.pair)),'Every non-arrow neighbor has a certificate');
let forcedSteps=0,deadSteps=0;
for(const certificate of certificates) {
 const patch=certificate.seed.map(pose);
 assert.ok(legal(tile(patch[1]),[tile(patch[0])]));
 for(const step of certificate.steps) {
  const candidates=domain(step.point,patch);
  if(step.candidate){assert.deepEqual(candidates,new Set([id(step.candidate)]));patch.push(pose(step.candidate));forcedSteps++;}
  else {assert.equal(candidates.size,0);deadSteps++;}
 }
}
const result={schemaVersion:1,scope:'integer translations and 24 proper cubic rotations; fixed centered relief',
 conclusion:'Every full tiling in this placement domain satisfies the original arrow rules.',
 verification:{neighbors:neighbors.size,excludedNonArrowPairs:certificates.length,forcedSteps,deadSteps,exactProfileVertices:vertices.size},certificates};
writeFileSync(resolve(out,'exclusion-certificates.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result.verification));
