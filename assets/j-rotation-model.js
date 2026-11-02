import {BASE,J} from './j-tiling-model.js';
export const CENTER=[0,-2,0,0];
// Translate by an integer lattice vector so the fixed lattice origin is near
// the tile centre. Every stopped pose is still exactly J^k of a lattice tile.
export const TILE=BASE.map(p=>p.map((v,i)=>v-CENTER[i]));
export const PROJECTIONS=[{id:'hat',name:'Hat projection',theta:Math.PI/3},{id:'turtle',name:'Turtle projection',theta:Math.PI/6},{id:'spectre',name:'Spectre projection',theta:Math.PI/4}];
export const EDGE_FAMILY=BASE.map((p,i)=>BASE[(i+1)%14].slice(0,2).some((v,k)=>v!==p[k])?0:1);
export function exactPose(point,step){let p=[...point];for(let k=0;k<((step%12)+12)%12;k++)p=J(p);return p;}
export const physical=([p,q,r,s])=>[p+q/2,Math.sqrt(3)*q/2,Math.sqrt(3)*r/2,r/2+s];
const rotate=(x,y,a)=>[Math.cos(a)*x-Math.sin(a)*y,Math.sin(a)*x+Math.cos(a)*y];
export function continuousPose(point,step){
 if(Math.abs(step-Math.round(step))<1e-12)return physical(exactPose(point,Math.round(step)));
 const [x,y,z,w]=physical(point),plus=rotate(x+z,y+w,step*Math.PI/6),minus=rotate(x-z,y-w,-step*5*Math.PI/6);
 return[(plus[0]+minus[0])/2,(plus[1]+minus[1])/2,(plus[0]-minus[0])/2,(plus[1]-minus[1])/2];
}
export function projectPose(point,step,theta){const [x,y,z,w]=continuousPose(point,step),a=Math.cos(theta),b=Math.sin(theta);return[a*x+b*z,a*y+b*w];}
export function projectedShape(projection,step){if(projection==='spectre')return'Equilateral Spectre polygon';return (projection==='hat')!==Boolean(step%2)?'Hat':'Turtle';}
export function radius(theta){const a=Math.cos(theta),b=Math.sin(theta);return Math.max(...TILE.map(point=>{const[x,y,z,w]=physical(point);return((a+b)*Math.hypot(x+z,y+w)+Math.abs(a-b)*Math.hypot(x-z,y-w))/2;}));}
