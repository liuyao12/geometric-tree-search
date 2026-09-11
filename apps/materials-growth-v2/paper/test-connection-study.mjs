import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {connectionDescriptor,descriptorDistance,fitConnectionLibrary,connectionScore,twistConnection} from '../connection-descriptor.mjs';
import {compileConnectionHypothesis} from '../connection-marking.mjs';
const report=JSON.parse(readFileSync(new URL('./connection-results.json',import.meta.url)));
for(const [p,hash] of Object.entries(report.sources))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex'),hash,p);
assert.equal(report.analyses.length,16);
assert.equal(report.verification.rotationChecks,2016);
assert.equal(report.verification.hingeBlindnessChecks,6048);
assert(report.verification.maxRotationError<1e-10);
assert.equal(report.verification.finiteChecks.length,32);
assert.equal(report.verification.finiteChecks.reduce((n,r)=>n+r.subsets,0),1024);
assert(report.verification.finiteChecks.every(r=>r.traceEqual));
assert.equal(report.verification.finiteChecks.filter(r=>r.terminal==='exhausted').length,1);
for(const row of report.analyses){
  for(const [index,g] of row.groups.entries())for(const [cutoff,summary] of [[row.threshold,row.summary[index]],[.06,row.strictSummary[index]]]){
    const known=g.scores.filter(s=>s.positive!==null),retained=known.filter(s=>s.positive<=cutoff);
    assert.equal(summary.retained,retained.length);assert.equal(summary.unknown,g.scores.length-known.length);
    assert.equal(summary.conditionalRejected,retained.reduce((n,s)=>n+s.twists.filter(x=>x!==null&&x>cutoff).length,0));
    if(!row.crossChannels)assert.equal(summary.conditionalRejected,0);
  }
}
for(const [domain,f] of Object.entries(report.illustrations)){
  const library=fitConnectionLibrary(f.training.map(sites=>({sites}))),first=report.analyses.find(r=>r.domain===domain&&r.fraction===1&&r.crossChannels).groups[0].scores[0];
  assert(Math.abs(connectionScore(library,f.sites)-first.positive)<1e-10);
  for(const [i,angle] of [Math.PI/3,2*Math.PI/3,Math.PI].entries())assert(Math.abs(connectionScore(library,twistConnection(f.sites,angle))-first.twists[i])<1e-10);
  const before=JSON.stringify(f.sites),twisted=twistConnection(f.sites,.4321);
  assert.equal(JSON.stringify(f.sites),before);
  assert(descriptorDistance(connectionDescriptor(f.sites,false),connectionDescriptor(twisted,false))<1e-10);
  const candidates=[{id:'a',t:[{point:'p',value:1}]},{id:'b',t:[{point:'q',value:1}]}];
  const unknown=f.sites.map(s=>({...s,species:'unseen label'}));
  const compiled=compileConnectionHypothesis(candidates,[{pair:['a','b'],sites:unknown}],library,.06);
  assert.equal(compiled.scores[0].status,'abstain');assert.equal(compiled.edges.length,0);
}
const audit=JSON.parse(readFileSync(new URL('./aperiodic-growth-results.json',import.meta.url)));
for(const [p,hash] of Object.entries(audit.sources))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex'),hash,p);
assert.equal(audit.rows.length,4);
const failure=audit.rows.find(r=>r.id==='asi'&&r.observedOnly).events.at(-1);
assert.equal(failure.event.kind,'unknown');assert.equal(failure.stats.backtracks,15);
console.log('PASS: source hashes, 16 score matrices, 32 finite trace records, invariance, illustration replay, unknown-stratum abstention, production failure preserved.');
