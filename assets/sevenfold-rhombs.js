// Sevenfold geometric control. Exact integer coordinates and corner/mark values;
// polygon separation uses floating point and is not an exact geometry proof.
import {createFrontierGraph} from './tiling-frontier-graph.js?v=20260924-sevenfold';
import {createPointMarking,createVertexCompletion} from './sevenfold-point-marking.js?v=20260924-gcts';

export const ZERO = [0, 0, 0, 0, 0, 0];
export const key = p => p.join(',');
export function add(a, b) {
  const p = a.map((n, i) => n + b[i]);
  if (!p.every(Number.isSafeInteger)) throw Error('Coordinate overflow');
  return p;
}
export const neg = p => p.map(n => -n);
export const sub = (a, b) => add(a, neg(b));
export const compare = (a, b) => a.reduce((c, n, i) => c || n - b[i], 0);
export function direction(i) {
  i = (i % 14 + 14) % 14;
  const exponent = (4 * i) % 7, sign = i % 2 ? -1 : 1;
  return exponent === 6 ? ZERO.map(() => -sign) : ZERO.map((_, j) => j === exponent ? sign : 0);
}
export const xy = p => p.reduce((q, n, i) => ({x:q.x + n * Math.cos(2 * Math.PI * i / 7), y:q.y + n * Math.sin(2 * Math.PI * i / 7)}), {x:0, y:0});

export function placement(template, origin) {
  const points = template.points.map(p => add(p, origin)), vertices = points.map(key), loop = points.map(xy);
  const edgeCodes=template.edgeCodes||[];
  const marks=edgeCodes.map((code,i)=>{const point=add(points[i],points[(i+1)%4]);return {...code,point,address:key(point)+'/'+code.channel};});
  // Exact point domain uses doubled coordinates. Vertices carry corner
  // weights; every edge midpoint carries 7/14 and must acquire its other half.
  const support=points.map((p,i)=>{const exact=add(p,p);return {key:key(exact),exact,weight:template.weights[i]};});
  points.forEach((p,i)=>{const exact=add(p,points[(i+1)%4]);support.push({key:key(exact),exact,weight:7});});
  return {kind:template.kind, type:template.type, origin, points, vertices, loop, weights:template.weights,
    id:template.type + '@' + key(origin), geometryId:template.type.split('~s')[0]+'@'+key(origin), marks,edgeCodes,corners:template.corners,support,
    bounds:{x0:Math.min(...loop.map(p => p.x)), x1:Math.max(...loop.map(p => p.x)), y0:Math.min(...loop.map(p => p.y)), y1:Math.max(...loop.map(p => p.y))}};
}
export function catalog(kinds = [1, 2, 3], rule='none') {
  if(!['none','socolar'].includes(rule))throw Error('Unknown sevenfold matching rule');
  if (!kinds.length || kinds.some(k => ![1,2,3].includes(k))) throw Error('Select at least one rhomb');
  const unique = new Map();
  for (const kind of new Set(kinds)) for (let i = 0; i < 14; i++) {
    const u = direction(i), v = direction(i + kind), corners = [ZERO, u, add(u,v), v];
    const origin = corners.slice().sort(compare)[0], points = corners.map(p => sub(p,origin));
    const weights = [kind, 7-kind, kind, 7-kind];
    const type = kind + ':' + points.map((p,j) => key(p) + '~' + weights[j]).sort().join('|');
    unique.set(type, {kind, type, points, weights});
  }
  const result=rule==='socolar'?[...unique.values()].flatMap(socolarDecorations):[...unique.values()];
  for(const t of result)t.corners=t.points.map((p,i)=>{const axis=edgeAxis(sub(t.points[(i+1)%4],p));return {start:(2*axis.axis+(axis.sign<0?7:0))%14,width:t.weights[i],from:t.edgeCodes?.[i].value||0,to:t.edgeCodes?.[(i+3)%4].value||0};});
  return result;
}
// Socolar (1990), section 5: one bit for each of the three rhomb shapes.
// Bit k means that a tile on the LEFT of e_m must use axis m+k (1) or
// m-k (0). A tile on the right uses the opposite choice. Across a rhomb,
// only the bit for that rhomb's shape flips; the other two are transported.
// These are 4 arrow types x 2 directions, not a ban on equal-shaped tiles.
export function edgeAxis(vector){
  for(let m=0;m<7;m++){
    const e=direction(2*m);
    if(compare(vector,e)===0)return {axis:m,sign:1};
    if(compare(vector,neg(e))===0)return {axis:m,sign:-1};
  }
  throw Error('Not a unit sevenfold edge');
}
export function socolarDecorations(template){
  const edges=template.points.map((p,i)=>edgeAxis(sub(template.points[(i+1)%4],p)));
  const codes=[];
  for(let free=0;free<16;free++){
    const edgeCodes=edges.map((edge,i)=>{
      const other=edges[(i+1)%4].axis,delta=(other-edge.axis+7)%7;
      const k=Math.min(delta,7-delta), own=edge.sign*(delta<=3?1:-1)>0?1:0;
      let value=own<<(k-1),cursor=0;
      for(let bit=0;bit<3;bit++)if(bit!==k-1){value|=((free>>((i%2)*2+cursor))&1)<<bit;cursor++;}
      return {channel:edge.axis,value};
    });
    // All 16 states of a FIXED oriented rhomb; rotation by pi pairs them,
    // giving eight decorated prototiles per shape (24 altogether).
    codes.push({...template,type:template.type+'~s'+edgeCodes.map(e=>e.value).join('.'),edgeCodes});
  }
  return codes;
}
export const translated = (tile, delta) => placement({kind:tile.kind,type:tile.type,points:tile.points.map(p=>sub(p,tile.origin)),weights:tile.weights,edgeCodes:tile.edgeCodes,corners:tile.corners},add(tile.origin,delta));
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

export function chooseSevenfoldPoint(points) {
  return points.slice().sort((a,b)=>(a.candidates.length===0?0:a.candidates.length===1?1:2)-(b.candidates.length===0?0:b.candidates.length===1?1:2)||a.depth-b.depth||a.candidates.length-b.candidates.length||a.key.localeCompare(b.key))[0];
}

export function createSevenfoldSearch({kinds=[1,2,3],rule='none',seed=1,nodeLimit=12000,method='gcts',trace=false}={}) {
  if(!['gcts','plain'].includes(method))throw Error('Unknown sevenfold search method');
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
  // Translations remain in Z[zeta_7]. Align every positive-support point;
  // parity rejects alignments requiring a forbidden half-integral translation.
  const movesAtSupport=p=>p.every(n=>n%2===0)?movesAt(p.map(n=>n/2)):(edgeAlignments.get(parity(p))||[]).map(({template,midpoint})=>placement(template,sub(p,midpoint).map(n=>n/2)));
  const tiles=[],ids=new Set(),totals=new Map(),positions=new Map(),generations=new Map(),frames=[],excluded=[new Set()];
  const marking=createPointMarking(),incident=new Map(),completion=createVertexCompletion(templates.flatMap(t=>t.corners));
  const stats={proposals:0,backtracks:0,forcedMoves:0,branches:0,deadEnds:0,peak:0,repeatedAttempts:trace?0:null};
  const attempts=trace?new Set():null;
  let status='searching',stopped=false;
  const geometryCache=new Map();
  const pair=(a,b)=>{
    const A=a.bounds,B=b.bounds,eps=1e-9;
    if(A.x1<B.x0-eps||B.x1<A.x0-eps||A.y1<B.y0-eps||B.y1<A.y0-eps)return true;
    if(method==='plain'&&rule==='socolar'&&!markingsAgree(a,b))return false;
    const cacheKey=a.geometryId<b.geometryId?a.geometryId+'#'+b.geometryId:b.geometryId+'#'+a.geometryId;
    if(geometryCache.has(cacheKey))return geometryCache.get(cacheKey);
    const allowed=geometryAllowed(a,b);if(geometryCache.size>=8192)geometryCache.delete(geometryCache.keys().next().value);geometryCache.set(cacheKey,allowed);return allowed;
  };
  const capacity=t=>!ids.has(t.id)&&t.support.every(p=>(totals.get(p.key)||0)+p.weight<=14);
  const locallyExtendible=t=>t.vertices.every((v,i)=>completion.allows([...(incident.get(v)||[]).map(x=>x.corner),t.corners[i]]));
  const legal=t=>capacity(t)&&(method==='plain'||!marking.rejects(t))&&tiles.every(a=>pair(a,t))&&(method==='plain'||locallyExtendible(t));
  const frontier=()=>[...totals].filter(([,n])=>n<14).map(([key,total])=>({key,total,exact:positions.get(key),depth:Math.min(...generations.get(key))}));
  const wrappers=new WeakMap(),wrap=t=>{if(!wrappers.has(t))wrappers.set(t,{id:t.id,vertices:t.support.map(p=>p.key),tile:t});return wrappers.get(t);};
  const graph=createFrontierGraph({enumerate:p=>movesAtSupport(p.exact).map(wrap),footprint:r=>r.tile.bounds,legal:r=>legal(r.tile),compatibleWithAddition:(r,s)=>{const t=r.tile,a=s.tile;return capacity(t)&&(method==='plain'||!marking.rejects(t))&&pair(t,a)&&(method==='plain'||locallyExtendible(t));}});
  // Read the complete graph directly: shared legacy consumers keep their own
  // scheduler, while this experiment is strictly global dead/forced/generation.
  function choose() {
    const point=chooseSevenfoldPoint(graph.inspect());if(!point)return null;
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
      const options=choice.candidates.sort((a,b)=>(rule==='socolar'?score(b)-score(a):0)||priority(a.id)-priority(b.id)||a.id.localeCompare(b.id));
      if(attempts){const fingerprint=tiles.map(t=>t.id+':'+t.generation).sort().join(';')+'>'+options[0].id;if(attempts.has(fingerprint))stats.repeatedAttempts++;attempts.add(fingerprint);}
      const tile=put(options[0]);stats.proposals++;stats[choice.forced?'forcedMoves':'branches']++;
      frames.push(graph.push(wrap(tile),frontier()));excluded.push(new Set());yield {type:'add',forced:choice.forced,tile:tile.id,choices:options.length,point:choice.point.key};
      yield*dfs();if(stopped)return;
      remove();graph.pop(frames.pop());excluded.pop();excluded.at(-1).add(tile.id);stats.backtracks++;
      const delta=graph.refine(t=>t.id!==tile.id);if(frames.length)frames.at(-1).push(...delta);
      yield {type:'remove',tile:tile.id};
    }
  }
  function* run(){put(placement(templates[0],ZERO));graph.build(frontier());yield {type:'seed'};yield*dfs();if(!stopped)status='Seeded search exhausted';}
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
