import {embedding,latticeKey} from './cyclotomic-five.js';
import {add,mul,conj,box} from './penrose-polygon.js';
import {FINITE_MARKINGS} from './penrose-finite-marking-data.js';
const cache=new WeakMap(),oriented=new Map();
const axes=Array.from({length:5},(_,j)=>({coeff:Array.from({length:5},(_,k)=>+(j===k)),denominator:1}));
const axisSquares=axes.map(a=>latticeKey(mul(a,a)));
function prepared(tile,extent){
  const t=tile.markingTransform;if(!t)throw Error('Missing fixed marking transform');
  const level=extent*4;if(!Number.isInteger(level)||level<0||level>16)throw Error('Invalid marking extent');
  const key=tile.kind+':'+latticeKey(t.factor)+':'+t.reflect+':'+level;
  if(oriented.has(key))return oriented.get(key);
  // Multiplication by -1 fixes unoriented families; conjugation reverses them.
  const rotation=axisSquares.indexOf(latticeKey(mul(t.factor,t.factor)));
  if(rotation<0)throw Error('Unknown marking rotation');
  const points=new Map();
  for(const[coeff,denominator,family,value,firstLevel,outside]of FINITE_MARKINGS[tile.kind]){
    if(firstLevel>level)continue;
    const local={coeff,denominator},point=mul(t.factor,t.reflect?conj(local):local),key=latticeKey(point);
    if(!points.has(key))points.set(key,{point,value:Array(5).fill(null),extension:false});
    const p=points.get(key),j=(rotation+(t.reflect?-family:family)+10)%5;
    if(p.value[j]!==null&&p.value[j]!==value)throw Error('Inconsistent fixed marking table');
    p.value[j]=value;p.extension ||= Boolean(outside);
  }
  const rows=[...points.values()];rows.forEach(p=>Object.freeze(p.value));
  const result={rows,bounds:box(rows.map(p=>p.point))};oriented.set(key,result);return result;
}
// Conservative spatial bounds do not construct a candidate's coordinate hash.
// Most proposed placements are eliminated by geometry before needing that hash.
export function finiteMarkingBounds(tile,extent=0){
  const b=prepared(tile,extent).bounds,d=embedding(tile.markingTransform.delta),p=box(tile.exactPoints);
  return{x0:Math.min(p.x0,b.x0+d.x),x1:Math.max(p.x1,b.x1+d.x),y0:Math.min(p.y0,b.y0+d.y),y1:Math.max(p.y1,b.y1+d.y)};
}
// Fixed tables only: no edge labels, line incidence, or candidate-dependent
// point construction enters this predicate. Null components are undefined.
export function finiteMarkingSupport(tile,extent=0) {
  let levels=cache.get(tile);if(!levels){levels=new Map();cache.set(tile,levels);}
  if(levels.has(extent))return levels.get(extent);
  const points=new Map();
  for(const p of prepared(tile,extent).rows){const point=add(p.point,tile.markingTransform.delta);points.set(latticeKey(point),{...p,point});}
  const result={points,bounds:finiteMarkingBounds(tile,extent)};levels.set(extent,result);return result;
}
export function finiteMarkingsCompatible(a,b,extent=0){
  let p=finiteMarkingSupport(a,extent).points,q=finiteMarkingSupport(b,extent).points;
  if(p.size>q.size)[p,q]=[q,p];
  for(const[key,x]of p){const y=q.get(key);if(y)for(let j=0;j<5;j++)if(x.value[j]!==null&&y.value[j]!==null&&x.value[j]!==y.value[j])return false;}
  return true;
}
export function finiteMarkingValue(tile,point,extent=0){return finiteMarkingSupport(tile,extent).points.get(latticeKey(point))?.value || null;}
