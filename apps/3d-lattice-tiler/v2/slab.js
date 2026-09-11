import {A2_TILE_LOOPS,tileOrientations} from '../../../assets/a2-tiling-engine.js';

export const SLAB_TILES={a2_hat_prism:'hat',a2_turtle_prism:'turtle',a2_hexagonal_prism:'hexagon'};
export const onIndex3=p=>(p[0]-p[1])%3===0&&(p[1]-p[2])%3===0;
const parity=p=>{let sign=1;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if(p[i]>p[j])sign=-sign;return sign;};

export function prepareSlab(config,version){
  const tile=SLAB_TILES[config.tile],index3=tile!=='hexagon';
  const radius=config.radius??1;
  if(!Number.isInteger(radius)||radius<1||radius>3)throw Error('Slab radius must be 1–3.');
  const orientations=tileOrientations(tile,A2_TILE_LOOPS[tile]).filter(o=>config.mirrors||parity(o.symmetry.permutation)===1).map((o,index)=>{
    // The demo normalizes the first vertex to zero, then samples this coset.
    const support=[...o.occupancy.values()].filter(p=>!index3||onIndex3(p.point));
    const vertices=[...o.loop.map(p=>p.slice()),...o.loop.map(p=>p.map(x=>x+1))],n=o.loop.length;
    const faces=[Array.from({length:n},(_,i)=>n-1-i),Array.from({length:n},(_,i)=>n+i),...Array.from({length:n},(_,i)=>[i,(i+1)%n,n+(i+1)%n,n+i])];
    const cells=[0,1].flatMap(layer=>support.map(p=>({pos:p.point.map(x=>x+layer),weight:4*p.weight,kind:p.weight===12?'cap_interior':'rim'})));
    // Before this adjustment each end carried 2*a/48. Now both copies carry
    // a/12, so a cap-interior point contributes 48/48 = 1 immediately.
    return {type:0,index,cells,vertices,faces,marks:[],planarSymmetry:o.symmetry};
  });
  const basis=index3?[[1,1,-2],[-1,2,-1]]:[[1,0,-1],[0,1,-1]],required=[];
  for(let q=-radius;q<=radius;q++)for(let r=-radius;r<=radius;r++){
    if(Math.abs(q+r)>radius)continue;
    const p=basis[0].map((x,i)=>q*x+r*basis[1][i]);
    for(const layer of [0,1])required.push({pos:p.map(x=>x+layer),generation:0});
  }
  return {version,capacity:48,orientations,required,name:`${tile[0].toUpperCase()+tile.slice(1)} · single slab`,domain:index3?'Two copies of the index-3 A₂ sublattice':'Two copies of A₂',
    boundary:'Single slab: support only on x+y+z=0 and 3; open lateral boundary. Normal translations are forbidden.',
    placementDomain:{kind:'a2_slab',layerSums:[0,3],translationSum:0,index3},
    slab:{normal:[1,1,1],height:[1,1,1],basis,sublatticeIndex:index3?3:1,capWeightMultiplier:2,planarCapacity:12,source:'GCTS-I.html: isTurtleSublatticeVector / tileOrientations',pointsPerCap:required.length/2},
    transformations:{point_group:'Planar A₂ isometries fixing the slab normal',reflections:!!config.mirrors,orientation_count:orientations.length,translation_basis:basis,origin:'first planar vertex',inventory:'unlimited copies of one tile; each oriented translated placement at most once'}};
}
