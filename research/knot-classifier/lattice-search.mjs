import {embeddingKey,unitLoop} from './lattice-state.mjs';
import {latticeMoves,verifyStep,VERSION,DEFAULT_DIRECTION,diagram} from './lattice-moves.mjs';
import {onlinePointSearch} from '../../apps/knot-movie/point-search.mjs';
// Exact finite whole-lattice-state seam reduction. Every root slot has
// generation zero. Geometry lives solely in the complete tile generator.
export function latticeCatalog(source,target,{depth=3,stateCap=20000,maxEdges=200,region=null,direction=DEFAULT_DIRECTION}={}){
 if(!Number.isInteger(depth)||depth<1||depth>8||!Number.isInteger(stateCap)||stateCap<1||!Number.isInteger(maxEdges)||maxEdges<4)throw Error('Invalid catalog bounds.');
 if(region&&(!Array.isArray(region.min)||!Array.isArray(region.max)||region.min.length!==3||region.max.length!==3||region.min.some((x,k)=>!Number.isSafeInteger(x)||!Number.isSafeInteger(region.max[k])||x>region.max[k])))throw Error('Invalid fixed move-support region.');
 if(unitLoop(source).length>maxEdges||unitLoop(target).length>maxEdges)return{complete:false,reason:'endpoint-edge-budget'};
 const sourceKey=embeddingKey(source),targetKey=embeddingKey(target);
 try{diagram(source,direction);diagram(target,direction);}catch{return{complete:false,reason:'projection-grammar-not-regular-or-outside-arithmetic-scope'};}
 const states=[new Map([[sourceKey,JSON.parse(sourceKey)]])],tiles=[];
 let stateCount=1;const transitionCache=new Map();
 for(let time=0;time<depth;time++){
  states[time+1]=new Map();
  for(const [before,vertices]of states[time]){
   if(!transitionCache.has(before))transitionCache.set(before,latticeMoves(vertices,{maxEdges,region,direction}));
   const choices=[...transitionCache.get(before),{kind:'hold',key:before,vertices}];
   for(const move of choices){
    if(!states[time+1].has(move.key)){
     states[time+1].set(move.key,JSON.parse(move.key));if(++stateCount>stateCap)return{complete:false,reason:'catalog-state-budget',stateCount};
    }
    const id=tiles.length;tiles.push({id,time,before,after:move.key,move,t:new Map([[time,1]]),m:new Map([[`seam:${time}`,before],[`seam:${time+1}`,move.key]])});
   }
  }
 }
 return{complete:true,sourceKey,targetKey,depth,states,tiles,stateCount,options:{depth,stateCap,maxEdges,region,direction}};
}
export function verifyLatticeCertificate(certificate,{shouldStop=()=>false}={}){
 if(certificate.version!==VERSION)throw Error('Unsupported lattice movie version.');
 let p=unitLoop(certificate.source);
 if(p.length>certificate.options.maxEdges||(certificate.options.depth!==undefined&&certificate.steps.length>certificate.options.depth))throw Error('Certificate exceeds bounds.');
 const options={...certificate.options,diagramMoveCache:new Map()};
 for(const step of certificate.steps){if(shouldStop())return false;verifyStep(p,step,options);p=JSON.parse(embeddingKey(step.vertices));}
 if(shouldStop())return false;
 if(embeddingKey(p)!==embeddingKey(certificate.target))throw Error('Wrong lattice endpoint.');return true;
}
export function solveLattice(source,target,{learn=true,nodeCap=10000,proofNodeCap=10000,learningAttemptCap=64,seed=31,...bounds}={}){
 const start=performance.now(),cat=latticeCatalog(source,target,bounds),catalogMs=performance.now()-start;
 if(!cat.complete)return{status:'unknown',reason:cat.reason,knotEquivalence:'unknown',catalogMs,totalMs:performance.now()-start,stateCount:cat.stateCount};
 // Semantic fields, coordinates, projection and move kinds never reach search.
 const opaque={depth:cat.depth,sourceKey:cat.sourceKey,targetKey:cat.targetKey,tiles:cat.tiles.map(({id,t,m})=>({id,t,m}))};
 const began=performance.now(),result=onlinePointSearch(opaque,{learn,nodeCap,proofNodeCap,learningAttemptCap,seed});
 const searchMs=performance.now()-began;let certificate=null,verificationMs=0;
 if(result.status==='equivalent'){
  certificate={version:VERSION,source:JSON.parse(cat.sourceKey),target:JSON.parse(cat.targetKey),options:cat.options,steps:result.selected.map(id=>cat.tiles[id]).sort((a,b)=>a.time-b.time).filter(t=>t.move.kind!=='hold').map(t=>t.move)};
  const v=performance.now();verifyLatticeCertificate(certificate);verificationMs=performance.now()-v;
 }
 return{...result,knotEquivalence:certificate?'equivalent':'unknown',certificate,catalogMs,searchMs,verificationMs,totalMs:performance.now()-start,stateCount:cat.stateCount,tileCount:cat.tiles.length};
}
// Positive-certificate classifier. Reference labels are attached only AFTER
// a successful spatial replay; no label or invariant enters the point solver.
export function classifyLattice(input,references,{comparisonCap=references.length,...options}={}){
 if(!Number.isInteger(comparisonCap)||comparisonCap<1)throw Error('Invalid comparison budget.');
 const vertices=unitLoop(Array.isArray(input)?input:input.vertices),attempts=[];
 for(let i=0;i<Math.min(references.length,comparisonCap);i++){
  const reference=references[i],result=solveLattice(vertices,unitLoop(reference.vertices),options);
  attempts.push({referenceIndex:i,status:result.status,knotEquivalence:result.knotEquivalence,stats:result.stats,totalMs:result.totalMs});
  if(result.certificate)return{status:'identified',referenceIndex:i,label:reference.id??null,certificate:result.certificate,attempts};
 }
 return{status:'unknown',reason:comparisonCap<references.length?'comparison-budget':'no-positive-certificate-within-bounds',attempts};
}
