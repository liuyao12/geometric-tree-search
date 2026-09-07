import assert from 'node:assert/strict';
import {hermiteDomains,quotientIndex,exactDomainModel,periodicDomainSearch} from '../apps/3d-lattice-tiler/periodic-domain-search.js';
import {createTilingStream,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
assert.equal([...hermiteDomains(2)].length,7);
assert.equal([...hermiteDomains(4)].length,35);
for(const h of hermiteDomains(4))for(const p of [[-5,2,-3],[0,0,0],[7,-8,1]]) {
 const [a,b,c,d,e,f]=h;
 for(const v of [[a,0,0],[b,d,0],[c,e,f]])assert.equal(quotientIndex(p,h),quotientIndex(p.map((x,i)=>x+v[i]),h));
}
assert.equal(exactDomainModel([{points:[{pos:[0,0,0],weight:0.1}]}],1),null);
const impossible=exactDomainModel([{points:[{pos:[0,0,0],weight:2}]}],3);
assert.ok(![...periodicDomainSearch(impossible,{maxCopies:6})].some(e=>e.type==='solution'));
// Unbounded discovery does not finish on these failed domains. A suspended
// generator resumes its exact cursor rather than repeating its first HNF.
const stream=periodicDomainSearch(impossible);let last=0,count=0;
while(last<8){const e=stream.next();assert.equal(e.done,false);if(e.value.type==='domain'){assert.ok(e.value.domains>count);count=e.value.domains;last=e.value.determinant;}}
stream.return();
for(const polycube_lattice of ['fcc','half'])for(const tiling_strategy of ['translational','isohedral']) {
 let final;for await(const e of createTilingStream({mode_key:'cube',polycube_lattice,tiling_strategy,criterion:'count',target_val:8,time_limit_ms:3000},tileSpecs))if(e.type==='finished')final=e;
 assert.equal(final.success,true);assert.equal(final.tile_count,8);
 assert.equal(final.search_stats.structural_scope,`exact_polycube_${polycube_lattice}`);
}
for(const tiling_strategy of ['translational','isohedral'])for(const criterion of ['count','shell']) {
 let final;
 for await(const e of createTilingStream({mode_key:'cube',tiling_strategy,criterion,target_val:criterion==='count'?40:2,time_limit_ms:5000},tileSpecs))if(e.type==='finished')final=e;
 assert.equal(final.success,true);assert.equal(final.result_kind,'certified_tiling');
 assert.equal(final.tiling_evidence.kind,tiling_strategy==='isohedral'?'isohedral_certificate':'translational_certificate');
 assert.equal(final.search_stats.structural_phase,'expansion');
 if(criterion==='count')assert.equal(final.tile_count,40);
}
let hard;
for await(const e of createTilingStream({mode_key:'a2_sliced_9_11364',tiling_strategy:'translational',criterion:'count',target_val:1,time_limit_ms:250},tileSpecs))if(e.type==='finished')hard=e;
assert.equal(hard.success,false);assert.equal(hard.can_tile,null);
assert.equal(hard.search_stats.termination_reason,'time_limit');
assert.notEqual(hard.search_stats.termination_reason,'translational_growth_goal_without_certificate');
assert.equal(hard.search_stats.structural_phase,'discovery');
// Synthetic exact weight obstruction: every contribution is 32, capacity 48.
// This exercises the engine's scoped negative result, not just the enumerator.
const build=()=>{const t=tileSpecs.TILING_REGISTRY.a2_sliced_9_11364.build()[0];t.unique_orientations=t.unique_orientations.map(o=>({...o,occupancy:[{pos:[0,0,0],weight:32}]}));return[t];};
const specs={...tileSpecs,TILING_REGISTRY:{...tileSpecs.TILING_REGISTRY,synthetic:{name:'Synthetic weight control',build}}};
let negative;for await(const e of createTilingStream({mode_key:'synthetic',tiling_strategy:'isohedral',criterion:'count',target_val:8,time_limit_ms:3000},specs))if(e.type==='finished')negative=e;
assert.equal(negative.result_kind,'no_isohedral_tiling');assert.equal(negative.can_tile,null);
assert.equal(negative.tiling_evidence.can_tile_isohedrally,false);
assert.equal(negative.tiling_evidence.complete_motif_bound,6);
console.log('HNF enumeration, exact integer arithmetic, finite negative exhaustion, unbounded continuation, certified count/shell expansion in both lanes and no-certificate goal regression passed.');
