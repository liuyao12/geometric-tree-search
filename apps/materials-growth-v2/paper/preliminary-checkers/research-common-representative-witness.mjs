import assert from 'node:assert/strict';
// Every finite binary64 input is interpreted as its exact binary rational.
// No floating subtraction, squared distance, square root or epsilon shell.
const zero={n:0n,e:0};
function dyadic(x){if(x===0)return zero;const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,x);const bits=view.getBigUint64(0),raw=Number((bits>>52n)&2047n),mant=bits&((1n<<52n)-1n);return {n:((bits>>63n)?-1n:1n)*(raw?mant+(1n<<52n):mant),e:raw?raw-1075:-1074};}
function add(a,b){const e=Math.min(a.e,b.e);return {n:(a.n<<BigInt(a.e-e))+(b.n<<BigInt(b.e-e)),e};}
const neg=a=>({n:-a.n,e:a.e}),square=a=>({n:a.n*a.n,e:2*a.e});
function compare(a,b){const difference=add(a,neg(b));return difference.n<0n?-1:difference.n>0n?1:0;}
function distanceSquared(a,b){let sum=zero;for(let k=0;k<3;k++)sum=add(sum,square(add(dyadic(a[k]),neg(dyadic(b[k])))));return sum;}
const exact=x=>({numerator:x.n.toString(),binaryExponent:x.e});
function dense(a){assert(Array.isArray(a));for(let i=0;i<a.length;i++)assert(Object.hasOwn(a,i),'Dense array required');}
function atom(a){assert(a&&typeof a.species==='string'&&a.species);dense(a.position);assert.equal(a.position.length,3);for(let k=0;k<3;k++)assert(Number.isFinite(a.position[k]));}
function identifier(id){assert(typeof id==='string'&&id);}
const claimKey=(id,i)=>JSON.stringify([id,i]);

/** Direct positive witness verification, NOT correspondence search. The
 * declared finite representatives form the whole proposed union. complete=true
 * is a caller premise about each donor support. Upstream must separately verify
 * source provenance and proper whole-pose transport; this checker verifies the
 * supplied placed coordinates, not a floating rotation as an exact isometry.
 * This fixed-boundary variant pins every center to an inherited fixed ID and
 * preserves signed-zero coordinate representation for inherited points.
 * Representatives form a position set: distinct IDs at identical coordinates
 * are conservatively rejected, regardless of their species labels.
 * Equal-radius representatives deliberately produce Unknown, although exact
 * open-ball membership itself can decide equality as outside. No +/-eps shell.
 */
export function verifyCommonRepresentativeWitness({fixedPoints,fixedClaims,fixedPoses,newPoses,representatives,bindings,epsilon,maxPoints=4096,maxPoses=256,maxBindings=100000,maxComparisons=1000000}){
 for(const rows of [fixedPoints,fixedClaims,fixedPoses,newPoses,representatives,bindings])dense(rows);
 assert(Number.isFinite(epsilon)&&epsilon>=0);for(const cap of [maxPoints,maxPoses,maxBindings,maxComparisons])assert(Number.isSafeInteger(cap)&&cap>=0);
 const counts={comparisons:0,sites:0,inheritedClaims:0,absencePairs:0},records=[],coverage=[];
 const scope='Exact binary-rational direct verification of one supplied finite representative/binding witness, conditional on complete donor supports and separately verified pose provenance. Stronger direct-positive semantics than the historical conservative +/-epsilon-shell audit. No correspondence search, impossibility certificate, exact-rotation claim or material growth claim.';
 const finish=(status,reason,detail=null)=>({schema:'common-representative-witness-v1',status,reason,detail,epsilon,counts:{...counts},records,coverage,arithmetic:'exact-binary-rational-inputs',boundaryPolicy:'exact-radius-equality-unknown',scope});
 if(representatives.length>maxPoints||fixedPoints.length>maxPoints||fixedPoses.length+newPoses.length>maxPoses||bindings.length>maxBindings||fixedClaims.length>maxBindings)return finish('unknown','witness-size-budget');
 const points=new Map(),coordinateKeys=new Set();for(const p of representatives){identifier(p.id);atom(p);if(points.has(p.id))return finish('rejected-witness','duplicate-representative-id',{id:p.id});const key=JSON.stringify(p.position.map(x=>x===0?0:x));if(coordinateKeys.has(key))return finish('rejected-witness','coincident-representatives',{id:p.id});coordinateKeys.add(key);points.set(p.id,p);}
 const poses=new Map(),oldIds=new Set(),fixedIds=new Set();
 for(const [rows,old] of [[fixedPoses,true],[newPoses,false]])for(const p of rows){identifier(p.id);identifier(p.seedId);atom(p.center);dense(p.neighbors);p.neighbors.forEach(atom);assert(Number.isFinite(p.radius)&&p.radius>0);if(poses.has(p.id))return finish('rejected-witness','duplicate-support-id',{id:p.id});if(p.complete!==true)return finish('unknown','missing-complete-support-premise',{id:p.id});poses.set(p.id,p);if(old)oldIds.add(p.id);}
 const spend=()=>counts.comparisons<maxComparisons?(counts.comparisons++,true):false;
 for(const before of fixedPoints){identifier(before.id);atom(before);if(fixedIds.has(before.id))return finish('rejected-witness','duplicate-fixed-id');fixedIds.add(before.id);const p=points.get(before.id);if(!p||p.species!==before.species)return finish('rejected-witness','missing-or-relabeled-fixed-point',{id:before.id});if(!spend())return finish('unknown','comparison-budget');if(compare(distanceSquared(p.position,before.position),zero)!==0)return finish('rejected-witness','moved-fixed-point',{id:p.id});if(!p.position.every((x,k)=>Object.is(x,before.position[k])))return finish('rejected-witness','changed-fixed-coordinate-representation',{id:p.id});}
 const ledger=new Map(),inherited=new Map();
 function index(rows,target,oldOnly){for(const b of rows){identifier(b.supportId);identifier(b.pointId);assert(Number.isSafeInteger(b.siteIndex)&&b.siteIndex>=0);const p=poses.get(b.supportId);if(!p||b.siteIndex>p.neighbors.length||(oldOnly&&!oldIds.has(b.supportId)))return 'unknown-support-or-site';const key=claimKey(b.supportId,b.siteIndex);if(target.has(key))return 'duplicate-site-binding';if(b.claimId!==undefined&&b.claimId!==JSON.stringify(['whole-pose-claim',b.supportId,b.siteIndex]))return 'inconsistent-claim-id';target.set(key,b);}return null;}
 const bad=index(bindings,ledger,false)??index(fixedClaims,inherited,true);if(bad)return finish('rejected-witness',bad);
 const epsilonSquared=square(dyadic(epsilon)),owned=new Set();
 for(const p of poses.values()){
  if(!fixedIds.has(p.seedId))return finish('rejected-witness','center-not-in-fixed-boundary',{supportId:p.id});
  const bound=new Set(),sites=[p.center,...p.neighbors];
  if(counts.sites+sites.length>maxBindings)return finish('unknown','site-budget');
  for(let i=0;i<sites.length;i++){
   const key=claimKey(p.id,i),b=ledger.get(key);if(!b)return finish('rejected-witness','missing-site-binding',{supportId:p.id,siteIndex:i});const point=points.get(b.pointId);if(!point||point.species!==sites[i].species)return finish('rejected-witness','missing-or-relabeled-bound-point',{supportId:p.id,siteIndex:i});if(bound.has(point.id))return finish('rejected-witness','within-support-noninjective',{supportId:p.id,pointId:point.id});
   if(oldIds.has(p.id)){const old=inherited.get(key);if(!old||old.pointId!==b.pointId||!fixedIds.has(old.pointId))return finish('rejected-witness','missing-or-rebound-inherited-claim',{supportId:p.id,siteIndex:i});counts.inheritedClaims++;}
   if(i===0&&point.id!==p.seedId)return finish('rejected-witness','wrong-center-identity',{supportId:p.id});
   if(!spend())return finish('unknown','comparison-budget');const squared=distanceSquared(sites[i].position,point.position);
   if(compare(squared,i===0?zero:epsilonSquared)>0)return finish('rejected-witness',i===0?'nonexact-center':'claim-exceeds-error',{supportId:p.id,siteIndex:i,pointId:point.id,squared:exact(squared)});
   bound.add(point.id);owned.add(point.id);counts.sites++;records.push({supportId:p.id,siteIndex:i,pointId:point.id,squaredResidual:exact(squared)});
  }
  const inside=[],radiusSquared=square(dyadic(p.radius));
  for(const point of points.values()){
   if(!spend())return finish('unknown','comparison-budget');counts.absencePairs++;const relation=compare(distanceSquared(point.position,p.center.position),radiusSquared);
   if(relation===0)return finish('unknown','representative-on-exact-radius',{supportId:p.id,pointId:point.id});
   if(relation<0){if(!bound.has(point.id))return finish('rejected-witness','unbound-representative-inside-support',{supportId:p.id,pointId:point.id});inside.push(point.id);}
  }
  coverage.push({supportId:p.id,insidePointIds:inside});
 }
 if(owned.size!==points.size)return finish('rejected-witness','unowned-representatives',{pointIds:[...points.keys()].filter(id=>!owned.has(id))});
 return finish('verified-common-representative-witness',null);
}
