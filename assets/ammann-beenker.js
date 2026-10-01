// Ammann–Beenker: exact Z[zeta_8] coordinates and point markings.
// Edge and vertex-house fragments: Tatham (2026), Figures 14 and 36.
// Polygon separation remains an explicitly numerical geometric control.
import {createFrontierGraph} from './tiling-frontier-graph.js?v=20260924-sevenfold';
import {createPointMarking} from './sevenfold-point-marking.js?v=20260924-gcts';
import {createABCompletion} from './ammann-beenker-marking.js?v=20261001-ab';
export const ZERO=[0,0,0,0],key=p=>p.join(',');
export function add(a,b){const p=a.map((n,i)=>n+b[i]);if(!p.every(Number.isSafeInteger))throw Error('Coordinate overflow');return p;}
export const neg=p=>p.map(n=>-n),sub=(a,b)=>add(a,neg(b)),compare=(a,b)=>a.reduce((c,n,i)=>c||n-b[i],0);
export function direction(i){i=(i%8+8)%8;return ZERO.map((_,j)=>j===i%4?(i<4?1:-1):0);}
export const xy=p=>({x:p[0]+(p[1]-p[3])/Math.SQRT2,y:p[2]+(p[1]+p[3])/Math.SQRT2});
export const rotate=(p,r)=>p.reduce((sum,n,j)=>add(sum,direction(j+r).map(x=>x*n)),ZERO);
export const star=p=>p.reduce((sum,n,j)=>add(sum,direction(3*j).map(x=>x*n)),ZERO);
export function ray(v){for(let i=0;i<8;i++)if(compare(v,direction(i))===0)return i;throw Error('Not a unit octagonal edge');}
// Normal direction of the outer boundary in each pi/4 sector of one complete
// house. Rotate sector indices AND normal directions together. Its polygon is
// [(sqrt2,0),(0,sqrt2),(-sqrt2,0),(-1,0),(-1,-1),(1,-1),(1,0)].
export const HOUSE=[1,1,3,3,4,6,6,0];
export function houseChoices(start,normals){return Array.from({length:8},(_,r)=>r).filter(r=>normals.every((n,j)=>(HOUSE[(start+j-r+8)%8]+r)%8===n));}
export function placement(template,origin){
 const points=template.points.map(p=>add(p,origin)),vertices=points.map(key),loop=points.map(xy);
 const support=points.map((p,i)=>{const exact=add(p,p);return {key:key(exact),exact,weight:template.weights[i]};});
 points.forEach((p,i)=>{const exact=add(p,points[(i+1)%4]);support.push({key:key(exact),exact,weight:4});});
 const marks=[];
 if(template.edgeCodes)template.edgeCodes.forEach((value,i)=>{const point=support[4+i].exact;marks.push({point,channel:'edge',value,address:key(point)+'/edge'});});
 if(template.houses)template.houses.forEach((value,i)=>{const point=support[i].exact;marks.push({point,channel:'house',value,address:key(point)+'/house'});});
 return {...template,origin,points,vertices,loop,support,marks,id:template.type+'@'+key(origin),geometryId:template.geometryType+'@'+key(origin),bounds:{x0:Math.min(...loop.map(p=>p.x)),x1:Math.max(...loop.map(p=>p.x)),y0:Math.min(...loop.map(p=>p.y)),y1:Math.max(...loop.map(p=>p.y))}};
}
export function catalog(kinds=[1,2],rule='full'){
 if(!['none','edges','full'].includes(rule))throw Error('Unknown Ammann–Beenker rule');
 if(!kinds.length||kinds.some(k=>![1,2].includes(k)))throw Error('Select at least one tile');
 const unique=new Map();
 for(const kind of new Set(kinds))for(const hand of (kind===1&&rule==='full'?['r','g']:['r']))for(let rotation=0;rotation<8;rotation++){
  const u=direction(0),v=direction(kind),base=[ZERO,u,add(u,v),v],weights=[kind,4-kind,kind,4-kind];
  const points0=base.map(p=>rotate(p,rotation)),origin=points0.slice().sort(compare)[0],points=points0.map(p=>sub(p,origin));
  const starts=points.map((p,i)=>ray(sub(points[(i+1)%4],p)));
  const geometryType=kind+':'+points.map((p,i)=>key(p)+'~'+weights[i]).sort().join('|');
  const edgeSigns=kind===1?[-1,1,-1,1]:[1,1,-1,-1];
  const edgeCodes=rule==='none'?null:starts.map((r,i)=>(r+(edgeSigns[i]===1?0:4))%8);
  // Exact normal indices transcribed from the shaded pieces in Figure 36.
  const fragments=kind===1?(hand==='r'?[[0],[1,3,4],[5],[5,6,0]]:[[1],[1,3,4],[4],[5,6,0]]):[[0,2],[2,4],[4,6],[6,0]];
  const normals=fragments.map(ns=>ns.map(n=>(n+rotation)%8));
  let combinations=[[]];if(rule==='full')for(let i=0;i<4;i++)combinations=combinations.flatMap(a=>houseChoices(starts[i],normals[i]).map(r=>[...a,r]));
  for(const choices of combinations){const houses=rule==='full'?choices:null;
   const marks=(edgeCodes||[]).map((value,i)=>key(add(points[i],points[(i+1)%4]))+'/e='+value).concat((houses||[]).map((value,i)=>key(add(points[i],points[i]))+'/h='+value)).sort().join('|');
   const type=geometryType+'~'+marks;
   unique.set(type,{kind,hand,rotation,type,geometryType,points,weights,edgeCodes,houses,normals,corners:starts.map((start,i)=>({start,width:weights[i],from:edgeCodes?.[i]??0,to:edgeCodes?.[(i+3)%4]??0,house:houses?.[i]??0}))});
  }
 }
 return [...unique.values()];
}
export const translated=(tile,delta)=>placement({...tile,points:tile.points.map(p=>sub(p,tile.origin))},add(tile.origin,delta));
export function markingsAgree(a,b) {
  return a.marks.every(x=>b.marks.every(y=>x.address!==y.address||x.value===y.value));
}
export function geometryAllowed(a,b) {
  const eps = 1e-9, A = a.bounds, B = b.bounds;
  if (A.x1 < B.x0-eps || B.x1 < A.x0-eps || A.y1 < B.y0-eps || B.y1 < A.y0-eps) return true;
  let separated = false;
  for (const loop of [a.loop,b.loop]) for (let i=0;i<4;i++) {
    const p=loop[i],q=loop[(i+1)%4],nx=q.y-p.y,ny=p.x-q.x;
    const ap=a.loop.map(v=>v.x*nx+v.y*ny),bp=b.loop.map(v=>v.x*nx+v.y*ny);
    if (Math.min(...ap)>=Math.max(...bp)-eps || Math.min(...bp)>=Math.max(...ap)-eps) separated=true;
  }
  if (!separated) return false;
  // Edge-to-edge control: reject vertices in another edge's relative interior.
  for (const [left,right] of [[a,b],[b,a]]) for (const p of left.loop) for (let i=0;i<4;i++) {
    const q=right.loop[i],r=right.loop[(i+1)%4],dx=r.x-q.x,dy=r.y-q.y;
    const cross=(p.x-q.x)*dy-(p.y-q.y)*dx, dot=(p.x-q.x)*dx+(p.y-q.y)*dy;
    if (Math.abs(cross)<eps && dot>eps && dot<dx*dx+dy*dy-eps) return false;
  }
  return true;
}

export function chooseABPoint(points) {
  return points.slice().sort((a,b)=>(a.candidates.length===0?0:a.candidates.length===1?1:2)-(b.candidates.length===0?0:b.candidates.length===1?1:2)||a.depth-b.depth||a.candidates.length-b.candidates.length||a.key.localeCompare(b.key))[0];
}

export function createABSearch({kinds=[1,2],rule='full',seed=1,nodeLimit=12000,method='gcts',trace=false,rootIndex=null}={}) {
  if(!['gcts','plain'].includes(method))throw Error('Unknown Ammann–Beenker search method');
  const templates=catalog(kinds,rule), anchored=new Map();
  for (const t of templates) for (const p of t.points) {
    const tile=placement(t,neg(p));anchored.set(tile.id,tile);
  }
  const movesAt=p=>[...anchored.values()].map(t=>translated(t,p));
  const parity=p=>p.map(n=>(n%2+2)%2).join(','),edgeAlignments=new Map();
  for(const t of templates)for(let i=0;i<4;i++){
    const midpoint=add(t.points[i],t.points[(i+1)%4]),k=parity(midpoint);
    if(!edgeAlignments.has(k))edgeAlignments.set(k,[]);edgeAlignments.get(k).push({template:t,midpoint});
  }
  // Translations remain in Z[zeta_8]. Align every positive-support point;
  // parity rejects alignments requiring a forbidden half-integral translation.
  const movesAtSupport=p=>p.every(n=>n%2===0)?movesAt(p.map(n=>n/2)):(edgeAlignments.get(parity(p))||[]).map(({template,midpoint})=>placement(template,sub(p,midpoint).map(n=>n/2)));
  const tiles=[],ids=new Set(),totals=new Map(),positions=new Map(),generations=new Map(),frames=[],excluded=[new Set()];
  const marking=createPointMarking(),incident=new Map(),completion=createABCompletion(templates.flatMap(t=>t.corners));
  const stats={proposals:0,backtracks:0,forcedMoves:0,branches:0,deadEnds:0,peak:0,repeatedAttempts:trace?0:null};
  const attempts=trace?new Set():null;
  let status='searching',stopped=false;
  const geometryCache=new Map();
  const pair=(a,b)=>{
    const A=a.bounds,B=b.bounds,eps=1e-9;
    if(A.x1<B.x0-eps||B.x1<A.x0-eps||A.y1<B.y0-eps||B.y1<A.y0-eps)return true;
    if(method==='plain'&&rule!=='none'&&!markingsAgree(a,b))return false;
    const cacheKey=a.geometryId<b.geometryId?a.geometryId+'#'+b.geometryId:b.geometryId+'#'+a.geometryId;
    if(geometryCache.has(cacheKey))return geometryCache.get(cacheKey);
    const allowed=geometryAllowed(a,b);if(geometryCache.size>=8192)geometryCache.delete(geometryCache.keys().next().value);geometryCache.set(cacheKey,allowed);return allowed;
  };
  const capacity=t=>!ids.has(t.id)&&t.support.every(p=>(totals.get(p.key)||0)+p.weight<=8);
  const locallyExtendible=t=>t.vertices.every((v,i)=>completion.allows([...(incident.get(v)||[]).map(x=>x.corner),t.corners[i]]));
  const legal=t=>capacity(t)&&(method==='plain'||!marking.rejects(t))&&tiles.every(a=>pair(a,t))&&(method==='plain'||locallyExtendible(t));
  const frontier=()=>[...totals].filter(([,n])=>n<8).map(([key,total])=>({key,total,exact:positions.get(key),depth:Math.min(...generations.get(key))}));
  const wrappers=new WeakMap(),wrap=t=>{if(!wrappers.has(t))wrappers.set(t,{id:t.id,vertices:t.support.map(p=>p.key),tile:t});return wrappers.get(t);};
  const graph=createFrontierGraph({enumerate:p=>movesAtSupport(p.exact).map(wrap),footprint:r=>r.tile.bounds,legal:r=>legal(r.tile),compatibleWithAddition:(r,s)=>{const t=r.tile,a=s.tile;return capacity(t)&&(method==='plain'||!marking.rejects(t))&&pair(t,a)&&(method==='plain'||locallyExtendible(t));}});
  // Read the complete graph directly: shared legacy consumers keep their own
  // scheduler, while this experiment is strictly global dead/forced/generation.
  function choose() {
    const point=chooseABPoint(graph.inspect());if(!point)return null;
    const records=new Map(graph.candidateRecords().map(r=>[r.tile.id,r.tile.tile]));
    return {point,dead:!point.candidates.length,forced:point.candidates.length===1,candidates:point.candidates.map(id=>records.get(id))};
  }
  function put(tile) {
    const near=tile.support.flatMap(p=>generations.get(p.key)||[]);tile={...tile,generation:near.length?Math.min(...near)+1:0};
    tiles.push(tile);ids.add(tile.id);marking.add(tile);stats.peak=Math.max(stats.peak,tiles.length);
    tile.support.forEach(p=>{const v=p.key;totals.set(v,(totals.get(v)||0)+p.weight);positions.set(v,p.exact);if(!generations.has(v))generations.set(v,[]);generations.get(v).push(tile.generation);});
    tile.vertices.forEach((v,i)=>{if(!incident.has(v))incident.set(v,[]);incident.get(v).push({tile,corner:tile.corners[i]});});
    return tile;
  }
  function remove() {
    const t=tiles.pop();ids.delete(t.id);marking.remove(t);
    t.support.forEach(p=>{const v=p.key,n=totals.get(v)-p.weight;if(n)totals.set(v,n);else{totals.delete(v);positions.delete(v);}generations.get(v).pop();if(!generations.get(v).length)generations.delete(v);});
    t.vertices.forEach(v=>{incident.get(v).pop();if(!incident.get(v).length)incident.delete(v);});
  }
  const priority=id=>{let h=(2166136261^seed)>>>0;for(const c of id)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h;};
  function* dfs() {
    while(true) {
      const choice=choose();
      if(choice?.dead){stats.deadEnds++;yield {type:'dead',point:choice.point.key};return;}
      if(stats.proposals>=nodeLimit){status='Budget reached · unknown';stopped=true;return;}
      if(!choice){status='Finite closed frontier';return;}
      // Within the selected point's complete domain, prefer closing existing
      // point deficits. This only orders alternatives; no candidate is excluded.
      const score=t=>t.support.reduce((s,p)=>s+(totals.has(p.key)?2*totals.get(p.key)*p.weight+p.weight**2:0),0);
      const options=choice.candidates.sort((a,b)=>(rule!=='none'?score(b)-score(a):0)||priority(a.id)-priority(b.id)||a.id.localeCompare(b.id));
      if(attempts){const fingerprint=tiles.map(t=>t.id+':'+t.generation).sort().join(';')+'>'+options[0].id;if(attempts.has(fingerprint))stats.repeatedAttempts++;attempts.add(fingerprint);}
      const tile=put(options[0]);stats.proposals++;stats[choice.forced?'forcedMoves':'branches']++;
      frames.push(graph.push(wrap(tile),frontier()));excluded.push(new Set());yield {type:'add',forced:choice.forced,tile:tile.id,choices:options.length,point:choice.point.key};
      yield*dfs();if(stopped)return;
      remove();graph.pop(frames.pop());excluded.pop();excluded.at(-1).add(tile.id);stats.backtracks++;
      const delta=graph.refine(t=>t.id!==tile.id);if(frames.length)frames.at(-1).push(...delta);
      yield {type:'remove',tile:tile.id};
    }
  }
  const rootTemplate=rootIndex===null?(templates.find(t=>t.kind===1&&t.rotation===0&&t.hand==='r'&&t.houses?.join(',')==='5,3,2,2')||templates[0]):templates[rootIndex%templates.length];
  function* run(){put(placement(rootTemplate,ZERO));graph.build(frontier());yield {type:'seed'};yield*dfs();if(!stopped)status='Seeded search exhausted';}
  const iterator=run();
  return {next:()=>iterator.next(),progress:()=>({tiles:tiles.length,deadPoints:graph.deadCount()}),snapshot:()=>({tiles:tiles.slice(),stats:{...stats},status,graph:graph.summary(),frontier:frontier(),rule,method,marking:marking.snapshot(),completion:completion.snapshot()}),inspectMarking:()=>marking.inspect(),
    // Independent enumeration checks completeness as well as absence of stale
    // links. Failed-child exclusions in the current parent are explicitly known.
    audit(){const forbiddenIds=new Set(excluded.flatMap(s=>[...s]));for(const p of graph.inspect()) {
      const actual=new Set(p.candidates), all=movesAtSupport(positions.get(p.key));
      for(const t of all)if(actual.has(t.id)&&!legal(t))throw Error('Illegal graph candidate');
      for(const t of all)if(legal(t)&&!forbiddenIds.has(t.id)&&!actual.has(t.id))throw Error('Missing graph candidate');
      for(const id of actual)if(forbiddenIds.has(id))throw Error('Failed child revived');
    }return true;},movesAt,movesAtSupport,choose};
}
