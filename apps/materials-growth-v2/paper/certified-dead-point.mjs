// Persistent, model-local nogoods certified by an unfilled required point with
// no physically legal candidate. No symmetry transfer or material hypothesis.
import assert from 'node:assert/strict';

export function checkDeadPointCertificate(model,certificate){
 const byid=new Map(model.candidates.map(c=>[c.id,c])),selected=new Set(certificate.ids);
 assert.equal(selected.size,certificate.ids.length);assert(model.required.includes(certificate.point));
 const totals=new Map(),marks=new Map();
 for(const id of selected){
  const c=byid.get(id);assert(c);
  for(const x of c.t)totals.set(x.point,(totals.get(x.point)||0)+x.value);
  for(const x of c.m||[]){const k=JSON.stringify([x.point,x.channel??'0']),v=marks.get(k)||[-Infinity,Infinity];
   v[0]=Math.max(v[0],x.lo);v[1]=Math.min(v[1],x.hi);assert(v[0]<=v[1]);marks.set(k,v);}
 }
 assert([...totals.values()].every(v=>v<=model.capacity));
 assert((totals.get(certificate.point)||0)<model.capacity);
 for(const c of model.candidates)if(c.t.some(x=>x.point===certificate.point)){
  if(selected.has(c.id)||c.t.some(x=>(totals.get(x.point)||0)+x.value>model.capacity))continue;
  assert((c.m||[]).some(x=>{const v=marks.get(JSON.stringify([x.point,x.channel??'0']));return v&&(x.lo>v[1]||x.hi<v[0]);}),'Unblocked candidate at certificate point');
 }
 return true;
}

export function certifiedDeadPointClass(Base){
 return class CertifiedDeadPointSearch extends Base{
  constructor(model){
   assert(!model.expand&&!model.constraint&&!model.initial?.length&&!model.fixedMarks?.length);
   assert(model.complete!==false&&model.required.every(p=>typeof p==='string'));
   const required=new Set(model.required);
   for(const c of model.candidates){
    assert(c.t.every(x=>required.has(x.point))&&!c.activate?.length);
    assert.equal(new Set((c.m||[]).map(x=>JSON.stringify([x.point,x.channel??'0']))).size,(c.m||[]).length);
   }
   super(model);this.proofModel=model;this.certificates=[];this.cutIndex=new Map();this.cutKeys=new Set();this.proofVersion=0;
   this.positiveCandidates=new Map();
   for(const c of this.candidates.values())for(const x of c.t){
    if(!this.positiveCandidates.has(x.point))this.positiveCandidates.set(x.point,[]);
    this.positiveCandidates.get(x.point).push(c);
   }
   this.proofDiagnostics={attempts:0,certified:0,reusedRejections:0,uncertifiedDeadEnds:0};
  }
  reason(c){
   const reason=super.reason(c);if(reason)return reason;
   for(const cert of this.cutIndex?.get(c.id)||[])if(cert.ids.every(id=>id===c.id||this.placed.has(id))){
    this.proofDiagnostics.reusedRejections++;return 'certified-dead-point';
   }
   return null;
  }
  addCandidate(c){assert(!this.proofModel,'Certified cuts require an immutable candidate pool');return super.addCandidate(c);}
  learnDeadPoint(point){
   this.proofDiagnostics.attempts++;const core=new Set();
   for(const c of this.positiveCandidates.get(point)||[]){
    if(this.placed.has(c.id)){core.add(c.id);continue;}
    const overflow=c.t.find(x=>this.points.get(x.point).total+x.value>this.capacity);
    if(overflow){
     let total=overflow.value;
     const contributors=[...this.placed.keys()].map(id=>[id,this.candidates.get(id).t.find(x=>x.point===overflow.point)?.value||0]).filter(([,v])=>v).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
     for(const [id,value] of contributors){core.add(id);total+=value;if(total>this.capacity)break;}
     assert(total>this.capacity);continue;
    }
    let blocker=null;
    for(const x of c.m)for(const y of this.points.get(x.point).marks.get(x.channel)||[])
     if(x.lo>y.hi||x.hi<y.lo)blocker=y.owner;
    if(blocker!==null){assert(this.placed.has(blocker));core.add(blocker);continue;}
    // A branch-local exclusion or another learned cut is not a direct
    // physical witness. Do not turn it into an unproved global certificate.
    this.proofDiagnostics.uncertifiedDeadEnds++;return false;
   }
   const cert={point,ids:[...core].sort()},key=JSON.stringify(cert.ids);
   if(this.cutKeys.has(key))return false;
   checkDeadPointCertificate(this.proofModel,cert);
   this.cutKeys.add(key);this.certificates.push(cert);this.proofDiagnostics.certified++;this.proofVersion++;
   const points=new Set();
   for(const id of cert.ids){
    if(!this.cutIndex.has(id))this.cutIndex.set(id,[]);this.cutIndex.get(id).push(cert);
    const c=this.candidates.get(id);for(const x of [...c.t,...c.m])points.add(x.point);
   }
   // A selected cut member changes legality of every other member, including
   // distant ones. Retain these persistent dependency edges across undo.
   for(const p of points)for(const id of cert.ids)this.dependencies.get(p).add(id);
   this.refresh(points);return true;
  }
  advance(){const d=this.decision();if(d.kind==='dead')this.learnDeadPoint(d.point);return super.advance();}
  clearCertificates(){
   assert(!this.placed.size&&!this.stack.length&&this.trail.length===0);
   this.certificates=[];this.cutIndex.clear();this.cutKeys.clear();this.proofVersion++;
   // Extra dependency edges are harmless; domain membership is rederived.
   this.refresh(new Set(this.points.keys()));
  }
 };
}
