// Node.js 24+, standard library only. Run from a repository checkout or download
// this script, preliminary-evidence.json and the four preliminary-checkers files.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {verifyCommonRepresentativeWitness} from './preliminary-checkers/research-common-representative-witness.mjs';
import {verifyRepresentativeSeparation} from './preliminary-checkers/research-verify-representative-separation.mjs';
import {admitExactPairDistances} from './preliminary-checkers/research-exact-pair-distance-admission.mjs';
import {certifyPairAdmittedTwoNeighborObstruction} from './preliminary-checkers/research-pair-admitted-two-neighbor-obstruction.mjs';
const raw=readFileSync(new URL('preliminary-evidence.json',import.meta.url));
assert.equal(createHash('sha256').update(raw).digest('hex'),'925bab7934529c7f4c66cf93ca85741cf5def4cc4d58b041e9b0496c8646b051');
const x=JSON.parse(raw);assert.equal(x.supports.length,6912);
for(const w of [x.witness,x.alternative]){
 assert.equal(w.points.length,34);
 assert.equal(verifyCommonRepresentativeWitness({...x,representatives:w.points,bindings:w.claims}).status,'verified-common-representative-witness');
 assert.equal(verifyRepresentativeSeparation(w.points,{terms:x.minimumSeparation.terms,maxPoints:4096,maxComparisons:1000000}).status,'verified-separation');
}
let admissionComparisons=0;for(const pose of [...x.fixedPoses,...x.newPoses]){const r=admitExactPairDistances({source:x.supports[pose.supportIndex],pose,tau:x.tau});assert.equal(r.status,'admitted-pair-distances');admissionComparisons+=r.counts.comparisons;}
const obstruction=certifyPairAdmittedTwoNeighborObstruction({supports:x.supports,center:x.triple[0],neighbors:x.triple.slice(1),epsilon:x.epsilon,tau:x.tau,radius:x.radius,premises:x.pairPremises});
assert.equal(obstruction.status,'certified-frozen-library-obstruction');assert.equal(obstruction.counts.pairs,83182);
console.log(JSON.stringify({verifiedUnions:2,pointsPerUnion:34,admittedPoses:14,admissionComparisons,obstruction:obstruction.status,donorPairs:obstruction.counts.pairs,scope:x.verificationScope},null,2));
