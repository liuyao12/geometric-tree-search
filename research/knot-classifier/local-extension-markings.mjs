// Target-conditioned, translation-transferable finite cover extension proofs.
// This is a declared graph-path marking adaptation, not the pair-corona learner.
import {unitLoop} from './lattice-state.mjs';
const pk=p=>p.join(',');
const edge=(a,b)=>[a,b].sort((x,y)=>pk(x).localeCompare(pk(y)));
const ek=e=>e.map(pk).join('|');
export function edgeSet(input){const p=unitLoop(input);return new Map(p.map((a,i)=>{const e=edge(a,p[(i+1)%p.length]);return[ek(e),e];}));}
function incidentFaces(e){
 const [a,b]=e,axis=a.findIndex((x,i)=>x!==b[i]),out=[];
 for(let j=0;j<3;j++)if(j!==axis)for(const sign of [-1,1]){
  const c=b.map((x,i)=>x+(i===j?sign:0)),d=a.map((x,i)=>x+(i===j?sign:0)),v=[a,b,c,d];
  out.push(v.map((x,i)=>edge(x,v[(i+1)%4])));
 }
 return out;
}
// Every face touching the finite window is included, even across its boundary.
// Faces outside it project to a hold. No search moves are restricted to a patch.
export function projectedAlphabet(edges){
 const index=new Map(edges.map((e,i)=>[ek(e),i])),masks=new Set();
 for(const e of edges)for(const f of incidentFaces(e)){
  let mask=0n;for(const x of f){const i=index.get(ek(x));if(i!==undefined)mask|=1n<<BigInt(i);}if(mask)masks.add(mask.toString(16));
 }
 return [...masks].sort().map(m=>BigInt('0x'+m));
}
export function extensionComponents(source,target){
 const a=edgeSet(source),b=edgeSet(target),diff=new Map([...a,...b].filter(([k])=>a.has(k)!==b.has(k)));
 const faceSets=new Map();
 for(const e of diff.values())for(const f of incidentFaces(e)){
  const ids=f.map(ek).sort(),inside=ids.filter(k=>diff.has(k));faceSets.set(ids.join(';'),inside);
 }
 const links=new Map([...diff.keys()].map(k=>[k,new Set()]));
 for(const f of faceSets.values())for(const k of f)for(const j of f)links.get(k).add(j);
 const unseen=new Set(diff.keys()),components=[];
 while(unseen.size){
  const root=unseen.values().next().value,keys=[root];unseen.delete(root);
  for(let i=0;i<keys.length;i++)for(const k of links.get(keys[i]))if(unseen.delete(k))keys.push(k);
  const es=keys.map(k=>diff.get(k)),mins=[0,1,2].map(i=>Math.min(...es.flat().map(p=>p[i])));
  const normalized=es.map(e=>edge(...e.map(p=>p.map((x,i)=>x-mins[i])))).sort((x,y)=>ek(x).localeCompare(ek(y)));
  const normalizedKey=e=>ek(edge(...e.map(p=>p.map((x,i)=>x-mins[i]))));
  const index=new Map(normalized.map((e,i)=>[ek(e),i]));
  const masks=[...new Set([...faceSets.values()].filter(f=>f.includes(root)||f.some(k=>keys.includes(k))).map(f=>f.reduce((m,k)=>m|(1n<<BigInt(index.get(normalizedKey(diff.get(k))))),0n).toString(16)))].map(x=>BigInt('0x'+x));
  components.push({signature:JSON.stringify(normalized),edges:normalized,masks,origin:mins});
 }
 return components;
}
const count=x=>{let n=0;while(x){x&=x-1n;n++;}return n;};
// Generic unmarked finite cover probe: opaque bit points and exhaustive masks.
// Covering a discrepancy is necessary; double flips, exterior, and embedding
// restrictions are relaxed. A positive cover is NOT a knot-move witness.
export function coverProbe(width,masks,horizon,{nodeCap=10000,shouldStop=()=>false}={}){
 if(!Number.isInteger(width)||width<1||!Number.isInteger(horizon)||horizon<0||!Number.isInteger(nodeCap)||nodeCap<0)throw Error('Invalid extension probe.');
 const full=(1n<<BigInt(width))-1n;if(masks.some(m=>m<=0n||(m&full)!==m))throw Error('Invalid cover alphabet.');
 const memo=new Set();let nodes=0,unknown=false;
 function visit(uncovered,left,path){
  if(shouldStop()){unknown=true;return null;}
  if(!uncovered)return path;
  if(nodes>=nodeCap){unknown=true;return null;}nodes++;
  if(!left)return null;
  const cache=uncovered.toString(16)+':'+left;if(memo.has(cache))return null;
  const candidates=masks.map((m,id)=>({id,cover:m&uncovered})).filter(c=>c.cover);
  const forward=new Map(),reverse=new Map();
  for(let i=0;i<width;i++)if(uncovered&(1n<<BigInt(i)))forward.set(i,[]);
  for(const c of candidates){const support=[...forward.keys()].filter(i=>c.cover&(1n<<BigInt(i)));reverse.set(c.id,support);for(const i of support)forward.get(i).push(c.id);}
  if([...forward.values()].some(a=>!a.length)){memo.add(cache);return null;}
  const maximum=Math.max(...candidates.map(c=>count(c.cover)));
  if(Math.ceil(count(uncovered)/maximum)>left){memo.add(cache);return null;}
  // All obligations are generation zero: degree only breaks generation ties.
  const point=[...forward.keys()].sort((a,b)=>forward.get(a).length-forward.get(b).length||a-b)[0];
  for(const id of forward.get(point)){
   const r=visit(uncovered&~masks[id],left-1,[...path,id]);if(r)return r;if(unknown)return null;
  }
  memo.add(cache);return null;
 }
 const witness=visit(full,horizon,[]);
 return{outcome:witness?'positive':unknown?'unresolved':'negative',nodes,witness,complete:!unknown};
}
export class LocalExtensionMarkings{
 constructor({enabled=true,probeNodeCap=10000,maxComponentEdges=48}={}){
  this.system='face-edge-cover-extension-v1';this.enabled=enabled;this.probeNodeCap=probeNodeCap;this.maxComponentEdges=maxComponentEdges;this.rules=new Map();this.events=[];this.version=0;this.nodes=0;this.probeMs=0;this.transferredApplications=0;this.cacheHits=0;this.transferValidationNodes=0;this.transferValidationMs=0;
 }
 learn(component,{shouldStop=()=>false}={}){
  const old=this.rules.get(component.signature);
  if(old){this.cacheHits++;if(old.origin.join(',')!==component.origin.join(','))this.transferredApplications++;return old;}
  if(!this.enabled||component.edges.length>this.maxComponentEdges)return{lower:0};
  if(JSON.stringify(component.masks.map(m=>m.toString(16)).sort())!==JSON.stringify(projectedAlphabet(component.edges).map(m=>m.toString(16)).sort()))throw Error('Incomplete extension alphabet.');
  const start=performance.now(),samples=[];let lower=0;
  // Probe every smaller budget, then the first positive; unknowns never exclude.
  for(let h=0;h<=component.edges.length;h++){
   const sample={horizon:h,...coverProbe(component.edges.length,component.masks,h,{nodeCap:this.probeNodeCap,shouldStop})};samples.push(sample);this.nodes+=sample.nodes;
   if(sample.outcome==='unresolved')break;
   if(sample.outcome==='negative')lower=h+1;else break;
  }
  // Explicit point stencil: boundary is 0, proven failed budgets carry 1;
  // positive and unresolved budgets are absent. No learned model is imported.
  const values=samples.filter(s=>s.outcome==='negative').map(s=>[s.horizon,1]);
  const rule={signature:component.signature,origin:component.origin,lower,values,masks:component.masks.map(m=>m.toString(16)),samples};
  const elapsed=performance.now()-start;this.probeMs+=elapsed;
  this.events.push({...rule,width:component.edges.length,probeMs:elapsed,activated:values.length>0,validation:{positive:samples.filter(s=>s.outcome==='positive').length,negative:samples.filter(s=>s.outcome==='negative').length,unresolved:samples.filter(s=>s.outcome==='unresolved').length,allResolvedLabelsUsed:true}});
  this.rules.set(component.signature,rule);if(values.length)this.version++;
  return rule;
 }
 compile(source,target,remaining,{shouldStop=()=>false}={}){
  const components=extensionComponents(source,target),rules=components.map(c=>this.learn(c,{shouldStop})),lower=rules.reduce((n,r)=>n+r.lower,0);
  // Disconnected projected alphabets are independent: one real face affects at
  // most one component. Sum the proved requirements, then compile a budget seam.
  const point='extension-budget',boundary=new Map([[point,0]]),m=new Map();
  if(lower>remaining)m.set(point,1);
  return{boundary,m,lower,remaining,version:this.version,components:components.map((c,i)=>({signature:c.signature,origin:c.origin,lower:rules[i].lower}))};
 }
 validateTransfer({shouldStop=()=>false}={}){
  const start=performance.now(),events=new Map(this.events.map(e=>[e.signature,e]));
  const stopped=()=>{this.transferValidationMs+=performance.now()-start;return false;};
  for(const [signature,r]of this.rules){
   if(shouldStop())return stopped();
   const event=events.get(signature);if(!event)throw Error('Unproven extension import.');
   if(JSON.stringify(r.masks.slice().sort())!==JSON.stringify(projectedAlphabet(JSON.parse(signature)).map(m=>m.toString(16)).sort()))throw Error('Incomplete extension alphabet.');
   let lower=0;
   for(const sample of r.samples){
    if(sample.outcome==='unresolved')continue; // No exclusion was learned from this sample.
    if(shouldStop())return stopped();
    const replay=coverProbe(JSON.parse(signature).length,r.masks.map(m=>BigInt('0x'+m)),sample.horizon,{nodeCap:this.probeNodeCap,shouldStop});this.transferValidationNodes+=replay.nodes;
    if(shouldStop())return stopped();
    if(replay.outcome!==sample.outcome)throw Error('Extension transfer proof failed.');
    if(replay.outcome==='negative')lower=sample.horizon+1;
   }
   if(r.lower!==lower||JSON.stringify(r.values)!==JSON.stringify(r.samples.filter(s=>s.outcome==='negative').map(s=>[s.horizon,1])))throw Error('Extension stencil differs from proof.');
  }
  this.transferValidationMs+=performance.now()-start;return true;
 }
 report(){return{transferValidationNodes:this.transferValidationNodes,transferValidationMs:this.transferValidationMs,system:this.system,version:this.version,prototypes:this.rules.size,assignedComponents:[...this.rules.values()].reduce((n,r)=>n+r.values.length,0),nodes:this.nodes,probeMs:this.probeMs,transferredApplications:this.transferredApplications,cacheHits:this.cacheHits,events:this.events,scope:'Translation only; full incident-face alphabet; target discrepancy window, finite remaining budget. Negative relaxed cover proofs are redundant constraints. No projection, knot label, invariant, or scramble provenance enters probes. Not the reference neighboring-pair/corona learner.'};}
}
