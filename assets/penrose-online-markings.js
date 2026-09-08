import {canonical,latticeKey} from './cyclotomic-five.js';
import {MIXED_TEMPLATES} from './penrose-mixed-templates.js';
import {num,add,sub,mul,div,conj,pointInPolygon} from './penrose-polygon.js';
import {mixedMarkingsCompatible,tileMarkingValue,tileStates} from './penrose-mixed-markings.js?v=20260907-frontier';
import {candidateBarContacts} from './penrose-candidate-contacts.js?v=20260907-restored';
const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
const squareKeys=axes.map(a=>latticeKey(mul(a,a))),rotations=new Map(),symmetryCache=new Map();
function rotation(f){const key=latticeKey(f);if(!rotations.has(key))rotations.set(key,squareKeys.indexOf(latticeKey(mul(f,f))));return rotations.get(key);}
const apply=(p,t)=>add(mul(t.factor,t.reflect?conj(p):p),t.delta);
const family=(j,t)=>(rotation(t.factor)+(t.reflect?-j:j)+10)%5;
const undo=(p,t)=>{const q=div(sub(p,t.delta),t.factor);return t.reflect?conj(q):q;};
const undoFamily=(j,t)=>((t.reflect?-1:1)*(j-rotation(t.factor))+10)%5;
const shape=t=>t.exactPoints.map(latticeKey).sort().join('|')+'@'+t.bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
function symmetries(kind){
  if(symmetryCache.has(kind))return symmetryCache.get(kind);
  const tile=MIXED_TEMPLATES.find(t=>t.kind===kind),signature=shape(tile),result=[];
  for(const reflect of[false,true])for(const axis of axes)for(const sign of[1,-1]){
    const raw={factor:mul(axis,num(sign)),reflect,delta:num(0)};
    for(const p of tile.exactPoints){const t={...raw,delta:sub(p,apply(tile.exactPoints[0],raw))};
      if(shape({exactPoints:tile.exactPoints.map(p=>apply(p,t)),bars:tile.bars.map(b=>({from:apply(b.from,t),to:apply(b.to,t)}))})===signature)result.push(t);
    }
  }
  symmetryCache.set(kind,result);return result;
}
// This helper is also used by the display. No geometric value is filled in at
// an address absent from the learned table; undefined is not zero.
export function learnedSupport(tile,rows=[]){
  const points=new Map();
  for(const row of rows){const point=apply(row.point,tile.markingTransform),j=family(row.family,tile.markingTransform),key=latticeKey(point);
    if(!points.has(key))points.set(key,{point,value:Array(5).fill(null),extension:false});
    const p=points.get(key);if(p.value[j]!==null&&p.value[j]!==row.value)throw Error('Inconsistent learned marking');
    p.value[j]=row.value;p.extension ||= row.extension;
  }
  return points;
}
export function supportsCompatible(p,q){
  if(p.size>q.size)[p,q]=[q,p];
  for(const[key,a]of p){const b=q.get(key);if(b)for(let j=0;j<5;j++)if(a.value[j]!==null&&b.value[j]!==null&&a.value[j]!==b.value[j])return false;}
  return true;
}
export function createOnlineMarkings(extent,{teacher=mixedMarkingsCompatible,autoLearn=true}={}){
  const tables=new Map(),versions=new Map(),cache=new WeakMap(),verdicts=new Map();
  const stats={lessons:0,learnedRejections:0,teacherChecks:0,verifiedReuses:0};let revision=0;
  const rows=kind=>[...(tables.get(kind)?.values()||[])];
  function support(tile){const version=versions.get(tile.kind)||0,old=cache.get(tile);if(old?.version===version)return old.points;
    const points=learnedSupport(tile,rows(tile.kind));cache.set(tile,{version,points});return points;}
  function orbit(tile,p,j,value){
    const point=undo(p,tile.markingTransform),f=undoFamily(j,tile.markingTransform),template=MIXED_TEMPLATES.find(t=>t.kind===tile.kind),result=new Map();
    for(const t of symmetries(tile.kind)){const q=apply(point,t),k=family(f,t);result.set(latticeKey(q)+':'+k,{point:q,family:k,value,extension:!pointInPolygon(q,template.exactPoints)});}
    return [...result.values()].map(row=>({kind:tile.kind,key:latticeKey(row.point)+':'+row.family,row}));
  }
  function cost(entries){
    const fresh=new Map();for(const e of entries)if(!tables.get(e.kind)?.has(e.key))fresh.set(e.kind+':'+e.key,e);
    const newPoints=new Set();for(const e of fresh.values()){
      const address=latticeKey(e.row.point);
      if(!rows(e.kind).some(r=>latticeKey(r.point)===address))newPoints.add(e.kind+':'+address);
    }
    return [newPoints.size,fresh.size];
  }
  function insert(entries){for(const {kind,key,row}of entries){if(!tables.has(kind))tables.set(kind,new Map());const table=tables.get(kind),old=table.get(key);
    if(old&&old.value!==row.value)throw Error('Teacher proposed inconsistent marking values');
    if(!old){table.set(key,row);versions.set(kind,(versions.get(kind)||0)+1);revision++;}
  }}
  function learn(a,b){
    let best=null,bestCost=[Infinity,Infinity];
    function consider(source,target,point,j,x,y){
      const entries=[...orbit(source,point,j,x),...orbit(target,point,j,y)],c=cost(entries);
      if(c[0]<bestCost[0]||c[0]===bestCost[0]&&c[1]<bestCost[1]){best=entries;bestCost=c;}
    }
    // Prefer reusing an address already learned on either tile. A new value at
    // an existing address adds no visible point. Only then propose fresh bar
    // intersections or exact witnesses in candidate-defined intervals.
    for(const[source,target]of[[a,b],[b,a]])for(const p of support(source).values()){
      const other=tileMarkingValue(target,tileStates(target)[0],p.point,extent);if(!other)continue;
      p.value.forEach((x,j)=>{if(x!==null&&other[j]!==null&&x!==other[j])consider(source,target,p.point,j,x,other[j]);});
    }
    for(const[source,target]of[[a,b],[b,a]])for(const c of candidateBarContacts(source,target,extent))if(c.value===0)consider(source,target,c.point,c.family,1,0);
    if(!best||!bestCost[1])throw Error('Bar rejection has no new exact point witness');
    insert(best);stats.lessons++;
    if(supportsCompatible(support(a),support(b)))throw Error('Learned witness did not reject its counterexample');
  }
  function pairKey(a,b){
    const pose=t=>t.kind+':'+latticeKey(t.markingTransform.factor)+':'+t.markingTransform.reflect;
    const x=pose(a),y=pose(b),d=sub(b.markingTransform.delta,a.markingTransform.delta);
    return[x+'|'+y+'|'+latticeKey(d),y+'|'+x+'|'+latticeKey(sub(num(0),d))].sort()[0];
  }
  function verdict(a,b){const key=pairKey(a,b);if(verdicts.has(key)){stats.verifiedReuses++;return verdicts.get(key);}
    stats.teacherChecks++;const value=teacher(a,b,extent);verdicts.set(key,value);return value;
  }
  function pointCompatible(a,b){return supportsCompatible(support(a),support(b));}
  function compatible(a,b){
    if(!pointCompatible(a,b)){stats.learnedRejections++;return false;}
    const value=verdict(a,b);if(!value&&autoLearn)learn(a,b);return value;
  }
  function explainRejection(a,b){
    if(!pointCompatible(a,b)||verdict(a,b))return false;
    learn(a,b);return true;
  }
  return{compatible,support,pointCompatible,explainRejection,
    snapshot(){const templates=Object.fromEntries([...tables].map(([kind])=>[kind,rows(kind)]));return{revision,extent,templates,...stats,entries:Object.values(templates).reduce((s,r)=>s+r.length,0),points:Object.values(templates).reduce((s,r)=>s+new Set(r.map(p=>latticeKey(p.point))).size,0)};}
  };
}
