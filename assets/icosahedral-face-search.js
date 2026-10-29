/** Exact, undecorated face-to-face geometric experiment.
 * Domain: the fixed icosahedral star and its integer translation module.
 * This is a face-obligation analogue of the GCTS scheduler, not a finite
 * point-capacity baseline. No window, multigrid witness or markings filter it.
 */
import { ONE, vector, vadd, vsub, vscale, dot, cross, pointKey } from './golden-field.js';
import { STAR, ORIENTATIONS, makeRhombohedron, containsPoint } from './icosahedral-exact.js';

export const faceKey = (tile, face) => face.map(i => pointKey(tile.vertices[i])).sort().join('|');
const CARTESIAN = [vector(1n,0n,0n),vector(0n,1n,0n),vector(0n,0n,1n)];
const NORMALS = STAR.flatMap((u,i) => STAR.slice(i+1).map(v => cross(u,v)));
const AXES = [...CARTESIAN,...NORMALS];
const projection = (t,n) => {
  let lo=dot(t.origin,n),hi=lo;
  for(const edge of t.edges){const d=dot(edge,n);if(d.sign()<0)lo=lo.add(d);else hi=hi.add(d);}
  return [lo,hi];
};
const cache = new WeakMap();
export function prepare(tile) {
  if(cache.has(tile))return cache.get(tile);
  const vertexKeys=tile.vertices.map(pointKey), faces=tile.faces.map(f=>faceKey(tile,f));
  const edges=[];
  for(let i=0;i<8;i++)for(let j=0;j<3;j++)if(!(i&(1<<j)))edges.push([i,i|(1<<j)]);
  const planes=tile.faces.map(f=>{
    const a=tile.vertices[f[0]],n=cross(vsub(tile.vertices[f[1]],a),vsub(tile.vertices[f[3]],a));
    return {normal:n,offset:dot(n,a)};
  });
  const features=new Set([...vertexKeys, ...edges.map(e=>e.map(i=>vertexKeys[i]).sort().join('|')), ...faces]);
  const result={vertexKeys,faces,edges,planes,features,intervals:AXES.map(n=>projection(tile,n))};
  cache.set(tile,result);return result;
}

/** Complete convex intersection vertices (vertex containment and edge/plane
 * intersections). Used only for degenerate contacts left by exact SAT.
 */
export function intersectionVertices(a,b) {
  const points=new Map();
  for(const [t,other] of [[a,b],[b,a]]){
    for(const p of t.vertices)if(containsPoint(other,p))points.set(pointKey(p),p);
    for(const [i,j] of prepare(t).edges){
      const start=t.vertices[i],delta=vsub(t.vertices[j],start);
      for(const plane of prepare(other).planes){
        const den=dot(plane.normal,delta);if(!den.sign())continue;
        const s=plane.offset.sub(dot(plane.normal,start)).div(den);
        if(s.sign()<0||s.compare(ONE)>0)continue;
        const p=vadd(start,vscale(delta,s));
        if(containsPoint(other,p)&&containsPoint(t,p))points.set(pointKey(p),p);
      }
    }
  }
  return [...points.values()];
}

/** Every intersection must be empty or a complete common face of both
 * polyhedra, including edges and vertices. Partial faces / T-junctions fail.
 */
export function pairRelation(a,b) {
  const pa=prepare(a),pb=prepare(b);let touch=null;
  for(let i=0;i<AXES.length;i++){
    const [al,ah]=pa.intervals[i],[bl,bh]=pb.intervals[i];
    const ab=ah.compare(bl),ba=bh.compare(al);
    if(ab<0||ba<0)return 'disjoint';
    if(ab===0||ba===0)touch={axis:AXES[i],value:ab===0?ah:al};
  }
  if(!touch)return 'overlap';
  const support=t=>t.vertices.filter(p=>dot(p,touch.axis).equals(touch.value)).map(pointKey).sort().join('|');
  const sa=support(a),sb=support(b);
  if(sa===sb)return 'common-face';
  const points=intersectionVertices(a,b);
  if(!points.length)return 'disjoint';
  const key=points.map(pointKey).sort().join('|');
  return pa.features.has(key)&&pb.features.has(key)?'common-face':'partial-contact';
}
export const compatiblePair=(a,b)=>['disjoint','common-face'].includes(pairRelation(a,b));

// Finite local domains: align every face of every declared orientation at
// every target corner, deduplicate exact identities and keep the outer side.
const attachmentCache=new Map();
export function faceAttachments(owner,faceIndex) {
  const face=owner.faces[faceIndex],anchor=owner.vertices[face[0]];
  const relative=face.map(i=>vsub(owner.vertices[i],anchor));
  const key=relative.map(pointKey).join('|');
  if(!attachmentCache.has(key)){
    const wanted=new Set(relative.map(pointKey)),normal=cross(relative[1],relative[3]),result=new Map();
    for(const prototype of ORIENTATIONS)for(const f of prototype.faces)for(const corner of f){
      const origin=vscale(prototype.vertices[corner],-1n);
      if(!f.every(i=>wanted.has(pointKey(vadd(prototype.vertices[i],origin)))))continue;
      const center=vadd(origin,vscale(prototype.edges.reduce(vadd,vector(0n,0n,0n)),ONE.div(2n)));
      if(dot(normal,center).sign()<=0)continue;
      const t=makeRhombohedron(prototype.axes,origin);result.set(t.id,t);
    }
    attachmentCache.set(key,[...result.values()]);
  }
  return attachmentCache.get(key).map(t=>makeRhombohedron(t.axes,vadd(t.origin,anchor)));
}

const cells=t=>{
  const ranges=prepare(t).intervals.slice(0,3).map(([lo,hi])=>[lo.div(4n).floor(),hi.div(4n).floor()]);
  const keys=[];for(let x=ranges[0][0];x<=ranges[0][1];x++)for(let y=ranges[1][0];y<=ranges[1][1];y++)for(let z=ranges[2][0];z<=ranges[2][1];z++)keys.push(`${x},${y},${z}`);return keys;
};
const hash=(text,seed)=>{let h=BigInt(seed)+2166136261n;for(let i=0;i<text.length;i++)h=((h^BigInt(text.charCodeAt(i)))*16777619n)&0xffffffffn;return h;};

export function chooseFace(frontier) {
  const all=[...frontier.values()];
  const compare=(a,b)=>a.generation-b.generation||a.candidates.size-b.candidates.size||a.key.localeCompare(b.key);
  const dead=all.find(p=>p.candidates.size===0);if(dead)return {point:dead,kind:'dead'};
  const forced=all.filter(p=>p.candidates.size===1).sort(compare);if(forced.length)return {point:forced[0],kind:'forced'};
  const point=all.sort(compare)[0];return point?{point,kind:'branch'}:null;
}

export class FaceSearch {
  constructor({seed=1,seedKind='prolate',target=40,budget=10000}={}){
    const started=performance.now();
    if(!Number.isSafeInteger(seed)||!Number.isSafeInteger(target)||target<2||!Number.isSafeInteger(budget)||budget<1)throw new TypeError('Invalid finite search configuration');
    this.config={seed,seedKind,target,budget};this.trail=[];this.frames=[];
    this.placed=new Map();this.frontier=new Map();this.faceOwners=new Map();this.candidates=new Map();
    this.placedBuckets=new Map();this.candidateBuckets=new Map();this.events=[];this.tree=[{id:0,parent:null,depth:0,status:'active'}];this.currentNode=0;
    this.stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0,eliminatedOverlap:0,eliminatedContact:0,checks:0,maxTiles:1,elapsedMs:0};
    this.state='ready';this.lastEvent={type:'seed'};
    const prototype=ORIENTATIONS.find(t=>t.kind===seedKind);if(!prototype)throw new TypeError('Unknown seed shape');
    this.seed=prototype;this.placed.set(prototype.id,{tile:prototype,generation:0});this.addIndex(this.placedBuckets,prototype,prototype.id);
    for(let i=0;i<6;i++)this.faceOwners.set(prepare(prototype).faces[i],[{tile:prototype,faceIndex:i,generation:0}]);
    this.sync();this.trail=[];this.stats.elapsedMs=performance.now()-started;
  }
  set(map,key,value){const had=map.has(key),old=map.get(key);this.trail.push(()=>had?map.set(key,old):map.delete(key));map.set(key,value);}
  del(map,key){if(!map.has(key))return;const old=map.get(key);this.trail.push(()=>map.set(key,old));map.delete(key);}
  add(set,key){if(set.has(key))return;this.trail.push(()=>set.delete(key));set.add(key);}
  drop(set,key){if(!set.has(key))return;this.trail.push(()=>set.add(key));set.delete(key);}
  undo(checkpoint){while(this.trail.length>checkpoint)this.trail.pop()();}
  addIndex(index,tile,id){for(const key of cells(tile)){if(!index.has(key))this.set(index,key,new Set());this.add(index.get(key),id);}}
  near(index,tile){return new Set(cells(tile).flatMap(key=>[...(index.get(key)||[])]));}
  relation(a,b){this.stats.checks++;return pairRelation(a,b);}
  legal(tile){
    if(this.placed.has(tile.id))return false;
    for(const id of this.near(this.placedBuckets,tile)){
      const relation=this.relation(tile,this.placed.get(id).tile);
      if(relation==='overlap'||relation==='partial-contact')return false;
    }return true;
  }
  invalidate(record,reason){
    if(!record.legal)return;
    this.trail.push(()=>{record.legal=true;});record.legal=false;
    for(const key of record.faces){const point=this.frontier.get(key);if(point)this.drop(point.candidates,record.tile.id);}
    if(reason==='failed-child'){const old=record.excluded;this.trail.push(()=>{record.excluded=old;});record.excluded=true;}
    if(reason==='overlap')this.stats.eliminatedOverlap++;else if(reason==='partial-contact')this.stats.eliminatedContact++;
  }
  ensure(tile){
    let record=this.candidates.get(tile.id);
    if(!record){record={tile,faces:prepare(tile).faces,legal:this.legal(tile),excluded:false};this.set(this.candidates,tile.id,record);this.addIndex(this.candidateBuckets,tile,tile.id);}
    if(record.legal)for(const key of record.faces){const point=this.frontier.get(key);if(point)this.add(point.candidates,tile.id);}
  }
  sync(){
    for(const [key] of this.frontier)if(this.faceOwners.get(key)?.length!==1)this.del(this.frontier,key);
    for(const [key,owners] of this.faceOwners)if(owners.length===1&&!this.frontier.has(key)){
      const owner=owners[0],point={key,generation:owner.generation,owner,candidates:new Set()};this.set(this.frontier,key,point);
      for(const tile of faceAttachments(owner.tile,owner.faceIndex))this.ensure(tile);
    }
  }
  apply(tile){
    if(!this.legal(tile))throw new Error('Attempted illegal placement');
    const touched=prepare(tile).faces.map(k=>this.frontier.get(k)).filter(Boolean);
    if(!touched.length)throw new Error('Disconnected candidate');
    const generation=1+Math.min(...touched.map(p=>p.generation));
    for(const id of this.near(this.candidateBuckets,tile)){
      const record=this.candidates.get(id);if(!record.legal)continue;
      const relation=this.relation(record.tile,tile);
      if(relation==='overlap'||relation==='partial-contact')this.invalidate(record,relation);
    }
    this.set(this.placed,tile.id,{tile,generation});this.addIndex(this.placedBuckets,tile,tile.id);
    prepare(tile).faces.forEach((key,faceIndex)=>this.set(this.faceOwners,key,[...(this.faceOwners.get(key)||[]),{tile,faceIndex,generation}]));
    this.sync();return generation;
  }
  step(){
    if(['checkpoint','exhausted','budget'].includes(this.state))return this.lastEvent;
    const start=performance.now();const choice=chooseFace(this.frontier);
    if(choice?.kind==='dead'){
      const frame=this.frames.pop();
      if(!frame){this.state='exhausted';this.lastEvent={type:'exhausted',face:choice.point.key};}
      else{
        this.undo(frame.before);this.invalidate(this.candidates.get(frame.id),'failed-child');
        this.tree[frame.node].status='failed';this.currentNode=frame.parent;
        this.stats.backtracks++;this.lastEvent={type:'remove',tile:frame.id,node:frame.node,reason:'global dead face'};
      }
    }else if(this.placed.size>=this.config.target){
      this.state='checkpoint';this.lastEvent={type:'checkpoint',reason:'finite patch with viable frontier; infinite extension unknown'};
    }else if(this.stats.attempts>=this.config.budget){this.state='budget';this.lastEvent={type:'budget',reason:'unknown'};}
    else if(choice){
      const ids=[...choice.point.candidates].sort((a,b)=>{const x=hash(a,this.config.seed),y=hash(b,this.config.seed);return x<y?-1:x>y?1:a.localeCompare(b);});
      const id=ids[0],before=this.trail.length,parent=this.currentNode,node=this.tree.length;
      this.stats.attempts++;const generation=this.apply(this.candidates.get(id).tile);
      this.tree.push({id:node,parent,depth:this.frames.length+1,status:'active',kind:this.candidates.get(id).tile.kind});this.currentNode=node;
      this.frames.push({id,before,node,parent});this.stats.accepted++;
      this.stats[choice.kind==='forced'?'forced':'branches']++;this.stats.maxTiles=Math.max(this.stats.maxTiles,this.placed.size);this.state='running';
      this.lastEvent={type:'add',tile:id,node,parent,generation,forced:choice.kind==='forced',domain:ids.length,face:choice.point.key};
    }else throw new Error('Unbounded geometric growth unexpectedly has no frontier');
    this.stats.elapsedMs+=performance.now()-start;this.events.push({...this.lastEvent,depth:this.frames.length,tiles:this.placed.size});return this.lastEvent;
  }
  summary(){let incidence=0;const live=new Set();for(const p of this.frontier.values())for(const id of p.candidates){incidence++;live.add(id);}
    return {state:this.state,tiles:this.placed.size,frontier:this.frontier.size,candidates:live.size,incidences:incidence,dead:[...this.frontier.values()].filter(p=>!p.candidates.size).length,...this.stats};}
  inspect(){const result={placed:[...this.placed].map(([id,r])=>[id,r.generation]),frontier:[...this.frontier].map(([k,p])=>[k,p.generation,[...p.candidates].sort()]),candidates:[...this.candidates].map(([id,r])=>[id,r.legal,r.excluded]),placedBuckets:[...this.placedBuckets].map(([k,s])=>[k,[...s].sort()]),candidateBuckets:[...this.candidateBuckets].map(([k,s])=>[k,[...s].sort()]),owners:[...this.faceOwners].map(([k,v])=>[k,v.map(o=>o.tile.id)])};for(const values of Object.values(result))values.sort((a,b)=>a[0].localeCompare(b[0]));return result;}
  export(){return {format:'icosahedral-face-search-v1',model:'undecorated face-to-face geometric search',arithmetic:'Q(tau), exact BigInt',orientations:20,markings:null,windowFilter:false,config:this.config,result:this.state==='checkpoint'?'consistent finite patch with viable frontier':'unknown',stats:this.summary(),tiles:[...this.placed.values()].map(r=>({...r.tile,generation:r.generation})),tree:this.tree,events:this.events};}
}
