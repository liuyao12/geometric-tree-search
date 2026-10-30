/** Exact whole-facet geometric search. This is a geometric experiment, not
 * the shared finite point-capacity baseline. No floating-point predicates.
 * All proper rigid face isometries are enumerated locally; orientations need
 * not form a finite global group. Geometry-only models remain explicit.
 */
import { Golden as G,ZERO,ONE,vector,vadd,vsub,vscale,dot,cross,determinant,inverseColumns,pointKey } from './golden-field.js';
import { PointMarkingState } from './exact-point-marking-state.js';
export const I=[vector(1n,0n,0n),vector(0n,1n,0n),vector(0n,0n,1n)],O=vector(0n,0n,0n);
export const mv=(m,p)=>m.reduce((s,c,i)=>vadd(s,vscale(c,p[i])),O);
export const mm=(a,b)=>b.map(c=>mv(a,c));
export const center=points=>vscale(points.reduce(vadd,O),ONE.div(BigInt(points.length)));
export const facetKey=points=>points.map(pointKey).sort().join('|');
const edgeKey=(a,b)=>[pointKey(a),pointKey(b)].sort().join('|');
const faceNormal=p=>{for(let i=1;i+1<p.length;i++){const n=cross(vsub(p[i],p[0]),vsub(p[i+1],p[0]));if(dot(n,n).sign())return n;}return O;};
const normalKey=n=>{const k=n.find(x=>x.sign());return n.map(x=>x.div(k).key()).join(';');};
export class SearchLimit extends Error{constructor(message){super(message);this.kind='budget';}}
const spend=(budget,n=1)=>{if(budget&&(budget.used+=n)>budget.max)throw new SearchLimit('Exact geometry work budget reached; result unknown');};
export function decimalScalar(value){
 if(typeof value==='string'&&value.includes('/')){const [a,d]=value.split('/');return new G(a,'0',d);}
 const match=String(value).match(/^(-?)(\d+)(?:\.(\d+))?(?:e([+-]?\d+))?$/i);if(!match)throw Error('Invalid decimal proxy coordinate');
 const digits=BigInt(match[2]+(match[3]||''))*(match[1]?-1n:1n),scale=(match[3]||'').length-Number(match[4]||0);
 return scale>=0?new G(digits,0n,10n**BigInt(scale)):new G(digits*10n**BigInt(-scale));
}
export const exactScalar=x=>Array.isArray(x)?G.fromJSON(x):decimalScalar(x);
export function meshVolume(vertices,faces){let v=ZERO;for(const f of faces)for(let i=1;i+1<f.length;i++)v=v.add(determinant(vertices[f[0]],vertices[f[i]],vertices[f[i+1]]).div(6n));return v;}
const faceSignature=ps=>`${ps.length}:`+ps.flatMap((p,i)=>ps.slice(i+1).map(q=>dot(vsub(p,q),vsub(p,q)).key())).sort().join('|');
const bounds=ps=>[0,1,2].map(i=>[ps.map(p=>p[i]).reduce((a,b)=>a.compare(b)<0?a:b),ps.map(p=>p[i]).reduce((a,b)=>a.compare(b)>0?a:b)]);
const separated=(a,b,closed=false)=>a.some(([lo,hi],i)=>closed?hi.compare(b[i][0])<=0||b[i][1].compare(lo)<=0:hi.compare(b[i][0])<0||b[i][1].compare(lo)<0);
function plane(p){const n=faceNormal(p);if(!dot(n,n).sign())throw Error('Degenerate boundary facet');return {n,w:dot(n,p[0])};}
function split(p,poly,front,back,coplanarFront,coplanarBack,budget){
 spend(budget,poly.length);const signs=poly.map(v=>dot(p.n,v).sub(p.w).sign()),hasFront=signs.some(x=>x>0),hasBack=signs.some(x=>x<0);
 if(!hasFront&&!hasBack){(dot(p.n,faceNormal(poly)).sign()>0?coplanarFront:coplanarBack).push(poly);return;}
 if(!hasBack){front.push(poly);return;}if(!hasFront){back.push(poly);return;}
 const f=[],b=[];for(let i=0;i<poly.length;i++){const j=(i+1)%poly.length,a=poly[i],c=poly[j],sa=signs[i],sb=signs[j];if(sa>=0)f.push(a);if(sa<=0)b.push(a);if(sa*sb<0){const delta=vsub(c,a),t=p.w.sub(dot(p.n,a)).div(dot(p.n,delta)),v=vadd(a,vscale(delta,t));f.push(v);b.push(v);}}
 if(f.length>=3)front.push(f);if(b.length>=3)back.push(b);
}
class BSP{
 constructor(polygons=[],budget){this.polygons=[];this.front=null;this.back=null;this.plane=null;this.budget=budget;if(polygons.length)this.build(polygons);}
 clone(){const n=new BSP([],this.budget);n.plane=this.plane;n.polygons=[...this.polygons];n.front=this.front?.clone()||null;n.back=this.back?.clone()||null;return n;}
 invert(){this.polygons=this.polygons.map(p=>[...p].reverse());if(this.plane)this.plane={n:vscale(this.plane.n,-1n),w:this.plane.w.neg()};this.front?.invert();this.back?.invert();[this.front,this.back]=[this.back,this.front];}
 clipPolygons(polygons){if(!this.plane)return [...polygons];let f=[],b=[];for(const p of polygons)split(this.plane,p,f,b,f,b,this.budget);if(this.front)f=this.front.clipPolygons(f);b=this.back?this.back.clipPolygons(b):[];return f.concat(b);}
 clipTo(other){this.polygons=other.clipPolygons(this.polygons);this.front?.clipTo(other);this.back?.clipTo(other);}
 all(){return this.polygons.concat(this.front?.all()||[],this.back?.all()||[]);}
 build(polygons){if(!polygons.length)return;this.plane??=plane(polygons[0]);const f=[],b=[];for(const p of polygons)split(this.plane,p,f,b,this.polygons,this.polygons,this.budget);if(f.length){this.front??=new BSP([],this.budget);this.front.build(f);}if(b.length){this.back??=new BSP([],this.budget);this.back.build(b);}}
}
function polygonVolume(polygons){let v=ZERO;for(const p of polygons)for(let i=1;i+1<p.length;i++)v=v.add(determinant(p[0],p[i],p[i+1]).div(6n));return v;}
export function exactIntersectionVolume(a,b,budget){
 if(separated(a.bounds,b.bounds,true))return ZERO;
 const x=new BSP(a.polygons,budget),y=new BSP(b.polygons,budget);x.invert();y.clipTo(x);y.invert();x.clipTo(y);y.clipTo(x);x.build(y.all());x.invert();return polygonVolume(x.all()).abs();
}
function clipPolygon(poly,clip){
 const n=faceNormal(clip);let out=[...poly];for(let i=0;i<clip.length&&out.length;i++){
  const a=clip[i],edge=vsub(clip[(i+1)%clip.length],a),half=cross(edge,n),w=dot(half,a),input=out;out=[];
  for(let j=0;j<input.length;j++){const p=input[j],q=input[(j+1)%input.length],u=dot(half,p).sub(w),v=dot(half,q).sub(w);if(u.sign()<=0)out.push(p);if(u.sign()*v.sign()<0)out.push(vadd(p,vscale(vsub(q,p),u.div(u.sub(v)))));}
 }return [...new Map(out.map(p=>[pointKey(p),p])).values()];
}
const inFace=(p,f)=>!dot(faceNormal(f),vsub(p,f[0])).sign()&&f.every((v,i)=>dot(cross(vsub(f[(i+1)%f.length],v),vsub(p,v)),faceNormal(f)).sign()>=0);
const onSegment=(p,a,b)=>!dot(cross(vsub(p,a),vsub(b,a)),cross(vsub(p,a),vsub(b,a))).sign()&&dot(vsub(p,a),vsub(p,b)).sign()<=0;
function faceIntersection(a,b){
 const pa=plane(a),pb=plane(b),parallel=!dot(cross(pa.n,pb.n),cross(pa.n,pb.n)).sign();
 if(parallel){if(dot(pa.n,vsub(b[0],a[0])).sign())return [];return clipPolygon(a,b);}
 const points=new Map();for(const [f,other,p]of [[a,b,pb],[b,a,pa]])for(let i=0;i<f.length;i++){
  const u=f[i],v=f[(i+1)%f.length],s=dot(p.n,u).sub(p.w),t=dot(p.n,v).sub(p.w);if(!s.sign()&&inFace(u,other))points.set(pointKey(u),u);
  if(s.sign()*t.sign()<0){const q=vadd(u,vscale(vsub(v,u),s.div(s.sub(t))));if(inFace(q,other))points.set(pointKey(q),q);}
 }return [...points.values()];
}
export function fullFeatureContacts(a,b,budget){
 const sharedFaces=a.polygons.filter((p,i)=>b.faceKeys.includes(a.faceKeys[i])),sharedEdges=a.edges.filter(e=>b.edgeKeys.has(edgeKey(...e))),sharedVertices=new Set(a.vertices.map(pointKey).filter(k=>b.vertexKeys.has(k)));
 const covered=p=>sharedVertices.has(pointKey(p))||sharedEdges.some(e=>onSegment(p,...e))||sharedFaces.some(f=>inFace(p,f));
 for(let i=0;i<a.polygons.length;i++)for(let j=0;j<b.polygons.length;j++){
  if(separated(a.faceBounds[i],b.faceBounds[j]))continue;spend(budget);if(a.faceKeys[i]===b.faceKeys[j])continue;
  const hit=faceIntersection(a.polygons[i],b.polygons[j]);if(!hit.length)continue;if(hit.some(p=>!covered(p)))return false;
  if(hit.length>=3){const n=cross(vsub(hit[1],hit[0]),vsub(hit[2],hit[0]));if(dot(n,n).sign())return false;}
  if(hit.length>=2){const u=hit[0],v=hit.find(p=>pointKey(p)!==pointKey(u));if(v&&!sharedFaces.some(f=>inFace(u,f)&&inFace(v,f))&&!sharedEdges.some(e=>onSegment(u,...e)&&onSegment(v,...e)))return false;}
 }return true;
}
export function preparePrototype(raw,{mirror=false,proxy=false}={}){
 let vertices=raw.vertices.map(p=>vector(...p.map(exactScalar))),faces=raw.faces.map(f=>[...f]);
 if(mirror){vertices=vertices.map(p=>vector(p[0].neg(),p[1],p[2]));faces=faces.map(f=>f.reverse());}
 const directed=new Map();for(const f of faces){if(f.length<3)throw Error('Invalid facet');const p=f.map(i=>vertices[i]),pl=plane(p);if(p.some(q=>dot(pl.n,q).compare(pl.w)!==0))throw Error('Nonplanar exact facet');for(let i=0;i<f.length;i++){const a=pointKey(vertices[f[i]]),b=pointKey(vertices[f[(i+1)%f.length]]),key=[a,b].sort().join('|');const entry=directed.get(key)||[0,0];entry[0]++;entry[1]+=a<b?1:-1;directed.set(key,entry);}}
 if([...directed.values()].some(([n,s])=>n!==2||s!==0))throw Error('Mesh is not a closed oriented boundary');
 const volume=meshVolume(vertices,faces);if(volume.sign()<=0)throw Error('Mesh has nonpositive oriented volume');
 return {raw,id:raw.id+(mirror?'~':''),kind:raw.id,name:raw.name,vertices,faces,volume,mirror,proxy,color:raw.color,faceColors:raw.faceColors,faceSymbols:raw.faceSymbols,rightAngleEdges:raw.rightAngleEdges||[]};
}
export function place(proto,rotation=I,translation=O){
 const vertices=proto.vertices.map(p=>vadd(mv(rotation,p),translation)),polygons=proto.faces.map(f=>f.map(i=>vertices[i])),keys=vertices.map(pointKey),edges=new Map();for(const f of proto.faces)for(let i=0;i<f.length;i++){const a=vertices[f[i]],b=vertices[f[(i+1)%f.length]];edges.set(edgeKey(a,b),[a,b]);}
 const marks=proto.raw.pointMarkings?.map(m=>({point:vadd(mv(rotation,vector(...m.point.map(exactScalar))),translation),components:m.components}));
 return {proto,kind:proto.kind,name:proto.name,rotation,translation,origin:translation,vertices,faces:proto.faces,polygons,volume:proto.volume,axes:[],color:proto.color,faceColors:proto.faceColors,faceSymbols:proto.faceSymbols,pointMarkings:marks||[],bounds:bounds(vertices),faceBounds:polygons.map(bounds),faceKeys:polygons.map(facetKey),vertexKeys:new Set(keys),edges:[...edges.values()],edgeKeys:new Set(edges.keys()),id:proto.kind+'@'+keys.sort().join('|')};
}
function reflectedVertices(tile,face){const p=tile.polygons[face],n=faceNormal(p),nn=dot(n,n);return tile.vertices.map(v=>vsub(v,vscale(n,dot(n,vsub(v,p[0])).mul(2n).div(nn))));}
const blueFace=(tile,i)=>tile.proto.rightAngleEdges.some(e=>e.every(v=>tile.faces[i].includes(v)));
const sourceCompatible=(a,ai,b,bi,mode)=>mode!=='danzer'||!(blueFace(a,ai)||blueFace(b,bi))||(a.kind===b.kind&&facetKey(reflectedVertices(a,ai))===facetKey(b.vertices));
function matrixFromFaces(source,target){
 const u=vsub(source[1],source[0]),v=vsub(source[2],source[0]),x=vsub(target[1],target[0]),y=vsub(target[2],target[0]);
 if(dot(u,u).compare(dot(x,x))||dot(v,v).compare(dot(y,y))||dot(u,v).compare(dot(x,y)))return null;
 const inverse=inverseColumns(u,v,cross(u,v)),cols=[x,y,cross(x,y)],rotation=[0,1,2].map(i=>cols.reduce((s,c,j)=>vadd(s,vscale(c,inverse[j][i])),O));
 return {rotation,translation:vsub(target[0],mv(rotation,source[0]))};
}
export class PolyhedralModel{
 constructor({id,tiles,mode='geometry',mirrors=true,scope,proxy=false,fixedFrame=false,maxWork=500000}){
  this.id=id;this.mode=mode;this.fixedFrame=fixedFrame;this.scope=scope;this.proxy=proxy;this.work={used:0,max:maxWork};this.prototypes=tiles.flatMap(t=>mirrors?[preparePrototype(t,{proxy}),preparePrototype(t,{mirror:true,proxy})]:[preparePrototype(t,{proxy})]);this.relative=new Map();
  this.faceIndex=new Map();for(const p of this.prototypes)for(let i=0;i<p.faces.length;i++){const ps=p.faces[i].map(j=>p.vertices[j]),key=faceSignature(ps);if(!this.faceIndex.has(key))this.faceIndex.set(key,[]);this.faceIndex.get(key).push({proto:p,face:i,points:ps});}
 }
 attachments(owner,face){
  const cacheKey=owner.proto.id+':'+face;if(!this.relative.has(cacheKey)){
   const base=place(owner.proto),target=base.polygons[face],list=new Map();
   for(const source of this.faceIndex.get(faceSignature(target))||[]){
    if(this.fixedFrame||this.mode==='wang'){
     const translation=vsub(target[0],source.points[0]),candidate=place(source.proto,I,translation);
     if(candidate.faceKeys[source.face]!==base.faceKeys[face]||dot(faceNormal(target),faceNormal(candidate.polygons[source.face])).sign()>=0)continue;
     list.set(candidate.id,{proto:source.proto,rotation:I,translation});continue;
    }
    for(let start=0;start<target.length;start++){
     spend(this.work);const mapped=target.map((_,i)=>target[(start-i+target.length)%target.length]),transform=matrixFromFaces(source.points,mapped);if(!transform)continue;
     if(source.points.some((v,i)=>pointKey(vadd(mv(transform.rotation,v),transform.translation))!==pointKey(mapped[i])))continue;
     const candidate=place(source.proto,transform.rotation,transform.translation);if(!sourceCompatible(base,face,candidate,source.face,this.mode))continue;
     list.set(candidate.id,{proto:source.proto,...transform});
    }
   }this.relative.set(cacheKey,[...list.values()]);
  }
  return this.relative.get(cacheKey).map(r=>place(r.proto,mm(owner.rotation,r.rotation),vadd(mv(owner.rotation,r.translation),owner.translation)));
 }
}
export function chooseObligation(frontier){
 const all=[...frontier.values()],compare=(a,b)=>a.generation-b.generation||a.candidates.size-b.candidates.size||a.key.localeCompare(b.key),dead=all.find(p=>!p.candidates.size);if(dead)return {point:dead,kind:'dead'};
 const forced=all.filter(p=>p.candidates.size===1).sort(compare);if(forced.length)return {point:forced[0],kind:'forced'};const point=all.sort(compare)[0];return point?{point,kind:'branch'}:null;
}
const hash=(s,seed)=>{let h=BigInt(seed)+2166136261n;for(const c of s)h=((h^BigInt(c.charCodeAt(0)))*16777619n)&0xffffffffn;return h;};
export class PolyhedralSearch{
 constructor(model,{seed=4,seedKind,target=30,budget=3000,maxCandidates=20000}={},progress=()=>{}){
  if(!Number.isSafeInteger(seed)||!Number.isSafeInteger(target)||target<2||!Number.isSafeInteger(budget)||budget<1)throw Error('Invalid search configuration');this.model=model;this.config={system:model.id,seed,seedKind,target,budget,maxCandidates};this.progress=progress;this.trail=[];this.frames=[];this.placed=new Map();this.frontier=new Map();this.owners=new Map();this.candidates=new Map();this.pointMarkings=new PointMarkingState({set:(m,k,v)=>this.set(m,k,v),add:(s,k)=>this.add(s,k)});this.state='ready';this.events=[];this.tree=[];this.lastEvent={type:'seed'};this.complete=true;
  this.stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0,eliminatedOverlap:0,eliminatedContact:0,eliminatedMarking:0,eliminatedRules:0,eliminatedLearned:0,checks:0,elapsedMs:0,maxTiles:1};
  const proto=model.prototypes.find(p=>p.kind===seedKind)||model.prototypes[0];if(!proto)throw Error('No concrete tiles in this model');this.seed=place(proto);this.placed.set(this.seed.id,{tile:this.seed,generation:0});this.pointMarkings.assign(this.seed);this.seed.faceKeys.forEach((key,i)=>this.owners.set(key,[{tile:this.seed,face:i,generation:0}]));
  try{this.sync();this.trail=[];}catch(error){if(error.kind!=='budget')throw error;this.stopBudget(error);}
 }
 set(m,k,v){const had=m.has(k),old=m.get(k);this.trail.push(()=>had?m.set(k,old):m.delete(k));m.set(k,v);}
 del(m,k){if(!m.has(k))return;const old=m.get(k);this.trail.push(()=>m.set(k,old));m.delete(k);}
 add(s,k){if(s.has(k))return;this.trail.push(()=>s.delete(k));s.add(k);}
 drop(s,k){if(!s.has(k))return;this.trail.push(()=>s.add(k));s.delete(k);}
 undo(n){while(this.trail.length>n)this.trail.pop()();}
 relation(a,b){
  this.stats.checks++;if(separated(a.bounds,b.bounds))return 'disjoint';const work={used:0,max:150000};if(exactIntersectionVolume(a,b,work).sign())return 'overlap';return fullFeatureContacts(a,b,work)?'contact':'partial-contact';
 }
 legal(tile){
  if(this.placed.has(tile.id)||!this.pointMarkings.compatible(tile))return false;
  for(const {tile:other}of this.placed.values()){if(separated(tile.bounds,other.bounds))continue;const relation=this.relation(tile,other);if(relation==='overlap'||relation==='partial-contact')return false;
   if(this.model.mode==='danzer')for(let i=0;i<tile.faces.length;i++){const j=other.faceKeys.indexOf(tile.faceKeys[i]);if(j>=0&&!sourceCompatible(tile,i,other,j,'danzer'))return false;}
  }return true;
 }
 ensure(tile){
  let r=this.candidates.get(tile.id);if(!r){if(this.candidates.size>=this.config.maxCandidates)throw new SearchLimit('Candidate memory budget reached; domains incomplete, result unknown');r={tile,legal:this.legal(tile),excluded:false};this.set(this.candidates,tile.id,r);this.pointMarkings.register(tile);}
  if(r.legal)for(const key of tile.faceKeys){const p=this.frontier.get(key);if(p)this.add(p.candidates,tile.id);}
 }
 sync(){
  for(const [key]of this.frontier)if(this.owners.get(key)?.length!==1)this.del(this.frontier,key);
  for(const [key,owners]of this.owners)if(owners.length===1&&!this.frontier.has(key)){const owner=owners[0],p={key,owner,generation:owner.generation,candidates:new Set()};this.set(this.frontier,key,p);for(const tile of this.model.attachments(owner.tile,owner.face))this.ensure(tile);this.progress({faces:this.frontier.size,candidates:this.candidates.size});}
 }
 invalidate(r,reason){if(!r.legal)return;this.trail.push(()=>r.legal=true);r.legal=false;for(const key of r.tile.faceKeys){const p=this.frontier.get(key);if(p)this.drop(p.candidates,r.tile.id);}if(reason==='failed-child'){const old=r.excluded;this.trail.push(()=>r.excluded=old);r.excluded=true;}else this.stats[reason==='overlap'?'eliminatedOverlap':reason==='marking'?'eliminatedMarking':reason==='rule'?'eliminatedRules':'eliminatedContact']++;}
 apply(tile){
  if(!this.legal(tile))throw Error('Illegal exact placement');const touched=tile.faceKeys.map(k=>this.frontier.get(k)).filter(Boolean);if(!touched.length)throw Error('Disconnected placement');const generation=1+Math.min(...touched.map(p=>p.generation));
  this.pointMarkings.assign(tile);this.set(this.placed,tile.id,{tile,generation});tile.faceKeys.forEach((key,face)=>this.set(this.owners,key,[...(this.owners.get(key)||[]),{tile,face,generation}]));
  for(const r of this.candidates.values())if(r.legal){
   if(r.tile.id===tile.id){this.invalidate(r,'overlap');continue;}
   if(!this.pointMarkings.compatible(r.tile)){this.invalidate(r,'marking');continue;}
   if(separated(r.tile.bounds,tile.bounds))continue;
   const relation=this.relation(r.tile,tile);if(relation==='overlap'||relation==='partial-contact'){this.invalidate(r,relation);continue;}
   if(this.model.mode==='danzer'&&r.tile.faceKeys.some((key,i)=>{const j=tile.faceKeys.indexOf(key);return j>=0&&!sourceCompatible(r.tile,i,tile,j,'danzer');}))this.invalidate(r,'rule');
  }
  this.sync();return generation;
 }
 stopBudget(error){this.complete=false;this.state='budget';this.lastEvent={type:'budget',reason:error.message};}
 step(){
  if(['checkpoint','budget','exhausted'].includes(this.state))return this.lastEvent;const started=performance.now(),before=this.trail.length;
  try{const choice=chooseObligation(this.frontier);
   if(choice?.kind==='dead'){const frame=this.frames.pop();if(!frame){this.state='exhausted';this.lastEvent={type:'exhausted',reason:'complete whole-facet search exhausted for the fixed root'};}else{this.undo(frame.before);this.invalidate(this.candidates.get(frame.id),'failed-child');this.stats.backtracks++;this.lastEvent={type:'remove',tile:frame.id,reason:'global dead facet'};}}
   else if(this.placed.size>=this.config.target){this.state='checkpoint';this.lastEvent={type:'checkpoint',reason:'consistent finite patch with viable whole-facet frontier'};}
   else if(this.stats.attempts>=this.config.budget){this.state='budget';this.lastEvent={type:'budget',reason:'placement attempt budget; extension unknown'};}
   else if(choice){const ids=[...choice.point.candidates].sort((a,b)=>{const x=hash(a,this.config.seed),y=hash(b,this.config.seed);return x<y?-1:x>y?1:a.localeCompare(b);}),id=ids[0];this.stats.attempts++;const generation=this.apply(this.candidates.get(id).tile);this.frames.push({id,before});this.stats.accepted++;this.stats[choice.kind==='forced'?'forced':'branches']++;this.stats.maxTiles=Math.max(this.stats.maxTiles,this.placed.size);this.state='running';this.lastEvent={type:'add',tile:id,generation,forced:choice.kind==='forced',domain:ids.length,face:choice.point.key};}
   else throw Error('Unbounded search has no active facet obligations');
  }catch(error){if(error.kind!=='budget')throw error;this.undo(before);this.stopBudget(error);}
  this.stats.elapsedMs+=performance.now()-started;this.events.push({...this.lastEvent,tiles:this.placed.size,depth:this.frames.length});return this.lastEvent;
 }
 summary(){const live=new Set();let incidences=0;for(const p of this.frontier.values())for(const id of p.candidates){live.add(id);incidences++;}return {state:this.state,tiles:this.placed.size,frontier:this.frontier.size,candidates:live.size,incidences,dead:this.complete?[...this.frontier.values()].filter(p=>!p.candidates.size).length:null,domainsComplete:this.complete,markingPoints:this.pointMarkings.pointCount,markingComponents:this.pointMarkings.componentCount,...this.stats};}
 inspect(){return {placed:[...this.placed.keys()].sort(),frontier:[...this.frontier].map(([k,p])=>[k,p.generation,[...p.candidates].sort()]).sort(),candidates:[...this.candidates].map(([k,r])=>[k,r.legal,r.excluded]).sort(),owners:[...this.owners].map(([k,v])=>[k,v.map(r=>[r.tile.id,r.generation])]).sort(),markings:this.pointMarkings.inspect()};}
 export(){return {format:'gcts-polyhedral-facet-search-v1',model:this.model.id,mode:this.model.mode,scope:this.model.scope,proxy:this.model.proxy,arithmetic:'exact BigInt Q(tau); decimal proxy input is explicitly distinguished',config:this.config,stats:this.summary(),result:this.state==='checkpoint'?'consistent finite whole-facet patch':this.state==='exhausted'?'fixed-root whole-facet search exhausted':'unknown',ruleCoverage:this.model.mode,tiles:[...this.placed.values()].map(r=>({kind:r.tile.kind,vertices:r.tile.vertices.map(p=>p.map(x=>x.toJSON())),faces:r.tile.faces,rotation:r.tile.rotation.map(p=>p.map(x=>x.toJSON())),translation:r.tile.translation.map(x=>x.toJSON()),generation:r.generation})),pointMarkingState:this.pointMarkings.inspect().values,events:this.events};}
}
