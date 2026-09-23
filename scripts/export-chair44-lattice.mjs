import fs from 'node:fs';
import {chair44PointExport} from '../3d-reptiles/chair/lattice-export.js';
const target=new URL('../3d-reptiles/chair/chair44-exact-points.json',import.meta.url);
const text=JSON.stringify(chair44PointExport())+'\n';
if(process.argv.includes('--check')){if(fs.readFileSync(target,'utf8')!==text)throw Error('Chair44 export is stale');}
else fs.writeFileSync(target,text);
console.log(`Chair44 exact export: ${Buffer.byteLength(text)} bytes; unchanged geometric solid.`);
