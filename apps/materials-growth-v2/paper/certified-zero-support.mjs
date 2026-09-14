// Static proof gate for a complete fixed integer point model. No geometry rule.
import assert from 'node:assert/strict';
const gcd=(a,b)=>b?gcd(b,a%b):(a<0n?-a:a);
function rational(s){const [a,b='1']=String(s).split('/');const n=BigInt(a),d=BigInt(b);assert(d>0n);return [n,d];}
export function certifiedZeroSupport(model,certificate){
 if(!certificate)return new Set();
 assert(!model.expand&&!model.constraint&&!model.initial?.length&&!model.fixedMarks?.length&&model.complete!==false);
 assert(Number.isSafeInteger(model.capacity)&&model.capacity>0);
 assert(model.required.every(p=>typeof p==='string'));
 const rows=[...certificate.y,...certificate.z],fractions=rows.map(([,v])=>rational(v)),bound=rational(certificate.bound);
 let scale=bound[1];for(const [,d] of fractions)scale=scale/gcd(scale,d)*d;
 const scaled=s=>{const [n,d]=rational(s);assert(scale%d===0n);return n*(scale/d);};
 const y=new Map(certificate.y.map(([p,v])=>[String(p),scaled(v)]));
 const z=new Map(certificate.z.map(([j,v])=>[String(j).padStart(6,'0'),scaled(v)]));
 const excluded=new Set(certificate.excluded.map(j=>String(j).padStart(6,'0')));
 assert.equal(y.size,certificate.y.length);assert.equal(z.size,certificate.z.length);assert.equal(excluded.size,certificate.excluded.length);
 const required=new Set(model.required),ids=new Set(model.candidates.map(c=>c.id));
 for(const p of y.keys())assert(required.has(p));
 for(const [id,v] of z){assert(ids.has(id));assert(v>=0n);}
 for(const id of excluded)assert(ids.has(id));
 for(const c of model.candidates){
  let lhs=z.get(c.id)||0n;const seen=new Set();
  for(const {point,value} of c.t){assert(required.has(point)&&!seen.has(point));seen.add(point);assert(Number.isSafeInteger(value)&&value>0&&value<=model.capacity);lhs+=(y.get(point)||0n)*BigInt(value);}
  assert(lhs>=(excluded.has(c.id)?scale:0n));
 }
 const upper=BigInt(model.capacity)*[...y.values()].reduce((a,b)=>a+b,0n)+[...z.values()].reduce((a,b)=>a+b,0n);
 assert.equal(upper,scaled(certificate.bound));assert(upper<scale);
 return excluded;
}
