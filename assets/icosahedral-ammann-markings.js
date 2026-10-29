/** Supplied Ammann face dots, transcribed from Fig. 1 and its caption in
 * Hann, Socolar & Steinhardt, arXiv:1604.02479. The four non-threefold
 * decorated prototypes (two hands per shape) are problem-defining input.
 * This is NOT a marking learned from unmarked-search labels.
 */
import { ONE, vector, vadd, vsub, vscale, dot, determinant, pointKey } from './golden-field.js';
import { STAR, ORIENTATIONS, makeRhombohedron } from './icosahedral-exact.js';
export const AMMANN_RULE_VERSION='ammann-face-dots-2016-v1';
const zero=()=>vector(0n,0n,0n);
const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];

// Figure coordinates: e0 is the downward/front-left edge of the prolate;
// its long diagonal joins coefficient vertices 1 and 6. For the oblate,
// e0,e1,e2 meet at the visible obtuse vertex (coefficient vertex 0).
// Both bases use (-u0,u1,u4) / (-u0,u1,u2), respectively.
function figureFaces(kind,hand){
 const visible=kind==='prolate'
  ?[{axis:0,side:0,black:2,red:6},{axis:1,side:1,black:2,red:6},{axis:2,side:0,black:hand==='left'?0:3,red:1}]
  :[{axis:0,side:0,black:0,red:4},{axis:1,side:0,black:0,red:hand==='left'?1:4},{axis:2,side:0,black:0,red:1}];
 return visible.flatMap(f=>[f,{axis:f.axis,side:1-f.side,
  black:f.black^(kind==='prolate'?(1<<f.axis):7),
  red:f.red^(kind==='prolate'?7:(1<<f.axis))}]);
}
const metadataByAxes=new Map();
for(const kind of ['prolate','oblate']){
 const sourceAxes=kind==='prolate'?[0,1,4]:[0,1,2];
 const source=[vscale(STAR[sourceAxes[0]],-1n),STAR[sourceAxes[1]],STAR[sourceAxes[2]]];
 for(const proto of ORIENTATIONS.filter(t=>t.kind===kind)){
  const variants=new Map();
  for(const hand of ['left','right'])for(const permutation of permutations)for(let signs=0;signs<8;signs++){
   const axes=permutation.map(i=>proto.axes[i]);
   const directions=axes.map((axis,i)=>vscale(STAR[axis],signs&(1<<i)?-1n:1n));
   if(determinant(...directions).sign()!==determinant(...source).sign())continue;
   if(!directions.every((u,i)=>directions.every((v,j)=>dot(u,v).equals(dot(source[i],source[j])))))continue;
   const mapMask=mask=>{let result=0;for(let j=0;j<3;j++)if(Boolean(mask&(1<<j))!==Boolean(signs&(1<<j)))result|=1<<proto.axes.indexOf(axes[j]);return result;};
   const authored=figureFaces(kind,hand).map(f=>{
    const vertices=Array.from({length:8},(_,i)=>i).filter(i=>((i>>f.axis)&1)===f.side).map(mapMask).sort((a,b)=>a-b);
    return {vertices,black:mapMask(f.black),red:mapMask(f.red)};
   });
   const faces=proto.faces.map(face=>{
    const key=[...face].sort((a,b)=>a-b).join(',');const f=authored.find(a=>a.vertices.join(',')===key);
    if(!f)throw new Error('Face decoration transcription did not cover all faces');
    return {black:f.black,red:f.red};
   });
   const code=faces.map(f=>`${f.black}${f.red}`).join('-');
   const existing=variants.get(code);
   if(existing&&existing.hand!==hand)throw new Error('The two supplied hands became congruent');
   variants.set(code,{code,hand,faces});
  }
  metadataByAxes.set(proto.axes.join(','),[...variants.values()].sort((a,b)=>a.code.localeCompare(b.code)));
 }
}
const translatedCache=new WeakMap();
export function decorateGeometry(geometry){
 if(geometry.geometry)geometry=geometry.geometry;
 if(translatedCache.has(geometry))return translatedCache.get(geometry);
 const metadata=metadataByAxes.get(geometry.axes.join(','));if(!metadata)throw new Error('Unknown rhombohedron orientation');
 const decorated=metadata.map(meta=>{
  const faceDots=geometry.faces.map((face,i)=>{
   const center=vscale(face.reduce((s,j)=>vadd(s,geometry.vertices[j]),zero()),ONE.div(4n));
   const blackCorner=geometry.vertices[meta.faces[i].black],redCorner=geometry.vertices[meta.faces[i].red];
   return {center,blackCorner,redCorner,
    black:vscale(vadd(vscale(blackCorner,3n),center),ONE.div(4n)),
    red:vscale(vadd(vscale(redCorner,3n),center),ONE.div(4n))};
  });
  // A common face center is the support point. Values are exact vectors
  // from the center to the selected corners. Support transforms affinely;
  // values rotate and are invariant under translation. Merely putting
  // isolated colored dots at different points would leave missing values
  // unconstrained and would NOT enforce coincidence.
  const pointMarkings=faceDots.map(f=>({point:f.center,components:{black:pointKey(vsub(f.blackCorner,f.center)),red:pointKey(vsub(f.redCorner,f.center))}}));
  return Object.freeze({...geometry,geometry,geometryId:geometry.id,id:`${geometry.id}#${AMMANN_RULE_VERSION}:${meta.code}`,
   decoration:{version:AMMANN_RULE_VERSION,hand:meta.hand,code:meta.code,source:'supplied'},faceDots,pointMarkings});
 });
 translatedCache.set(geometry,decorated);return decorated;
}
export const AMMANN_ORIENTATIONS=Object.freeze(ORIENTATIONS.flatMap(decorateGeometry));
export function pointMarkingsAgree(a,b){
 const assigned=new Map((a.pointMarkings||[]).map(m=>[pointKey(m.point),m.components]));
 for(const mark of b.pointMarkings||[]){const old=assigned.get(pointKey(mark.point));if(!old)continue;for(const [channel,value]of Object.entries(mark.components))if(Object.hasOwn(old,channel)&&old[channel]!==value)return false;}
 return true;
}
export function translatedDecoration(tile,origin){
 const geometry=makeRhombohedron(tile.axes,origin);
 return decorateGeometry(geometry).find(t=>t.decoration.code===tile.decoration.code);
}
