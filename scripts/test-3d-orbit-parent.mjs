// Explicit source migration preserves receipts; imports may not change labels
// for a different pair or replace a proved result by a conflicting one.
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=await mkdtemp(join(tmpdir(),'gcts-orbit-parent-')),sha=b=>createHash('sha256').update(b).digest('hex');
const run=args=>execFileSync(process.execPath,['scripts/learn-3d-voxel-pair-catalog.mjs','--tile=cube','--pair-ms=10000','--frontier=occupancy',...args],{encoding:'utf8',stdio:'pipe'});
run([`--output=${root}/parent`,'--max-groups=1']);
let parent=JSON.parse(await readFile(`${root}/parent/checkpoint.json`));
// Model an older source revision; direct resume must reject the change.
parent.sources['old-source']='historical';await writeFile(`${root}/parent/checkpoint.json`,JSON.stringify(parent));
assert.throws(()=>run([`--output=${root}/parent`,'--resume=true']),/source version changed/);
run([`--output=${root}/child`,`--parent=${root}/parent`,'--frontier-batch=4']);
const child=JSON.parse(await readFile(`${root}/child/summary.json`));
assert.equal(child.learning.counts.valid,26);assert.equal(child.learning.counts.unresolved,0);assert.equal(child.protocol.parents.length,1);assert.equal(child.protocol.runs[0].frontierBatch,4);
const original=JSON.parse(await readFile(`${root}/parent/${parent.groups[0].file}`));
for(const [kind,mutate] of [['wrong-pair',r=>r.problemSha256='wrong'],['conflict',r=>r.status='invalid']]){
 const r=structuredClone(original);mutate(r);const file=`${root}/${kind}.json`,raw=JSON.stringify(r);await writeFile(file,raw);
 const manifest=`${root}/${kind}-manifest.json`;await writeFile(manifest,JSON.stringify({sources:{},rows:[{orbit:0,file,sha256:sha(raw)}]}));
 assert.throws(()=>run([`--output=${root}/${kind}-child`,`--parent=${root}/parent`,`--resolved=${manifest}`]),/another problem|conflicts with a resolved/);
}
console.log('PASS explicit parent migration, inherited positive replay, full cube completion, and rejection of mismatched/conflicting imports.');
