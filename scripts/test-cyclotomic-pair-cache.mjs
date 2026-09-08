import assert from 'node:assert/strict';
import {selectedPenroseProblem,TILE_PRESETS} from '../assets/penrose-selection-problem.js';
import {geometricPairAllowed} from '../assets/cyclotomic-tile-catalog.js';
import {num,add} from '../assets/penrose-polygon.js';
const p=selectedPenroseProblem(TILE_PRESETS.all),delta={coeff:[7,-3,4,1],denominator:1};let checks=0;
for(let i=0;i<p.catalog.length;i+=3){const a=p.resolve(p.catalog[i].type,num(0));for(const b of p.movesAt(a.exactPoints[0]).filter((_,i)=>i%17===0)){
 const expected=geometricPairAllowed(a,b);assert.equal(p.pairAllowed(a,b),expected);assert.equal(p.pairAllowed(b,a),expected);assert.equal(p.pairAllowed(p.translate(a,delta),p.translate(b,delta)),expected);checks++;
}}
const limited=p.memoizePairs(geometricPairAllowed,{limit:3});for(let i=1;i<10;i++)limited(p.seedTile,p.translate(p.seedTile,num(i,100)));assert.equal(p.cacheStats().at(-1).entries,3);
assert(p.cacheStats()[0].hits>0);console.log('ok:',checks,'relative pairs, reverse order, exact translations, and bounded eviction');
