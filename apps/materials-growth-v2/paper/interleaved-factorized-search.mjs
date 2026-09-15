// Ordering only: diagonal Cartesian traversal, round-robin over incident blocks.
// No candidate is removed, merged, scored by a supplied solution, or made forced.
import {DynamicFactorizedSupportSearch} from './dynamic-factorized-support.mjs';
export function* diagonalPairs(left,right){
 if(!left.length||!right.length)return;
 for(let sum=0;sum<left.length+right.length-1;sum++){
  for(let a=Math.max(0,sum-right.length+1);a<=Math.min(left.length-1,sum);a++)yield [left[a],right[sum-a]];
 }
}
export class InterleavedFactorizedSearch extends DynamicFactorizedSupportSearch {
 *candidateIds(point){
  // Snapshot all parent incidence and endpoint lists before yielding. Descendant
  // changes must not change enumeration when the saved parent is restored.
  let iterators=[...(this.graph.get(point)||[])].sort((a,b)=>a-b).map(index=>{
   const b=this.blocks[index],left=[...b.domain.endpointIndices(0)],right=[...b.domain.endpointIndices(1)],self=this;
   return (function*(){for(const [a,c] of diagonalPairs(left,right))if(b.domain.has(a,c))yield self.candidateId(index,a,c);})();
  });
  while(iterators.length){
   const remaining=[];
   for(const iterator of iterators){const item=iterator.next();if(!item.done){remaining.push(iterator);yield item.value;}}
   iterators=remaining;
  }
 }
}
