import assert from 'node:assert/strict';
import {patchPeriodProposals} from './lib/patch-period-proposals.mjs';
const cube=[[0,0,0]],placements=[];for(let x=0;x<2;x++)for(let y=0;y<2;y++)for(let z=0;z<2;z++)placements.push({oi:0,translation:[2*x,2*y,2*z]});
const result=patchPeriodProposals(cube,placements);assert.ok(result.found);assert.ok(result.certificate.verification.verified);
assert.equal(patchPeriodProposals(cube,placements.slice(0,2)).found,false);
assert.throws(()=>patchPeriodProposals(cube,[placements[0],{oi:0,translation:[1,0,0]}]),/even/);
console.log('PASS period proposal, independent quotient replay, insufficient-rank and invalid-domain controls.');
