import assert from 'node:assert/strict';
import {VectorMarkings} from '../apps/3d-lattice-tiler/vector-markings.js';
const prepareLatticeSearch = tiles => tiles.map((t,type) => t.unique_orientations.map((orientation,index) => ({orientation,type,index})));
const tile=weights=>({unique_orientations:[{occupancy:weights.map((weight,x)=>({pos:[x,0,0],weight})),verts:[],faces:[]}]});
const move=(o,x)=>({...o,translation:[x,0,0]});
// Independent pair oracle: all geometrically legal pairs MUST glue. Exercise
// every one-dimensional positive integer tile through length four, including
// mixed species and both signs of translation.
let pairs=0;
for(let n=1;n<=4;n++) for(let mask=0;mask<2**n;mask++) {
  const weights=Array.from({length:n},(_,i)=>1+((mask>>i)&1));
  const prepared=prepareLatticeSearch([tile(weights),tile([1,2])],2);
  const marking=new VectorMarkings(prepared,2,{extent:1});
  for(const a of prepared.flat())for(const b of prepared.flat())for(let d=-6;d<=6;d++) {
    if(a===b&&d===0)continue;
    const occupancy=new Map(a.orientation.occupancy.map(p=>[p.pos[0],p.weight]));
    const legal=b.orientation.occupancy.every(p=>(occupancy.get(p.pos[0]+d)||0)+p.weight<=2);
    marking.add(move(a,0));
    if(legal){assert.equal(marking.compatible(move(b,d)),true);pairs++;}
    marking.add(move(b,d));marking.remove(move(b,d));marking.remove(move(a,0));
    assert.equal(marking.section.size,0);assert.equal(marking.conflicts,0);
  }
}
// Full vector equality (not per-component wildcards) and reference counts.
const prepared=prepareLatticeSearch([tile([2,2])],2),o=prepared[0][0];
const field=new VectorMarkings(prepared,2);
assert.equal(field.rank,2);
field.add(move(o,0));assert.equal(field.compatible(move(o,1)),false);
field.add(move(o,1));assert.equal(field.conflicts,1);
field.remove(move(o,1));assert.equal(field.conflicts,0);
field.add(move(o,0));field.remove(move(o,0));assert.equal(field.section.size,2);
field.remove(move(o,0));assert.equal(field.section.size,0);
assert.ok(field.representation.some(p=>p[0]===1&&p[1]===0));
// Resource fallback can weaken the marking, never add constraints.
const fallback=new VectorMarkings(prepared,2,{maxSlots:1});
assert.equal(fallback.rank,1);assert.equal(fallback.trivial,true);
// A real certified pair: discover dead-point obstructions independently,
// refine fields, and verify that all OTHER geometrically legal pairs still
// glue unless symmetry carries them to a certified forbidden pair.
let witnesses=0;
for(let mask=0;mask<16;mask++) {
  const p=prepareLatticeSearch([tile(Array.from({length:4},(_,i)=>1+((mask>>i)&1)))],2),a=p[0][0];
  for(let d=1;d<4;d++) {
    const weights=new Map();for(const shift of [0,d])for(const c of a.orientation.occupancy)weights.set(c.pos[0]+shift,(weights.get(c.pos[0]+shift)||0)+c.weight);
    if([...weights.values()].some(w=>w>2))continue;
    const dead=[...weights].some(([x,w])=>w<2&&a.orientation.occupancy.every(anchor=>{
      const shift=x-anchor.pos[0];
      return shift===0||shift===d||a.orientation.occupancy.some(c=>(weights.get(c.pos[0]+shift)||0)+c.weight>2);
    }));
    if(!dead)continue;
    const m=new VectorMarkings(p,2);
    // A minimal singleton certificate is deliberately not a pair update.
    // Check every deficient point to find the certified two-owner witness.
    const refined=[...weights].some(([x,w])=>w<2&&m.observeDeadPoint([x,0,0],[move(a,0),move(a,d)]));
    if(!refined)continue;
    m.rebuild([move(a,0)]);
    assert.ok(m.forbidden.size>0);m.remove(move(a,0));assert.equal(m.section.size,0);witnesses++;
  }
}
assert.ok(witnesses>0);
console.log(`Vector sections: ${pairs} legal pairs preserved; ${witnesses} certified pair refinements; rollback and group representation passed.`);

const {createTilingStream,tileSpecs}=await import('../apps/3d-lattice-tiler/engine.js');
for(const mode_key of ['cube','orthoscheme','polycube_p9_02127']) {
  for(const tiling_strategy of ['free_range','learning_free_range','rl_free_range','gcts_rl']) {
    const gcts=['learning_free_range','gcts_rl'].includes(tiling_strategy),rl=['rl_free_range','gcts_rl'].includes(tiling_strategy);
    let final;
    for await(const e of createTilingStream({mode_key,tiling_strategy,move_order:rl?'rl':'balanced',agent_policy:rl?'cold_linucb':null,
      complete_lattice_point_branching:true,gcts_failure_marking:gcts,criterion:'count',target_val:8,node_limit:1000,time_limit_ms:5000},tileSpecs))if(e.type==='finished')final=e;
    assert.equal(final.success,true,`${mode_key}/${tiling_strategy}`);
    if(gcts){assert.ok(final.search_stats.marking_rank>0);assert.equal(final.search_stats.global_section_conflicts,0);assert.ok(final.search_stats.marking_synthesis_ms>=0);}
  }
}
console.log('Published-engine integration: four lanes × three real tiles reached their goals with consistent global sections.');
