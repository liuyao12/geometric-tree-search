// Evaluation only. No imports from the search, learner or legality predicates.
const dist=(a,b)=>Math.hypot(...a.map((v,k)=>v-b[k]));
const move=(g,p)=>g.r.map((row,k)=>row.reduce((v,x,j)=>v+x*p[j],g.t[k]));
const identity={r:[[1,0,0],[0,1,0],[0,0,1]],t:[0,0,0]};
export function referenceSpacing(reference) {
  let minimum=Infinity;
  for(const a of reference.sites)for(const b of reference.sites)
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++) {
      const d=Math.hypot(...[x,y,z].map((n,k)=>(b.fractional[k]+n-a.fractional[k])*reference.cell[k]));
      if(d>1e-7)minimum=Math.min(minimum,d);
    }
  return minimum;
}
export function referenceBall(reference,center,radius) {
  const out=[];
  for(const [index,s] of reference.sites.entries()) {
    const ranges=reference.cell.map((a,k)=>[Math.ceil((center[k]-radius)/a-s.fractional[k]),Math.floor((center[k]+radius)/a-s.fractional[k])]);
    for(let x=ranges[0][0];x<=ranges[0][1];x++)for(let y=ranges[1][0];y<=ranges[1][1];y++)for(let z=ranges[2][0];z<=ranges[2][1];z++) {
      const position=[x,y,z].map((n,k)=>(n+s.fractional[k])*reference.cell[k]);
      if(dist(position,center)<=radius+1e-9)out.push({species:s.species,position,key:`${index}:${x}:${y}:${z}`});
    }
  }return out;
}
function siteIdentity(reference,atom,epsilon) {
  let best=null;
  for(const [i,s] of reference.sites.entries())if(s.species===atom.species) {
    const cell=reference.cell.map((a,k)=>Math.round(atom.position[k]/a-s.fractional[k]));
    const p=cell.map((n,k)=>(n+s.fractional[k])*reference.cell[k]);
    const d=dist(p,atom.position);
    if(d<=epsilon&&(!best||d<best.error))best={key:`${i}:${cell.join(':')}`,error:d,position:p};
  }return best;
}
function angle(a,b,c) {
  const u=a.map((v,k)=>v-b[k]),v=c.map((x,k)=>x-b[k]);
  return Math.acos(Math.max(-1,Math.min(1,u.reduce((n,x,k)=>n+x*v[k],0)/(Math.hypot(...u)*Math.hypot(...v)))))*180/Math.PI;
}
export function scoreStructure(reference,atoms,{poses=[identity],epsilon=.03,windowFactors=[2,4,6]}={}) {
  if(!atoms.length)return null;
  let best;
  for(const pose of poses) {
    const aligned=atoms.map(a=>({species:a.species,position:move(pose,a.position)}));
    const matches=aligned.map(a=>siteIdentity(reference,a,epsilon));
    const matched=matches.filter(Boolean).length;
    if(!best||matched>best.matched)best={pose,aligned,matches,matched};
    if(matched===atoms.length)break;
  }
  const spacing=referenceSpacing(reference),center=move(best.pose,[0,0,0]),cutoff=1.35*spacing;
  const labels=[...new Set(reference.sites.map(a=>a.species))].sort();
  const counts=Object.fromEntries(labels.map(s=>[s,best.aligned.filter(a=>a.species===s).length]));
  const compositionTV=.5*labels.reduce((s,l)=>s+Math.abs(counts[l]/atoms.length-reference.sites.filter(a=>a.species===l).length/reference.sites.length),0);
  const unique=new Set(best.matches.filter(Boolean).map(m=>m.key));
  const windows=windowFactors.map(factor=>{
    const radius=factor*spacing,truth=referenceBall(reference,center,radius),inside=best.aligned.filter(a=>dist(a.position,center)<=radius+1e-9);
    const truthKeys=new Set(truth.map(a=>a.key));
    const covered=new Set(best.matches.filter(m=>m&&truthKeys.has(m.key)).map(m=>m.key));
    const extended=referenceBall(reference,center,radius+cutoff);
    // Matched centres in a seed-centred inner ball; missing neighbours are errors,
    // not discarded by conditioning on a complete generated neighbourhood.
    const seen=new Set();let centers=0,expectedEdges=0,recoveredEdges=0,exactStars=0;
    const angleReference=Array(18).fill(0),angleGenerated=Array(18).fill(0);
    for(const [i,m] of best.matches.entries()) {
      if(!m||seen.has(m.key)||dist(m.position,center)>radius-cutoff)continue;
      seen.add(m.key);centers++;
      const neighbors=extended.filter(a=>a.key!==m.key&&dist(a.position,m.position)<=cutoff);
      const present=neighbors.filter(a=>unique.has(a.key));
      expectedEdges+=neighbors.length;recoveredEdges+=present.length;
      if(neighbors.length===present.length)exactStars++;
      const observed=best.aligned.filter((a,j)=>j!==i&&dist(a.position,best.aligned[i].position)<=cutoff);
      for(const [list,bins,origin] of [[neighbors,angleReference,m.position],[observed,angleGenerated,best.aligned[i].position]])
        for(let j=0;j<list.length;j++)for(let k=j+1;k<list.length;k++) {
          const degrees=angle(list[j].position,origin,list[k].position);
          if(Number.isFinite(degrees))bins[Math.min(17,Math.floor(degrees/10+1e-8))]++;
        }
    }
    const na=angleReference.reduce((a,b)=>a+b,0),nb=angleGenerated.reduce((a,b)=>a+b,0);
    const angleTV=na&&nb?.5*angleReference.reduce((s,n,i)=>s+Math.abs(n/na-angleGenerated[i]/nb),0):null;
    return {factor,radius,referenceSites:truth.length,generatedAtoms:inside.length,coveredSites:covered.size,siteRecall:truth.length?covered.size/truth.length:null,numberRatio:truth.length?inside.length/truth.length:null,centers,expectedEdges,recoveredEdges,neighborRecall:expectedEdges?recoveredEdges/expectedEdges:null,exactStars,exactStarFraction:centers?exactStars/centers:null,angleReference,angleGenerated,angleTV};
  });
  return {atoms:atoms.length,matched:best.matched,sitePrecision:best.matched/atoms.length,duplicateSiteAssignments:best.matched-unique.size,counts,compositionTV,spacing,cutoff,alignment:best.pose,windows};
}
