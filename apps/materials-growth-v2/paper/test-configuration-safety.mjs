import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=name=>JSON.parse(fs.readFileSync(new URL(name,import.meta.url)));
const sha=name=>crypto.createHash('sha256').update(fs.readFileSync(new URL(name,import.meta.url))).digest('hex');
const a=read('configuration-safety-results.json'),b=read('envelope-results.json');
assert.equal(a.runnerSha256,sha('configuration-safety.mjs'));assert.equal(b.runnerSha256,sha('envelope-study.mjs'));
assert.equal(a.dataset.sha256,b.datasetSha256);
for(const [r,min,max] of [[a,24,95],[b,96,167]]){
  const ids=Object.values(r.split).flat();assert.equal(new Set(ids).size,72);assert.equal(Math.min(...ids),min);assert.equal(Math.max(...ids),max);
  assert.deepEqual(Object.values(r.split).map(x=>x.length),[48,12,12]);
}
assert.equal(a.results.length,18);assert.equal(b.results.length,3);
function verify(record,frames,reject){
  const perFrame=frames.map(f=>{let rejected=0,unknown=0,twistRejected=0,twistKnown=0;for(const c of f.connections){if(!c.positive){unknown++;continue;}if(reject(c.positive)){rejected++;continue;}for(const t of c.twists)if(t){twistKnown++;if(reject(t))twistRejected++;}}return {id:f.id,total:f.connections.length,rejected,unknown,twistRejected,twistKnown};});
  assert.deepEqual(record.perFrame,perFrame);assert.equal(record.preserved,perFrame.filter(f=>!f.rejected).length);
  for(const key of ['total','rejected','unknown','twistRejected','twistKnown'])assert.equal(record[key],perFrame.reduce((s,f)=>s+f[key],0));
  assert.equal(record.promotion,record.preserved>=11&&record.twistKnown>0&&record.twistRejected/record.twistKnown>=.1&&record.unknown===0);
}
for(const r of a.results){
  const raw=a.rawScores.find(s=>s.count===r.count),values=raw.calibration.flatMap(f=>f.connections.filter(c=>c.positive).map(c=>c.positive[r.score])).sort((a,b)=>a-b);
  assert.equal(r.threshold,values[r.policy==='maximum'?values.length-1:Math.ceil(.99*values.length)-1]);
  verify(r,raw.test,s=>s[r.score]>r.threshold);
}
const reject=(s,name)=>name==='conjunction'?s.baseline>b.cutoffs.baseline||s.envelope>b.cutoffs.envelope:s[name]>b.cutoffs[name];
for(const name of ['baseline','envelope'])assert.equal(b.cutoffs[name],Math.max(...b.calibration.flatMap(f=>f.connections.filter(c=>c.positive).map(c=>c.positive[name]))));
for(const r of b.results)verify(r,b.test,s=>reject(s,r.name));
const inc={eligible:0,baselineOnly:0,envelopeOnly:0,both:0,neither:0};
for(const f of b.test)for(const c of f.connections)if(c.positive&&!reject(c.positive,'conjunction'))for(const t of c.twists)if(t){inc.eligible++;const x=reject(t,'baseline'),y=reject(t,'envelope');inc[x&&y?'both':x?'baselineOnly':y?'envelopeOnly':'neither']++;}
assert.deepEqual(b.incremental,inc);
assert.equal([...a.results,...b.results].filter(r=>r.promotion).length,0);
console.log('PASS: disjoint splits, frozen runner hashes, 21 settings replayed from raw scores, calibration cutoffs, configuration survival, incremental baseline comparison');
