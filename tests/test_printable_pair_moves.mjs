import assert from 'node:assert/strict';
import {solveA2Tiling,tileOrientations,a2Transform,a2Add} from '../turtle-trefoil-printables/search/a2-tiling-engine.js';
import {options,loops,support,parity,placementMatrix} from '../turtle-trefoil-printables/search/model.js';
import {findSequence,stateKey} from '../turtle-trefoil-printables/search/flips.js';
globalThis.requestAnimationFrame=cb=>setTimeout(cb,0);
// Recompute t and m from prototypes, independently of flip-transformed caches.
function replay(ps){const totals=new Map(),marks=new Map();for(const p of ps){const sym=p.orientation.symmetry,base=tileOrientations(p.tile,loops[p.tile])[0];for(const e of base.occupancy.values()){const point=a2Add(a2Transform(e.point,sym),p.translation),k=point.join(','),n=(totals.get(k)||0)+e.weight;assert(n<=12);totals.set(k,n);assert.equal(p.occupancy.get(k)?.weight,e.weight);}for(const m of support.filter(m=>m.tile===p.tile)){const k=a2Add(a2Transform(m.point,sym),p.translation).join(',')+'|'+sym.permutation.indexOf(m.component),v=m.value*parity(sym.permutation);if(marks.has(k))assert.equal(marks.get(k),v);marks.set(k,v);}}return [...totals].sort();}
const result=await solveA2Tiling({...options('trefoil',10),targetPlacements:48,nodeLimit:2000});assert.equal(result.result,'yes');
const sequence=findSequence(result.placements);assert(sequence.moves.length>=8);assert(sequence.moves.some(m=>m.kind==='flip'));assert(sequence.moves.some(m=>m.kind==='turn'));
let previous=result.placements;const original=replay(previous),seen=new Set([stateKey(previous)]);
const world=(p,v)=>{const m=placementMatrix(p),a=m.slice(0,3).map(row=>row[0]*v[0]+row[1]*v[1]+row[2]*v[2]+row[3]);return [a[0],-a[1],4-a[2]];};
for(const move of sequence.moves){assert.deepEqual(replay(move.next),original);assert(!seen.has(stateKey(move.next)));seen.add(stateKey(move.next));assert.deepEqual(move.indices.map(i=>previous[i].tile),['trefoil','turtle']);for(let i=0;i<previous.length;i++){if(!move.indices.includes(i)){assert.strictEqual(previous[i],move.next[i]);continue;}for(const vertex of [[0,0,0],[1,0,0],[0,1,0],[0,0,4]]){const a=world(previous[i],vertex),b=world(move.next[i],vertex),v=a.map((n,j)=>n-move.axisPoint[j]),dot=v.reduce((n,x,j)=>n+x*move.axis[j],0),end=v.map((x,j)=>move.axisPoint[j]+2*dot*move.axis[j]-x);assert(end.every((n,j)=>Math.abs(n-b[j])<1e-8),'Animation endpoint must equal exact flipped CAD pose');}}previous=move.next;}
console.log(`${sequence.moves.length} distinct moves across ${sequence.states} states: independent t/m replay, fixed exterior, and 3D animation endpoints passed`);
