// Restricted learned model: retain paired observations i,i rather than their
// Cartesian product. This is not redundant pruning of the factorized model.
import {FactorizedCandidateDomain} from './factorized-candidate-domain.mjs';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';

export class CoupledEndpointDomain extends FactorizedCandidateDomain {
 constructor(left,right,pairs=null){
  super(left,right);
  if(pairs===null){if(left!==right)throw Error('Paired endpoints require equal lengths');pairs=Array.from({length:left},(_,i)=>[i,i]);}
  this.pairs=pairs.map(([a,b])=>{this.validate(0,a);this.validate(1,b);return [a,b];});
  this.byEndpoint=[new Map(),new Map()];
  for(const pair of this.pairs)for(let s=0;s<2;s++){if(this.byEndpoint[s].has(pair[s]))throw Error('Endpoint must have one observed partner');this.byEndpoint[s].set(pair[s],pair);}
 }
 containsEndpoint(side,index){
  this.validate(side,index);
  const pair=this.byEndpoint[side].get(index);return !!pair&&this.pairActive(...pair);
 }
 pairActive(a,b){return super.containsEndpoint(0,a)&&super.containsEndpoint(1,b)&&!this.exclusions.has(`${a}:${b}`);}
 has(left,right){
  this.validate(0,left);this.validate(1,right);
  return this.enabled&&this.byEndpoint[0].get(left)?.[1]===right&&this.pairActive(left,right);
 }
 get count(){let n=0n;if(this.enabled)for(const [a,b] of this.pairs)if(this.pairActive(a,b))n++;return n;}
 *endpointIndices(side){for(let i=0;i<this.sizes[side];i++)if(this.containsEndpoint(side,i))yield i;}
 *values(){if(this.enabled)for(const [a,b] of this.pairs)if(this.pairActive(a,b))yield [a,b];}
 snapshot(){return {...super.snapshot(),coupledPairs:this.pairs};}
}

export class CoupledEndpointSearch extends DynamicFactorizedSupportSearch {
 constructor(model,options={}){
  super(model,options);
  for(const b of this.blocks){
   let pairs=null;
   if(b.endpointChoices.flat().some(c=>c&&typeof c==='object'&&'sourceCandidate' in c)){
    const maps=b.endpointChoices.map(cs=>{const m=new Map();cs.forEach((c,i)=>{if(typeof c.sourceCandidate!=='string'||m.has(c.sourceCandidate))throw Error('Unique source identities required');m.set(c.sourceCandidate,i);});return m;});
    pairs=[...maps[0]].filter(([id])=>maps[1].has(id)).map(([id,i])=>[i,maps[1].get(id)]);
   }
   b.domain=new CoupledEndpointDomain(...b.endpointChoices.map(cs=>cs.length),pairs);
  }
  this.refresh(new Set(this.points.keys()));
 }
}
