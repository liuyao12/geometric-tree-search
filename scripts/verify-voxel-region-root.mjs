// Independently enumerate every candidate at one root obligation, then verify
// a dead frontier after every possible placement. No DFS caches are trusted.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {compileCertifiedPairs} from '../apps/3d-lattice-tiler/certified-marking.js';
import {GrowthGraph,verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
import {allowedTranslation,add,sub,pointKey} from '../apps/3d-lattice-tiler/corona-graph.js';
const folder=process.argv[2]??'/tmp/nonacube-region-screen',out=process.argv[3]??'/tmp/nonacube-region-root.json';
const summary=JSON.parse(fs.readFileSync(`${folder}/summary.json`)),source=JSON.parse(fs.readFileSync(`${folder}/input.json`));
const model=prepareModel({tile:source.tile,mirrors:false,radius:1});assert.deepEqual(source.model.orientations,model.orientations);
const proofs=summary.rows.filter(r=>r.status==='excluded').map(r=>({...r,status:'invalid',certificate:r.proof}));
const fields=compileCertifiedPairs(model,proofs),marked={...model,orientations:model.orientations.map((o,i)=>({...o,marks:fields.fields[i]}))},root={oi:0,translation:[0,0,0]};
const graph=new GrowthGraph(marked);graph.apply(root,{root:true});const selected=graph.schedule();assert.equal(selected.kind,'branch');
const point=selected.point.pos,totals=new Map(),section=new Map();
for(const c of marked.orientations[root.oi].cells)totals.set(pointKey(add(c.pos,root.translation)),c.weight);
for(const m of marked.orientations[root.oi].marks)section.set(`${pointKey(add(m.pos,root.translation))}|${m.component}`,m.value);
assert((totals.get(pointKey(point))??0)>0&&totals.get(pointKey(point))<marked.capacity,'root obligation is exposed');
const domain=new Map();
for(const [oi,o] of marked.orientations.entries())for(const anchor of o.cells){
 const translation=sub(point,anchor.pos),id=`${oi}@${translation}`;
 if(!allowedTranslation(marked,translation)||id===`${root.oi}@${root.translation}`)continue;
 if(!o.cells.every(c=>(totals.get(pointKey(add(c.pos,translation)))??0)+c.weight<=marked.capacity))continue;
 if(!o.marks.every(m=>{const k=`${pointKey(add(m.pos,translation))}|${m.component}`;return !section.has(k)||section.get(k)===m.value;}))continue;
 domain.set(id,{oi,translation});
}
assert.deepEqual(new Set(domain.keys()),new Set([...selected.point.incident].filter(c=>c.valid).map(c=>`${c.oi}@${c.translation}`)));
const branches=[...domain.values()].map(placement=>{const replay=verifyGrowth(marked,[root,placement]);assert(!replay.ok);assert(replay.deadPoints.length);return {placement,deadPoints:replay.deadPoints};});
const result={verified:true,scope:'Conditional on independently proved region exclusions. Every candidate at the root obligation immediately leaves a globally dead point.',root,point,branches,exclusions:proofs.map(r=>r.id),components:fields.componentCount};
fs.writeFileSync(out,JSON.stringify(result));console.log(JSON.stringify(result));
