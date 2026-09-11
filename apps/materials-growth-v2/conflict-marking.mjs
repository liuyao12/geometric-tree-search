// Exact finite-candidate reference construction, NOT a learned spatial field.
// Each forbidden pair (or star group) receives a mark-only point: 0 vs 1.
// The domain is the disjoint union of original points and auxiliary witnesses.
// No physical atom, t-value, activation or scheduling rule is added.
export function compileConflictMarkings(candidates, forbiddenPairs, {grouping='pair',reservedPoints=[]}={}) {
  if(!['pair','star'].includes(grouping))throw Error('Unknown conflict grouping');
  const copy=()=>candidates.map(c=>({...c,t:c.t.map(x=>({...x})),m:(c.m||[]).map(x=>({...x})),...(c.activate?{activate:[...c.activate]}:{})}));
  const marked=copy(),neutral=copy(),indices=new Map(candidates.map((c,i)=>[c.id,i]));
  if(indices.size!==candidates.length)throw Error('Duplicate candidate identity');
  // Callers reserve target/fixed-mark points absent from all candidate supports.
  const used=new Set([...reservedPoints,...candidates.flatMap(c=>[...c.t.map(x=>x.point),...(c.m||[]).map(x=>x.point),...(c.activate||[])])]);
  const edges=[],seen=new Set(),pending=[];let serial=0;
  for(const [left,right] of forbiddenPairs){
    if(!indices.has(left)||!indices.has(right)||left===right)throw Error('A conflict needs two distinct known candidates');
    const pair=[indices.get(left),indices.get(right)].sort((a,b)=>a-b),key=pair.join(':');
    if(seen.has(key))continue;seen.add(key);
    pending.push(pair);
  }
  const groups=[];
  while(pending.length){
    if(grouping==='pair'){const [a,b]=pending.shift();groups.push([[a],[b]]);continue;}
    const degree=Array(candidates.length).fill(0);
    for(const [a,b] of pending){degree[a]++;degree[b]++;}
    const center=degree.indexOf(Math.max(...degree)),neighbors=[];
    for(let i=pending.length-1;i>=0;i--){const pair=pending[i];if(pair.includes(center)){neighbors.push(pair.find(x=>x!==center));pending.splice(i,1);}}
    groups.push([[center],neighbors.sort((a,b)=>a-b)]);
  }
  for(const sides of groups){
    let point;do{point=`gcts-conflict-witness:${serial++}`;}while(used.has(point));used.add(point);
    sides.forEach((side,value)=>side.forEach(i=>{
      marked[i].m.push({point,channel:'0',lo:value,hi:value});
      // Neutral marks reproduce the dependency graph for a relational baseline.
      neutral[i].m.push({point,channel:'0',lo:0,hi:0});
    }));
    for(const a of sides[0])for(const b of sides[1])edges.push({pair:[candidates[a].id,candidates[b].id],point});
  }
  return {candidates:marked,neutralCandidates:neutral,edges,grouping,auxiliaryPoints:groups.length,additionalAssignments:groups.reduce((n,sides)=>n+sides[0].length+sides[1].length,0),
    scope:'Exact for the supplied finite unordered conflict relation and unchanged original point values. Candidate-conditioned auxiliary points, not motif-local geometric fields. No claim about unseen placements or continuous-pose completeness.'};
}
