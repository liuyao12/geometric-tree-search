import {readFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {verify} from '../apps/3d-lattice-tiler/v2/search.js';
const path=process.argv[2];if(!path)throw Error('Pass an exported evidence JSON or JSON.gz file');
const bytes=await readFile(path),data=JSON.parse(path.endsWith('.gz')?gunzipSync(bytes):bytes);
let checked=0;
function walk(value){
  if(!value||typeof value!=='object')return;
  if(value.result==='finite_exact'){
    if(!value.model||!Array.isArray(value.placements))throw Error('Missing replay data');
    const check=verify(value.model,value.placements);if(!check.ok)throw Error(`Certificate failed: ${check.reason}`);checked++;
    return;
  }
  // Summary rows intentionally omit full model data.
  for(const [k,v] of Object.entries(value))if(k!=='rows')walk(v);
}
walk(data);if(!checked)throw Error('No finite exact certificates found');
console.log(`PASS: ${checked} independently replayed finite exact windows.`);
