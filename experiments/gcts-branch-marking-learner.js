// Experimental GCTS branch-domain learner. No directional or periodic marking hypotheses.
// The learner consumes abstract overlap equalities and sets of alternative extensions.
export function learnSparse({siteCount,positive,choices,seed=1,steps=24,trials=80,penalty=.025}){
  let rng=seed>>>0;const random=()=>((rng=(Math.imul(rng,1664525)+1013904223)>>>0)/4294967296);
  const n=siteCount,parent=new Int32Array(n),sign=new Int8Array(n),zero=new Uint8Array(n);
  function find(x){let r=x,s=1;while(parent[r]!==r){s*=sign[r];r=parent[r]}return [r,s]}
  function evaluate(active,details=false){
    for(let i=0;i<n;i++){parent[i]=i;sign[i]=1;zero[i]=0}
    for(const [u,v,w] of positive){if(!active[u]||!active[v])continue;const [a,sa]=find(u),[b,sb]=find(v);if(a===b){if(sa!==w*sb)zero[a]=1}else{parent[b]=a;sign[b]=w*sa*sb;zero[a]|=zero[b]}}
    const roots=new Int32Array(n),sg=new Int8Array(n);for(let i=0;i<n;i++)if(active[i]){const [r,s]=find(i);roots[i]=r;sg[i]=s}
    const conflict=([u,v,w])=>active[u]&&active[v]&&!(zero[roots[u]]&&zero[roots[v]])&&(roots[u]!==roots[v]||sg[u]!==w*sg[v]);
    let total=0,log=0,pruned=0,counts=[],uncovered=[];
    for(const group of choices){let count=1;for(const alt of group){if(alt.some(conflict))pruned++;else{count++;if(details)uncovered.push(alt)}}total+=count;log+=Math.log(count);counts.push(count)}
    let size=0;for(const v of active)size+=v;
    return {score:log/choices.length+penalty*size/choices.length,mean:total/choices.length,geomean:Math.exp(log/choices.length),pruned,size,counts,uncovered,values:details?Array.from(roots,(r,i)=>active[i]?(zero[r]?0:sg[i]*(r+1)):null):null};
  }
  const active=new Uint8Array(n);let cur=evaluate(active,true),history=[{size:0,mean:cur.mean,geomean:cur.geomean}];
  for(let k=0;k<steps;k++){
    let best=null,bestChange=null;
    for(let j=0;j<trials;j++){
      const alternatives=cur.uncovered;if(!alternatives.length)break;const edges=alternatives[Math.floor(random()*alternatives.length)];if(!edges.length)continue;const [u,v]=edges[Math.floor(random()*edges.length)];if(active[u]&&active[v])continue;
      const oldU=active[u],oldV=active[v];active[u]=active[v]=1;const score=evaluate(active);active[u]=oldU;active[v]=oldV;
      if(score.score<cur.score-1e-10&&(!best||score.score<best.score)){best=score;bestChange=[u,v]}
    }
    if(!best)break;for(const i of bestChange)active[i]=1;cur=evaluate(active,true);
    for(let j=0;j<n;j++)if(active[j]){active[j]=0;const e=evaluate(active);if(e.score<=cur.score){cur=evaluate(active,true)}else active[j]=1}
    history.push({size:cur.size,mean:cur.mean,geomean:cur.geomean,pruned:cur.pruned});
    if(cur.mean<1.95)break;
  }
  return {active:Array.from(active),values:cur.values,history,mean:cur.mean,geomean:cur.geomean,counts:cur.counts};
}

export function makeDataset(E,patchSpecs,{halo=1}={}){
  const tiles=["hat","turtle"],orients=Object.fromEntries(tiles.map(t=>[t,E.tileOrientations(t,E.A2_TILE_LOOPS[t])]));
  const key=p=>p.join(","),parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
  const plus=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]);
  const sites=[],byTile={};for(const tile of tiles){const points=new Map();for(const {point} of orients[tile][0].occupancy.values())for(let x=-halo;x<=halo;x++)for(let y=-halo;y<=halo;y++)if(Math.abs(x+y)<=halo){const p=plus(point,[x,y,-x-y]);points.set(key(p),p)}byTile[tile]=[];for(const point of points.values())for(let component=0;component<3;component++){const id=sites.length;sites.push({tile,point,component});byTile[tile].push(id)}}
  function materialize(tile,index,translation){const orientation=orients[tile][index];return {tile,orientation,translation,id:`${tile}:${index}:${key(translation)}`,loop:orientation.loop.map(p=>plus(p,translation)),occupancy:[...orientation.occupancy.values()].map(e=>({point:plus(e.point,translation),weight:e.weight}))}}
  function marks(p){const sym=p.orientation.symmetry,sign=parity(sym.permutation),out=[];for(const id of byTile[p.tile]){const {point,component}=sites[id];const global=plus(sym.permutation.map(i=>sym.sign*point[i]),p.translation);out.push([key(global)+"|"+sym.permutation.indexOf(component),id,sign])}return out}
  function contacts(p,global){const result=[],seen=new Set();for(const [k,id,sg] of marks(p))for(const [other,os] of global.get(k)||[]){const edge=id<=other?[id,other,sg*os]:[other,id,sg*os],token=edge.join(",");if(!seen.has(token)&&!(id===other&&sg===os)){seen.add(token);result.push(edge)}}return result}
  function pushMarks(p,global){for(const [k,id,sg] of marks(p)){if(!global.has(k))global.set(k,[]);global.get(k).push([id,sg])}}
  const positive=[],choices=[],stats=[];for(const specs of patchSpecs){const patch=specs.map(p=>materialize(...p)),global=new Map(),sums=new Map(),boundary=new Map(),seen=new Set();for(const [i,p] of patch.entries()){
      if(i){const edges=E.polygonBoundaryEdges(p.loop);const shared=edges.find(e=>boundary.get(e.key)===-e.direction);
        if(!shared)throw Error("positive patch not edge connected at "+i);
        const point=shared.from.split(",").map(Number),alts=[],dedup=new Set();
        for(const tile of tiles)for(const o of orients[tile])for(const e of o.occupancy.values()){
          const t=sub(point,e.point),id=`${tile}:${o.index}:${key(t)}`;if(dedup.has(id)||seen.has(id)||id===p.id)continue;dedup.add(id);
          const q=materialize(tile,o.index,t);if(q.occupancy.some(e=>(sums.get(key(e.point))||0)+e.weight>12))continue;
          if(!E.polygonBoundaryEdges(q.loop).some(e=>e.key===shared.key&&e.direction===shared.direction))continue;
          alts.push(contacts(q,global));
        }
        choices.push(alts);stats.push(alts.length+1);
      }
      positive.push(...contacts(p,global));pushMarks(p,global);seen.add(p.id);
      for(const e of p.occupancy)sums.set(key(e.point),(sums.get(key(e.point))||0)+e.weight);
      for(const e of E.polygonBoundaryEdges(p.loop)){const n=(boundary.get(e.key)||0)+e.direction;if(n)boundary.set(e.key,n);else boundary.delete(e.key)}
    }}
  return {sites,positive,choices,stats};
}
