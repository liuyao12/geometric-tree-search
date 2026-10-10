'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),root=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal'),N=require(path.join(root,'native-wang-search.js'));
const data=JSON.parse(fs.readFileSync(path.join(root,'native-wang-search-reader-001.json'))),result=N.validate(data),mutations=[];
const tests={
 'palette-pin':d=>d.inventory.literal_table_sha256='0'.repeat(64),
 'palette-count':d=>d.inventory.tile_types++,
 'state-count':d=>d.inventory.Q++,
 'start-state':d=>d.inventory.start++,
 'audit-binding':d=>d.audit.input_sha256='1'.repeat(64),
 'missing-case':d=>d.cases.pop(),
 'tile-north':d=>d.cases[0].runs.projected.tiles[0].N++,
 'tile-pair':d=>d.cases[0].runs.projected.tiles[0].E[0]++,
 'tile-identity':d=>d.cases[0].runs.projected.tiles[0].identity='0:0:0',
 'tile-outside':d=>d.cases[0].runs.projected.tiles[0].x=-1,
 'duplicate-center':d=>d.cases[0].runs.projected.tiles.push(d.cases[0].runs.projected.tiles[0]),
 'missing-center':d=>d.cases[0].runs.projected.tiles.pop(),
 'generation':d=>d.cases[0].runs.projected.tile_generations[0]=2,
 'root-value':d=>d.cases[0].runs.projected.boundary[0][1]=[0,0],
 'cone-value':d=>d.cases[0].runs.projected.certificate.pins[0][1]=0,
 'missing-cone':d=>d.cases[0].runs.projected.certificate.pins.pop(),
 'head-position':d=>d.cases[0].runs.projected.certificate.head_position=0,
 'incorrect-method':d=>d.cases[0].runs.projected.projected=false,
 'root-census-total':d=>d.cases[0].runs.projected.initial_candidate_nodes++,
 'root-census-cell':d=>d.cases[0].runs.projected.initial_census.pop(),
 'first-census':d=>d.cases[0].runs.projected.first_event.census[0][1]++,
 'point-check':d=>d.cases[0].runs.projected.point_checks.original.mark_points++,
 'median':d=>d.cases[0].timings.projected.median_seconds++,
 'order':d=>d.cases[0].timings.projected.samples[0].order.reverse(),
 'stage-clock':d=>d.cases[0].timings.projected.samples[0].stage_seconds=-1,
 'primary-clock':d=>d.cases[0].runs.projected.total_seconds=-1,
 'unknown-as-proof':d=>d.cases[5].runs.base.status='finite_exact_native_rectangle',
 'missing-raw-state':d=>d.inventory.rows=d.inventory.rows.filter(r=>r.q!==8642),
 'used-raw-action':d=>d.inventory.rows.find(r=>r.q===8642).actions[0][2]=0,
 'empty-input':d=>d.cases[0].spec.pattern[0]=[0]
};
for(const [name,edit] of Object.entries(tests)){const bad=JSON.parse(JSON.stringify(data));edit(bad);assert.throws(()=>N.validate(bad),undefined,name);mutations.push(name);}
assert.equal(data.cases[4].runs.base.first_event.kind,'dead');assert(data.cases[4].runs.base.initial_census.some(v=>v[1]===1));assert.equal(data.cases[5].runs.base.tiles.length,0);
console.log(JSON.stringify({...result,mutations_rejected:mutations,dead_before_forced:true,zero_budget_unknown:true,scope:'Displayed leaves and table actions, literal original/decorated point agreement, cone derivation and summary algebra. Full factored domain counts and fallback trees are covered by the separate all-tree audit.'}));
