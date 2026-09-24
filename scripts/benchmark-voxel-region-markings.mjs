// Headless research control: freshly proof-checked region exclusions become
// ordinary point markings in the unchanged reference growth engine.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {compileCertifiedPairs,certifiedSymmetries,pairOrbitKey} from '../apps/3d-lattice-tiler/certified-marking.js';
import {neighboringPairs,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {grow} from '../apps/3d-lattice-tiler/growth-search.js';
const args=process.argv.slice(2),option=(key,fallback)=>{const i=args.indexOf(key);return i<0?fallback:args[i+1];};
const folder=option('--input','/tmp/nonacube-region-screen'),out=option('--output','/tmp/nonacube-region-benchmark.json');
const checker=option('--drat-trim',null);if(!checker)throw Error('--drat-trim is required: saved exclusions must be independently re-proved');
execFileSync(option('--python','python3'),[new URL('./replay-voxel-pair-regions.py',import.meta.url).pathname,'--input',folder,'--drat-trim',checker,'--output',`${folder}/replay.json`],{stdio:'inherit'});
const replay=JSON.parse(fs.readFileSync(`${folder}/replay.json`));
const source=JSON.parse(fs.readFileSync(`${folder}/input.json`)),summary=JSON.parse(fs.readFileSync(`${folder}/summary.json`));
const model=prepareModel({tile:source.tile,mirrors:false,radius:1});
assert.deepEqual(source.model.orientations,model.orientations);assert.deepEqual(source.model.placementDomain,model.placementDomain);assert.equal(source.model.capacity,model.capacity);
const transforms=certifiedSymmetries(model),pairs=[...neighboringPairs(model,transforms)],catalogue=new Map(source.rows.map(r=>[r.key,r]));
assert.deepEqual(new Set(pairs.map(p=>pairOrbitKey(p,transforms))),new Set(catalogue.keys()));
assert.equal(source.rawPairs,pairs.length);
for(const [key,row] of catalogue)assert.equal(row.multiplicity,pairs.filter(p=>pairOrbitKey(p,transforms)===key).length);
const proofs=summary.rows.filter(r=>r.status==='excluded').map(r=>{
 assert(replay.checked.includes(r.id));assert(r.proof?.verified&&r.proof.checker==='DRAT-trim');assert.equal(pairOrbitKey(r.pair,transforms),r.key);assert.deepEqual(catalogue.get(r.key).pair,r.pair);
 return {...r,status:'invalid',certificate:{kind:'finite_window_rup',...r.proof}};
});
const seeds=option('--seeds','1,10,42').split(',').map(Number),targetTiles=Number(option('--target','32')),nodes=Number(option('--nodes','1000')),timeMs=Number(option('--seconds','15'))*1000;
const output={tile:source.tile,scope:'Different finite patch sets: exclusions preserve infinite tilings only. Pruning experiment, not a same-finite-problem speedup.',preparationMs:summary.totalMs,proofReplayMs:replay.elapsedMs,seeds,targetTiles,nodes,timeMs,rows:[]};
// The fixed illustrative orbit is selected by its geometry, not a presumed ID.
const exampleKey=source.tile==='nonacube_cross'?pairOrbitKey([{oi:0,translation:[0,0,0]},{oi:0,translation:[0,6,-4]}],transforms):proofs[0]?.key;
for(const [name,selected] of [['unmarked',[]],['single-pair',proofs.filter(r=>r.key===exampleKey)],['all-certified',proofs]]){
 const began=performance.now(),marking=compileCertifiedPairs(model,selected),keys=new Set(selected.map(r=>r.key));
 for(const pair of pairs)assert.equal(!pairCompatible(marking.fields,pair),keys.has(pairOrbitKey(pair,transforms)),'complete catalogue disagreement audit');
 const compilationMs=performance.now()-began;
 const marked={...model,required:[],orientations:model.orientations.map((o,i)=>({...o,marks:marking.fields[i]}))};
 for(const seed of seeds){
  let result;for await(const e of grow(marked,{mode:'free',seed,targetTiles,timeMs,nodes,learnedRestriction:!!selected.length}))if(e.type==='result')result=e;
  const row={name,seed,exclusions:selected.length,components:marking.componentCount,assignedValues:marking.values,compilationMs,result:result.result,reason:result.reason,placements:result.placements,verification:result.verification,stats:result.stats};
  output.rows.push(row);fs.writeFileSync(out,JSON.stringify(output));console.log(JSON.stringify({...row,placements:row.placements.length,verification:row.verification.ok}));
 }
}
