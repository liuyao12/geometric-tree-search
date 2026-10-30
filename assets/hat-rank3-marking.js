import {SparseA2Marking} from './a2-tiling-engine.js?v=20260921-viable-corona';

// Rank-3 signs on the existing Hat rank-1 Kagome pattern, 2026-10-30.
// There are eight core Kagome points, two nonzero directions per point:
// 16 independent signs. Complete enumeration gives eight full assignments
// matching the 7,921-tile patch. All give the same 228 excluded Hat pairs;
// independent unmarked integer-capacity certificates prove those impossible.
// The canonical interior values also follow the periodic Kagome sign rule.
// Core support is certified for Hat-only point tilings. Exterior extents 1–3
// pass the known patch but have no universal or mixed-inventory certificate.
export const HAT_RANK3_ID='hat-kagome-rank3';
export const HAT_RANK3_MAX_EXTENT=3;
export const HAT_RANK3_CERTIFIED_EXTENT=0;
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
export function normalizeHatRank3Extent(value){
 const n=Number.parseInt(value,10);
 return Number.isFinite(n)?Math.max(0,Math.min(HAT_RANK3_MAX_EXTENT,n)):0;
}
const gcd=(a,b)=>b?gcd(b,a%b):Math.abs(a);
export function hatRank3Support({extent=0,pattern='more'}={}){
 const extra=normalizeHatRank3Extent(extent),reverse=pattern==='alternate'||pattern==='reverse';
 const points=new Map(HAT_RANK3_ZERO_POINTS.map(point=>[point.join(','),{point,values:[0,0,0]}]));
 for(const [a,b]of HAT_RANK3_SEGMENTS){
  const delta=b.map((v,i)=>v-a[i]),steps=delta.reduce(gcd),step=delta.map(v=>v/steps);
  for(let k=-extra;k<=steps+extra;k++){
   const point=a.map((v,i)=>v+k*step[i]),values=hatKagomeValues(point);
   if(!values)throw new Error('Hat marking segment left its rank-1 Kagome pattern');
   points.set(point.join(','),{point,values});
  }
 }
 return [...points.values()].flatMap(({point,values})=>values.map((value,component)=>({tile:'hat',point:[...point],component,value:reverse?-value:value})));
}
export function createHatRank3Marking(options={}){
 const extent=normalizeHatRank3Extent(options.extent??0);
 return new SparseA2Marking(hatRank3Support({...options,extent}),{
  label:`Hat rank 3 Kagome · extent ${extent}`,valueAction:'signed-permutation',version:'hat-kagome-rank3-v1',
  coreSignMask:42598,coreAssignments:72,coreCertified:true,exteriorCertified:false
 });
}
