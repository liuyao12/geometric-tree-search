import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {VARIANTS,worldMarks,markPoint,verifyPatch,parentContainingChild,chairLeaves,key} from '../3d-reptiles/chair/chair44.js';
import {reliefFrame,reliefHeight} from '../3d-reptiles/chair/relief-profile.js';
import {PROBES,FULL,indexState,graphFor,shellTarget,clearCache} from './lib/chair-relief-points.mjs';
const out=resolve(process.env.CHAIR_RELIEF_OUT??'output/chair44-relief-search');
const report=JSON.parse(readFileSync(resolve(out,'results.json'),'utf8'));
for(const pair of report.pairs)for(const result of pair.extensions){result.limits??={maxNodes:500,maxTiles:256};for(const attempt of result.priorAttempts??[])attempt.limits??={maxNodes:500,maxTiles:256};}
const summary={witnesses:0,independentGeometryChecks:0,seedHierarchy:{}};
const id=p=>`${p.variantId}@${key(p.origin)}`;
// A gap between two already-owned cells cannot be filled by a third tile:
// its bulk center would overlap one of those cells, and all other panel
// modifications lie in disjoint L1 neighborhoods.
for(const pair of report.pairs.filter(p=>p.extra)) {
 const index=indexState([{variantId:0,origin:[0,0,0]},pair]);
 let certificate=null;
 for(const [face,mask] of index.faceOccupancy) {
  if(mask===FULL)continue;
  const [axisText,cellText]=face.split(':'),a=cellText.split(',').map(Number),b=[...a];b[Number(axisText)]++;
  if(index.occupied.has(key(a))&&index.occupied.has(key(b))) {
   const probe=PROBES.findIndex((_,i)=>!(mask&(1<<i)));
   certificate={face,probe,position:PROBES[probe],adjacentOccupiedCells:[a,b]};break;
  }
 }
 assert.ok(certificate,'Every additional pair has a sealed gap');pair.gapCertificate=certificate;
}
for(const entry of report.witnesses) {
 clearCache();
 const witness=JSON.parse(readFileSync(resolve(out,entry.file),'utf8'));
 const {placements,seed,radius}=witness;
 const occupied=new Set(),faces=new Map();
 for(const p of placements) {
  for(const cell of VARIANTS[p.variantId].cells) {
   const cellKey=key(cell.map((v,i)=>v+p.origin[i]));assert.ok(!occupied.has(cellKey));occupied.add(cellKey);
  }
  for(const mark of worldMarks(p)) {
   const face=key(markPoint(mark)),other=faces.get(face);
   if(other) {
    const frame=reliefFrame(mark),axis=mark.direction.findIndex(v=>v!==0),tangents=[0,1,2].filter(i=>i!==axis);
    for(const {x,y} of PROBES) {
     const point=[...frame.center];point[tangents[0]]+=Math.SQRT2*x/100;point[tangents[1]]+=Math.SQRT2*y/100;
     assert.ok(Math.abs(reliefHeight(mark,point)+reliefHeight(other,point))<1e-10,'Actual geometry agrees at every shared face');
     summary.independentGeometryChecks++;
    }
   }
   faces.set(face,mark);
  }
 }
 assert.ok([...shellTarget(seed,radius)].every(cell=>occupied.has(cell)),'Every requested surrounding cell is covered');
 assert.equal(graphFor(placements).dead,null,'No known frontier dead point');
 assert.deepEqual(placements.slice(0,2).map(id),seed.map(id),'Both roots remain fixed');
 assert.equal(verifyPatch(placements).valid,true,'Post-search arrow-rule comparison');
 const present=new Set(placements.map(id));
 entry.seedParents=seed.map(tile=>{
  const compatible=[],complete=[];
  for(let child=0;child<8;child++) {
   const parent=parentContainingChild({...tile,rotation:VARIANTS[tile.variantId].rotation,size:2},child);
   const leaves=chairLeaves(1,parent.origin,parent.rotation),missing=leaves.filter(p=>!present.has(id(p)));
   if(!missing.length)complete.push(parent);
   try{indexState([...placements,...missing]);compatible.push(parent);}catch(error){if(!error.message.startsWith('Overlapping'))throw error;}
  }
  return {completeCount:complete.length,compatibleCount:compatible.length,complete,compatible};
 });
 summary.seedHierarchy[radius]??={seeds:0,completeUnique:0,compatibleUnique:0};
 for(const parent of entry.seedParents){const s=summary.seedHierarchy[radius];s.seeds++;s.completeUnique+=parent.completeCount===1;s.compatibleUnique+=parent.compatibleCount===1;}
 summary.witnesses++;
}
report.verification=summary;
writeFileSync(resolve(out,'results.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(summary));
