import {canonical,latticeKey} from './cyclotomic-five.js?v=20260908-speed';
import {num,add,sub,mul,conj,areaSign,overlap,onSegment,same,box,separated} from './penrose-polygon.js?v=20260908-speed';
// Input labels are optional directed edge labels from the problem definition.
// No marking patterns, bar positions, reference patch, or tile-name rules exist
// in this catalog generator or its geometry predicate.
export function coordinateOrder(a,b){a=canonical(a);b=canonical(b);for(let i=0;i<4;i++){const d=BigInt(a.coeff[i])*BigInt(b.denominator)-BigInt(b.coeff[i])*BigInt(a.denominator);if(d)return d<0n?-1:1;}return 0;}
const axisKey=p=>[latticeKey(p),latticeKey(mul(p,num(-1)))].sort()[0];
const labelValue=l=>l.ports?l.code+':'+[...new Set(l.ports.map(p=>latticeKey(p.point)+'@'+axisKey(p.axis)))].sort().join(';'):l.code+':'+latticeKey(l.from)+'>'+latticeKey(l.to);
const transformLabel=(l,point,vector)=>({...l,from:point(l.from),to:point(l.to),...(l.ports?{ports:l.ports.map(p=>({point:point(p.point),axis:vector(p.axis)}))}:{})});
export const tileSignature=(kind,points,weights,labels)=>kind+':'+points.map((p,i)=>latticeKey(p)+'~'+weights[i]).sort().join('|')+'@'+labels.map(l=>l.ports?[latticeKey(l.from),latticeKey(l.to)].sort().join('>')+'@'+labelValue(l):labelValue(l)).sort().join('|');
export function cyclotomicCatalog(templates,{reflections=true}={}){
 const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1})),unique=new Map();
 for(const template of templates)for(const reflect of(reflections?[false,true]:[false]))for(const axis of axes)for(const sign of[1,-1]){
  const factor=mul(axis,num(sign)),transform=p=>mul(factor,reflect?conj(p):p);
  let exactPoints=template.exactPoints.map(transform),weights=template.weights.slice();
  if(areaSign(exactPoints)<0){exactPoints.reverse();weights.reverse();}
  const origin=exactPoints.slice().sort(coordinateOrder)[0];
  exactPoints=exactPoints.map(p=>sub(p,origin));
  const labels=(template.labels||[]).map(l=>transformLabel(l,p=>sub(transform(p),origin),transform));
  const type=tileSignature(template.kind,exactPoints,weights,labels);
  unique.set(type,{kind:template.kind,type,exactPoints,weights,labels,sourceTransform:{factor,reflect,offset:origin}});
 }
 return [...unique.values()];
}
export function translateCatalogTile(v,origin){
 const exactPoints=v.exactPoints.map(p=>add(p,origin)),vertices=exactPoints.map(latticeKey);
 const physicalOrigin=add(origin,v.offset||num(0));
 const tile={...v,exactPoints,vertices,origin:physicalOrigin,id:v.type+'#'+latticeKey(physicalOrigin)};
 let labels,signatures;
 // Most enumerated placements are duplicates or fail capacity/geometry.
 // Construct boundary decorations only if an actual comparison needs them.
 Object.defineProperties(tile,{
  labels:{enumerable:true,get:()=>labels||(labels=v.labels.map(l=>transformLabel(l,p=>add(p,origin),p=>p)))},
  signatures:{enumerable:true,get:()=>signatures||(signatures=new Map(tile.labels.map(l=>[[latticeKey(l.from),latticeKey(l.to)].sort().join('|'),labelValue(l)])))}
 });
 return tile;
}
export function geometricPairAllowed(a,b){
 if(separated(box(a.exactPoints),box(b.exactPoints)))return true;
 if(overlap(a.exactPoints,b.exactPoints))return false;
 for(const[p,q]of[[a,b],[b,a]])for(const v of p.exactPoints)for(let i=0;i<q.exactPoints.length;i++){
  const x=q.exactPoints[i],y=q.exactPoints[(i+1)%q.exactPoints.length];if(!same(v,x)&&!same(v,y)&&onSegment(v,x,y))return false;
 }
 for(const[e,label]of a.signatures)if(b.signatures.has(e)&&b.signatures.get(e)!==label)return false;
 return true;
}
export function makeCyclotomicProblem(templates,{fullWeight,reflections=true}={}){
 if(!Number.isSafeInteger(fullWeight)||fullWeight<1||!templates.length)throw Error('A nonempty catalog and positive integer full weight are required');
 for(const t of templates)if(t.exactPoints.length<3||t.weights.length!==t.exactPoints.length||t.weights.some(w=>!Number.isSafeInteger(w)||w<=0||w>=fullWeight)||!areaSign(t.exactPoints))throw Error('Tiles require nonzero area and positive integer corner weights below the full weight');
 const catalog=cyclotomicCatalog(templates,{reflections}),anchored=new Map();
 for(const v of catalog)for(const p of v.exactPoints){const t=translateCatalogTile(v,sub(num(0),p));anchored.set(t.id,t);}
 // Normalize anchored placements as templates for translation at a frontier.
 const moves=[...anchored.values()].map(t=>({...t,offset:t.origin}));
 const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
 const actions=axes.flatMap(a=>[1,-1].flatMap(sign=>(reflections?[false,true]:[false]).map(reflect=>({factor:mul(a,num(sign)),reflect}))));
 const actionCache=new Map(),byType=new Map(catalog.map(v=>[v.type,v]));
 const typeNumbers=new Map(catalog.map((t,i)=>[t.type,i])),memoStats=[];
 // Predicates on fixed oriented tiles depend on relative placement only.
 // Bound each cache; do not retain tile objects or whole search branches.
 function memoizePairs(predicate,{limit=8192,footprint=t=>box(t.exactPoints)}={}){
  const values=new Map(),stats={hits:0,misses:0,entries:0,limit};memoStats.push(stats);
  return(a,b)=>{
   if(separated(footprint(a),footprint(b)))return true;
   let i=typeNumbers.get(a.type),j=typeNumbers.get(b.type);if(i===undefined||j===undefined)return predicate(a,b);
   let delta=sub(b.origin,a.origin);if(i>j){[i,j]=[j,i];delta={...delta,coeff:delta.coeff.map(n=>-n)};}
   let key=latticeKey(delta);if(i===j)key=[key,latticeKey({...delta,coeff:delta.coeff.map(n=>-n)})].sort()[0];key=i+'|'+j+'|'+key;
   if(values.has(key)){stats.hits++;return values.get(key);}stats.misses++;const value=predicate(a,b);
   if(values.size>=limit)values.delete(values.keys().next().value);values.set(key,value);stats.entries=values.size;return value;
  };
 }
 const pairAllowed=memoizePairs(geometricPairAllowed);

 function rigid(tile,g){
  const key=tile.type+'@'+JSON.stringify(g),act=p=>mul(g.factor,g.reflect?conj(p):p);let plan=actionCache.get(key);
  if(!plan){const v=byType.get(tile.type);let points=v.exactPoints.map(act),weights=v.weights.slice();if(areaSign(points)<0){points.reverse();weights.reverse();}
   const offset=points.slice().sort(coordinateOrder)[0];points=points.map(p=>sub(p,offset));
   const labels=v.labels.map(l=>transformLabel(l,p=>sub(act(p),offset),act));
   const type=tileSignature(v.kind,points,weights,labels),target=byType.get(type);if(!target)throw Error('Orientation catalog is not closed under requested action');
   plan={target,offset};actionCache.set(key,plan);
  }
  return translateCatalogTile(plan.target,add(act(tile.origin),plan.offset));
 }
 return{catalog,actions,rigid,resolve:(type,origin)=>{const v=byType.get(type);if(!v)throw Error('Unknown oriented tile in proof');return translateCatalogTile(v,origin);},translate:(t,d)=>translateCatalogTile(byType.get(t.type),add(t.origin,d)),fullWeight,seedTile:translateCatalogTile(catalog[0],num(0)),
  movesAt:p=>moves.map(t=>translateCatalogTile(t,p)),pairAllowed,memoizePairs,cacheStats:()=>memoStats.map(s=>({...s})),
  footprint:t=>box(t.exactPoints),pose:t=>t.type,anchor:t=>t.origin};
}
