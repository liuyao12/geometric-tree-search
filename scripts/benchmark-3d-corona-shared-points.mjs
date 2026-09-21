// Compare the complete mutation trace with an explicitly supplied prior oracle.
// Example: git show d4377be:apps/3d-lattice-tiler/corona-graph.js > /tmp/oracle-before.mjs
// node scripts/benchmark-3d-corona-shared-points.mjs /tmp/oracle-before.mjs /tmp/corona-ab.json
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import * as current from '../apps/3d-lattice-tiler/corona-graph.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {pointSymmetries,neighboringPairs} from '../apps/3d-lattice-tiler/marking-learning.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const referenceURL=pathToFileURL(process.argv[2]),reference=await import(referenceURL);
const output=process.argv[3]??'/tmp/gcts-shared-points-ab.json';
const digest=data=>createHash('sha256').update(data).digest('hex');
const report={protocol:{referenceSha256:digest(await readFile(referenceURL)),currentSha256:digest(await readFile(new URL('../apps/3d-lattice-tiler/corona-graph.js',import.meta.url))),nodes:500,dependencyLimit:1000000,timeLimit:'none',trace:'Every apply and rollback, including the selected prefix after each mutation',scope:'Two diagnostic pairs per system; no complete-catalogue speedup claim'},rows:[]};
async function run(oracle,model,pair){
 const trace=createHash('sha256'),proto=oracle.CoronaGraph.prototype,originals={apply:proto.apply,rollback:proto.rollback};let mutations=0;
 for(const name of Object.keys(originals))proto[name]=function(...args){
  try{return originals[name].apply(this,args);}
  finally{trace.update(JSON.stringify([name,this.descriptors()]));mutations++;}
 };
 const start=performance.now();let result;
 try{for await(const event of oracle.checkCorona(model,pair,{nodes:500}))result=event;}
 finally{Object.assign(proto,originals);}
 const elapsedMs=performance.now()-start;
 return {elapsedMs,mutations,traceDigest:trace.digest('hex'),result};
}
for(const [tile,kind] of [['a2_turtle_prism','slab'],['p9-42947','vertex'],['p9-42947','voxel'],['p10-054782','voxel'],['fcc_pure','vertex']]){
 const record=POLYCUBE_GCTS_CANDIDATES.find(c=>c.id===tile);
 const model=kind==='voxel'?prepareVoxelPointModel(record.voxels,{name:tile,radius:1}):prepareModel({tile,radius:1,mirrors:kind==='slab',...(record?{custom:{name:tile,polycubes:[{voxels:record.voxels}]}}:{})});
 const pairs=neighboringPairs(model,pointSymmetries(model));
 for(let index=0;index<2;index++){
  const pair=pairs.next().value;if(!pair)break;
  const runs={};
  for(const version of index?['current','reference']:['reference','current'])runs[version]=await run(version==='current'?current:reference,model,pair);
  assert.deepEqual(runs.current.result,runs.reference.result,`${tile}/${kind}/${index}: final result`);
  assert.equal(runs.current.traceDigest,runs.reference.traceDigest,`${tile}/${kind}/${index}: complete mutation trace`);
  assert.equal(runs.current.mutations,runs.reference.mutations);
  const {placements,...result}=runs.current.result;
  const row={tile,kind,index,pair,result,referenceMs:runs.reference.elapsedMs,currentMs:runs.current.elapsedMs,mutations:runs.current.mutations,traceDigest:runs.current.traceDigest};
  report.rows.push(row);console.log(JSON.stringify(row));await writeFile(output,JSON.stringify(report,null,2)+'\n');
 }
}
