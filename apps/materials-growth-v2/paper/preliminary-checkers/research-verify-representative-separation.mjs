// Independent necessary-condition checker; no proposer/field compiler imports.
import assert from 'node:assert/strict';
function integer(x){assert(Number.isFinite(x));const v=new DataView(new ArrayBuffer(8));v.setFloat64(0,x);const h=v.getUint32(0),l=v.getUint32(4),e=h>>>20&2047;let n=(BigInt(h&1048575)<<32n)|BigInt(l);if(e)n|=1n<<52n;return(h>>>31?-n:n)<<BigInt(e?e-1:0);}
function dense(a){assert(Array.isArray(a));for(let i=0;i<a.length;i++)assert(Object.hasOwn(a,i));}
const exact=(numerator,binaryExponent)=>({numerator:numerator.toString(),binaryExponent});
export function verifyRepresentativeSeparation(points,{terms,maxPoints,maxComparisons}={}){
 const counts={points:0,comparisons:0},scope='Exact fixed-representative separation only, across all labels. Not source authentication, complete-neighborhood validity, support closure or search proof.';
 try{
  assert(Number.isSafeInteger(maxPoints)&&maxPoints>=0&&Number.isSafeInteger(maxComparisons)&&maxComparisons>=0,'Explicit finite caps required');assert(Array.isArray(points)&&Array.isArray(terms));assert(terms.length>0&&terms.length<=16);dense(terms);
  let threshold=0n;for(const t of terms)threshold+=integer(t);assert(threshold>=0n,'Nonnegative exact threshold required');
  const bound=exact(threshold,-1074);if(points.length>maxPoints)return {status:'unknown',reason:'point-budget',counts,threshold:bound,scope};dense(points);
  const ids=new Set(),rows=[];for(const p of points){assert(p&&typeof p.id==='string'&&p.id&&!ids.has(p.id),'Distinct point IDs required');ids.add(p.id);dense(p.position);assert.equal(p.position.length,3);rows.push({id:p.id,position:p.position.map(integer)});counts.points++;}
  for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){
   if(counts.comparisons>=maxComparisons)return {status:'unknown',reason:'comparison-budget',counts,threshold:bound,scope};counts.comparisons++;
   const squared=rows[i].position.reduce((s,x,k)=>s+(x-rows[j].position[k])**2n,0n);
   if(squared===0n||squared<threshold*threshold)return {status:'conflict',reason:squared===0n?'distinct-coincident-representatives':'strict-separation-violation',indices:[i,j],pointIds:[rows[i].id,rows[j].id],squaredDistance:exact(squared,-2148),threshold:bound,counts,scope};
  }
  return {status:'verified-separation',threshold:bound,counts,scope};
 }catch(error){return {status:'unknown',reason:'invalid-input',detail:error.message,counts,scope};}
}
