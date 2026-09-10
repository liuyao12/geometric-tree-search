import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {QuotientGraph,reducePoint,hnfForms,periodVectors,searchPeriodic,verifyPeriodic,certifyIsohedral,exactOrientations,periodicStream} from '../apps/3d-lattice-tiler/periodic-search.js';
import {createTilingStream,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
const point=(pos,weight=1)=>({pos,weight});
const orientation=(points,index=0)=>({type:0,index,species:0,translationLattice:'z3',points,orientation:{occupancy:points,verts:[],faces:[]}});

// Exhaustive incidence and rollback comparison against an independent scan.
const rows=[[[0,1],[1,1]],[[0,2]],[[1,1],[2,1]],[[2,2]],[[0,1],[2,1]],[[1,2]]].map(entries=>({entries}));
const graph=new QuotientGraph(rows,3,2);
let visited=0;
function check(){
  visited++;
  const legal=rows.map((r,i)=>!graph.selected.has(i)&&r.entries.every(([p,w])=>graph.totals[p]+w<=2));
  assert.deepEqual([...graph.live],legal.map(Number));
  assert.deepEqual([...graph.degree],[0,1,2].map(p=>rows.filter((r,i)=>legal[i]&&r.entries.some(([q])=>p===q)).length));
  const before=JSON.stringify({totals:[...graph.totals],live:[...graph.live],degree:[...graph.degree],selected:[...graph.selected],trail:graph.trail});
  for(let i=0;i<rows.length;i++)if(legal[i]){const mark=graph.apply(i);check();graph.undo(i,mark);assert.equal(JSON.stringify({totals:[...graph.totals],live:[...graph.live],degree:[...graph.degree],selected:[...graph.selected],trail:graph.trail}),before);}
}
check();assert.ok(visited>20);
assert.equal(new QuotientGraph([{entries:[[0,1]]}],2,1).decision().kind,'dead','global dead outranks forced');
const forced=new QuotientGraph([{entries:[[0,1]]},{entries:[[0,1],[1,1]]}],2,1).decision();
assert.equal(forced.kind,'forced');assert.equal(forced.point,1);

// HNF invariance for skew periods, negative coordinates, and exact index counts.
for(let q=1;q<=8;q++)for(const diagonal of [true,false])for(const h of hnfForms(q,diagonal)) {
  const reps=new Set();
  for(let x=-3;x<=3;x++)for(let y=-3;y<=3;y++)for(let z=-3;z<=3;z++) {
    const p=[x,y,z],r=reducePoint(p,h);reps.add(r.join(','));
    for(const v of periodVectors(h))assert.deepEqual(reducePoint(p.map((x,i)=>x+v[i]),h),r);
  }
  assert.ok(reps.size<=q);
}
// A half-weight singleton needs two DISTINCT translates per torus point;
// a one-residue torus has only one and cannot be certified.
const half=[orientation([point([0,0,0],1)])];
const halfResult=await searchPeriodic(half,2,{periodic_patch_max_tiles:2,periodic_template_max_volume:1});
assert.equal(halfResult.status,'unknown');
const cube=[orientation([point([0,0,0])])];
const c=await searchPeriodic(cube,1,{tiling_strategy:'isohedral',periodic_patch_max_tiles:1});
assert.equal(c.status,'certified_tiling');assert.ok(c.certificate.isohedral);
assert.equal(verifyPeriodic(cube,1,{...c.certificate,motif:[...c.certificate.motif,...c.certificate.motif]}),false);
assert.equal(verifyPeriodic(cube,1,{...c.certificate,hnf:{...c.certificate.hnf,a:0}}),false);

// A valid periodic domino tiling with two local environments is NOT isohedral.
const domino=[orientation([point([0,0,0]),point([1,0,0])]),orientation([point([0,0,0]),point([0,1,0])],1)];
const motif=[...Array.from({length:4},(_,y)=>({prototile_idx:0,orientation_index:0,translation:[2,y,0]})),
  ...[2,3].map(y=>({prototile_idx:0,orientation_index:0,translation:[0,y,0]})),
  ...[0,1].map(x=>({prototile_idx:0,orientation_index:1,translation:[x,0,0]}))];
const noniso={hnf:{a:4,d:4,f:1,b:0,c:0,e:0},motif};
assert.ok(verifyPeriodic(domino,1,noniso));assert.equal(certifyIsohedral(domino,1,noniso,true),null);

const summaries=[];
for(const strategy of ['translational','isohedral']) {
  let final,snapshot;
  for await(const m of createTilingStream({mode_key:'mathematica_16_vertex',tiling_strategy:strategy,include_mirrors:true,periodic_patch_max_tiles:8,criterion:'count',target_val:24,time_limit_ms:30000},tileSpecs)) {
    if(m.type==='finished')final=m;if(m.type==='full_update')snapshot=m;
  }
  assert.equal(final.result_kind,'certified_tiling');assert.equal(final.tiling_evidence.patch_size,8);assert.equal(snapshot.tile_count,24);
  const t=tileSpecs.TILING_REGISTRY.mathematica_16_vertex.build()[0];t.__species_id=0;const mirror=t.get_mirror_copy();mirror.__species_id=0;
  const os=exactOrientations([t,mirror],24),cert=final.tiling_evidence.certificate;
  assert.ok(verifyPeriodic(os,24,cert));
  const damaged=structuredClone(cert);damaged.motif[0].translation[0]++;
  assert.equal(verifyPeriodic(os,24,damaged),false);
  if(strategy==='isohedral'){assert.equal(cert.isohedral.witnesses.length,8);assert.ok(certifyIsohedral(os,24,cert,true));}
  for(const p of snapshot.placements)assert.equal(p.color_id,p.periodic_motif_index%tileSpecs.COLOR_PALETTE.length);
  summaries.push(final);
}
// Cancelling while the consumer holds a checkpoint must release the suspended
// producer; otherwise a paused/closed worker could keep searching in background.
const token={stop:false},stream=periodicStream({periodic_patch_max_tiles:8,include_mirrors:true},
  [tileSpecs.TILING_REGISTRY.mathematica_16_vertex.build()[0]],24,tileSpecs.COLOR_PALETTE,token);
while((await stream.next()).value?.type!=='periodic_work') {}
await Promise.race([stream.return(),new Promise((_,reject)=>setTimeout(()=>reject(Error('checkpoint cancellation hung')),1000))]);
assert.equal(token.stop,true);
const stopped=await searchPeriodic(cube,1,{}, {stop:true});assert.equal(stopped.reason,'stopped');assert.equal(stopped.status,'unknown');
const capped=await searchPeriodic(domino,1,{periodic_patch_max_tiles:2,periodic_hnf_candidate_limit:1});assert.equal(capped.status,'unknown');
assert.ok(Object.values(tileSpecs.TILING_REGISTRY).every(t=>!t.census_candidate));
for(const id of ['mathematica_16_vertex','cube','tet_oct'])assert.ok(tileSpecs.TILING_REGISTRY[id]);
writeFileSync(new URL('../runs/3d-periodic-rewrite-20260910/regressions.json',import.meta.url),JSON.stringify({graph_states:visited,summaries},null,2));
console.log('Periodic rewrite: graph/exhaustive rollback, global scheduler, skew/negative HNF, multiplicity, damaged witnesses, nonisohedral rejection, eight-tile rediscovery, cancellation, limits and catalog preservation passed.', {graph_states:visited});
