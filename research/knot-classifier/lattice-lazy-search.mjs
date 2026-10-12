import {embeddingKey,unitLoop} from './lattice-state.mjs';
import {rawFaceSweeps,moveContext,resolveSweep,VERSION,DEFAULT_DIRECTION,diagram} from './lattice-moves.mjs';
import {verifyLatticeCertificate} from './lattice-search.mjs';
import {LocalExtensionMarkings} from './local-extension-markings.mjs';
import {LocalPointMarkings} from './local-point-markings.mjs';
import {lazyPointPath} from '../../apps/knot-movie/lazy-point-path.mjs';
const pk=p=>p.join(',');
export function latticeProvider(source,target,{maxEdges=200,direction=DEFAULT_DIRECTION,region=null,model=new LocalPointMarkings(),extensionModel=null,shouldStop=()=>false}={}){
 if(extensionModel&&Object.getPrototypeOf(extensionModel)!==LocalExtensionMarkings.prototype)throw Error('Extension models must be native immutable proof catalogs.');
 if(extensionModel&&extensionModel.system!=='face-edge-cover-extension-v1')throw Error('Extension system does not match face grammar.');
 if(model.system!=='unit-cubic-face-internal-vertex-capacity-v1')throw Error('Marking system does not match face grammar.');
 const sourceKey=embeddingKey(source),targetKey=embeddingKey(target),entries=new Map(),diagramMoveCache=new Map();let nextId=0;
 return{
  sourceKey,targetKey,entries,model,diagramMoveCache,reversible:true,version:()=>model.version,
  ...(extensionModel?{extensionDomain(accepted,{targetKey:goal,remaining}){
   const candidates=[];for(const edge of accepted){
    if(shouldStop())return{complete:false,reason:"search-time-budget"};
    const compiled=extensionModel.compile(JSON.parse(edge.destination),JSON.parse(goal),remaining,{shouldStop});
    candidates.push({id:edge.id,edge,t:new Map([[edge.raw.point,1]]),m:compiled.m});
   }
   // All candidate stencils are frozen before this complete incidence is built.
   // New prototypes cannot alter old contexts: every component in them was
   // already resolved or permanently left unresolved. No mutable prefix trail.
   return{complete:true,boundary:new Map([['extension-budget',0]]),candidates,version:extensionModel.version};
  }}:{}),
  domain(key){
   const p=JSON.parse(key),occupied=new Set(p.map(pk)),context=moveContext(p,{direction,diagramMoveCache}),point=`choice:${key}`,boundary=new Map([['current',key]]);
   const candidates=rawFaceSweeps(p,{maxEdges,region}).map(sweep=>{
    const internal=sweep.replacement.slice(1,-1),contextId=JSON.stringify(sweep.face.map(pk).sort());
    for(const v of internal)boundary.set(`occupancy:${pk(v)}`,occupied.has(pk(v))?1:0);
    const id=nextId++,entry={id,key,sweep,internal,point,context,contextId,occupied};return entry;
   });
   return{complete:true,point,boundary,candidates};
  },
  decorate(entry){
   const m=new Map([['current',entry.key]]),values=model.values(entry.internal.length,entry.contextId);
   entry.internal.forEach((v,i)=>{if(values[i]!==null)m.set(`occupancy:${pk(v)}`,values[i]);});
   if(entry.move)m.set('next',entry.move.key);
   return{id:entry.id,t:new Map([[entry.point,1]]),m};
  },
  resolve(entry){
   if(entry.move)return{key:entry.move.key};
   if(entry.internal.some(v=>entry.occupied.has(pk(v)))){entry.failure='vertex-capacity';return null;}
   const move=resolveSweep(entry.sweep,entry.context);if(!move)return null;entry.move={...move,vertices:undefined};entry.sweep=null;entry.context=null;entry.occupied=null;entries.set(entry.id,entry);return{key:move.key};
  },
  observeRejected(entry){if(entry.failure==='vertex-capacity')model.observe(entry.internal.length,entry.contextId);}
 };
}
const inverseKind=k=>({'I+':'I−','I−':'I+','II+':'II−','II−':'II+','III':'III',routing:'routing'})[k];
export function solveLatticeLazy(source,target,{learn=true,model=null,probeNodeCap=64,extensionLearn=false,extensionModel=null,extensionProbeNodeCap=10000,maxDepth=4,nodeCap=20000,stateCap=200000,seed=31,maxMs=Infinity,maxEdges=200,direction=DEFAULT_DIRECTION,region=null}={}){
 if(!(maxMs>=0))throw Error("Invalid time budget.");
 const started=performance.now(),shouldStop=()=>performance.now()-started>=maxMs;unitLoop(source);unitLoop(target);
 if(unitLoop(source).length>maxEdges||unitLoop(target).length>maxEdges)return{status:'unknown',knotEquivalence:'unknown',reason:'endpoint-edge-budget'};
 try{diagram(source,direction);diagram(target,direction);}catch{return{status:'unknown',knotEquivalence:'unknown',reason:'projection-grammar-not-regular-or-outside-arithmetic-scope'};}
 const marks=model||new LocalPointMarkings({enabled:learn,probeNodeCap}),initial=marks.report(),initialVersion=marks.version,initialEventCount=marks.events.length;
 if(!learn&&model)throw Error('Unmarked baseline cannot import a marking model.');
 if(model)marks.validateTransfer();
 if(!learn&&(extensionLearn||extensionModel))throw Error('Unmarked baseline cannot enable extension markings.');
 const extensions=extensionModel||(extensionLearn?new LocalExtensionMarkings({probeNodeCap:extensionProbeNodeCap}):null),extensionInitial=extensions?.report(),extensionInitialEventCount=extensions?.events.length;
 if(extensionModel)extensions.validateTransfer({shouldStop});
 const provider=latticeProvider(source,target,{maxEdges,direction,region,model:marks,extensionModel:extensions,shouldStop});
 const result=lazyPointPath(provider,{maxDepth,nodeCap,stateCap,seed,shouldStop});let certificate=null,verificationMs=0;
 if(result.status==='equivalent'){
  const left=result.leftPath.map(id=>{const move=provider.entries.get(id).move;return{...move,vertices:JSON.parse(move.key)};});
  const right=[...result.rightPath].reverse().map(id=>{
   const entry=provider.entries.get(id),m=entry.move;
   return{...m,vertices:JSON.parse(entry.key),key:entry.key,kind:inverseKind(m.kind),old:m.replacement,replacement:m.old,beforeDiagram:m.afterDiagram,afterDiagram:m.beforeDiagram};
  });
  certificate={version:VERSION,source:JSON.parse(provider.sourceKey),target:JSON.parse(provider.targetKey),options:{depth:maxDepth,maxEdges,direction,region},steps:[...left,...right]};
  const check=performance.now();verifyLatticeCertificate(certificate);verificationMs=performance.now()-check;
 }
 return{...result,inventoryMemoization:{scope:'Query-local exact canonical signed diagram; unchanged complete endpoint move map.',diagrams:provider.diagramMoveCache.size,hits:provider.diagramMoveCache.hits||0,misses:provider.diagramMoveCache.misses||0},knotEquivalence:certificate?'equivalent':'unknown',certificate,learning:{...marks.report(),cold:initialVersion===0,initialVersion,initialAssignedValues:initial.assignedComponents,eventsThisRun:marks.events.slice(initialEventCount),probeNodesThisRun:marks.report().nodes-initial.nodes,probeMsThisRun:marks.report().probeMs-initial.probeMs,transferValidationNodesThisRun:marks.report().transferValidationNodes-initial.transferValidationNodes,transferValidationMsThisRun:marks.report().transferValidationMs-initial.transferValidationMs,transferredApplicationsThisRun:marks.report().transferredApplications-initial.transferredApplications},extensions:extensions?{...extensions.report(),initialVersion:extensionInitial.version,activationValidationNodesThisRun:extensions.activationValidationNodes-extensionInitial.activationValidationNodes,activationValidationMsThisRun:extensions.activationValidationMs-extensionInitial.activationValidationMs,cachedTransferChecksThisRun:extensions.cachedTransferChecks-extensionInitial.cachedTransferChecks,eventsThisRun:extensions.events.slice(extensionInitialEventCount),probeNodesThisRun:extensions.nodes-extensionInitial.nodes,probeMsThisRun:extensions.probeMs-extensionInitial.probeMs,transferValidationNodesThisRun:extensions.transferValidationNodes-(extensionInitial.transferValidationNodes||0),transferValidationMsThisRun:extensions.transferValidationMs-(extensionInitial.transferValidationMs||0),transferredApplicationsThisRun:extensions.transferredApplications-extensionInitial.transferredApplications,cacheHitsThisRun:extensions.cacheHits-extensionInitial.cacheHits}:null,verificationMs,totalMs:performance.now()-started,scope:'Lazy bidirectional finite-path adaptation. Complete all-face domains, opaque keys, no patch restriction unless explicitly supplied. Capacity markings preserve all legal edges. Optional extension-budget markings preserve paths within the declared horizon, not unrestricted edges; future domains remain unknown until exhausted.'};
}
export function classifyLatticeLazy(input,references,{comparisonCap=references.length,learn=true,iterativeDepth=true,...options}={}){
 if(!Number.isInteger(comparisonCap)||comparisonCap<0)throw Error('Invalid comparison budget.');
 const vertices=unitLoop(Array.isArray(input)?input:input.vertices),attempts=[],model=learn?new LocalPointMarkings({probeNodeCap:options.probeNodeCap??64}):null,extensionModel=learn&&options.extensionLearn?new LocalExtensionMarkings({probeNodeCap:options.extensionProbeNodeCap??10000}):null;
 for(let i=0;i<Math.min(references.length,comparisonCap);i++){
  const reference=references[i],solver=iterativeDepth?solveLatticeIterative:solveLatticeLazy,result=solver(vertices,unitLoop(reference.vertices),{maxDepth:options.maxDepth??4,...options,learn,model,extensionModel});
  attempts.push({referenceIndex:i,status:result.status,knotEquivalence:result.knotEquivalence,stats:result.stats,totalMs:result.totalMs,initialMarkingVersion:result.learning?.initialVersion});
  if(result.certificate)return{status:'identified',referenceIndex:i,label:reference.id??null,certificate:result.certificate,attempts};
 }
 return{status:'unknown',reason:comparisonCap<references.length?'comparison-budget':'no-positive-certificate-within-bounds',attempts};
}
// Generic increasing finite-path bounds. Both lanes use the same schedule.
// Budgets cover the sum of all attempts, including repeated construction.
export function solveLatticeIterative(source,target,{maxDepth=10,maxMs=60000,nodeCap=5000,stateCap=200000,learn=true,model=null,extensionLearn=true,extensionModel=null,...options}={}){
 if(!Number.isInteger(maxDepth)||maxDepth<0||!Number.isInteger(nodeCap)||nodeCap<0||!Number.isInteger(stateCap)||stateCap<2||!(maxMs>=0))throw Error('Invalid iterative search bounds.');
 const started=performance.now(),marks=learn?(model||new LocalPointMarkings()):null;
 const extensions=learn&&extensionLearn?(extensionModel||new LocalExtensionMarkings({probeNodeCap:options.extensionProbeNodeCap??512})):null;
 const attempts=[],stats={},events=[],capacityEvents=[];let certificate=null,last=null;
 for(let depth=0;depth<=maxDepth;depth++){
  const remainingMs=maxMs-(performance.now()-started),remainingNodes=nodeCap-(stats.nodes||0);
  if(remainingMs<=0||remainingNodes<0)break;
  const run=solveLatticeLazy(source,target,{...options,maxDepth:depth,maxMs:remainingMs,nodeCap:remainingNodes,stateCap,learn,model:marks,extensionLearn:learn&&extensionLearn,extensionModel:extensions});
  if(run.extensions)events.push(...run.extensions.eventsThisRun);
  if(run.learning)capacityEvents.push(...run.learning.eventsThisRun);
  for(const [key,value]of Object.entries(run.stats||{}))stats[key]=(key.startsWith('peak')||key.endsWith('Versions'))?Math.max(stats[key]||0,value):(stats[key]||0)+value;
  attempts.push({depth,status:run.status,reason:run.reason,totalMs:run.totalMs,stats:run.stats,inventoryMemoization:run.inventoryMemoization,verificationMs:run.verificationMs,extensionProbeMs:run.extensions?.probeMsThisRun||0,activationValidationMs:run.extensions?.activationValidationMsThisRun||0,transferValidationMs:(run.extensions?.transferValidationMsThisRun||0)+(run.learning?.transferValidationMsThisRun||0),initialVersion:run.extensions?.initialVersion,version:run.extensions?.version});
  last=run;
  if(run.certificate){certificate=run.certificate;break;}
  if(run.status==='unknown')break; // A truncated horizon has not been exhausted.
 }
 const sum=key=>attempts.reduce((n,a)=>n+(a[key]||0),0);
 return{status:certificate?'equivalent':'unknown',knotEquivalence:certificate?'equivalent':'unknown',reason:certificate?undefined:last?.reason||(performance.now()-started>=maxMs?'search-time-budget':(stats.nodes||0)>=nodeCap?'search-node-budget':'no-positive-certificate-within-horizon'),certificate,stats,attempts,totalMs:performance.now()-started,verificationMs:sum('verificationMs'),extensions:extensions?{...extensions.report(),initialVersion:attempts[0]?.initialVersion??extensions.version,events:undefined,eventsThisRun:events,probeNodesThisRun:events.reduce((n,e)=>n+e.samples.reduce((m,s)=>m+s.nodes,0),0),probeMsThisRun:sum('extensionProbeMs'),activationValidationMsThisRun:sum('activationValidationMs'),transferValidationMsThisRun:attempts.reduce((n,a)=>n+(a.transferValidationMs||0),0)}:null,learning:marks?{...marks.report(),events:undefined,eventsThisRun:capacityEvents}:null,scope:'Increasing horizons from zero through the declared maximum; same opaque bidirectional BFS in both lanes. Aggregate time/node budgets, per-attempt live-state cap, complete all-face domains, no patch region. Finite exhaustion remains knot unknown. Proof catalogs reused only in memory.'};
}
