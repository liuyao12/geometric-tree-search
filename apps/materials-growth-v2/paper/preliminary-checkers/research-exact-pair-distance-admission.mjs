import assert from 'node:assert/strict';
// Exact binary64 integer units, independently implemented here. This checks
// a supplied indexed source/world correspondence, not its provenance or SO(3).
function units(x){assert(Number.isFinite(x));const a=new DataView(new ArrayBuffer(8));a.setFloat64(0,x);const bits=a.getBigUint64(0),exponent=Number((bits>>52n)&2047n);let n=bits&((1n<<52n)-1n);if(exponent)n+=1n<<52n;return ((bits>>63n)?-n:n)<<BigInt(exponent?exponent-1:0);}
function dense(a){assert(Array.isArray(a));for(let i=0;i<a.length;i++)assert(Object.hasOwn(a,i));}
function site(p){assert(p&&typeof p.species==='string'&&p.species);dense(p.position);assert.equal(p.position.length,3);return p.position.map(units);}
const squared=(a,b)=>a.reduce((s,x,k)=>s+(x-b[k])**2n,0n);
function within(A,B,d){const z=A+B-d*d;return z<=0n||z*z<=4n*A*B;}
export function admitExactPairDistances({source,pose,tau,maxSites=256,maxComparisons=100000}){
 const counts={sites:0,comparisons:0},scope='Exact distance-distortion admission for the supplied indexed site correspondence only. Source provenance, full-support completeness, proper orientation and representative bindings require separate verification.';
 const done=(status,reason,detail=null)=>({schema:'exact-pair-distance-admission-v1',status,reason,detail,tau,counts:{...counts},arithmetic:'exact-binary64-rational-radical-elimination',scope});
 try{
  assert(Number.isFinite(tau)&&tau>=0);for(const n of [maxSites,maxComparisons])assert(Number.isSafeInteger(n)&&n>=0);
  assert(source&&pose);dense(source.neighbors);dense(pose.neighbors);assert.equal(source.neighbors.length,pose.neighbors.length);
  counts.sites=source.neighbors.length+1;if(counts.sites>maxSites)return done('unknown','site-budget');
  const s=[source.center,...source.neighbors],w=[pose.center,...pose.neighbors];
  for(let i=0;i<s.length;i++)assert.equal(s[i].species,w[i].species,'Indexed label mismatch');
  const a=s.map(site),b=w.map(site),d=units(tau);
  for(let i=0;i<a.length;i++)for(let j=0;j<i;j++){
   if(counts.comparisons>=maxComparisons)return done('unknown','comparison-budget');counts.comparisons++;
   if(!within(squared(a[i],a[j]),squared(b[i],b[j]),d))return done('rejected-pair-distance','source-world-distance-distortion',{siteIndices:[j,i]});
  }
  return done('admitted-pair-distances',null);
 }catch(error){return done('unknown','invalid-input',{message:error.message});}
}
