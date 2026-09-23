// Exact occupancy probes for the displayed relief, restricted to integer
// translations and the 24 proper cubic rotations. No matching values are used.
import { VARIANTS, FACE_DIRECTIONS, key, add } from '../../3d-reptiles/chair/chair44.js';
import { selectFrontier } from '../../3d-reptiles/chair/chair-gcts.js';

export function createReliefPointModel({centered=false}={}) {
// Tangential positions are sqrt(2)/100 times (x,y); normal depth is h/400.
// These are the apex projections of all rotated reliefs, sampled near both tips.
const tangentPoints = new Map();
if(centered) {
  tangentPoints.set('0,0',[0,0]);
  for(const x of [-8,8])for(const y of [-8,8])tangentPoints.set(`${x},${y}`,[x,y]);
} else {
for (const x of [-5,5]) for (const y of [-5,5]) tangentPoints.set(`${x},${y}`, [x,y]);
for (const a of [-1,1]) for (const b of [-1,1]) for (const swap of [false,true]) {
  const xy = swap ? [a*4,b*12] : [a*12,b*4]; tangentPoints.set(xy.join(','),xy);
}
}
const PROBES = [...tangentPoints.values()].flatMap(([x,y])=>[-47,47].map(h=>({x,y,h})));
const FULL = (1 << PROBES.length) - 1;
function height400(mark, x, y) {
  const axis = mark.direction.findIndex(v=>v!==0), tangents=[0,1,2].filter(i=>i!==axis);
  const a=mark.arrow,n=mark.direction;
  const side=[a[1]*n[2]-a[2]*n[1],a[2]*n[0]-a[0]*n[2],a[0]*n[1]-a[1]*n[0]];
  const u=side[tangents[0]]*x+side[tangents[1]]*y;
  const v=a[tangents[0]]*x+a[tangents[1]]*y;
  if(mark.color==='blue') return 3*Math.max(0,16-Math.max(Math.abs(u-16),Math.abs(v-(centered?0:8))))
    -3*Math.max(0,16-Math.max(Math.abs(u+16),Math.abs(v-(centered?0:8))));
  return (mark.color==='red'?2:-2)*Math.max(0,24-Math.max(Math.abs(u),Math.abs(v-(centered?0:10))));
}
function faceMask(mark) {
  const sign=mark.direction.find(v=>v!==0);
  let mask=0;
  PROBES.forEach(({x,y,h},i)=>{
    const height=height400(mark,x,y);
    if(sign*h===height) throw Error('Probe lies on a relief surface');
    if(sign*h<height) mask |= 1<<i;
  });
  return mask;
}
const faceId=(axis,lower)=>`${axis}:${key(lower)}`;
const templates=VARIANTS.map(variant=>{
  const cells=new Set(variant.cells.map(key)),faces=new Map();
  for(const cell of variant.cells) for(const direction of FACE_DIRECTIONS) {
    const axis=direction.findIndex(v=>v!==0),lower=direction[axis]>0?cell:add(cell,direction);
    const id=faceId(axis,lower);
    if(cells.has(key(add(cell,direction)))) faces.set(id,{axis,lower,mask:FULL});
    else {
      const mark=variant.marks.find(m=>key(m.cell)===key(cell)&&key(m.direction)===key(direction));
      faces.set(id,{axis,lower,mask:faceMask(mark)});
    }
  }
  return {cells:variant.cells,faces:[...faces.values()]};
});
const cache=new Map();
function clearCache(){cache.clear();}
function compile(placement) {
  const {variantId,origin}=placement,id=`${variantId}@${key(origin)}`;
  if(!cache.has(id)) {
    const template=templates[variantId];
    cache.set(id,{variantId,origin:[...origin],id,
      cells:template.cells.map(cell=>key(add(cell,origin))),
      faces:template.faces.map(face=>({id:faceId(face.axis,add(face.lower,origin)),mask:face.mask}))});
  }
  return cache.get(id);
}
function indexState(placements) {
  const occupied=new Map(),faceOccupancy=new Map();
  for(const placement of placements) {
    const tile=compile(placement);
    for(const cell of tile.cells) {
      if(occupied.has(cell)) throw Error('Overlapping cell centers');
      occupied.set(cell,placement.generation??0);
    }
    for(const {id,mask} of tile.faces) {
      const old=faceOccupancy.get(id)??0;
      if(old&mask) throw Error('Overlapping relief probes');
      faceOccupancy.set(id,old|mask);
    }
  }
  return {occupied,faceOccupancy};
}
function isLegal(tile,index) {
  return !tile.cells.some(cell=>index.occupied.has(cell))
    && !tile.faces.some(({id,mask})=>(index.faceOccupancy.get(id)??0)&mask);
}
function graphFor(placements) {
  const index=indexState(placements),frontier=new Map(),cells=new Map();
  for(const [id,generation] of index.occupied) for(const d of FACE_DIRECTIONS) {
    const p=add(id.split(',').map(Number),d),cell=key(p);
    if(!index.occupied.has(cell)) {
      const old=cells.get(cell);
      if(!old||generation<old.generation) cells.set(cell,{id:`c:${cell}`,cell,point:p,generation,candidates:new Set()});
    }
  }
  for(const point of cells.values()) frontier.set(point.id,point);
  for(const [id,mask] of index.faceOccupancy) {
    if(mask===FULL) continue;
    const [axisText,cell]=id.split(':'),axis=Number(axisText),a=cell.split(',').map(Number),b=[...a];b[axis]++;
    const generation=Math.min(index.occupied.get(key(a))??Infinity,index.occupied.get(key(b))??Infinity);
    for(let i=0;i<PROBES.length;i++) if(!(mask&(1<<i))) {
      const probeId=`p:${id}:${i}`;
      frontier.set(probeId,{id:probeId,generation,candidates:new Set()});
    }
  }
  const candidates=new Map(),seen=new Set();let tested=0,rejected=0;
  for(const point of cells.values()) for(const variant of VARIANTS) for(const cell of variant.cells) {
    const tile=compile({variantId:variant.id,origin:point.point.map((v,i)=>v-cell[i])});
    if(seen.has(tile.id))continue;seen.add(tile.id);tested++;
    if(!isLegal(tile,index)){rejected++;continue;}
    const incidence=[];
    for(const cell of tile.cells) {const node=frontier.get(`c:${cell}`);if(node)incidence.push(node);}
    for(const {id,mask} of tile.faces) {
      // Faces outside the active domain have no frontier incidence yet.
      const available = mask & (FULL ^ (index.faceOccupancy.get(id) ?? FULL));
      if(!available)continue;
      for(let i=0;i<PROBES.length;i++)if(available&(1<<i))incidence.push(frontier.get(`p:${id}:${i}`));
    }
    if(!incidence.length)continue;
    candidates.set(tile.id,{...tile,generation:1+Math.min(...incidence.map(p=>p.generation))});
    incidence.forEach(point=>point.candidates.add(tile.id));
  }
  const {dead,forced,selected}=selectFrontier([...frontier.values()]);
  const choices=dead?[]:[...(selected?.candidates??[])].map(id=>candidates.get(id));
  choices.sort((a,b)=>a.origin.reduce((s,v)=>s+v*v,0)-b.origin.reduce((s,v)=>s+v*v,0)||a.id.localeCompare(b.id));
  return {index,frontier,candidates,choices,dead:dead?.id??null,forced:Boolean(forced),tested,rejected};
}
function shellTarget(seed,radius) {
  const target=new Set(seed.flatMap(p=>compile(p).cells));let layer=[...target];
  for(let i=0;i<radius;i++) {
    const next=[];
    for(const id of layer)for(const d of FACE_DIRECTIONS){const k=key(add(id.split(',').map(Number),d));if(!target.has(k)){target.add(k);next.push(k);}}
    layer=next;
  }
  return target;
}
function extend(seed,{radius=1,maxNodes=2000,maxTiles=256}={}) {
  const target=shellTarget(seed,radius),stats={nodes:0,forced:0,branches:0,backtracks:0,maxTiles:seed.length};
  const start=performance.now();let witness=null,reason=null;
  function visit(placements) {
    if(stats.nodes>=maxNodes){reason='node budget';return 'unknown';}
    stats.nodes++;stats.maxTiles=Math.max(stats.maxTiles,placements.length);
    const graph=graphFor(placements);
    if(graph.dead){stats.backtracks++;return 'exhausted';}
    if([...target].every(cell=>graph.index.occupied.has(cell))){witness=placements;return 'consistent finite patch';}
    if(placements.length>=maxTiles){reason='tile budget';return 'unknown';}
    if(graph.forced)stats.forced++;else stats.branches++;
    for(const candidate of graph.choices) {
      const result=visit([...placements,{variantId:candidate.variantId,origin:candidate.origin,generation:candidate.generation}]);
      if(result!=='exhausted')return result;
    }
    return 'exhausted';
  }
  const status=visit(seed.map(p=>({...p,origin:[...p.origin],generation:p.generation??0})));
  return {status,reason,radius,targetCells:target.size,...stats,milliseconds:Math.round(performance.now()-start),witness};
}

return {PROBES,FULL,height400,faceMask,compile,indexState,isLegal,graphFor,clearCache,shellTarget,extend};
}
export const {PROBES,FULL,height400,faceMask,compile,indexState,isLegal,graphFor,clearCache,shellTarget,extend}=createReliefPointModel();
