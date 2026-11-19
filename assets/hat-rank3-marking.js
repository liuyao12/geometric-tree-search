import {FixedA2Marking, SparseA2Marking} from './a2-tiling-engine.js?v=20260921-viable-corona';

// Rank-3 signs on the existing Hat rank-1 Kagome pattern, 2026-10-30.
// There are eight core Kagome points, two nonzero directions per point:
// 16 independent signs. Complete enumeration gives eight full assignments
// matching the 7,921-tile patch. All give the same 228 excluded Hat pairs;
// independent unmarked integer-capacity certificates prove those impossible.
// The canonical interior values also follow the periodic Kagome sign rule.
// A sparse core retains ten negative entries and leaves six line entries *.
// Its 115 exclusions also have independently replayed unmarked certificates.
// It reached 100 Hats in 158 nodes versus 1546 for the full rule in seed 10.
// research/hat-kagome-phase/verify.py certifies the common field and the
// full marking at extents 0–3 for complete Hat-only point tilings.
export const HAT_RANK3_ID='hat-kagome-rank3';
export const HAT_RANK3_MAX_EXTENT=9;
export const HAT_RANK3_CERTIFIED_EXTENT=3;
export const HAT_RANK3_ZERO_POINTS=Object.freeze([
 [1,0,-1],[3,0,-3],[3,2,-5],[1,4,-5],[-1,6,-5],[-1,4,-3],[-1,2,-1],
 [0,1,-1],[0,2,-2],[0,4,-4],[0,5,-5],[1,2,-3],[1,3,-4],[2,1,-3],[2,3,-5],[3,1,-4]
].map(Object.freeze));
export const HAT_RANK3_CORE_POINTS=Object.freeze([
 [-1,5,-4],[0,0,0],[0,3,-3],[0,6,-6],[1,1,-2],[2,2,-4],[3,3,-6],[4,1,-5]
].map(Object.freeze));
// These are exactly the four Hat rank-1 segment domains, including their
// complete lattice sampling. Extent adds primitive Kagome steps at both ends.
export const HAT_RANK3_SEGMENTS=Object.freeze([
 [[0,0,0],[3,3,-6]],[[1,1,-2],[-1,5,-4]],[[4,1,-5],[0,3,-3]],[[0,6,-6],[-1,5,-4]]
].map(pair=>Object.freeze(pair.map(Object.freeze))));
export function hatKagomeValues([x,y,z]){
 if(x+y+z!==0||(x-y)%3!==0)return null;
 const i=(-2*x-y)/3,j=(-x-2*y)/3;
 if(!(i&1)&&!(j&1))return [1,0,-1];
 if((i&1)&&(j&1))return [0,-1,1];
 if((i&1)&&!(j&1))return [-1,1,0];
 return null;
}
export const HAT_RANK3_POINTS=Object.freeze([
 ...HAT_RANK3_CORE_POINTS.map(point=>Object.freeze({point,values:Object.freeze(hatKagomeValues(point))})),
 ...HAT_RANK3_ZERO_POINTS.map(point=>Object.freeze({point,values:Object.freeze([0,0,0])}))
]);
export const HAT_RANK3_SPARSE_POINTS=Object.freeze([
 [[-1,5,-4],[0,-1,-1]],[[0,0,0],[-1,0,-1]],[[0,3,-3],[-1,-1,0]],
 [[0,6,-6],['*',0,'*']],[[1,1,-2],[0,-1,-1]],[[2,2,-4],[-1,0,-1]],
 [[3,3,-6],[0,'*','*']],[[4,1,-5],['*','*',0]]
].map(([point,values])=>Object.freeze({point:Object.freeze(point),values:Object.freeze(values)})));
export function normalizeHatRank3Extent(value){
 const n=Number.parseInt(value,10);
 return Number.isFinite(n)?Math.max(0,Math.min(HAT_RANK3_MAX_EXTENT,n)):0;
}
const gcd=(a,b)=>b?gcd(b,a%b):Math.abs(a);
function alternatingSupport(tiles, extent) {
  const core = new FixedA2Marking(0, {tiles, rank: 1});
  const entries = new Map();
  function assign(tile, point, component, value) {
    entries.set(`${tile}:${point}|${component}`, {tile, point, component, value});
  }
  for (const {tile, point} of core.support) {
    const values = hatKagomeValues(point) ?? [0, 0, 0];
    values.forEach((value, component) => assign(tile, point, component, value));
  }
  if (extent > 0) {
    const orientation = {symmetry: {sign: 1, permutation: [0, 1, 2]}};
    for (const tile of new Set(tiles)) {
      const lines = core.segments({tile, orientation, translation: [0, 0, 0]});
      for (const {fromPoint, toPoint} of lines) {
        const delta = toPoint.map((v, i) => v - fromPoint[i]);
        const steps = delta.reduce(gcd);
        const step = delta.map(v => v / steps);
        const component = step.findIndex(v => Math.abs(v) === 2);
        for (let k = 1; k <= extent; k++) {
          const before = fromPoint.map((v, i) => v - k * step[i]);
          const after = toPoint.map((v, i) => v + k * step[i]);
          for (const point of [before, after]) {
            // Other directions remain unassigned unless their own stripes reach this point.
            assign(tile, point, component, hatKagomeValues(point)[component]);
          }
        }
      }
    }
  }
  return [...entries.values()];
}

export function hatRank3Support({extent=0,pattern='sparse'}={}){
 const sparse=pattern==='sparse'||pattern==='sparse-reverse';
 const reverse=pattern==='alternate'||pattern==='reverse'||pattern==='sparse-reverse';
 if(!sparse){
  const support=alternatingSupport(['hat'],normalizeHatRank3Extent(extent));
  return reverse?support.map(entry=>({...entry,value:entry.value===0?0:-entry.value})):support;
 }
 const points=new Map(HAT_RANK3_ZERO_POINTS.map(point=>[point.join(','),{point,values:[0,0,0]}]));
 for(const entry of HAT_RANK3_SPARSE_POINTS)points.set(entry.point.join(','),entry);
 return [...points.values()].flatMap(({point,values})=>values.flatMap((value,component)=>value==='*'?[]:[{tile:'hat',point:[...point],component,value:reverse&&value!==0?-value:value}]));
}
export function createHatRank3Marking(options={}){
 const sparse=(options.pattern??'sparse').startsWith('sparse');
 const extent=sparse?0:normalizeHatRank3Extent(options.extent??0);
 return new SparseA2Marking(hatRank3Support({...options,extent}),{
  label:`Hat rank 3 Kagome · ${sparse?'sparse core':`extent ${extent}`}`,valueAction:'signed-permutation',version:'hat-kagome-rank3-v3',
  coreSignMask:sparse?0:42598,activeLineMask:sparse?3903:65535,coreAssignments:sparse?66:72,coreCertified:true,exteriorCertified:!sparse && extent>0 && extent<=HAT_RANK3_CERTIFIED_EXTENT
 });
}

// Both prototiles sample the same Kagome field in first-vertex coordinates.
// The fixed scalar stripes supply the four geometric line domains per tile.
// An exterior stripe samples only its own directional component of the field.
export const MIXED_RANK3_ID = 'mixed-hat-turtle-rank3';
export function createAlternatingMarking(tiles = ['turtle'], extent = 0) {
  extent = normalizeHatRank3Extent(extent);
  const tileSet = [...new Set(tiles)];
  let support;
  if (tileSet.length === 1 && tileSet[0] === 'turtle') {
    // On all four Turtle stripes the opposite phase matches the constant sign at
    // both original endpoints. Only the signs at odd steps along the stripe flip.
    const constant = new FixedA2Marking(extent, {tiles: tileSet, rank: 3});
    support = constant.support.map(entry => ({
      ...entry, value: entry.value === 0 ? 0 : -hatKagomeValues(entry.point)[entry.component]
    }));
  } else {
    support = alternatingSupport(tileSet, extent);
  }
  return new SparseA2Marking(support, {label: 'Alternating rank 3 · extent ' + extent});
}
export {createAlternatingMarking as createAlternatingCoreMarking};
