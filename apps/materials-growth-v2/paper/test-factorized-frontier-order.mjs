import assert from 'node:assert/strict';
import {factorizedDecision,FactorizedCandidateDomain} from './factorized-candidate-domain.mjs';
let count=0;
function* permutations(a){if(!a.length){yield [];return;}for(let i=0;i<a.length;i++)for(const r of permutations(a.filter((_,j)=>j!==i)))yield [a[i],...r];}
const action=d=>['dead','unknown'].includes(d.kind)?{kind:d.kind}:d;
// Enumerate all degree/complete flags and all orders, including distant dead
// points, incomplete zero domains, and forced/branch ties at two generations.
for(let code=0;code<4096;code++){
 let n=code;const points=[];
 for(let i=0;i<4;i++){const value=n%8;n=Math.floor(n/8);points.push({id:String(i),generation:i%2,complete:value<4,blocks:[new FactorizedCandidateDomain(value%4,1)]});}
 const expected=action(factorizedDecision(points));
 for(const order of permutations(points)){assert.deepEqual(action(factorizedDecision(order)),expected);count++;}
}
console.log(JSON.stringify({states:4096,permutations:count,actionInvariant:true,limit:'Only diagnostic dead/unknown point identity may differ; no point-conditioned pruning is enabled.'}));
