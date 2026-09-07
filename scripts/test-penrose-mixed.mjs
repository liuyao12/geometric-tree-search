import assert from 'node:assert/strict';
import {MIXED_TEMPLATES} from '../assets/penrose-mixed-templates.js';
import {createMixedGrowth,mixedGeometryConflict,TILE_KINDS} from '../assets/penrose-mixed-growth.js';
import {tileStates,mixedMarkingsCompatible,tileMarkingValue} from '../assets/penrose-mixed-markings.js';
import {inspectionPoints,inspectionText} from '../apps/penrose-model-set/point-inspection.js';
import {num,sub,add,mul,div,conj,norm,pointInPolygon,clipSegment} from '../assets/penrose-polygon.js';
import {latticeKey} from '../assets/cyclotomic-five.js';
assert.deepEqual(MIXED_TEMPLATES.map(t=>t.kind).sort(),TILE_KINDS.slice().sort());
for(const t of MIXED_TEMPLATES){
 assert.equal(t.weights.reduce((s,n)=>s+n,0),(t.exactPoints.length-2)*5);
 assert(t.exactPoints.every(p=>p.denominator===1));
 if(t.presentation!=='P3')assert(t.occurrences>=5,'same fixed decoration must recur in independent locations');
 for(const b of t.bars)assert(b.family>=0&&b.family<5);
}
// Exact field inversion and a concave polygon with two disjoint clip intervals.
const z={coeff:[0,1,0,0],denominator:1};assert.equal(latticeKey(mul(z,div(num(1),z))),latticeKey(num(1)));
const P=(x,y)=>add(num(x),mul(z,num(y)));
const u=[[0,0],[3,0],[3,3],[2,3],[2,1],[1,1],[1,3],[0,3]].map(([x,y])=>P(x,y));
assert(!pointInPolygon(add(num(3,2),mul(z,num(2))),u));assert.equal(clipSegment(P(-1,2),P(4,2),u).length,2);
function grow(tileKinds,useMarkings,targetCount=20){const search=createMixedGrowth({tileKinds,useMarkings,extent:2,targetCount,nodeLimit:10000});let events=0;while(!search.next().done){assert(++events<50000);}const s=search.snapshot();assert.equal(s.status,'target reached');assert.equal(s.tiles.length,targetCount);assert(s.tiles.every(t=>tileKinds.includes(t.kind)));assert.equal(s.stats[useMarkings?'edgeChecks':'markingChecks'],0);return s;}
const p1=['p5','p3','p2','diamond','boat','star'],p2=['kite','dart'],mix=['thick','thin','kite','dart'];
for(const kinds of[p1,p2,mix])for(const enabled of[false,true]){
 const s=grow(kinds,enabled,kinds===p1?12:20),totals=new Map(),depths=new Map();
 for(const t of s.tiles){assert(t.exactPoints.every(p=>p.denominator===1));t.vertices.forEach((v,k)=>{totals.set(v,(totals.get(v)||0)+t.weights[k]);depths.set(v,Math.min(depths.get(v)??Infinity,t.generation));});}
 assert([...totals.values()].every(t=>t<=10));assert.equal(s.minimumFrontierGeneration,Math.min(...[...totals].filter(([,t])=>t<10).map(([v])=>depths.get(v))));
 for(let i=0;i<s.tiles.length;i++)for(let j=i+1;j<s.tiles.length;j++){
  const a=s.tiles[i],b=s.tiles[j];assert(!mixedGeometryConflict(a,b));
  for(const[e,sig]of tileStates(a)[0].signatures)if(tileStates(b)[0].signatures.has(e))assert.equal(sig,tileStates(b)[0].signatures.get(e));
  if(enabled)assert(mixedMarkingsCompatible(a,b,2));
 }
 if(kinds===mix&&enabled)assert.equal(new Set(s.tiles.map(t=>t.kind)).size,4,'a real mixed patch must contain P2 and P3 tiles');
 const points=inspectionPoints(s);assert(points.some(p=>p.intermediate&&p.extension));const t=s.tiles[0],bar=t.bars[0];assert.equal(tileMarkingValue(t,tileStates(t)[0],bar.from,2)[bar.family],1);assert.match(inspectionText(points.find(p=>p.vertex),enabled).coordinate,/x = /);
 console.log('ok:',kinds.join('/'),enabled?'markings':'edges',s.tiles.length,'tiles',s.stats.proposals,'proposals');
}
assert.throws(()=>createMixedGrowth({tileKinds:[]}));
