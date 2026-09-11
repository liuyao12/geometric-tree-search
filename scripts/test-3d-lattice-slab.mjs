import assert from 'node:assert/strict';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {PointGraph,verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {A2_TILE_LOOPS,tileOrientations} from '../assets/a2-tiling-engine.js';
const sum=p=>p.reduce((a,b)=>a+b,0),k=p=>p.join(',');
for(const name of ['hat','turtle'])for(const mirrors of [false,true]){
  const model=prepareModel({tile:`a2_${name}_prism`,radius:2,mirrors});
  assert.equal(model.required.length,38);assert.equal(model.orientations.length,mirrors?12:6);
  const original=tileOrientations(name,A2_TILE_LOOPS[name]);
  for(const o of model.orientations){
    const planar=original.find(p=>p.symmetry.sign===o.planarSymmetry.sign&&String(p.symmetry.permutation)===String(o.planarSymmetry.permutation));
    const table=new Map([...planar.occupancy.values()].map(c=>[k(c.point),c.weight]));
    assert.equal(o.cells.length,name==='hat'?22:26);
    assert.equal(o.cells.filter(c=>c.kind==='cap_interior').length,name==='hat'?2:4);
    for(const c of o.cells){
      assert([0,3].includes(sum(c.pos)));assert((c.pos[0]-c.pos[1])%3===0);assert((c.pos[1]-c.pos[2])%3===0);
      const layer=sum(c.pos)/3,planarWeight=table.get(k(c.pos.map(x=>x-layer)));
      assert.equal(c.weight,4*planarWeight); // exactly twice the old 2*a cap weight
      if(c.kind==='cap_interior')assert.equal(c.weight,model.capacity);
    }
  }
  const graph=new PointGraph(model),initial=graph.digest();
  // Exhaustive alignment oracle independent of PointGraph's enumeration.
  const expected=new Set();
  for(const q of model.required)for(const [oi,o] of model.orientations.entries())for(const c of o.cells){
    const t=q.pos.map((x,i)=>x-c.pos[i]);if(sum(t)!==0)continue;
    if((t[0]-t[1])%3||(t[1]-t[2])%3)continue;expected.add(`${oi}@${t}`);
  }
  assert.deepEqual(new Set(graph.candidates.map(c=>c.id)),expected);
  for(const c of graph.candidates.slice(0,15)){
    assert.equal(sum(c.translation),0);const mark=graph.apply(c);graph.verifyDomains();
    for(const cell of c.cells)if(cell.weight===model.capacity){assert.equal(graph.totals.get(cell.k),model.capacity);const point=graph.points.get(cell.k);if(point){assert.equal(point.degree,0);assert.notEqual(graph.schedule().point,point);}}
    graph.rollback(mark);assert.equal(graph.digest(),initial);
  }
  const interior=graph.candidates.find(c=>c.cells.some(p=>p.weight===model.capacity&&graph.points.has(p.k)));
  assert(interior);graph.apply(interior);
  assert(graph.selected[0].cells.some(p=>graph.points.has(p.k)&&p.weight===model.capacity&&graph.totals.get(p.k)===48));
  assert.equal(verify(model,[{oi:0,translation:[1,1,1]}]).reason,'translation leaves slab');
  assert.equal(verify(model,[{oi:0,translation:[1,0,-1]}]).reason,'translation leaves sublattice');
}
for(const name of ['hat','turtle'])for(const mode of ['free','gcts','rl','both']){
  let result;for await(const e of runExperiment({tile:`a2_${name}_prism`,radius:1,mirrors:true,mode,seed:1,timeMs:3000,nodes:10000}))if(e.type==='result')result=e;
  assert.equal(result.result,'finite_exact',`${name} ${mode}`);assert(verify(result.model,result.placements).ok);
}
let probe;for await(const e of runExperiment({tile:'a2_hat_prism',radius:1,action:'probe',strategy:'translational'}))probe=e;
assert.equal(probe.type,'error');assert.match(probe.message,/one-slab/);
const cube=prepareModel({tile:'cube',radius:1});assert.equal(cube.required.length,27);assert.equal(cube.slab,undefined);
console.log('PASS: doubled cap weights; demo index-3 support; complete slab incidence; saturated interiors excluded from frontier; rollback; all four lanes verified; old 3D probe rejected for slab; cube unchanged.');
