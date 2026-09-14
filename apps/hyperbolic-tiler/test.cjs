'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),H=require('./engine.js');
const close=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
for(const m of [2,3,4]){
 test(`m=${m}: geometry, congruence, convexity, and a non-overlapping known patch`,()=>{
  const spec=H.family(m),patch=H.construction(spec,2.5);assert.equal(spec.v.length,m+3);
  for(let i=0;i<m;i++)close(spec.lengths[i],spec.lengths[m+1]);
  close(spec.lengths[m],Math.log(m));close(spec.lengths[m+2],Math.log(m));
  for(const t of patch){for(let i=0;i<t.v.length;i++)close(H.distance(t.v[i],t.v[(i+1)%t.v.length]),spec.lengths[i]);
   for(let i=0;i<t.k.length;i++){const a=H.sub(t.k[(i+1)%t.k.length],t.k[i]),b=H.sub(t.k[(i+2)%t.k.length],t.k[(i+1)%t.k.length]);assert.ok(a[0]*b[1]-a[1]*b[0]>0);}
  }
  for(let i=0;i<patch.length;i++)for(let j=0;j<i;j++)assert.equal(H.overlaps(patch[i],patch[j]),false);
 });
 for(const prune of [false,true])test(`m=${m}, prune=${prune}: actual DFS covers disk; complete replay`,()=>{
  const spec=H.family(m),s=new H.Search(spec,{radius:1.8,seed:1,anglePrune:prune});let e,limit=50000;const replay=[];let pops=0;
  while(--limit&&(e=s.next())){
   if(e.type==='seed')replay.push(0);if(e.type==='place')replay.push(e.node);if(e.type==='backtrack'){assert.equal(replay.pop(),e.node);pops++;}
   assert.deepEqual(replay,s.tiles.map(t=>t.node));if(e.type==='solved')break;
  }
  assert.equal(e.type,'solved');assert.ok(H.frontier(s.tiles).every(e=>e.d>=Math.tanh(1.8)-1e-8));
  assert.equal(pops,s.stats.backtracks);if(!prune)assert.ok(pops>0,'Expected real removals, not just rejected candidates');
  for(let i=0;i<s.tiles.length;i++)for(let j=0;j<i;j++)assert.equal(H.overlaps(s.tiles[i],s.tiles[j]),false);
 });
}
test('angle feasibility is exactly the two permitted corner multisets',()=>{
 for(let a=0;a<5;a++)for(let b=0;b<3;b++)for(let c=0;c<4;c++)assert.equal(H.anglePossible({a,b,c}),(a<=2&&b===0&&c<=2)||(a===0&&b<=1&&c<=2));
});
test('bad geometry and T-junctions really are rejected',()=>{
 const sp=H.family(2),t=H.tile(sp.v,sp);assert.equal(H.validate(t,[t],false).reason,'interior overlap');
 const shifted=H.tile(sp.v.map(p=>H.invPhi(H.phi(p,[0,0]),[.05,0])),sp);assert.equal(H.validate(shifted,[t],false).ok,false);
 const k=[[0,0],[.2,0],[.2,.2],[0,.2]],other=[[.1,0],[.1,-.1],[.3,-.1],[.3,0]];
 const a=H.tile(k.map(H.fromKlein),{angles:['a','a','c','c']}),b=H.tile(other.map(H.fromKlein),{angles:['a','a','c','c']});
 assert.equal(H.validate(b,[a],false).reason,'non-edge-to-edge contact');
});
test('search safety limit is not an impossibility assertion',()=>{const s=new H.Search(H.family(2),{radius:2,maxTiles:2});let e,last;while((e=s.next()))last=e;assert.equal(last.type,'limit');});
test('seed and options reproduce the same entire event stream',()=>{function trace(){const s=new H.Search(H.family(2),{radius:1.5,seed:37,anglePrune:false});const result=[];let e;while((e=s.next()))result.push([e.type,e.node,e.depth,e.reason]);return result;}assert.deepEqual(trace(),trace());});
