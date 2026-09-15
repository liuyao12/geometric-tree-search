// Candidate ranking only. Scores are static conservative complement counts;
// no training selection, oracle answer or material label is consulted.
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
export class SupportOrderedFactorizedSearch extends DynamicFactorizedSupportSearch {
 constructor(model,options={}){
  super(model,options);
  if(!this.partnerIndex)throw Error('Support ordering requires a complete partner index');
  this.supportOrder=this.blocks.map(b=>b.endpointChoices.map((cs,side)=>cs.map((_,j)=>j).sort((a,c)=>this.score(b.index,side,c)-this.score(b.index,side,a)||a-c)));
  this.blockOrder=this.blocks.map(b=>b.index).sort((a,b)=>this.blockScore(b)-this.blockScore(a)||a-b);
 }
 score(index,side,j){return this.partnerIndex.neighbors[this.endpointIndex[index][side][j]].length;}
 blockScore(index){return Math.min(...[0,1].map(side=>{const j=this.supportOrder[index][side][0];return j===undefined?0:this.score(index,side,j);}));}
 *candidateIds(point){
  // Snapshot parent incidence: the live Set may be replaced when this point
  // completes in a child and is reintroduced on rollback.
  const incident=new Set(this.graph.get(point)||[]);
  for(const i of this.blockOrder){
   if(!incident.has(i))continue;const b=this.blocks[i];
   // This generator is resumed only after parent rollback. Static order and
   // restored domain membership enumerate each parent candidate exactly once.
   for(const left of this.supportOrder[i][0]){
    if(!b.domain.containsEndpoint(0,left))continue;
    for(const right of this.supportOrder[i][1])if(b.domain.has(left,right))yield this.candidateId(i,left,right);
   }
  }
 }
}
