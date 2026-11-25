import {selectPointBranch} from "../../../assets/gcts-point-branching.js";

// A common denominator and a canonical sparse numerator for each polynomial.
// The four exponents count x, exp(x), sin(x), cos(x), in that order.
function gcd(a,b) {
  a = a < 0n ? -a : a; b = b < 0n ? -b : b;
  while (b) [a,b] = [b,a%b];
  return a;
}
function polynomial(entries, denominator=1n) {
  if (denominator <= 0n) throw Error("A positive denominator is required");
  const sums = new Map();
  for (const [key,c] of entries) sums.set(key, (sums.get(key) || 0n) + c);
  const terms = [...sums].filter(([,c])=>c!==0n).sort(([a],[b])=>a<b?-1:a>b?1:0);
  let divisor=denominator;
  for (const [,c] of terms) divisor=gcd(divisor,c);
  const den=denominator/divisor;
  const normalized=terms.map(([k,c])=>[k,c/divisor]);
  return {terms:normalized, den, key:normalized.map(([k,c])=>k+":"+c).join(";")+"/"+den};
}
export const zero=polynomial([]);
export function monomial(powers,n=1,d=1) {
  if (powers.length!==4 || powers.some(p=>!Number.isSafeInteger(p)||p<0)) throw Error("Invalid exponents");
  return polynomial([[powers.join(","),BigInt(n)]],BigInt(d));
}
export function scale(a,num,den=1n) {
  return polynomial(a.terms.map(([k,c])=>[k,c*num]),a.den*den);
}
export function add(a,b,sign=1n) {
  return polynomial([...a.terms.map(([k,c])=>[k,c*b.den]),
    ...b.terms.map(([k,c])=>[k,sign*c*a.den])],a.den*b.den);
}
export function derivative(a) {
  const out=[];
  for (const [key,c] of a.terms) {
    const [x,e,s,k]=key.split(",").map(Number);
    if(x)out.push([[x-1,e,s,k].join(","),c*BigInt(x)]);
    if(e)out.push([key,c*BigInt(e)]);
    if(s)out.push([[x,e,s-1,k+1].join(","),c*BigInt(s)]);
    if(k)out.push([[x,e,s+1,k-1].join(","),-c*BigInt(k)]);
  }
  return polynomial(out,a.den);
}
export function primitiveMove(primitive) {
  return {primitive, change:derivative(primitive), source:"rewrite"};
}
export function applyMove(residual,move) { return add(residual,move.change,-1n); }

export const tasks=[
  ["product","Exponential product",monomial([1,1,0,0])],
  ["transfer","Exponential product plus cosine",add(monomial([1,1,0,0]),monomial([0,0,0,1]))],
  ["cosine","Cosine product",monomial([1,0,0,1])],
  ["sine","Sine product",monomial([1,0,1,0])],
  ["chain","Sine times cosine",monomial([0,0,1,1])],
  ["power","Quadratic",monomial([2,0,0,0])]
];

const byCost=new Map();
export function cards(cost) {
  if (byCost.has(cost)) return byCost.get(cost);
  const result=[];
  // One unit for the extraction, one per factor, and |n|-1 plus d-1
  // units for a reduced coefficient n/d. A sign has two possible spellings.
  for(let degree=1;degree<cost;degree++){
    const sum=cost-degree+1;
    for(let n=1;n<sum;n++){
      const d=sum-n;
      if(gcd(BigInt(n),BigInt(d))!==1n)continue;
      for(let x=0;x<=degree;x++) for(let e=0;e<=degree-x;e++)
        for(let s=0;s<=degree-x-e;s++) for(const sign of [1,-1]){
          result.push(primitiveMove(monomial([x,e,s,degree-x-e-s],sign*n,d)));
        }
    }
  }
  byCost.set(cost,result);
  return result;
}

export function admit(target,moves) {
  if (!target.terms.length || !moves.length) throw Error("A nonempty solved game is required");
  let total=zero;
  for(const move of moves) {
    if(derivative(move.primitive).key!==move.change.key)throw Error("Invalid differential");
    total=add(total,move.primitive);
  }
  if(derivative(total).key!==target.key)throw Error("The proposed primitive fails differentiation");
  return {target,primitive:total};
}

// There is at most one scalar per entry. Match a complete proportional part
// of the residual. The unmatched terms remain a new integration obligation.
export function libraryMoves(residual,library) {
  const r=new Map(residual.terms), result=[];
  for(const entry of library){
    const [[pivot,pivotCoefficient]]=entry.target.terms;
    if(!r.has(pivot))continue;
    let n=r.get(pivot)*entry.target.den, d=residual.den*pivotCoefficient;
    if(d<0n){n=-n;d=-d;}
    if(!entry.target.terms.every(([k,c])=>r.has(k)&&r.get(k)*entry.target.den*d===c*n*residual.den))continue;
    const candidate=primitiveMove(scale(entry.primitive,n,d));
    result.push({...candidate,source:"saved"});
  }
  return result;
}
function pathTo(node,move) {
  const moves=[move];
  while(node.parent){moves.push(node.move);node=node.parent;}
  return moves.reverse();
}
export class FairSearch {
  constructor(target,library=[],seed=0) {
    const root={residual:target,parent:null};
    this.levels=[[root]];this.seen=new Set([target.key]);this.cost=0;
    this.target=target;this.library=library.slice();this.solution=target.terms.length?null:[];
    let state=seed>>>0;
    this.random=()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/4294967296);
  }
  advance() {
    if(this.solution!==null)throw Error("This search already has a solution");
    const cost=++this.cost, next=[];
    let tested=0, revisited=0, parents=0;
    for(let prior=0;prior<cost;prior++){
      const stepCost=cost-prior, deck=cards(stepCost);
      for(const node of this.levels[prior]){
        const moves=stepCost===1?libraryMoves(node.residual,this.library):deck;
        if(!moves.length)continue;
        parents++;
        // One open rewrite obligation for this parent and cost. GCTS orders
        // the equal-cost siblings. The outer cost loop provides fairness.
        const point={id:"rewrite",introducedAt:0,legal:moves.map((m,i)=>({id:i,move:m}))};
        for(const {placement} of selectPointBranch([point],this.random).moves){
          tested++;
          const move=placement.move, residual=applyMove(node.residual,move);
          if(!residual.terms.length){
            this.solution=pathTo(node,move);admit(this.target,this.solution);
            return {cost,tested,revisited,parents,fresh:next.length,solved:true};
          }
          if(this.seen.has(residual.key)){revisited++;continue;}
          this.seen.add(residual.key);next.push({residual,parent:node,move});
        }
      }
    }
    this.levels.push(next);
    return {cost,tested,revisited,parents,fresh:next.length,solved:false};
  }
}
