import assert from 'node:assert/strict';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {solveA2Tiling,makeHexBoundary,NoA2Marking} from '../assets/a2-tiling-engine.js';
import {frontierReference} from './corona-reference.mjs';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
const learner=createCoronaLearner('turtle'),pair=[learner.roots[0],{tile:'turtle',orientation:0,translation:[4,-8,4]}],required=learner.corePoints(pair);
const options={boundary:makeHexBoundary(10),tiles:['turtle'],allowReflections:true,initialPlacements:pair.map(learner.materialize),fixedInitialPlacements:true,completePointGrowth:true,requiredPoints:required,maximize:true,targetPlacements:Infinity,nodeLimit:5000,randomSeed:75193};
// Reproduce an actual complete core with dead outer points using the former
// criterion at runtime. No trained markings or generated witnesses are bundled.
const old=await solveA2Tiling({...options,marking:new NoA2Marking()}),oldSpecs=old.placements.map(p=>({tile:p.tile,orientation:p.orientation.index,translation:p.translation}));
assert.equal(old.result,'yes');const oldCheck=learner.verifyCorona(pair,oldSpecs);assert.ok(oldCheck.coreComplete);assert.equal(oldCheck.complete,false);assert.equal(oldCheck.frontierViable,false);assert.ok(oldCheck.deadPoints.length>0);
const core=new Set(required.map(p=>p.join()));assert.ok(oldCheck.deadPoints.every(p=>!core.has(p.join())));
const independent=frontierReference(learner,oldSpecs);assert.deepEqual(independent.deadPoints,oldCheck.deadPoints);
// Even at the target and with no placement budget left, this fixed completion
// must fail its outer-frontier check. Audit all graph incidences directly.
const rejected=await solveA2Tiling({...options,initialPlacements:old.placements,requireViableFrontier:true,nodeLimit:0,marking:new NoA2Marking(),auditFrontierGraph:true});assert.equal(rejected.result,'no');
// Rejecting this completion does not reject the pair: another corona is viable.
const result=await learner.examine({root:pair[0],attachment:pair[1],seed:75193,budget:5000,audit:true});assert.equal(result.status,'valid');assert.ok(result.verification.frontierViable);assert.ok(result.verification.frontierPoints>0);assert.deepEqual(frontierReference(learner,result.placements).deadPoints,[]);
const accepted=await solveA2Tiling({...options,initialPlacements:result.placements.map(learner.materialize),requireViableFrontier:true,nodeLimit:0,marking:new NoA2Marking(),auditFrontierGraph:true});assert.equal(accepted.result,'yes');
assert.equal((await learner.examine({root:pair[0],attachment:pair[1],budget:0})).status,'unresolved');
console.log(`PASS complete core with ${oldCheck.deadPoints.length} dead outer points rejected; alternate viable corona accepted; entire frontier graph and independent enumeration agree.`);
// A failed finite extension must not erase a t-legal candidate from a later
// frontier probe. This Hat sublattice search backtracks through that case.
const hat=createCoronaLearner('hat',{lattice:'turtle-sublattice'});
const hatResult=await hat.examine({root:hat.roots[0],attachment:{tile:'hat',orientation:0,translation:[0,6,-6]},seed:98158,budget:5000,audit:true});
assert.equal(hatResult.status,'valid');assert.ok(hatResult.backtracks>0);
assert.deepEqual(frontierReference(hat,hatResult.placements).deadPoints,[]);
console.log('PASS Hat sublattice backtracking retains all legal frontier candidates.');
