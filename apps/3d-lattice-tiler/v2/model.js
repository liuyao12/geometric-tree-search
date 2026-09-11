import {tileSpecs, preprocessTilingSystem} from '../engine.js';
import {SLAB_TILES,prepareSlab} from './slab.js?v=2.1.0';

export const VERSION = '2.1.0';
export const MODES = [
  {id:'free',name:'Free-range',color:'#9dacc4'},
  {id:'gcts',name:'GCTS',color:'#4fdac5'},
  {id:'rl',name:'RL clusters',color:'#b7a2ff'},
  {id:'both',name:'GCTS + RL',color:'#ffc56c'}
];
export const CASES = [
  {id:'a2_hat_prism',name:'Hat prism',group:'Research',note:'Single slab on the index-3 A₂ sublattice. Cap weights are doubled: interior t = 1, rim values are planar angles. Six in-plane rotations; reflected tiles are optional.'},
  {id:'a2_turtle_prism',name:'Turtle prism',group:'Research',note:'Single slab using the Turtle demo’s index-3 point domain. Each cap retains 11 boundary vertices and 2 interior points. Interior t = 1; rim values are planar angles.'},
  {id:'buckled_ring',name:'Buckled ring',group:'Periodic stress control',note:'The reference screen found small periodic and isohedral point certificates. Retained as a nonconvex search stress control, not a nonperiodic example.'},
  {id:'twisted_h',name:'Twisted H',group:'Periodic stress control',note:'The reference screen found small periodic and isohedral point certificates. Retained as a search stress control, not a nonperiodic example.'},
  {id:'tuning_fork',name:'Reinhardt tuning fork',group:'Research',note:'Large nonconvex support. The reference eight-copy periodic and isohedral probes remained unknown within two seconds. This is a bounded miss, not aperiodicity.'},
  {id:'mathematica_16_vertex',name:'16-vertex lattice tile',group:'Periodic control',note:'Known periodic control: 64 proper-rotation copies in a 12³ cell; an eight-copy motif is available with reflections. It is not a hard nonperiodic example.'},
  {id:'cube',name:'Cube',group:'Easy control',note:'Easy periodic control. Useful for checking the protocol and measuring the overhead of extra search machinery.'}
];
export function catalog() {
  return [...CASES,...Object.entries(tileSpecs.TILING_REGISTRY).filter(([id])=>!CASES.some(c=>c.id===id)).map(([id,c])=>({id,name:c.name,group:'Catalog',note:'Legacy catalog geometry. V2 accepts only exact integer point weights; structural status is independent of the finite-window result.'}))];
}
const gcd=(a,b)=>b?gcd(b,a%b):a;
export function prepareModel(config) {
  if(!config.custom&&SLAB_TILES[config.tile])return prepareSlab(config,VERSION);
  const prepared = preprocessTilingSystem({mode_key:config.tile,include_mirrors:config.mirrors,custom_system:config.custom,polycube_lattice:'z3'},tileSpecs);
  const capacity=prepared.prototiles.reduce((a,t)=>a*t.solid_angle.max_value/gcd(a,t.solid_angle.max_value),1);
  if(!Number.isSafeInteger(capacity)||capacity<1)throw Error('This tile needs an exact point representation before it can enter the v2 comparison.');
  const orientations=[];
  prepared.prototiles.forEach((tile,type)=>{
    if(tile.solid_angle.kind!=='rational')throw Error('This catalog tile has numerical or symbolic weights. V2 does not round them into an exact certificate. Use the original explorer for its geometry.');
    tile.rescaleOccupancyWeights(capacity);
    const seen=new Set();
    tile.unique_orientations.forEach((o,index)=>{
      const cells=o.occupancy.map(p=>({pos:p.pos.slice(),weight:p.weight}));
      if(cells.some(p=>!Number.isSafeInteger(p.weight)||p.weight<=0||p.weight>capacity||p.pos.some(x=>!Number.isSafeInteger(x))))throw Error('Noninteger point data is unsupported by the exact v2 engine.');
      const signature=cells.map(p=>`${p.pos}:${p.weight}`).sort().join('|');
      if(seen.has(signature))return;seen.add(signature);
      orientations.push({type,index,cells,vertices:o.verts,faces:o.faces,marks:[]});
    });
  });
  const radius=config.radius??1,required=[];
  if(!Number.isInteger(radius)||radius<1||radius>3)throw Error('Window radius must be 1–3.');
  for(let x=-radius;x<=radius;x++)for(let y=-radius;y<=radius;y++)for(let z=-radius;z<=radius;z++)required.push({pos:[x,y,z],generation:0});
  return {version:VERSION,capacity,orientations,required,name:prepared.modeDef.name,domain:'Z³',boundary:'open exterior; every selected placement touches the finite required cube',transformations:prepared.summary};
}
