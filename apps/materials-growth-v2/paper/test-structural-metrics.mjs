import assert from 'node:assert/strict';
import {referenceBall,scoreStructure} from './structural-metrics.mjs';
const reference={cell:[1,1,1],sites:[{species:'X',fractional:[0,0,0]}]};
const full=referenceBall(reference,[0,0,0],9);
const exact=scoreStructure(reference,full);
assert.equal(exact.sitePrecision,1);
for(const w of exact.windows){assert.equal(w.siteRecall,1);assert.equal(w.neighborRecall,1);assert.equal(w.angleTV,0);}
const sparse=scoreStructure(reference,full.filter(a=>a.position[0]%2===0));
assert.equal(sparse.sitePrecision,1);assert(sparse.windows[2].siteRecall<.6);assert(sparse.windows[2].neighborRecall<1);
const shifted=full.map(a=>({...a,position:[-a.position[1]+2,a.position[0]+3,a.position[2]+4]}));
const aligned=scoreStructure(reference,shifted,{poses:[{r:[[0,1,0],[-1,0,0],[0,0,1]],t:[-3,2,-4]}]});
assert.equal(aligned.sitePrecision,1);assert.equal(aligned.windows[0].siteRecall,1);
const corrupted=scoreStructure(reference,[...full,{species:'X',position:[.25,.25,.25]}]);assert(corrupted.sitePrecision<1);
const duplicate=scoreStructure(reference,[...full,full[0]]);assert.equal(duplicate.duplicateSiteAssignments,1);
console.log('PASS: full reference, incomplete 100%-precision subset, rigid transform, off-site atom, duplicate detection.');
