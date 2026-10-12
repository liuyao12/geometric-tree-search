// Evaluation-only seeded scrambler. Histories are provenance, never solver input.
import {latticeMoves,VERSION,DEFAULT_DIRECTION,diagram} from './lattice-moves.mjs';
import {embeddingKey} from './lattice-state.mjs';
export function scrambleLattice(input,{steps=2,seed=1,maxEdges=200,direction=DEFAULT_DIRECTION}={}){
 let p=JSON.parse(embeddingKey(input)),state=seed>>>0;const source=p,history=[],seen=new Set([embeddingKey(p)]);
 for(let i=0;i<steps;i++){
  const options=latticeMoves(p,{maxEdges,direction,region:null}).filter(m=>!seen.has(m.key));
  if(!options.length)throw Error('Scrambler has no unvisited legal move.');
  state=(1664525*state+1013904223)>>>0;const move=options[Math.floor(state/4294967296*options.length)];history.push(move);seen.add(move.key);p=JSON.parse(move.key);
 }
 return{vertices:p,seed,initialDiagram:diagram(source,direction).canonical,finalDiagram:diagram(p,direction).canonical,provenance:{version:VERSION,source,target:p,options:{depth:steps,maxEdges,direction,region:null},steps:history}};
}
