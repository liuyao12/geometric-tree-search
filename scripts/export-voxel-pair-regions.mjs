// Fresh unmarked pair catalogue; no saved labels or marking assignments.
import fs from 'node:fs';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {neighboringPairs} from '../apps/3d-lattice-tiler/marking-learning.js';
import {certifiedSymmetries,pairOrbitKey} from '../apps/3d-lattice-tiler/certified-marking.js';
const args=process.argv.slice(2),option=(key,fallback)=>{const i=args.indexOf(key);return i<0?fallback:args[i+1];};
const tile=option('--tile','nonacube_cross'),out=option('--output','/tmp/voxel-pair-regions-input.json');
const model=prepareModel({tile,mirrors:false,radius:1});
if(!model.orientations.every(o=>o.voxels&&!o.marks?.length))throw Error('Expected unmarked voxel model');
const transforms=certifiedSymmetries(model),byKey=new Map();let rawPairs=0;
for(const pair of neighboringPairs(model,transforms)){
 rawPairs++;const key=pairOrbitKey(pair,transforms);
 if(!byKey.has(key))byKey.set(key,{id:byKey.size,key,pair,multiplicity:0});
 byKey.get(key).multiplicity++;
}
const data={version:1,tile,model,rawPairs,rows:[...byKey.values()]};
fs.writeFileSync(out,JSON.stringify(data));console.log(JSON.stringify({output:out,rawPairs,orbits:data.rows.length}));
