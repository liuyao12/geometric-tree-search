/** Exact finite marking support on the half-star module. Integer lifts are
 * BigInts; numeric indices and categorical labels never encode coordinates.
 * Proper rotations act by signed permutations of the six lift axes.
 */
import { ONE, vector, vadd, vscale, dot, determinant, inverseColumns, pointKey } from './golden-field.js';
import { STAR, ORIENTATIONS, makeRhombohedron } from './icosahedral-exact.js';
import { AMMANN_ORIENTATIONS, decorateGeometry, AMMANN_RULE_VERSION } from './icosahedral-ammann-markings.js?v=ammann-point-v2';
import { selectMask } from '../apps/3d-lattice-tiler/marking-mask.js';

export const LEARNING_VERSION='icosahedral-gcts-corona-v1';
export const liftKey=p=>p.join(',');
export const liftAdd=(a,b)=>a.map((x,i)=>x+b[i]);
export const liftSub=(a,b)=>a.map((x,i)=>x-b[i]);
export const liftZero=()=>Array(6).fill(0n);
export const orientationKey=t=>`${t.axes.join(',')}:${t.decoration.code}`;
const orientationLookup=new Map(AMMANN_ORIENTATIONS.map((t,i)=>[orientationKey(t),i]));
export const orientationIndex=t=>orientationLookup.get(orientationKey(t));
export const liftPoint=p=>p.reduce((sum,x,i)=>vadd(sum,vscale(STAR[i],x)),vector(0n,0n,0n));
export function pointLift(p){
 const [x,y,z]=p;const values=[z.b+y.a,z.b-y.a,y.b+x.a,y.b-x.a,x.b+z.a,x.b-z.a];
 if(p.some(s=>s.d!==1n)||values.some(n=>n%2n))throw Error('Placement is outside the integer star module');
 return values.map(n=>n/2n);
}
export const halfPoint=p=>vscale(liftPoint(p),ONE.div(2n));
const centerLift=t=>t.axes.reduce((p,i)=>{p[i]=1n;return p;},liftZero());
const maskLift=(t,mask)=>t.axes.reduce((p,axis,i)=>{p[axis]=(mask&(1<<i))?1n:0n;return p;},liftZero());

let group;
export function properRotations(){
 if(group)return group;
 const source=STAR.slice(0,3),inverse=inverseColumns(...source),found=new Map();
 for(let a=0;a<6;a++)for(let b=0;b<6;b++)for(let c=0;c<6;c++){
  if(new Set([a,b,c]).size!==3)continue;
  for(let signs=0;signs<8;signs++){
   const columns=[a,b,c].map((axis,i)=>vscale(STAR[axis],signs&(1<<i)?-1n:1n));
   if(determinant(...columns).sign()!==determinant(...source).sign())continue;
   if(!columns.every((v,i)=>columns.every((w,j)=>dot(v,w).equals(dot(source[i],source[j])))))continue;
   const physical=p=>inverse.reduce((sum,row,i)=>vadd(sum,vscale(columns[i],dot(row,p))),vector(0n,0n,0n));
   const axes=STAR.map(p=>{const q=pointKey(physical(p));for(let i=0;i<6;i++)for(const sign of [1n,-1n])if(pointKey(vscale(STAR[i],sign))===q)return {axis:i,sign};throw Error('Rotation does not preserve star');});
   const transform=p=>{const result=liftZero();p.forEach((x,i)=>{result[axes[i].axis]+=axes[i].sign*x;});return result;};
   const map=AMMANN_ORIENTATIONS.map(t=>{
    const shift=liftZero();t.axes.forEach(i=>{if(axes[i].sign<0n)shift[axes[i].axis]=-1n;});
    const targetAxes=t.axes.map(i=>axes[i].axis).sort((x,y)=>x-y),bare=ORIENTATIONS.find(o=>o.axes.join(',')===targetAxes.join(','));
    const mapped=t.vertices.map((_,mask)=>{const p=liftSub(transform(maskLift(t,mask)),shift);return targetAxes.reduce((m,i,j)=>m+(p[i]===1n?(1<<j):0),0);});
    const dots=t.faces.map((f,i)=>({face:f.map(j=>mapped[j]).sort((x,y)=>x-y).join(','),black:mapped[t.vertices.findIndex(v=>pointKey(v)===pointKey(t.faceDots[i].blackCorner))],red:mapped[t.vertices.findIndex(v=>pointKey(v)===pointKey(t.faceDots[i].redCorner))]}));
    const code=bare.faces.map(f=>{const d=dots.find(d=>d.face===[...f].sort((x,y)=>x-y).join(','));return `${d.black}${d.red}`;}).join('-');
    const oi=orientationLookup.get(`${targetAxes.join(',')}:${code}`);if(oi===undefined)throw Error('Rotation does not preserve decorated inventory');
    return {oi,shift};
   });
   if(new Set(map.map(m=>m.oi)).size!==120)throw Error('Rotation action is not bijective');
   found.set(axes.map(a=>`${a.axis}:${a.sign}`).join(','),{transform,map});
  }
 }
 group=[...found.values()];if(group.length!==60)throw Error('Expected the 60 exact proper icosahedral rotations');return group;
}
export const placementOf=t=>({oi:orientationIndex(t),translation:pointLift(t.origin)});
export function tileOf(p){const proto=AMMANN_ORIENTATIONS[p.oi];if(!proto)throw Error('Unknown decorated orientation');return decorateGeometry(makeRhombohedron(proto.axes,liftPoint(p.translation))).find(t=>t.decoration.code===proto.decoration.code);}
export const placementKey=p=>`${p.oi}@${liftKey(p.translation)}`;
export function transformPair(pair,g){
 const transformed=pair.map(p=>({oi:g.map[p.oi].oi,translation:liftAdd(g.transform(p.translation),g.map[p.oi].shift)}));
 const origin=transformed[0].translation;return transformed.map(p=>({...p,translation:liftSub(p.translation,origin)}));
}
export function pairKey(pair){
 const normalized=pair.map(p=>({...p,translation:liftSub(p.translation,pair[0].translation)}));return normalized.map(placementKey).join('|');
}
export function canonicalPair(pair,transforms=properRotations()){
 let best=null;for(const g of transforms)for(const p of [pair,[pair[1],pair[0]]]){const key=pairKey(transformPair(p,g));if(best===null||key<best)best=key;}return best;
}
export function haloOffsets(extent=2){
 if(!Number.isInteger(extent)||extent<1||extent>3)throw Error('Support extent must be 1, 2 or 3');
 const result=new Map([[liftKey(liftZero()),liftZero()]]);
 for(let n=0;n<extent;n++)for(const p of [...result.values()])for(let i=0;i<6;i++)for(const sign of [-1n,1n]){const q=[...p];q[i]+=sign;result.set(liftKey(q),q);}
 return [...result.values()];
}

/** Equality synthesis from positive overlaps; negatives supply alternative
 * unequal endpoint pairs. Unknowns supply no edges. Free masks are searched
 * in complete rotation orbits. No supplied dot values seed these variables.
 */
export const supportSlots=(oi,extent)=>haloOffsets(extent).map(offset=>({pos:liftAdd(centerLift(AMMANN_ORIENTATIONS[oi]),offset)}));
export class OnlineFields{
 constructor({extent=2}={}){
  this.extent=extent;this.transforms=properRotations();this.offsets=haloOffsets(extent);this.rows=[];this.counts={positive:0,negative:0,unresolved:0};this.revision=0;
  this.fields=AMMANN_ORIENTATIONS.map(t=>this.offsets.map(offset=>({pos:liftAdd(centerLift(t),offset)})));this.slots=this.fields.flat();this.slots.forEach((s,i)=>s.id=i);
  const lookup=new Map(this.slots.map(s=>[`${Math.floor(s.id/this.offsets.length)}:${liftKey(s.pos)}`,s.id]));
  this.actions=this.transforms.map(g=>this.fields.flatMap((f,oi)=>f.map(s=>lookup.get(`${g.map[oi].oi}:${liftKey(liftSub(g.transform(s.pos),g.map[oi].shift.map(x=>2n*x)))}`))));
  if(this.actions.some(a=>a.some(i=>i===undefined)))throw Error('Support not closed under rotations');
  const seen=new Set();this.orbits=[];for(let i=0;i<this.slots.length;i++)if(!seen.has(i)){const orbit=[...new Set(this.actions.map(a=>a[i]))];orbit.forEach(j=>seen.add(j));this.orbits.push(orbit);}
  this.edges=new Map();this.masks=[];this.snapshot=null;
 }
 contacts(pair){const first=new Map(this.fields[pair[0].oi].map(s=>[liftKey(liftAdd(s.pos,pair[0].translation.map(x=>2n*x))),s.id]));return this.fields[pair[1].oi].flatMap(s=>{const i=first.get(liftKey(liftAdd(s.pos,pair[1].translation.map(x=>2n*x))));return i===undefined?[]:[[i,s.id]];});}
 add(row){
  if(!Object.hasOwn(this.counts,row.status))throw Error('Unknown oracle label');this.rows.push(row);this.counts[row.status]++;
  const contacts=this.contacts(row.pair);
  if(row.status==='positive')for(const [i,j]of contacts)for(const action of this.actions){const a=action[i],b=action[j];if(a!==b)this.edges.set(`${Math.min(a,b)},${Math.max(a,b)}`,[a,b]);}
  return this.update();
 }
 update(maxEvaluations=48){
  const started=performance.now(),components=[],fields=this.fields.map(()=>[]),representation=this.transforms.map(()=>({}));let remaining=this.rows.filter(r=>r.status==='negative'),labelOffset=0;
  const parent=Int32Array.from({length:this.slots.length},(_,i)=>i),find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  for(const [i,j]of this.edges.values()){const a=find(i),b=find(j);if(a!==b)parent[Math.max(a,b)]=Math.min(a,b);}
  const witnesses=this.rows.filter(r=>r.status==='negative').map(r=>this.contacts(r.pair).filter(([i,j])=>find(i)!==find(j))).filter(w=>w.length),kept=new Set(this.slots.map(s=>s.id));
  if(this.counts.positive)for(const orbit of this.orbits){orbit.forEach(i=>kept.delete(i));if(witnesses.some(w=>!w.some(([i,j])=>kept.has(i)&&kept.has(j))))orbit.forEach(i=>kept.add(i));}
  const sparseMask=this.orbits.map(o=>kept.has(o[0]));
  for(let channel=0;channel<3;channel++){
   const negatives=remaining.map(row=>this.contacts(row.pair));
   const chosen=selectMask(this.slots.length,this.orbits,[...this.edges.values()],negatives,{initialMasks:[sparseMask,...this.masks],maxEvaluations,iterations:maxEvaluations,seed:this.rows.length+channel*65537});
   if(channel&&chosen.blocked===0)break;
   // With no negatives there is no reason to assign a provisional restriction.
   if(!this.counts.negative)chosen.active.fill(0);
   const codes=new Map(),values=this.slots.map((_,i)=>{if(!chosen.active[i])return null;const root=chosen.find(i);if(!codes.has(root))codes.set(root,labelOffset+codes.size);return codes.get(root);});
   this.fields.forEach((f,oi)=>f.forEach(s=>{if(values[s.id]!==null)fields[oi].push({pos:s.pos.map(String),channel,value:values[s.id]});}));
   this.actions.forEach((action,g)=>{const map={};for(let i=0;i<values.length;i++)if(values[i]!==null){const a=values[i],b=values[action[i]];if(b===null||(map[a]!==undefined&&map[a]!==b))throw Error('Non-equivariant learned values');map[a]=b;}if(new Set(Object.values(map)).size!==codes.size)throw Error('Noninvertible learned label action');Object.assign(representation[g],map);});
   components.push(chosen.mask);labelOffset+=codes.size;remaining=remaining.filter(row=>fieldsAgree(fields,row.pair));if(!remaining.length)break;
  }
  this.masks=components;const positivePassed=this.rows.filter(r=>r.status==='positive'&&fieldsAgree(fields,r.pair)).length;if(positivePassed!==this.counts.positive)throw Error('Learned field rejected a positive sample');
  this.snapshot={version:LEARNING_VERSION,ruleVersion:AMMANN_RULE_VERSION,extent:this.extent,revision:++this.revision,fields,representation,components:components.length,counts:{...this.counts},positivePassed,negativeBlocked:this.counts.negative-remaining.length,points:fields.reduce((n,f)=>n+new Set(f.map(m=>m.pos.join(','))).size,0),values:fields.reduce((n,f)=>n+f.length,0),supportSlots:this.slots.length,labelCount:labelOffset,updateMs:performance.now()-started};return this.snapshot;
 }
}
export function fieldsAgree(fields,pair){
 const section=new Map();for(const p of pair)for(const m of fields[p.oi]||[]){const key=`${liftKey(liftAdd(m.pos.map(BigInt),p.translation.map(x=>2n*x)))}:${m.channel}`;if(section.has(key)&&section.get(key)!==m.value)return false;section.set(key,m.value);}return true;
}
export function markingGate(snapshot,{complete=false,total=0}={}){return complete&&total>0&&Object.values(snapshot.counts).reduce((a,b)=>a+b,0)===total&&snapshot.counts.unresolved===0&&snapshot.counts.positive>0&&snapshot.positivePassed===snapshot.counts.positive&&(snapshot.counts.negative===0||snapshot.negativeBlocked*2>snapshot.counts.negative);}
export function verifyFieldAction(model){
 const transforms=properRotations();if(!Array.isArray(model.representation)||model.representation.length!==60)throw Error('Missing learned value action');
 const lookup=new Map(model.fields.flatMap((f,oi)=>f.map(m=>[`${oi}:${m.pos.join(',')}:${m.channel}`,m.value])));
 for(const [gi,g]of transforms.entries())for(const [oi,field]of model.fields.entries())for(const m of field){
  const target=g.map[oi],pos=liftSub(g.transform(m.pos.map(BigInt)),target.shift.map(x=>2n*x)),value=lookup.get(`${target.oi}:${liftKey(pos)}:${m.channel}`);
  if(value===undefined||model.representation[gi][m.value]!==value)throw Error('Saved learned field does not transform with its declared point group');
 }
 return true;
}
export class LearnedPointModel{
 constructor(model){
  if(model?.version!==LEARNING_VERSION||model.ruleVersion!==AMMANN_RULE_VERSION||!Array.isArray(model.fields)||model.fields.length!==120)throw Error('Learned marking belongs to a different exact system');
  const support=new Set(haloOffsets(model.extent).map(liftKey));
  this.model=model;this.tag=model.id||`${model.version}:${model.revision}`;this.cache=new WeakMap();this.fields=model.fields.map((field,oi)=>{const seen=new Set();return field.map(m=>{if(!Array.isArray(m.pos)||m.pos.length!==6||!m.pos.every(x=>typeof x==='string'&&/^-?\d+$/.test(x))||!Number.isSafeInteger(m.value)||m.value<0||!Number.isInteger(m.channel)||m.channel<0||m.channel>2)throw Error('Malformed learned point value');const pos=m.pos.map(BigInt),offset=liftSub(pos,centerLift(AMMANN_ORIENTATIONS[oi])),key=`${liftKey(pos)}:${m.channel}`;if(!support.has(liftKey(offset))||seen.has(key))throw Error('Invalid learned support');seen.add(key);return {...m,point:halfPoint(pos)};});});
 }
 decorate(tile){
  if(tile.learnedMarkingTag===this.tag)return tile;if(this.cache.has(tile))return this.cache.get(tile);const oi=orientationIndex(tile);if(oi===undefined)throw Error('Learned marking requires decorated inventory');
  const points=new Map();for(const m of this.fields[oi]){const point=vadd(m.point,tile.origin),key=pointKey(point);if(!points.has(key))points.set(key,{point,components:{},source:'learned'});points.get(key).components[`gcts:${m.channel}`]=m.value;}
  const learned=[...points.values()],result={...tile,pointMarkings:[...(tile.pointMarkings||[]),...learned],learnedMarkings:learned,learnedMarkingTag:this.tag};this.cache.set(tile,result);return result;
 }
}
