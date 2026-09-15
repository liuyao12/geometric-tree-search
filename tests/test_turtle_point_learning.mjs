import assert from 'node:assert/strict';
import { createModel, trainStep, freezeModel, loss, makeMarking, verifyPatch, TURTLE } from '../assets/turtle-point-learning.js';
import { FixedTurtleMarking, solveA2Tiling, makeHexBoundary } from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame = callback=>setTimeout(callback,0);
let fitted;
for(const seed of [1,7,99]){
 const model=createModel(seed),before=structuredClone(model);
 assert.throws(()=>freezeModel(model));
 for(let step=0;step<120;step++)trainStep(model);
 assert.ok(loss(model)<1e-9);
 assert.ok(model.anchors.every(a=>Math.abs(a.point.reduce((s,v)=>s+v,0))<1e-12));
 assert.ok(model.anchors.some((a,i)=>Math.abs(a.point[0]-before.anchors[i].point[0])>.1));
 assert.ok(model.anchors.some((a,i)=>Math.abs(a.t-before.anchors[i].t)>.1));
 fitted=freezeModel(model);
 const reference=new FixedTurtleMarking(1),learned=makeMarking(fitted);
 const p={tile:'turtle',id:'seed',orientation:TURTLE,translation:[0,0,0]};
 assert.deepEqual(learned.entries(p),reference.entries(p));
 const corrupt=structuredClone(model);corrupt.anchors[0].t=.01;assert.throws(()=>freezeModel(corrupt));
 const collision=structuredClone(model);collision.anchors[1].point=[...collision.anchors[0].point];assert.throws(()=>freezeModel(collision));
}
const result=await solveA2Tiling({boundary:makeHexBoundary(12),tiles:['turtle'],maximize:true,targetPlacements:12,nodeLimit:500,randomSeed:7,marking:makeMarking(fitted),auditFrontierGraph:true,initialPlacements:[{tile:'turtle',orientation:TURTLE,translation:[0,0,0]}]});
assert.equal(result.result,'yes');
const verification=verifyPatch(fitted,result.placements);assert.equal(verification.tiles,12);assert.ok(verification.completePoints>0);assert.ok(verification.frontierPoints>0);assert.ok(verification.matched>0);
assert.throws(()=>verifyPatch(fitted,[...result.placements,result.placements[0]]));
const invalid=structuredClone(result.placements);invalid[0].translation=[.1,0,-.1];assert.throws(()=>verifyPatch(fitted,invalid));
console.log(JSON.stringify({passed:true,seeds:3,frontierGraphAudit:true,verification},null,2));
