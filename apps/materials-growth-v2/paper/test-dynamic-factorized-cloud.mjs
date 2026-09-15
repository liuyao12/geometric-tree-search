import assert from 'node:assert/strict';
import {makeFactorizedCloudSearch} from './factorized-cloud-search.mjs';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
import {InterleavedFactorizedSearch} from './interleaved-factorized-search.mjs';
import {CoupledEndpointSearch} from './coupled-endpoint-search.mjs';
const Engine=process.argv.includes('--coupled')?CoupledEndpointSearch:process.argv.includes('--interleaved')?InterleavedFactorizedSearch:DynamicFactorizedSupportSearch;
const cloud=(x,reverse=false)=>({colors:[[0],[0]],vectors:reverse?[[1+x,0,0],[x,0,0]]:[[x,0,0],[1+x,0,0]]});
const model={capacity:2,cloudRadius:.1,required:['a','b'],blocks:[0,1].map(i=>({id:String(i),inventory:String(i),t:[{point:'a',value:1},{point:'b',value:1}],markPoints:['a','b'],endpointChoices:[[{cloud:i}],[{cloud:i}]]}))};
const build=pool=>makeFactorizedCloudSearch(model,pool,{Engine});
const good=build([cloud(0),cloud(.19,true)]);
const root=good.blocks.map(b=>b.domain.count.toString());
good.advance();good.advance();assert.equal(good.advance().kind,'complete');assert(good.cloudCheck().valid);
good.undo(0);assert.deepEqual(good.blocks.map(b=>b.domain.count.toString()),root);
// Distinct-axis signatures alone would pass, but no true bijection at radius0.
const crossed=[{colors:[[0],[0]],vectors:[[0,0,0],[1,1,0]]},{colors:[[0],[0]],vectors:[[0,1,0],[1,0,0]]}];
const bad=makeFactorizedCloudSearch({...model,cloudRadius:0},crossed,{Engine});assert.equal(bad.advance().kind,'exhausted');
// Two-sided membership guard: legal midpoint exists, even though the current
// common-value proposer may not find it. Support must not prune this case.
const guarded=build([cloud(0),cloud(.20000000015)]);
assert(guarded.blocks.every(b=>b.domain.count===1n));guarded.advance();guarded.advance();assert.equal(guarded.advance().kind,'unknown');assert.notEqual(guarded.status,'exhausted');
assert.throws(()=>makeFactorizedCloudSearch({...model,capacity:1},[cloud(0),cloud(0)],{Engine}),/half-weight/);
console.log(JSON.stringify({coupled:Engine===CoupledEndpointSearch,interleaved:Engine===InterleavedFactorizedSearch,permutedCloudCompletion:true,rootRollback:true,signatureFalsePositiveRejected:true,twoSidedGuardPreserved:true,unknownNotPruned:true,invalidCapacityRejected:true}));
