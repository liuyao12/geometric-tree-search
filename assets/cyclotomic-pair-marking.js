import {canonical,latticeKey,cycloAdd,cycloMultiply,starMap} from './cyclotomic-five.js?v=20260908-speed';
const zero={coeff:[0,0,0,0],denominator:1};
const sub=(a,b)=>cycloAdd(a,{...canonical(b),coeff:canonical(b).coeff.map(n=>-n)});
// A fresh channel encodes one proven forbidden relative pair. Distinct
// channels cannot introduce accidental cross-rule conflicts. Group images
// permute channels; no assumed bar direction or learned line is involved.
export function createPairPointMarking({pose,anchor,rigid,actions}){
 const tables=new Map(),known=new Set(),cache=new WeakMap(),prepared=new Map(),certificates=[];let revision=0,ruleCount=0,aggregate=new Map();
 const stats={entries:0,checks:0,prunes:0};
 let detailCache=null,activeMemory=null;
 const pairKey=(a,b)=>[pose(a)+'|'+pose(b)+'|'+latticeKey(sub(anchor(b),anchor(a))),pose(b)+'|'+pose(a)+'|'+latticeKey(sub(anchor(a),anchor(b)))].sort()[0];
 function support(tile){const old=cache.get(tile);if(old?.revision===revision)return old.rows;
  const type=pose(tile);let plan=prepared.get(type);
  if(plan?.revision!==revision){const points=new Map();for(const r of tables.get(type)?.values()||[]){const key=latticeKey(r.offset);if(!points.has(key))points.set(key,{offset:r.offset,zeros:0n,ones:0n});const p=points.get(key);p[r.value?'ones':'zeros']|=1n<<BigInt(r.channel);}
   plan={revision,points:[...points.values()]};prepared.set(type,plan);
  }
  const origin=anchor(tile),rows=plan.points.map(r=>{
   let point;
   if(origin.denominator===1&&r.offset.denominator===1&&origin.coeff.length===4){const coeff=origin.coeff.map((x,i)=>x+r.offset.coeff[i]);if(coeff.every(Number.isSafeInteger))point={coeff,denominator:1};}
   point ||= cycloAdd(origin,r.offset);
   return{...r,point,key:point.denominator===1?point.coeff.join(',')+'/1':latticeKey(point)};
  });cache.set(tile,{revision,rows});return rows;
 }
 function add(type,offset,channel,value){if(!tables.has(type))tables.set(type,new Map());const rows=tables.get(type),key=latticeKey(offset)+'@'+channel;
  if(rows.has(key)&&rows.get(key).value!==value)throw Error('Degenerate obstruction cannot be represented by this pair stencil');
  if(!rows.has(key)){rows.set(key,{offset,channel,value});stats.entries++;}
 }
 function learnPair(a,b,point=null,method='direct'){
  const images=actions.map(g=>{const x=rigid(a,g),y=rigid(b,g);return{x,y,key:pairKey(x,y)};}),orbitKey=images.map(r=>r.key).sort()[0];
  if(known.has(orbitKey))return false;known.add(orbitKey);const rule=ruleCount++;certificates.push({a:{type:pose(a),origin:anchor(a)},b:{type:pose(b),origin:anchor(b)},point,method});
  images.forEach(({x,y},g)=>{const channel=rule*actions.length+g,action=actions[g];
   // Reuse the certified frontier vertex whenever available. This changes
   // neither the forbidden displacement nor the fiber action, but avoids
   // adding a fresh geometric address for every learned pair.
   const source=point||anchor(a),witness=cycloMultiply(action.factor,action.reflect?starMap(starMap(source)):source);
   add(pose(x),sub(witness,anchor(x)),channel,0);add(pose(y),sub(witness,anchor(y)),channel,1);
  });revision++;return true;
 }
 function rebuild(tiles){activeMemory=null;aggregate=new Map();for(const tile of tiles)for(const r of support(tile)){
  const old=aggregate.get(r.key);if(old){old.zeros|=r.zeros;old.ones|=r.ones;}else aggregate.set(r.key,{zeros:r.zeros,ones:r.ones});
 }}
 function rejects(tile){stats.checks++;for(const r of support(tile)){const value=aggregate.get(r.key);if(value){const conflict=(value.zeros&r.ones)|(value.ones&r.zeros);if(conflict){stats.prunes++;return{point:r.point,channels:conflict.toString()};}}}return null;}
 function memory(){if(activeMemory)return activeMemory;let values=0;for(const r of aggregate.values())for(let bits of [r.zeros,r.ones])while(bits){bits&=bits-1n;values++;}return activeMemory={points:aggregate.size,values};}
 return{learnPair,support,rebuild,rejects,memory,get revision(){return revision;},
  snapshot({details=true}={}){
   if(detailCache?.revision!==revision)detailCache={revision,addresses:[...tables.values()].reduce((s,rows)=>s+new Set([...rows.values()].map(r=>latticeKey(r.offset))).size,0),certificates:certificates.slice(),tables:[...tables].map(([type,rows])=>({type,rows:[...rows.values()]}))};
   return{revision,rules:ruleCount,...stats,addresses:detailCache.addresses,...(details?{certificates:detailCache.certificates,tables:detailCache.tables}:{})};
  }};
}
