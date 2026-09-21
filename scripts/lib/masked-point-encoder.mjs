// Research synthesis: removing a free slot also removes its positive equality
// edges. This can split classes that an all-assigned encoder merged together.
import {OnlineMarking,pairCompatible} from '../../apps/3d-lattice-tiler/marking-learning.js';
export function selectMask(slotCount,orbits,positiveEdges,negatives,{iterations=1000,seed=1}={}){
 const owner=new Int32Array(slotCount).fill(-1);orbits.forEach((orbit,i)=>orbit.forEach(s=>{if(!Number.isInteger(s)||s<0||s>=slotCount||owner[s]!==-1)throw Error('Orbits must partition slots');owner[s]=i;}));if(owner.some(i=>i<0))throw Error('Orbits must cover all slots');
 const assess=mask=>{
  const active=Uint8Array.from(owner,i=>mask[i]?1:0),parent=Int32Array.from({length:slotCount},(_,i)=>i);
  const find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  for(const [i,j] of positiveEdges)if(active[i]&&active[j]){const a=find(i),b=find(j);if(a!==b)parent[Math.max(a,b)]=Math.min(a,b);}
  const blocked=negatives.filter(contacts=>contacts.some(([i,j])=>active[i]&&active[j]&&find(i)!==find(j))).length;
  const points=active.reduce((s,v)=>s+v,0);return {mask:[...mask],active,parent,find,blocked,points};
 };
 let best=assess(orbits.map(()=>true)),evaluations=1;
 const consider=mask=>{const candidate=assess(mask);evaluations++;if(candidate.blocked>best.blocked||candidate.blocked===best.blocked&&candidate.points<best.points)best=candidate;};
 // Every negative needs two active endpoints. Try the orbit pairs containing
 // those endpoints before broader, deterministic random support proposals.
 const pairs=new Set();for(const contacts of negatives)for(const [i,j] of contacts){const a=owner[i],b=owner[j];pairs.add(`${Math.min(a,b)},${Math.max(a,b)}`);}
 for(const p of pairs){const [a,b]=p.split(',').map(Number),mask=orbits.map(()=>false);mask[a]=mask[b]=true;consider(mask);}
 let rng=(seed>>>0)||1;const random=()=>{rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return (rng>>>0)/4294967296;};
 for(let trial=0;trial<iterations&&best.blocked<negatives.length;trial++){
  let mask;if(trial%3===0){const density=.05+.9*random();mask=orbits.map(()=>random()<density);}else{mask=[...best.mask];const changes=1+Math.floor(random()*Math.max(1,orbits.length/4));for(let i=0;i<changes;i++){const k=Math.floor(random()*orbits.length);mask[k]=!mask[k];}}
  consider(mask);
 }
 for(let i=0;i<orbits.length;i++)if(best.mask[i]){const mask=[...best.mask];mask[i]=false;consider(mask);}
 return {...best,evaluations};
}
export function learnMaskedMarking(model,rows,{extent=1,iterations=1000,seed=1,transforms}={}){
 if(!transforms?.length)throw Error('Supply verified point transforms');
 const started=performance.now(),trainer=new OnlineMarking(model,transforms,{extent});
 const samples=rows.map(r=>({...r,contacts:trainer.contacts(r.pair)})),n=trainer.slots.length,edges=new Set(),counts={valid:0,invalid:0,unresolved:0};
 for(const r of samples){if(!Object.hasOwn(counts,r.status))throw Error('Unknown label');counts[r.status]++;if(r.status==='valid')for(const [i,j] of r.contacts)for(const action of trainer.actions){const a=action[i],b=action[j];if(a!==b)edges.add(Math.min(a,b)*n+Math.max(a,b));}}
 const positiveEdges=[...edges].map(k=>[Math.floor(k/n),k%n]),negatives=samples.filter(r=>r.status==='invalid').map(r=>r.contacts);
 const chosen=selectMask(n,trainer.orbits,positiveEdges,negatives,{iterations,seed}),labels=new Map(),values=new Int32Array(n);
 for(let i=0;i<n;i++)if(chosen.active[i]){const root=chosen.find(i);if(!labels.has(root))labels.set(root,labels.size+1);values[i]=labels.get(root);}
 const fields=trainer.byOrientation.map(list=>list.filter(s=>chosen.active[s.id]).map(s=>({pos:s.pos,component:s.component,value:values[s.id]})));
 const representation=trainer.actions.map(action=>{const mapping={};for(let i=0;i<n;i++)if(chosen.active[i]){if(!chosen.active[action[i]])throw Error('Mask not equivariant');const a=values[i],b=values[action[i]];if(mapping[a]!==undefined&&mapping[a]!==b)throw Error('Values not equivariant');mapping[a]=b;}if(new Set(Object.values(mapping)).size!==labels.size)throw Error('Noninvertible masked label action');return mapping;});
 let positivePassed=0,negativeBlocked=0;for(const r of rows){const compatible=pairCompatible(fields,r.pair);if(r.status==='valid'&&compatible)positivePassed++;if(r.status==='invalid'&&!compatible)negativeBlocked++;}
 if(positivePassed!==counts.valid||negativeBlocked!==chosen.blocked)throw Error('Independent masked marking replay failed');
 return {version:'masked-orbit-equalities-research-1',fields,representation,extent,counts,positivePassed,negativeBlocked,points:chosen.points,values:chosen.points,labelCount:labels.size,evaluations:chosen.evaluations,elapsedMs:performance.now()-started,scope:'Research support-mask search; each mask rebuilds positive equalities. All observed positives pass, no optimum or unobserved-pair claim.'};
}
