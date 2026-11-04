import {BASE,J,key,add,sub} from './j-tiling-model.js';
export {BASE,J,key,add,sub};
export const VERSION='j-learned-corner-point-v1';
export const CAPACITY=12;
// Exact rank-14 solution from closed-star equations in the known 7,921-tile
// lifted patch, confirmed by 30- and 60-tile mixed patches. Finite evidence.
export const WEIGHTS=[8,3,4,6,4,9,4,3,4,9,4,3,8,3];
export const F=([p,q,r,s])=>[p+q,-q,r,-r-s];
export function createPointModel({branch='mixed',support='corners'}={}){
 const coordinateScale=support==='edges'?2:1;
 const ORIENTATIONS=Array.from({length:12},(_,index)=>{
  const power=branch==='mixed'?index:2*(index%6),reflected=branch==='pure'&&index>=6;
  const vertices=BASE.map(point=>{let p=reflected?F(point):[...point];for(let k=0;k<power;k++)p=J(p);return p.map(x=>x*coordinateScale);});
  const corners=vertices.map((point,corner)=>({point,corner,weight:WEIGHTS[corner]}));
  if(support==='edges')for(let i=0;i<14;i++)corners.push({point:vertices[i].map((v,k)=>(v+vertices[(i+1)%14][k])/2),corner:14+i,weight:6});
  return{index,vertices,corners,power,reflected};
 });
 function materialize(orientation,translation){const o=ORIENTATIONS[orientation];return{id:`${orientation}|${key(translation)}`,orientation,translation:[...translation],corners:o.corners.map(e=>{const point=add(e.point,translation);return{...e,point,key:key(point)};}),vertices:o.vertices.map(p=>add(p,translation))};}
 return{ORIENTATIONS,materialize,coordinateScale,branch,support,validTranslation:t=>t.every(x=>Number.isInteger(x)&&x%coordinateScale===0)};
}
