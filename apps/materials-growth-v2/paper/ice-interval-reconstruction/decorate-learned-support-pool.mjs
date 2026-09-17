// Transfer training-only invariant interval codes to independently registered poses.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {basename} from 'node:path';
const [poolPath,supportPath,markingPath,channelArg,out]=process.argv.slice(2);
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>JSON.parse(readFileSync(p));
const pool=read(poolPath),support=read(supportPath),markings=read(markingPath),channels=Number(channelArg);
assert.equal(pool.sourceHashes[basename(supportPath)],sha(supportPath));
assert.equal(markings.sourceHashes[basename(supportPath)],sha(supportPath));
assert.equal(markings.radius,.5);
const run=markings.runs.find(r=>r.channels===channels);assert(run);
assert.equal(run.values.length,support.anchors.length);
const byType=new Map();
support.anchors.forEach((a,i)=>{if(!byType.has(a.type))byType.set(a.type,[]);byType.get(a.type).push(i);});
for(const row of pool.models)for(const candidate of row.model.candidates){
 assert.equal(candidate.m.length,0);
 const g=row.geometry[candidate.id],anchors=byType.get(g.type);assert.equal(anchors.length,g.ids.length);
 assert.deepEqual(candidate.t,g.ids.map((a,i)=>({point:`a:${a}`,value:g.units[i]})));
 candidate.m=anchors.flatMap((index,i)=>{
  assert.equal(2*support.anchors[index].t,g.units[i]);
  return run.values[index].map((v,k)=>({point:`a:${g.ids[i]}`,channel:String(k),lo:v-.5,hi:v+.5}));
 });
}
pool.sourcePoolHash=sha(poolPath);
pool.marking={hash:sha(markingPath),channels,radius:.5,action:'identity',representation:'Cartesian product of scalar closed intervals',
 support:'positive t anchors only',status:'learned hypothesis; not proved redundant',adapterHash:sha(new URL(import.meta.url))};
pool.scope='Finite known-target registration pool with training-only interval markings. All geometry candidates retained. This marked problem may have fewer solutions than the unmarked source; failure does not imply unmarked impossibility. No learned extended support or joint anchor/t/m optimization.';
writeFileSync(out,JSON.stringify(pool),{flag:'wx'});
console.log(JSON.stringify({channels,configurations:pool.models.length,markingHash:pool.marking.hash}));
