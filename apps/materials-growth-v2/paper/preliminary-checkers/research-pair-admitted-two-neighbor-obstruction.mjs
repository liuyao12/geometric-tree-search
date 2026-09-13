import assert from 'node:assert/strict';
// Binary64 values are integer multiples of 2^-1074. Squared lengths share
// scale 2^-2148, so all radical-elimination comparisons below are integer exact.
function integer(x){assert(Number.isFinite(x));const v=new DataView(new ArrayBuffer(8));v.setFloat64(0,x);const h=v.getUint32(0),l=v.getUint32(4),e=h>>>20&2047;let n=(BigInt(h&1048575)<<32n)|BigInt(l);if(e)n|=1n<<52n;return(h>>>31?-n:n)<<BigInt(e?e-1:0);}
function dense(a){assert(Array.isArray(a));for(let i=0;i<a.length;i++)assert(Object.hasOwn(a,i));}
function atom(a){assert(a&&typeof a.species==='string'&&a.species);dense(a.position);assert.equal(a.position.length,3);return a.position.map(integer);}
const squared=(a,b)=>a.reduce((s,x,i)=>s+(x-b[i])**2n,0n);
export function exactLengthDifferenceWithin(A,B,d){assert(typeof A==='bigint'&&A>=0n&&typeof B==='bigint'&&B>=0n&&typeof d==='bigint'&&d>=0n);const z=A+B-d*d;return z<=0n||z*z<=4n*A*B;}
export function certifyPairAdmittedTwoNeighborObstruction({supports,center,neighbors,epsilon,tau,radius,premises,maxSupports=10000,maxSites=100000,maxPairs=250000,maxComparisons=1000000}){
 const counts={supports:0,sites:0,pairs:0,comparisons:0,labelRejected:0,firstRadialRejected:0,secondRadialRejected:0,pairRejected:0};
 const scope='Frozen two-neighbor boundary and declared complete finite donor inventory only. Conditional on distinct identities, fixed center, complete support within radius and representative deviations at most epsilon from world claims and every future pose passing the exact all-pair source/world distance-distortion admission at tau. No physics, infinite extension or other-boundary impossibility claim.';
 const result=(status,reason,extra={})=>({schema:'pair-admitted-two-neighbor-obstruction-v1',status,reason,counts:{...counts},epsilon,tau,radius,arithmetic:'exact-binary64-rational-radical-elimination',scope,...extra});
 try{
  for(const cap of [maxSupports,maxSites,maxPairs,maxComparisons])assert(Number.isSafeInteger(cap)&&cap>=0);dense(supports);dense(neighbors);assert.equal(neighbors.length,2);
  assert(Number.isFinite(epsilon)&&epsilon>=0&&Number.isFinite(tau)&&tau>=0&&Number.isFinite(radius)&&radius>0);
  for(const p of ['completeInventory','completeRadiusSupports','fixedCenter','distinctNeighborIdentities','allFuturePosesPassExactPairDistanceAdmission'])assert.equal(premises?.[p],true);
  if(supports.length>maxSupports)return result('unknown','support-budget');
  const c=atom(center),q=neighbors.map(atom),R=integer(radius),e=integer(epsilon)+integer(tau),pairTolerance=2n*integer(epsilon)+integer(tau),A=q.map(p=>squared(c,p)),C=squared(q[0],q[1]);
  assert(A.every(x=>x>0n&&x<R*R)&&C>0n,'Two distinct noncentral neighbors strictly inside radius required');
  const spend=()=>counts.comparisons<maxComparisons?(counts.comparisons++,true):false;
  for(let si=0;si<supports.length;si++){
   const support=supports[si],s=atom(support.center);dense(support.neighbors);if(support.neighbors.length>maxSites-counts.sites)return result('unknown','site-budget');const sites=support.neighbors.map(atom);counts.supports++;counts.sites+=sites.length;
   if(support.center.species!==center.species){counts.labelRejected++;continue;}
   for(let i=0;i<sites.length;i++)for(let j=0;j<sites.length;j++){
    if(i===j)continue;if(counts.pairs>=maxPairs)return result('unknown','pair-budget');counts.pairs++;
    if(support.neighbors[i].species!==neighbors[0].species||support.neighbors[j].species!==neighbors[1].species){counts.labelRejected++;continue;}
    if(!spend())return result('unknown','comparison-budget');if(!exactLengthDifferenceWithin(A[0],squared(s,sites[i]),e)){counts.firstRadialRejected++;continue;}
    if(!spend())return result('unknown','comparison-budget');if(!exactLengthDifferenceWithin(A[1],squared(s,sites[j]),e)){counts.secondRadialRejected++;continue;}
    if(!spend())return result('unknown','comparison-budget');if(!exactLengthDifferenceWithin(C,squared(sites[i],sites[j]),pairTolerance)){counts.pairRejected++;continue;}
    return result('inconclusive','necessary-distance-conditions-survive',{survivingMapping:{supportIndex:si,mapping:[i,j]}});
   }
  }
  return result('certified-frozen-library-obstruction','all-label-preserving-injections-fail-necessary-distances',{premises:{...premises},supportCount:supports.length});
 }catch(error){return result('unknown','invalid-input-or-premise',{message:error.message});}
}
