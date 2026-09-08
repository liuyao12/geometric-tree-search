import {canonical,cycloAdd,cycloMultiply,embedding,latticeKey} from './cyclotomic-five.js';
import {rationalOrientation as orient} from './cyclotomic-orientation.js';
export {orient};
export const num=(n,d=1)=>canonical({coeff:[n,0,0,0],denominator:d});
export const neg=p=>({...canonical(p),coeff:canonical(p).coeff.map(n=>-n)});
export const add=cycloAdd, mul=cycloMultiply;
export const sub=(a,b)=>add(a,neg(b));
export function auto(p,k){p=canonical(p);const c=[0,0,0,0,0];p.coeff.forEach((n,i)=>c[i*k%5]+=n);return canonical({coeff:c,denominator:p.denominator});}
export const conj=p=>auto(p,4);
export function inverse(p){const q=mul(mul(auto(p,2),auto(p,3)),auto(p,4)),n=mul(p,q);if(n.coeff.slice(1).some(Boolean)||!n.coeff[0])throw Error('Noninvertible field element');return mul(q,num(Math.sign(n.coeff[0])*n.denominator,Math.abs(n.coeff[0])));}
export const div=(a,b)=>mul(a,inverse(b));
export const norm=p=>mul(p,conj(p));
const sign=(a,b)=>{if(!b)return a<0n?-1:a>0n?1:0;if(!a)return b<0n?-1:1;if((a>0n)===(b>0n))return a>0n?1:-1;const d=a*a-5n*b*b;return a>0n?(d>0n?1:-1):(d>0n?-1:1);};
export const realSign=p=>{const c=canonical(p).coeff.map(BigInt);return sign(4n*c[0]-c[1]-c[2]-c[3],c[1]-c[2]-c[3]);};
export const cmp=(a,b)=>realSign(sub(a,b));
export const cross=(u,v)=>sub(mul(conj(u),v),mul(u,conj(v)));
export const lerp=(a,b,t)=>add(a,mul(sub(b,a),t));
export const same=(a,b)=>latticeKey(a)===latticeKey(b);
export const onSegment=(p,a,b)=>!orient(a,b,p)&&realSign(mul(sub(p,a),conj(sub(p,b))))<=0;
export function pointInPolygon(p,poly){let winding=0; // compare imaginary parts using an oriented fixed vertical vector
 const ysign=q=>orient(num(0),num(1),q);
 for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length];if(onSegment(p,a,b))return true;const ay=ysign(sub(a,p)),by=ysign(sub(b,p)),o=orient(a,b,p);if(ay<=0&&by>0&&o>0)winding++;if(ay>0&&by<=0&&o<0)winding--;}
 return winding!==0;
}
export function areaSign(poly){const a=poly.reduce((s,p,i)=>add(s,cross(p,poly[(i+1)%poly.length])),num(0));return orient(num(0),num(1),a);}
const trianglesCache=new WeakMap();
export function triangles(poly){if(trianglesCache.has(poly))return trianglesCache.get(poly);let ids=poly.map((_,i)=>i),result=[];const winding=areaSign(poly);
 while(ids.length>3){let found=false;for(let k=0;k<ids.length;k++){const a=ids[(k+ids.length-1)%ids.length],b=ids[k],c=ids[(k+1)%ids.length];if(orient(poly[a],poly[b],poly[c])*winding<=0)continue;
 if(ids.some(j=>j!==a&&j!==b&&j!==c&&[orient(poly[a],poly[b],poly[j]),orient(poly[b],poly[c],poly[j]),orient(poly[c],poly[a],poly[j])].every(x=>x*winding>=0)))continue;
 result.push([poly[a],poly[b],poly[c]]);ids.splice(k,1);found=true;break;}if(!found)throw Error('Cannot triangulate polygon');}
 result.push(ids.map(i=>poly[i]));trianglesCache.set(poly,result);return result;}
const boxes=new WeakMap();export function box(poly){if(!boxes.has(poly)){const p=poly.map(p=>embedding(p));boxes.set(poly,{x0:Math.min(...p.map(p=>p.x)),x1:Math.max(...p.map(p=>p.x)),y0:Math.min(...p.map(p=>p.y)),y1:Math.max(...p.map(p=>p.y))});}return boxes.get(poly);}
export const separated=(a,b)=>a.x1<b.x0-1e-8||b.x1<a.x0-1e-8||a.y1<b.y0-1e-8||b.y1<a.y0-1e-8;
export function overlap(a,b){if(separated(box(a),box(b)))return false;for(const ta of triangles(a))for(const tb of triangles(b)){let separate=false;for(const [p,q]of[[ta,tb],[tb,ta]]){const w=orient(...p);for(let k=0;k<3;k++)if(q.every(v=>w*orient(p[k],p[(k+1)%3],v)<=0))separate=true;}if(!separate)return true;}return false;}
export function segmentCuts(a,b,poly){const u=sub(b,a),cuts=new Map([[latticeKey(num(0)),num(0)],[latticeKey(num(1)),num(1)]]);
 for(let k=0;k<poly.length;k++){const c=poly[k],d=poly[(k+1)%poly.length],v=sub(d,c),den=cross(u,v);if(den.coeff.every(n=>n===0)){for(const p of[c,d])if(onSegment(p,a,b)){const t=div(sub(p,a),u);cuts.set(latticeKey(t),t);}continue;}
 const t=div(cross(sub(c,a),v),den),s=div(cross(sub(c,a),u),den);if(cmp(t,num(0))>=0&&cmp(t,num(1))<=0&&cmp(s,num(0))>=0&&cmp(s,num(1))<=0)cuts.set(latticeKey(t),t);
 }return [...cuts.values()].sort(cmp);}
export function clipSegment(a,b,poly){const cuts=segmentCuts(a,b,poly),result=[];for(let i=0;i<cuts.length-1;i++){const t=mul(add(cuts[i],cuts[i+1]),num(1,2));if(pointInPolygon(lerp(a,b,t),poly))result.push([lerp(a,b,cuts[i]),lerp(a,b,cuts[i+1])]);}return result;}
