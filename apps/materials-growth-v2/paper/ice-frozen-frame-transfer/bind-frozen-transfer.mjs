// Bind frame-exclusion evidence to the actual geometry pool and search receipts.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [dir,out]=process.argv.slice(2),read=n=>JSON.parse(readFileSync(`${dir}/${n}`));
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const manifest=read('manifest.json'),cohort=read('cohort-check.json'),pool=read('base-pool.json'),proposal=read('proposals.json'),summary=read('summary.json');
assert.equal(cohort.manifestHash,sha(`${dir}/manifest.json`));
assert.equal(cohort.targetHash,manifest.targetHash);
assert.equal(manifest.targetHash,sha(`${dir}/heldout-coordinates.json`));
assert.equal(pool.sourceHashes['heldout-coordinates.json'],manifest.targetHash);
assert(pool.noFixed&&!pool.usedSuppliedPoses&&proposal.externalTargets);
assert.deepEqual(pool.models.map(r=>r.id),cohort.targetIds);
assert.deepEqual(proposal.rows.map(r=>r.id),cohort.targetIds);
assert(pool.models.every(r=>r.model.initial.length===0));
const frozen=Object.fromEntries(Object.entries(manifest.sourceHashes).map(([p,h])=>[p.split('/').at(-1),h]));
assert.equal(pool.sourceHashes['gcts-ice-learned-point-support-v2.json'],frozen['gcts-ice-learned-point-support-v2.json']);
const base=read('base-search.json');assert.equal(base.poolHash,sha(`${dir}/base-pool.json`));
assert.equal(summary.baseSearchHash,sha(`${dir}/base-search.json`));
for(const run of summary.runs){
 assert.equal(run.markingHash,frozen['gcts-ice-tolerant-support-markings-v1.json']);
 assert.equal(run.searchHash,sha(`${dir}/interval-${run.channels}-search-v1.json`));
 assert.equal(run.checkHash,sha(`${dir}/interval-${run.channels}-check-v1.json`));
 assert.deepEqual(run.rows.map(r=>r.id),cohort.targetIds);
}
const result={manifestHash:sha(`${dir}/manifest.json`),cohortCheckHash:sha(`${dir}/cohort-check.json`),summaryHash:sha(`${dir}/summary.json`),
 binderHash:sha(new URL(import.meta.url)),generatorHash:pool.codeHash,sourcePoolHash:sha(`${dir}/base-pool.json`),proposalHash:sha(`${dir}/proposals.json`),
 targetIds:cohort.targetIds,preparationAndDiagnosticSeconds:proposal.rows.reduce((a,r)=>a+r.seconds,0),
 proposalPassesTruncated:proposal.rows.filter(r=>r.truncated).length,
 baseComplete:base.results.filter(r=>r.complete).length,markedComplete:summary.runs.map(r=>({channels:r.channels,complete:r.complete})),
 admission:'Excluded recorded frames and exact source geometries, not independent trajectories or verified matched conditions.'};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify(result));
