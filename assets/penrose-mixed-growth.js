import {canonical,embedding,latticeKey} from './cyclotomic-five.js';
import {MIXED_TEMPLATES} from './penrose-mixed-templates.js';
import {exactlyPerpendicular} from './penrose-ammann.js?v=20260907-extent';
import {validateExtent} from './penrose-extensions.js?v=20260907-extent';
import {num,add,sub,mul,conj,areaSign,overlap,onSegment,same,box,separated} from './penrose-polygon.js';
import {tileStates,edgeKey,mixedMarkingsCompatible} from './penrose-mixed-markings.js';
export const TILE_KINDS=['thick','thin','kite','dart','p5','p3','p2','diamond','boat','star'];
const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
const hash=(s,seed)=>{let h=(2166136261^seed)>>>0;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h;};
let variants;
export function mixedVariants(){
  if(variants)return variants;
  const unique=new Map();
  for(const template of MIXED_TEMPLATES)for(const reflect of[false,true])for(const axis of axes)for(const sign of[1,-1]){
    const factor=mul(axis,num(sign)),transform=p=>mul(factor,reflect?conj(p):p);
    let exactPoints=template.exactPoints.map(transform),weights=template.weights.slice();
    if(areaSign(exactPoints)<0){exactPoints.reverse();weights.reverse();}
    const bars=template.bars.map(b=>{const from=transform(b.from),to=transform(b.to);return{from,to,family:axes.findIndex(a=>exactlyPerpendicular(sub(to,from),a))};});
    const id=template.kind+':'+exactPoints.map(latticeKey).sort().join('|')+'@'+bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
    unique.set(id,{kind:template.kind,presentation:template.presentation,exactPoints,weights,bars,variantId:id});
  }
  variants=[...unique.values()];return variants;
}
export function translateVariant(v,delta){
  const exactPoints=v.exactPoints.map(p=>add(p,delta)),vertices=exactPoints.map(latticeKey);
  const bars=v.bars.map(b=>({...b,from:add(b.from,delta),to:add(b.to,delta)}));
  const id=v.kind+':'+vertices.slice().sort().join('|')+'@'+bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
  return {kind:v.kind,presentation:v.presentation,exactPoints,vertices,weights:v.weights,bars,id};
}
export function mixedGeometryConflict(a,b){
  if(separated(box(a.exactPoints),box(b.exactPoints)))return false;
  if(overlap(a.exactPoints,b.exactPoints))return true;
  // Whole-edge placement excludes T-junctions and partial edge contacts.
  for(const[p,q]of[[a,b],[b,a]])for(const v of p.exactPoints)for(let k=0;k<q.exactPoints.length;k++){
    const x=q.exactPoints[k],y=q.exactPoints[(k+1)%q.exactPoints.length];
    if(!same(v,x)&&!same(v,y)&&onSegment(v,x,y))return true;
  }
  return false;
}
export function createMixedGrowth({tileKinds=TILE_KINDS,useMarkings=true,extent=2,targetCount=null,nodeLimit=100000,seed=17}={}){
  validateExtent(extent);
  if(!Array.isArray(tileKinds)||!tileKinds.length||tileKinds.some(k=>!TILE_KINDS.includes(k)))throw Error('Choose at least one tile');
  if(!Number.isSafeInteger(nodeLimit)||nodeLimit<1||nodeLimit>100000||!Number.isSafeInteger(seed)||(targetCount!==null&&(!Number.isSafeInteger(targetCount)||targetCount<1||targetCount>420)))throw Error('Invalid search settings');
  const allowed=new Set(tileKinds),pool=mixedVariants().filter(t=>allowed.has(t.kind)),edgeIndex=new Map();
  for(const v of pool)v.exactPoints.forEach((p,k)=>{const q=v.exactPoints[(k+1)%v.exactPoints.length],key=latticeKey(sub(q,p));if(!edgeIndex.has(key))edgeIndex.set(key,[]);edgeIndex.get(key).push({v,k});});
  const active=[],totals=new Map(),depths=new Map(),edges=new Map(),ids=new Set();
  const stats={proposals:0,capacityPrunes:0,geometryPrunes:0,topologyPrunes:0,markingPrunes:0,edgePrunes:0,edgeChecks:0,markingChecks:0,backtracks:0,peak:0};
  let status='ready',event=null,minimumFrontierGeneration=0,stopped=false;
  function corona(){let n=Infinity;for(const[v,t]of totals)if(t>0&&t<10)n=Math.min(n,...depths.get(v));minimumFrontierGeneration=Number.isFinite(n)?n:null;}
  function put(t){const generations=t.vertices.flatMap(v=>depths.get(v)||[]);t.generation=generations.length?Math.min(...generations)+1:0;active.push(t);ids.add(t.id);t.vertices.forEach((v,k)=>{totals.set(v,(totals.get(v)||0)+t.weights[k]);if(!depths.has(v))depths.set(v,[]);depths.get(v).push(t.generation);const key=edgeKey(t.exactPoints[k],t.exactPoints[(k+1)%t.vertices.length]);if(!edges.has(key))edges.set(key,[]);edges.get(key).push({tile:t,k,key});});corona();}
  function remove(t){active.pop();ids.delete(t.id);t.vertices.forEach((v,k)=>{const total=totals.get(v)-t.weights[k];if(total)totals.set(v,total);else totals.delete(v);depths.get(v).pop();if(!depths.get(v).length)depths.delete(v);const key=edgeKey(t.exactPoints[k],t.exactPoints[(k+1)%t.vertices.length]);edges.get(key).pop();if(!edges.get(key).length)edges.delete(key);});corona();}
  function singleBoundary(){const graph=new Map();for(const records of edges.values()){if(records.length>2)return false;if(records.length!==1)continue;const{tile:t,k}=records[0],a=t.vertices[k],b=t.vertices[(k+1)%t.vertices.length];for(const[x,y]of[[a,b],[b,a]]){if(!graph.has(x))graph.set(x,[]);graph.get(x).push(y);}}if(!graph.size||[...graph.values()].some(n=>n.length!==2))return false;const seen=new Set(),queue=[graph.keys().next().value];while(queue.length){const v=queue.pop();if(seen.has(v))continue;seen.add(v);queue.push(...graph.get(v));}return seen.size===graph.size;}
  function candidates(e){const a=e.tile.exactPoints[e.k],b=e.tile.exactPoints[(e.k+1)%e.tile.vertices.length];const unique=new Map();for(const{v,k}of edgeIndex.get(latticeKey(sub(a,b)))||[]){const t=translateVariant(v,sub(b,v.exactPoints[k]));if(!ids.has(t.id))unique.set(t.id,t);}return [...unique.values()].sort((a,b)=>hash(a.id,seed)-hash(b.id,seed)||a.id.localeCompare(b.id));}
  const depth=e=>Math.min(...depths.get(e.tile.vertices[e.k]),...depths.get(e.tile.vertices[(e.k+1)%e.tile.vertices.length]));
  const distance=e=>{const p=embedding(add(e.tile.exactPoints[e.k],e.tile.exactPoints[(e.k+1)%e.tile.vertices.length]));return p.x*p.x+p.y*p.y;};
  function edgeMatch(t){for(const[key,sig]of tileStates(t)[0].signatures){const records=edges.get(key);if(records&&records.some(r=>tileStates(r.tile)[0].signatures.get(key)!==sig))return false;}return true;}
  function* dfs(){
    if(targetCount!==null&&active.length>=targetCount){status='target reached';return true;}
    if(stats.proposals>=nodeLimit||active.length>=2000){status=active.length>=2000?'2000-tile safety limit reached':'search limit reached';stopped=true;return false;}
    const frontier=[...edges.values()].filter(r=>r.length===1).map(r=>r[0]).sort((a,b)=>depth(a)-depth(b)||distance(a)-distance(b)||a.key.localeCompare(b.key));
    if(!frontier.length)return false;
    for(const t of candidates(frontier[0])){
      if(stats.proposals>=nodeLimit){status='search limit reached';stopped=true;return false;}
      stats.proposals++;yield{type:'try',tile:t,message:`Try ${t.kind} on the frontier`};
      if(t.vertices.some((v,k)=>(totals.get(v)||0)+t.weights[k]>10)){stats.capacityPrunes++;yield{type:'reject',tile:t,message:'Corner capacity exceeds ten'};continue;}
      if(active.some(a=>mixedGeometryConflict(t,a))){stats.geometryPrunes++;yield{type:'reject',tile:t,message:'Exact polygon overlap'};continue;}
      stats[useMarkings?'markingChecks':'edgeChecks']++;
      if(useMarkings?!active.every(a=>mixedMarkingsCompatible(t,a,extent)):!edgeMatch(t)){stats[useMarkings?'markingPrunes':'edgePrunes']++;yield{type:'reject',tile:t,message:useMarkings?'Extended markings disagree':'Edge decorations disagree'};continue;}
      put(t);if(!singleBoundary()){remove(t);stats.topologyPrunes++;yield{type:'reject',tile:t,message:'Placement pinches the boundary or encloses a hole'};continue;}
      stats.peak=Math.max(stats.peak,active.length);yield{type:'add',tile:t,message:`Place ${t.kind}`};
      if(yield*dfs())return true;if(stopped)return false;
      remove(t);stats.backtracks++;yield{type:'remove',tile:t,message:'Backtrack from an exhausted frontier'};
    }
    return false;
  }
  function* run(){const kind=TILE_KINDS.find(k=>allowed.has(k)),v=pool.find(t=>t.kind===kind),t=translateVariant(v,sub(num(0),v.exactPoints[0]));put(t);stats.peak=1;status='searching';yield{type:'add',tile:t,message:`${kind} seed`};if(!(yield*dfs())&&!stopped)status='frontier exhausted';}
  const iterator=run();return{next(){const r=iterator.next();if(r.value)event=r.value;return r;},progress(){return{minimumFrontierGeneration};},snapshot(){return{tiles:active.slice(),orientations:active.map(t=>[t.id,0]),stats:{...stats},status,event,minimumFrontierGeneration,useMarkings,extent,markingDirections:5,tileKinds:[...allowed],mixed:true};}};
}
