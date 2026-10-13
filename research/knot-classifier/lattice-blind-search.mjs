import {createHash} from 'node:crypto';
import {unitLoop,embeddingKey} from './lattice-state.mjs';
import {latticeProvider} from './lattice-lazy-search.mjs';
import {depthPointSteps} from '../../apps/knot-movie/depth-point-path.mjs';
import {verifyLatticeCertificate} from './lattice-search.mjs';
import {LocalExtensionMarkings} from './local-extension-markings.mjs';
import {LocalPointMarkings} from './local-point-markings.mjs';
import {VERSION,DEFAULT_DIRECTION} from './lattice-moves.mjs';
export const proofId=signature=>createHash('sha256').update(signature).digest('hex');
const mismatch=(m,b)=>[...m].some(([p,v])=>b.has(p)&&b.get(p)!==v);
const snapshot=(model,initial,eventStart)=>{if(!model)return null;const r=model.report();delete r.events;return{...r,initialVersion:initial.version,eventsThisRun:model.events.slice(eventStart),probeMsThisRun:r.probeMs-initial.probeMs,activationValidationMsThisRun:(r.activationValidationMs||0)-(initial.activationValidationMs||0),transferValidationMsThisRun:r.transferValidationMs-initial.transferValidationMs};};
// Geometry authors the point domains. The fair driver uses reference indices,
// complete point compatibility, and resumable opaque search results only.
export function classifyLatticeBlind(input,references,{learn=true,maxDepth=16,maxEdges=240,maxMs=10000,nodeCap=5000,stateCap=100000,seed=31,direction=DEFAULT_DIRECTION,rootProbeNodeCap=64,extensionProbeNodeCap=512,model=null,extensionModel=null,rootModel=null,wholeWindowChildren=false,searchSeeds=null}={}){
 if(!Number.isInteger(maxDepth)||maxDepth<0||!Number.isInteger(nodeCap)||nodeCap<0||!Number.isInteger(stateCap)||stateCap<1||!(maxMs>=0))throw Error('Invalid blind classifier budgets.');
 if(!learn&&(model||extensionModel||rootModel))throw Error('Unmarked classifier cannot import marking models.');
 const orderSeeds=searchSeeds??[seed];if(!Array.isArray(orderSeeds)||!orderSeeds.length||orderSeeds.some(s=>!Number.isInteger(s)))throw Error('Invalid neutral search seeds.');
 const started=performance.now(),source=unitLoop(Array.isArray(input)?input:input.vertices),bank=references.map(r=>unitLoop(Array.isArray(r)?r:r.vertices));
 const marks=learn?(model||new LocalPointMarkings()):null,extensions=learn?(extensionModel||new LocalExtensionMarkings({probeNodeCap:extensionProbeNodeCap})):null;
 const roots=learn?(rootModel||new LocalExtensionMarkings({probeNodeCap:rootProbeNodeCap,maxComponentEdges:2*maxEdges,maxProbeHorizon:maxDepth})):null;
 for(const m of [roots,extensions])if(m&&Object.getPrototypeOf(m)!==LocalExtensionMarkings.prototype)throw Error('Blind markings must be native immutable proof catalogs.');
 const models=[marks,extensions,roots],initials=models.map(m=>m?.report()),eventStarts=models.map(m=>m?.events.length);
 let nodes=0,storedStates=0,certificate=null,candidateCertificate=null,referenceIndex=null,verificationMs=0,reason=null;
 const shouldStop=()=>performance.now()-started>=maxMs;
 const rootGraph={point:'reference-choice',boundary:[['root-budget',0]],complete:false,candidates:[]},contexts=[],retired=[];
 if(source.length>maxEdges||bank.some(r=>r.length>maxEdges))reason='endpoint-edge-budget';
 if(!reason&&roots)roots.validateTransfer({shouldStop});
 // Complete bank graph first. Root proofs describe whole discrepancy windows;
 // child extension proofs retain the existing local 48-edge support limit.
 if(!reason)for(let i=0;i<bank.length;i++){
  if(shouldStop()){reason='classification-budget-during-root-domain';break;}
  const c=roots?roots.compile(source,bank[i],maxDepth,{shouldStop}):{m:new Map(),lower:0,components:[]};
  const point='root-budget',m=new Map();if(c.lower>maxDepth)m.set(point,1);
  const candidate={id:i,t:[['reference-choice',1]],m:[...m],lower:c.lower,components:c.components.map(p=>({proofId:proofId(p.signature),origin:p.origin,lower:p.lower}))};rootGraph.candidates.push(candidate);
  // Skipped short horizons are proved failures of the root marking, not
  // guessed knot labels or an attempt to infer inequivalence.
  if(!mismatch(m,new Map(rootGraph.boundary)))contexts.push({referenceIndex:i,depth:c.lower,history:[],iterator:null,provider:null,current:null,nodesBefore:0,statesBefore:0});
  else retired.push({referenceIndex:i,status:'root-marking-excluded-within-horizon'});
 }
 if(rootGraph.candidates.length===bank.length&&!reason)rootGraph.complete=true;
 rootGraph.forward=rootGraph.complete?[[rootGraph.point,contexts.map(c=>c.referenceIndex)]]:[];
 rootGraph.reverse=rootGraph.complete?contexts.map(c=>[c.referenceIndex,[rootGraph.point]]):[];
 const referenceChecks=contexts.length;
 // Generic fair portfolio over neutral permutations. Every reference keeps its
 // one root candidate; independent resumable DFS contexts share exact author
 // caches and validated markings, with aggregate budgets across all work.
 const originals=[...contexts];contexts.length=0;for(const c of originals)for(const orderSeed of orderSeeds)contexts.push({...c,history:[],orderSeed});
 const diagramMoveCache=new Map(),authorDomainCache=new Map(),extensionContextCache=new Map();
 while(!reason&&!certificate&&contexts.length){
  for(let i=0;i<contexts.length;){
   if(shouldStop()){reason='classification-time-budget';break;}
   const c=contexts[i],stepStart=performance.now();
   if(!c.iterator){
    if(marks)marks.validateTransfer();if(extensions)extensions.validateTransfer({shouldStop});
    c.provider=latticeProvider(source,bank[c.referenceIndex],{maxEdges,direction,model:marks||new LocalPointMarkings({enabled:false}),extensionModel:extensions,globalExtensionModel:wholeWindowChildren?roots:null,shouldStop,diagramMoveCache,authorDomainCache,extensionContextCache});
    c.nodesBefore=0;c.statesBefore=0;c.iterator=depthPointSteps(c.provider,{maxDepth:c.depth,nodeCap,stateCap,seed:c.orderSeed,shouldStop,allowNode:n=>nodes-c.nodesBefore+n<nodeCap,allowState:n=>storedStates-c.statesBefore+n<stateCap});c.current={depth:c.depth,seed:c.orderSeed,status:'running',stats:{},activeMs:0};
   }
   const step=c.iterator.next(),r=step.value;c.current.activeMs+=performance.now()-stepStart;c.current.stats={...r.stats};
   nodes+=r.stats.nodes-c.nodesBefore;storedStates+=r.stats.generatedStates-c.statesBefore;c.nodesBefore=r.stats.nodes;c.statesBefore=r.stats.generatedStates;
   if(!step.done){i++;continue;}
   c.current.status=r.status;c.current.reason=r.reason;c.history.push(c.current);
   // Release this comparison's live states before its next finite horizon.
   storedStates-=c.statesBefore;c.iterator=null;c.current=null;
   if(r.status==='equivalent'){
    referenceIndex=c.referenceIndex;const left=r.path.map(id=>{const move=c.provider.entries.get(id).move;return{...move,vertices:JSON.parse(move.key)};});
    certificate={version:VERSION,source:JSON.parse(embeddingKey(source)),target:JSON.parse(embeddingKey(bank[referenceIndex])),options:{depth:c.depth,maxEdges,direction,region:null},steps:left};
    const v=performance.now(),valid=verifyLatticeCertificate(certificate,{shouldStop});verificationMs=performance.now()-v;
    if(!valid){candidateCertificate=certificate;certificate=null;referenceIndex=null;reason='certificate-verification-time-budget';}break;
   }
   if(r.status==='unknown'){reason=r.reason;break;}
   c.provider=null;c.depth++;
   if(c.depth>maxDepth){retired.push({referenceIndex:c.referenceIndex,status:'exhausted-finite-path-bounds',attempts:c.history});contexts.splice(i,1);}else i++;
  }
 }
 const comparisons=contexts.map(c=>({referenceIndex:c.referenceIndex,attempts:[...c.history,...(c.current?[c.current]:[])]}));
 const results=models.map((m,i)=>snapshot(m,initials[i],eventStarts[i]));
 return{status:certificate?'identified':'unknown',referenceIndex,certificate,candidateCertificate,reason:certificate?undefined:reason||'no-positive-certificate-within-bounds',nodes,verificationMs,totalMs:performance.now()-started,referenceChecks:rootGraph.candidates.length,referencesAdmitted:referenceChecks,rootGraph,comparisons,retired,learning:results[0],extensions:results[1],rootLearning:results[2],inventoryMemoization:{diagrams:diagramMoveCache.size,hits:diagramMoveCache.hits||0,misses:diagramMoveCache.misses||0,authorDomains:authorDomainCache.size,authorHits:authorDomainCache.hits||0,authorMisses:authorDomainCache.misses||0,extensionContexts:extensionContextCache.size,extensionHits:extensionContextCache.hits||0,extensionMisses:extensionContextCache.misses||0},wholeWindowChildren,searchSeeds:orderSeeds,scope:'Full-bank fair round-robin resumable depth-first path search. Aggregate query time/node/live-state budgets; independent finite horizons per reference. Complete root reference graph and complete move incidence before branching. Root windows are whole finite discrepancies; child learned supports remain local. Only vertices enter search. Finite failure remains knot unknown.'};
}
