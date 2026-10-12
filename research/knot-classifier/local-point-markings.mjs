import {pointSearch} from '../../apps/knot-movie/point-search.mjs';
// Generic finite equality/mismatch synthesis, with * represented by null.
// These labels concern local capacity compatibility, never knot type.
export function synthesize(samples,width){
 if(samples.some(s=>!['positive','negative'].includes(s.outcome)||s.profile.length!==width||s.profile.some(v=>v!==0&&v!==1)))return null;
 let best=null;
 function visit(values){
  if(values.length<width){for(const v of [null,0,1])visit([...values,v]);return;}
  if(!samples.every(s=>s.outcome==='positive'?values.every((v,i)=>v===null||v===s.profile[i]):values.some((v,i)=>v!==null&&v!==s.profile[i])))return;
  if(!best||values.filter(v=>v!==null).length<best.filter(v=>v!==null).length)best=values;
 }
 visit([]);return best;
}
// Unmarked point-cover probe. The candidate occupies every new internal
// corner; the fixed exterior occupies exactly the profile's occupied corners.
// Fillers complete the one-root local cover; overcapacity proves failure.
export function localProbe(profile,{nodeCap=64}={}){
 const width=profile.length,depth=width+1,tiles=[{id:0,t:new Map([[0,1],...profile.map((_,i)=>[i+1,1])]),m:new Map()}];
 const fixed=[0];
 for(let i=0;i<width;i++){
  const id=tiles.length;tiles.push({id,t:new Map([[i+1,1]]),m:new Map()});if(profile[i])fixed.push(id);
 }
 const r=pointSearch({depth,sourceKey:'local',targetKey:'local',tiles},{initialSelected:fixed,nodeCap});
 return{outcome:r.status==='equivalent'?'positive':r.status==='exhausted-finite-search'?'negative':'unresolved',nodes:r.stats.nodes};
}
export class LocalPointMarkings{
 constructor({enabled=true,probeNodeCap=64}={}){this.system='unit-cubic-face-internal-vertex-capacity-v1';this.enabled=enabled;this.probeNodeCap=probeNodeCap;this.rules=new Map();this.version=0;this.events=[];this.transferredApplications=0;this.trainingContexts=new Set();this.testedWidths=new Set();this.transferValidationNodes=0;this.transferValidationMs=0;}
 observe(width,context){
  if(width!==0&&width!==1&&width!==2)throw Error('Rule width outside unit-face system.');
  if(!this.enabled||!width||this.testedWidths.has(width))return;
  this.testedWidths.add(width);
  const samples=[];const started=performance.now();
  for(let bits=0;bits<(1<<width);bits++){
   const profile=Array.from({length:width},(_,k)=>(bits>>k)&1),r=localProbe(profile,{nodeCap:this.probeNodeCap});samples.push({profile,...r});
  }
  const resolved=samples.every(s=>s.outcome!=='unresolved'),values=resolved?synthesize(samples,width):null;
  const event={width,context,samples,values,activated:values!==null,probeMs:performance.now()-started,validation:{positives:samples.filter(s=>s.outcome==='positive').length,negatives:samples.filter(s=>s.outcome==='negative').length,unresolved:samples.filter(s=>s.outcome==='unresolved').length,allResolvedProfilesReplayed:values!==null}};this.events.push(event);
  if(values!==null){this.rules.set(width,{values,context});this.trainingContexts.add(context);this.version++;}
 }
 validateTransfer(){
  const start=performance.now();let nodes=0;
  for(const [width,rule]of this.rules){
   if(!this.events.some(e=>e.width===width&&e.activated&&e.context===rule.context))throw Error('Unproven marking import.');
   for(let bits=0;bits<(1<<width);bits++){
    const profile=Array.from({length:width},(_,k)=>(bits>>k)&1),r=localProbe(profile);nodes+=r.nodes;
    const accepts=rule.values.every((v,i)=>v===null||v===profile[i]);
    if(r.outcome==='unresolved'||accepts!==(r.outcome==='positive'))throw Error('Marking transfer fails complete local profile replay.');
   }
  }
  this.transferValidationNodes+=nodes;this.transferValidationMs+=performance.now()-start;
 }
 values(width,context){const r=this.rules.get(width);if(r&&r.context!==context)this.transferredApplications++;return r?.values??Array(width).fill(null);}
 report(){return{transferValidationNodes:this.transferValidationNodes,transferValidationMs:this.transferValidationMs,system:this.system,enabled:this.enabled,applicationsIncludeReplays:true,cold:true,initialAssignedValues:0,version:this.version,events:this.events,transferredApplications:this.transferredApplications,scope:'Exact local vertex-capacity compatibility. All binary exterior profiles exhaustively probed; translations, signed coordinate permutations and traversal reversal preserve the point model. No target-dependent failure transfer.',assignedComponents:[...this.rules.values()].reduce((n,r)=>n+r.values.filter(v=>v!==null).length,0),nodes:this.events.reduce((n,e)=>n+e.samples.reduce((k,s)=>k+s.nodes,0),0),probeMs:this.events.reduce((n,e)=>n+e.probeMs,0)};}
}
