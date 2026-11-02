export const VERSION='j-sector-surface-v1';
export const BASE=[[0,0,0,0],[0,0,0,1],[-1,0,0,1],[-1,-1,0,1],[-1,-2,0,1],[0,-3,0,1],[0,-3,-1,1],[0,-3,-1,0],[1,-3,-1,0],[1,-2,-1,0],[1,-2,0,-1],[1,-2,1,-1],[0,-1,1,-1],[0,0,1,-1]];
const SECTORS=[[3,4,5,6,7,8,9,10],[6,7,8],[8,9,10,11],[8,9,10,11,0,1],[10,11,0,1],[7,8,9,10,11,0,1,2,3],[9,10,11,0],[0,1,2],[2,3,4,5],[11,0,1,2,3,4,5,6,7],[1,2,3,4],[4,5,6],[2,3,4,5,6,7,8,9],[5,6,7]];
export const J=([p,q,r,s])=>[-s,r+s,p,q];
export const key=p=>p.join(',');
export const add=(a,b)=>a.map((x,i)=>x+b[i]);
export const sub=(a,b)=>a.map((x,i)=>x-b[i]);
export const bits=mask=>{let n=0;for(;mask;mask&=mask-1)n++;return n;};
export const ORIENTATIONS=Array.from({length:12},(_,index)=>{
 const vertices=BASE.map(p=>{let v=[...p];for(let k=0;k<index;k++)v=J(v);return v;});
 return {index,vertices,corners:vertices.map((point,i)=>({point,mask:SECTORS[i].reduce((m,k)=>m|(1<<((k+index)%12)),0),weight:SECTORS[i].length}))};
});
export function materialize(orientation,translation){
 const o=ORIENTATIONS[orientation];
 return {id:`${orientation}|${key(translation)}`,orientation,translation:[...translation],corners:o.corners.map(e=>{const point=add(e.point,translation);return{...e,point,key:key(point)};}),vertices:o.vertices.map(p=>add(p,translation))};
}
export function project([p,q,r,s],theta=Math.PI/6){
 const a=Math.cos(theta),b=Math.sin(theta);
 return [a*(p+q/2)+b*Math.sqrt(3)*r/2,a*Math.sqrt(3)*q/2+b*(r/2+s)];
}
