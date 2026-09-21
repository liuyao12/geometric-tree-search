import {writeFile,mkdir,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {checkCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {pointSymmetries,neighboringPairs} from '../apps/3d-lattice-tiler/marking-learning.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const out=process.argv[2]??'/tmp/gcts-fixed-seed-ab';await mkdir(out,{recursive:true});
const oracleSha256=createHash('sha256').update(await readFile(new URL('../apps/3d-lattice-tiler/corona-graph.js',import.meta.url))).digest('hex');
const rows=[];
for(const tile of ['p9-42947','p9-08203','p10-054782','p10-290795','fcc_pure']){
 const record=POLYCUBE_GCTS_CANDIDATES.find(c=>c.id===tile);
 const model=prepareModel({tile,radius:1,mirrors:false,...(record?{custom:{name:tile,polycubes:[{voxels:record.voxels}]}}:{})});
 const pairs=neighboringPairs(model,pointSymmetries(model));
 for(let index=0;index<2;index++){
  const pair=pairs.next().value;if(!pair)break;
  for(const fixedSeedFilter of index?[true,false]:[false,true]){
   const start=performance.now();let result;
   for await(const e of checkCorona(model,pair,{fixedSeedFilter,nodes:500,deadline:start+10000}))result=e;
   const {placements,...stats}=result;
   const row={tile,index,fixedSeedFilter,elapsedMs:performance.now()-start,...stats,traceDigest:createHash('sha256').update(JSON.stringify(placements)).digest('hex')};rows.push(row);console.log(JSON.stringify(row));
   await writeFile(`${out}/summary.json`,JSON.stringify({protocol:{oracleSha256,nodes:500,timeMs:10000,mirrors:false,pairsPerTile:2,ordering:'AB then BA, sequential',scope:'Same unmarked point model and search order; first pairs are a diagnostic sample, not a completed catalogue'},rows},null,2));
  }
 }
}
