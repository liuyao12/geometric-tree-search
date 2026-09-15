// Explicit sparse relation of learned endpoint pairs, not a Cartesian quotient.
import {FactorizedCandidateDomain} from './factorized-candidate-domain.mjs';
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
export class RelationalEndpointDomain extends FactorizedCandidateDomain {
 constructor(left,right,pairs){
  super(left,right);this.pairs=[];this.keys=new Set();this.byEndpoint=[new Map(),new Map()];this.cachedCount=null;
  for(const [a,b] of pairs){this.validate(0,a);this.validate(1,b);const key=`${a}:${b}`;if(this.keys.has(key))throw Error('Duplicate pair');this.keys.add(key);this.pairs.push([a,b]);
   for(const [s,i] of [a,b].entries()){if(!this.byEndpoint[s].has(i))this.byEndpoint[s].set(i,[]);this.byEndpoint[s].get(i).push([a,b]);}}
  this.pairs.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
 }
 pairActive(a,b){return super.containsEndpoint(0,a)&&super.containsEndpoint(1,b)&&!this.exclusions.has(`${a}:${b}`);}
 containsEndpoint(side,i){this.validate(side,i);return (this.byEndpoint[side].get(i)||[]).some(([a,b])=>this.pairActive(a,b));}
 has(a,b){this.validate(0,a);this.validate(1,b);return this.enabled&&this.keys.has(`${a}:${b}`)&&this.pairActive(a,b);}
 setAllowed(side,indices){super.setAllowed(side,indices);this.cachedCount=null;}
 setEnabled(v){super.setEnabled(v);this.cachedCount=null;}
 forbid(a,b){super.forbid(a,b);this.cachedCount=null;}
 undo(cp){super.undo(cp);this.cachedCount=null;}
 get count(){if(this.cachedCount===null)this.cachedCount=this.enabled?BigInt(this.pairs.filter(([a,b])=>this.pairActive(a,b)).length):0n;return this.cachedCount;}
 *endpointIndices(side){for(let i=0;i<this.sizes[side];i++)if(this.containsEndpoint(side,i))yield i;}
 *values(){if(this.enabled)for(const [a,b] of this.pairs)if(this.pairActive(a,b))yield [a,b];}
 snapshot(){return {...super.snapshot(),relation:this.pairs};}
}
export class RelationalEndpointSearch extends DynamicFactorizedSupportSearch {
 constructor(model,options={}){
  if(!Array.isArray(model.allowedPairs)||model.allowedPairs.length!==model.blocks.length)throw Error('Explicit relation required');
  super(model,options);
  for(const b of this.blocks)b.domain=new RelationalEndpointDomain(...b.endpointChoices.map(cs=>cs.length),model.allowedPairs[b.index]);
  this.refresh(new Set(this.points.keys()));
 }
}
