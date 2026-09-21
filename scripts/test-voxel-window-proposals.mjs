import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';import {join} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {pairOrbits} from './lib/3d-pair-orbits.mjs';
const dir=await mkdtemp(join(tmpdir(),'gcts-window-proposal-test-'));
const sha=x=>createHash('sha256').update(x).digest('hex'),canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
try{
 const model=prepareVoxelPointModel([[0,0,0]],{radius:0}),orbits=pairOrbits(model),data={model,fixed:[{oi:0,translation:[0,0,0]}]},placements=[];
 for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)placements.push({oi:0,translation:[2*x,2*y,2*z]});
 await mkdir(join(dir,'catalog'));
 await writeFile(join(dir,'catalog/pair-0.json'),JSON.stringify({model,pair:orbits.groups[0].pair}));
 const checkpoint={modelSha:sha(JSON.stringify(model)),groups:{}};
 await writeFile(join(dir,'catalog/checkpoint.json'),JSON.stringify(checkpoint));
 await writeFile(join(dir,'input.json'),JSON.stringify(data));
 await writeFile(join(dir,'window.json'),JSON.stringify({status:'valid',placements,problemSha256:sha(JSON.stringify(canonical(data))),stats:{elapsedMs:0}}));
 const run=name=>execFileSync(process.execPath,['scripts/propose-voxel-window-pairs.mjs',`--catalog=${dir}/catalog`,`--input=${dir}/input.json`,`--result=${dir}/window.json`,`--output=${dir}/${name}`,'--max-pairs=1','--pair-ms=1000'],{stdio:'pipe',timeout:20000});
 run('one');const report=JSON.parse(await readFile(join(dir,'one/summary.json'))),manifest=JSON.parse(await readFile(join(dir,'one/resolved.json')));
 assert.equal(report.rows.length,1);assert.equal(report.rows[0].status,'valid');assert.ok(report.rows[0].stats.phaseHints>0);assert.equal(manifest.rows.length,1);
 for(let i=0;i<orbits.groups.length;i++)checkpoint.groups[i]={status:'valid'};
 await writeFile(join(dir,'catalog/checkpoint.json'),JSON.stringify(checkpoint));run('empty');
 assert.deepEqual(JSON.parse(await readFile(join(dir,'empty/summary.json'))).rows,[]);assert.deepEqual(JSON.parse(await readFile(join(dir,'empty/resolved.json'))).rows,[]);
 console.log('PASS independently replayed transported hints, explicit full corona labels, and empty proposal reports.');
}finally{await rm(dir,{recursive:true,force:true});}
