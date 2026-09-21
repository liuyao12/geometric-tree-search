// Free components remove equality edges, not merely displayed assignments.
// Each trial solves the induced positive graph and tests negative alternatives.
export function selectMask(slotCount,orbits,positiveEdges,negatives,{iterations=1000,seed=1,initialMasks=[],maxEvaluations=Infinity}={}){
 const owner=new Int32Array(slotCount).fill(-1);orbits.forEach((orbit,i)=>orbit.forEach(s=>{if(!Number.isInteger(s)||s<0||s>=slotCount||owner[s]!==-1)throw Error('Orbits must partition slots');owner[s]=i;}));if(owner.some(i=>i<0))throw Error('Orbits must cover all slots');
 const assess=mask=>{
  const active=Uint8Array.from(owner,i=>mask[i]?1:0),parent=Int32Array.from({length:slotCount},(_,i)=>i);
  const find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  for(const [i,j] of positiveEdges)if(active[i]&&active[j]){const a=find(i),b=find(j);if(a!==b)parent[Math.max(a,b)]=Math.min(a,b);}
  const blocked=negatives.filter(contacts=>contacts.some(([i,j])=>active[i]&&active[j]&&find(i)!==find(j))).length;
  const points=active.reduce((s,v)=>s+v,0);return {mask:[...mask],active,parent,find,blocked,points};
 };
 let best=assess(orbits.map(()=>true)),evaluations=1;
 const consider=mask=>{if(evaluations>=maxEvaluations)return;const candidate=assess(mask);evaluations++;if(candidate.blocked>best.blocked||candidate.blocked===best.blocked&&candidate.points<best.points)best=candidate;};
 for(const mask of initialMasks)if(mask?.length===orbits.length)consider(mask);
 // Every negative needs two active endpoints. Try the orbit pairs containing
 // those endpoints before broader, deterministic random support proposals.
 const pairs=new Set();for(const contacts of negatives)for(const [i,j] of contacts){const a=owner[i],b=owner[j];pairs.add(`${Math.min(a,b)},${Math.max(a,b)}`);}
 for(const p of pairs){if(evaluations>=maxEvaluations)break;const [a,b]=p.split(',').map(Number),mask=orbits.map(()=>false);mask[a]=mask[b]=true;consider(mask);}
 let rng=(seed>>>0)||1;const random=()=>{rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return (rng>>>0)/4294967296;};
 for(let trial=0;trial<iterations&&evaluations<maxEvaluations&&best.blocked<negatives.length;trial++){
  let mask;if(trial%3===0){const density=.05+.9*random();mask=orbits.map(()=>random()<density);}else{mask=[...best.mask];const changes=1+Math.floor(random()*Math.max(1,orbits.length/4));for(let i=0;i<changes;i++){const k=Math.floor(random()*orbits.length);mask[k]=!mask[k];}}
  consider(mask);
 }
 for(let i=0;i<orbits.length;i++)if(best.mask[i]){const mask=[...best.mask];mask[i]=false;consider(mask);}
 return {...best,evaluations};
}
