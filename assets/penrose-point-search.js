import {finiteMarkingSupport,finiteMarkingBounds,finiteMarkingsCompatible} from './penrose-finite-markings.js';
import {embedding,latticeKey} from './cyclotomic-five.js';
import {num,sub,box,separated} from './penrose-polygon.js';
import {mixedVariants,translateVariant,mixedGeometryConflict,TILE_KINDS} from './penrose-mixed-growth.js?v=20260907-finite';
import {tileStates} from './penrose-mixed-markings.js?v=20260907-frontier';
import {arrowStates} from './penrose-arrows.js?v=20260907-extent';
import {validateExtent} from './penrose-extensions.js?v=20260907-extent';
import {createFrontierGraph} from './tiling-frontier-graph.js?v=20260907-finite';
const priority=(key,seed)=>{let h=(2166136261^seed)>>>0;for(const c of key)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h;};
export function createPenrosePointSearch({tileKinds=['thick','thin'],useMarkings=true,extent=0,targetCount=60,nodeLimit=10000,seed=1,markingDirections=5}={}) {
  validateExtent(extent);
  if(!Array.isArray(tileKinds)||!tileKinds.length||tileKinds.some(k=>!TILE_KINDS.includes(k)))throw Error('Choose at least one tile');
  if(markingDirections!==5)throw Error('Tiling requires all five Ammann directions');
  if(!Number.isSafeInteger(nodeLimit)||nodeLimit<1||nodeLimit>100000||!Number.isSafeInteger(seed)||(targetCount!==null&&(!Number.isSafeInteger(targetCount)||targetCount<1||targetCount>420)))throw Error('Invalid search settings');
  const allowed=new Set(tileKinds),classic=[...allowed].every(k=>k==='thick'||k==='thin');
  const pool=mixedVariants().filter(t=>allowed.has(t.kind)),anchored=new Map();
  for(const v of pool)for(const point of v.exactPoints){const t=translateVariant(v,sub(num(0),point));anchored.set(t.id,t);}
  const active=[],totals=new Map(),positions=new Map(),depths=new Map(),ids=new Set();
  const stats={proposals:0,capacityPrunes:0,geometryPrunes:0,topologyPrunes:0,markingPrunes:0,edgePrunes:0,edgeChecks:0,markingChecks:0,backtracks:0,peak:0,forcedMoves:0,branches:0,deadPoints:0};
  let status='ready',event=null,minimumFrontierGeneration=0,stopped=false;
  const bounds=new WeakMap(),edgeLabels=new WeakMap();
  function footprint(tile){
    if(!bounds.has(tile))bounds.set(tile,useMarkings?finiteMarkingBounds(tile,extent):box(tile.exactPoints));
    return bounds.get(tile);
  }
  function signatures(tile){
    if(!edgeLabels.has(tile))edgeLabels.set(tile,classic?arrowStates(tile).find(s=>s.start===tile.arrowStart).signatures:tileStates(tile)[0].signatures);
    return edgeLabels.get(tile);
  }
  function pair(a,b){
    if(separated(footprint(a),footprint(b)))return true;
    if(mixedGeometryConflict(a,b)){stats.geometryPrunes++;return false;}
    stats[useMarkings?'markingChecks':'edgeChecks']++;
    if(useMarkings){if(!finiteMarkingsCompatible(a,b,extent)){stats.markingPrunes++;return false;}}
    else for(const[e,s]of signatures(a))if(signatures(b).has(e)&&signatures(b).get(e)!==s){stats.edgePrunes++;return false;}
    return true;
  }
  function capacity(t){if(ids.has(t.id))return false;if(t.vertices.some((v,k)=>(totals.get(v)||0)+t.weights[k]>10)){stats.capacityPrunes++;return false;}return true;}
  const graph=createFrontierGraph({
    enumerate(point){return [...anchored.values()].map(v=>translateVariant(v,point.exact));},
    legal(t){return capacity(t)&&active.every(a=>pair(t,a));},
    compatibleWithAddition(t,added){return capacity(t)&&pair(t,added);}, footprint
  });
  function frontier(){const points=[];for(const[key,total]of totals)if(total>0&&total<10)points.push({key,total,exact:positions.get(key),depth:Math.min(...depths.get(key))});minimumFrontierGeneration=points.length?Math.min(...points.map(p=>p.depth)):null;return points;}
  function put(t){const near=t.vertices.flatMap(v=>depths.get(v)||[]);t.generation=near.length?Math.min(...near)+1:0;active.push(t);ids.add(t.id);t.vertices.forEach((v,k)=>{totals.set(v,(totals.get(v)||0)+t.weights[k]);positions.set(v,t.exactPoints[k]);if(!depths.has(v))depths.set(v,[]);depths.get(v).push(t.generation);});}
  function remove(t){active.pop();ids.delete(t.id);t.vertices.forEach((v,k)=>{const total=totals.get(v)-t.weights[k];if(total)totals.set(v,total);else{totals.delete(v);positions.delete(v);}depths.get(v).pop();if(!depths.get(v).length)depths.delete(v);});frontier();}
  const compare=(a,b)=>a.depth-b.depth||distance(a)-distance(b)||a.key.localeCompare(b.key);
  function distance(p){const e=embedding(p.exact);return e.x*e.x+e.y*e.y;}
  function* dfs(){
    const choice=graph.choose(compare);
    if(choice?.dead){stats.deadPoints++;yield{type:'dead',frontier:choice.point.key,message:'Dead point: no legal candidate'};return false;}
    if(targetCount!==null&&active.length>=targetCount){status='target reached';return true;}
    if(stats.proposals>=nodeLimit||active.length>=2000){status=active.length>=2000?'2000-tile safety limit reached':'budget reached';stopped=true;return false;}
    if(!choice)return false;
    const options=choice.candidates.sort((a,b)=>priority(a.id,seed)-priority(b.id,seed)||a.id.localeCompare(b.id));
    if(!choice.forced)stats.branches++;
    for(const candidate of options){
      const t={...candidate}; // Candidate nodes stay immutable; generation belongs to the placement.
      if(stats.proposals>=nodeLimit){status='budget reached';stopped=true;return false;}
      stats.proposals++;yield{type:'try',tile:t,forced:choice.forced,branchCount:options.length,frontier:choice.point.key,message:choice.forced?'Forced tile at a one-candidate point':`${options.length}-way branch at a minimum-degree point`};
      put(t);const delta=graph.push(t,frontier());stats.peak=Math.max(stats.peak,active.length);if(choice.forced)stats.forcedMoves++;
      yield{type:'add',tile:t,forced:choice.forced,branchCount:options.length,frontier:choice.point.key,message:choice.forced?`Forced ${t.kind}`:`Place ${t.kind}`};
      if(yield*dfs())return true;if(stopped)return false;
      remove(t);graph.pop(delta);stats.backtracks++;yield{type:'remove',tile:t,forced:choice.forced,message:'Restore points, candidates and incidences'};
    }
    return false;
  }
  function* run(){const kind=TILE_KINDS.find(k=>allowed.has(k)),v=pool.find(t=>t.kind===kind),t=translateVariant(v,sub(num(0),v.exactPoints[0]));put(t);graph.build(frontier());stats.peak=1;status='searching';yield{type:'add',tile:t,message:`${kind} seed · point–candidate graph ready`};if(!(yield*dfs())&&!stopped)status='frontier exhausted';}
  const iterator=run();return{
    next(){const r=iterator.next();if(r.value)event=r.value;return r;},
    progress(){return{minimumFrontierGeneration,deadPoints:graph.summary().deadPoints};},
    snapshot(){return{tiles:active.slice(),orientations:active.map(t=>[t.id,t.arrowStart ?? 0]),stats:{...stats},status,event,minimumFrontierGeneration,useMarkings,extent,markingDirections:5,tileKinds:[...allowed],mixed:!classic,graph:graph.summary()};},
    inspectGraph(){return graph.inspect();},
    candidateContacts(displayExtent=extent){
      validateExtent(displayExtent);
      const candidates=graph.candidateRecords().filter(({tile:t})=>!ids.has(t.id)&&!t.vertices.some((v,k)=>(totals.get(v)||0)+t.weights[k]>10)&&active.every(a=>!mixedGeometryConflict(t,a)));
      const points=new Map(),metadata=[];
      for(const {tile,legal}of candidates){const index=metadata.length;metadata.push({kind:tile.kind,legal});const q=finiteMarkingSupport(tile,displayExtent).points;
        active.forEach((a,placed)=>{for(const[key,p]of finiteMarkingSupport(a,displayExtent).points){const other=q.get(key);if(!other)continue;
          for(let family=0;family<5;family++){const value=other.value[family],placedValue=p.value[family];if(value===null||placedValue===null)continue;
            if(!points.has(key))points.set(key,{point:p.point,extension:p.extension,records:[]});
            points.get(key).records.push({candidate:index,placed,family,value,placedValue,weight:tile.weights[tile.vertices.indexOf(key)]||0,type:value===placedValue?'contact':'witness'});
          }
        }});
      }
      return {points:[...points.values()],candidates:metadata};
    },
    // Slow independent rebuild is exposed only for invariant tests.
    rebuildGraphForAudit(){const before={...stats};try{return frontier().map(p=>({key:p.key,depth:p.depth,total:p.total,candidates:[...anchored.values()].map(v=>translateVariant(v,p.exact)).filter(t=>!ids.has(t.id)&&!t.vertices.some((v,k)=>(totals.get(v)||0)+t.weights[k]>10)&&active.every(a=>pair(t,a))).map(t=>t.id).sort()})).sort((a,b)=>a.key.localeCompare(b.key));}finally{Object.assign(stats,before);}}
  };
}
