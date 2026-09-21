import {writeFile,mkdir,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {checkCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {pointSymmetries,neighboringPairs} from '../apps/3d-lattice-tiler/marking-learning.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const out=process.argv[2]??'/tmp/gcts-corona-cache-ab';await mkdir(out,{recursive:true});
const oracleSha256=createHash('sha256').update(await readFile(new URL('../apps/3d-lattice-tiler/corona-graph.js',import.meta.url))).digest('hex');
const rows=[];
for(const tile of ['p9-42947','p9-08203','p10-054782','p10-290795']){
 const record=POLYCUBE_GCTS_CANDIDATES.find(c=>c.id===tile),model=prepareVoxelPointModel(record.voxels),pairs=neighboringPairs(model,pointSymmetries(model));
 for(let index=0;index<2;index++){
  const pair=pairs.next().value;
  for(const retainBranchCaches of index?[false,true]:[true,false]){
   const start=performance.now();let result;
   for await(const e of checkCorona(model,pair,{retainBranchCaches,nodes:500,deadline:start+10000}))result=e;
   const {placements,...stats}=result;
   rows.push({tile,index,retainBranchCaches,elapsedMs:performance.now()-start,...stats,traceDigest:createHash('sha256').update(JSON.stringify(placements)).digest('hex')});console.log(JSON.stringify(rows.at(-1)));
   await writeFile(`${out}/summary.json`,JSON.stringify({protocol:{oracleSha256,model:'voxel-center-corner-1',nodes:500,timeMs:10000,mirrors:false,pairsPerTile:2,ordering:'AB then BA, sequential',experiment:'retain=false deletes branch caches and omits newly enumerated candidates blocked by that branch prefix',scope:'Diagnostic pairs, not completed catalogue'},rows},null,2));
  }
 }
}
