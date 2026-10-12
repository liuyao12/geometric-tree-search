import {embeddingKey,unitLoop} from './lattice-state.mjs';
import {rawFaceSweeps,moveContext,resolveSweep,VERSION,DEFAULT_DIRECTION,diagram} from './lattice-moves.mjs';
import {verifyLatticeCertificate} from './lattice-search.mjs';
import {LocalPointMarkings} from './local-point-markings.mjs';
import {lazyPointPath} from '../../apps/knot-movie/lazy-point-path.mjs';
const pk=p=>p.join(',');
export function latticeProvider(source,target,{maxEdges=200,direction=DEFAULT_DIRECTION,region=null,model=new LocalPointMarkings()}={}){
 if(model.system!=='unit-cubic-face-internal-vertex-capacity-v1')throw Error('Marking system does not match face grammar.');
 const sourceKey=embeddingKey(source),targetKey=embeddingKey(target),entries=new Map();let nextId=0;
 return{
  sourceKey,targetKey,entries,model,reversible:true,version:()=>model.version,
  domain(key){
   const p=JSON.parse(key),occupied=new Set(p.map(pk)),context=moveContext(p,{direction}),point=`choice:${key}`,boundary=new Map([['current',key]]);
   const candidates=rawFaceSweeps(p,{maxEdges,region}).map(sweep=>{
    const internal=sweep.replacement.slice(1,-1),contextId=JSON.stringify(sweep.face.map(pk).sort());
    for(const v of internal)boundary.set(`occupancy:${pk(v)}`,occupied.has(pk(v))?1:0);
    const id=nextId++,entry={id,key,sweep,internal,point,context,contextId,occupied};entries.set(id,entry);return entry;
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
   if(entry.internal.some(v=>entry.occupied.has(pk(v)))){entry.failure='vertex-capacity';return null;}
   const move=resolveSweep(entry.sweep,entry.context);if(!move)return null;entry.move=move;return{key:move.key};
  },
  observeRejected(entry){if(entry.failure==='vertex-capacity')model.observe(entry.internal.length,entry.contextId);}
 };
}
const inverseKind=k=>({'I+':'I−','I−':'I+','II+':'II−','II−':'II+','III':'III',routing:'routing'})[k];
export function solveLatticeLazy(source,target,{learn=true,model=null,probeNodeCap=64,maxDepth=4,nodeCap=20000,stateCap=200000,seed=31,maxEdges=200,direction=DEFAULT_DIRECTION,region=null}={}){
 const started=performance.now();unitLoop(source);unitLoop(target);
 if(unitLoop(source).length>maxEdges||unitLoop(target).length>maxEdges)return{status:'unknown',knotEquivalence:'unknown',reason:'endpoint-edge-budget'};
 try{diagram(source,direction);diagram(target,direction);}catch{return{status:'unknown',knotEquivalence:'unknown',reason:'projection-grammar-not-regular-or-outside-arithmetic-scope'};}
 const marks=model||new LocalPointMarkings({enabled:learn,probeNodeCap}),initial=marks.report(),initialVersion=marks.version,initialEventCount=marks.events.length;
 if(!learn&&model)throw Error('Unmarked baseline cannot import a marking model.');
 if(model)marks.validateTransfer();
 const provider=latticeProvider(source,target,{maxEdges,direction,region,model:marks});
 const result=lazyPointPath(provider,{maxDepth,nodeCap,stateCap,seed});let certificate=null,verificationMs=0;
 if(result.status==='equivalent'){
  const left=result.leftPath.map(id=>provider.entries.get(id).move);
  const right=[...result.rightPath].reverse().map(id=>{
   const entry=provider.entries.get(id),m=entry.move;
   return{...m,vertices:JSON.parse(entry.key),key:entry.key,kind:inverseKind(m.kind),old:m.replacement,replacement:m.old,beforeDiagram:m.afterDiagram,afterDiagram:m.beforeDiagram};
  });
  certificate={version:VERSION,source:JSON.parse(provider.sourceKey),target:JSON.parse(provider.targetKey),options:{depth:maxDepth,maxEdges,direction,region},steps:[...left,...right]};
  const check=performance.now();verifyLatticeCertificate(certificate);verificationMs=performance.now()-check;
 }
 return{...result,knotEquivalence:certificate?'equivalent':'unknown',certificate,learning:{...marks.report(),cold:initialVersion===0,initialVersion,initialAssignedValues:initial.assignedComponents,eventsThisRun:marks.events.slice(initialEventCount),probeNodesThisRun:marks.report().nodes-initial.nodes,probeMsThisRun:marks.report().probeMs-initial.probeMs,transferValidationNodesThisRun:marks.report().transferValidationNodes-initial.transferValidationNodes,transferValidationMsThisRun:marks.report().transferValidationMs-initial.transferValidationMs,transferredApplicationsThisRun:marks.report().transferredApplications-initial.transferredApplications},verificationMs,totalMs:performance.now()-started,scope:'Lazy bidirectional finite-path adaptation. Complete all-face domains, opaque keys, no patch restriction unless explicitly supplied. Local capacity markings preserve legal-edge reachability; future domains remain unknown until exhausted.'};
}
export function classifyLatticeLazy(input,references,{comparisonCap=references.length,learn=true,...options}={}){
 if(!Number.isInteger(comparisonCap)||comparisonCap<0)throw Error('Invalid comparison budget.');
 const vertices=unitLoop(Array.isArray(input)?input:input.vertices),attempts=[],model=learn?new LocalPointMarkings({probeNodeCap:options.probeNodeCap??64}):null;
 for(let i=0;i<Math.min(references.length,comparisonCap);i++){
  const reference=references[i],result=solveLatticeLazy(vertices,unitLoop(reference.vertices),{...options,learn,model});
  attempts.push({referenceIndex:i,status:result.status,knotEquivalence:result.knotEquivalence,stats:result.stats,totalMs:result.totalMs,initialMarkingVersion:result.learning?.initialVersion});
  if(result.certificate)return{status:'identified',referenceIndex:i,label:reference.id??null,certificate:result.certificate,attempts};
 }
 return{status:'unknown',reason:comparisonCap<references.length?'comparison-budget':'no-positive-certificate-within-bounds',attempts};
}
