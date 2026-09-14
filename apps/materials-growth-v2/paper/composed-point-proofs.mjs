// Model-local proof-producing search: dead-point clauses, forced implications,
// and propositional resolution. No geometric transfer or material hypothesis.
import assert from 'node:assert/strict';
import {certifiedDeadPointClass} from './certified-dead-point.mjs';
const canonical=ids=>[...new Set(ids)].sort();
export function proofContext(model){
 const byid=new Map(model.candidates.map(c=>[c.id,c])),at=new Map();
 for(const c of model.candidates)for(const x of c.t){if(!at.has(x.point))at.set(x.point,[]);at.get(x.point).push(c);}
 return {model,byid,at};
}
export function checkComposedNode(context,nodes,node,limit=nodes.length){
 const {model,byid,at}=context;assert.deepEqual(node.ids,canonical(node.ids));
 assert(node.ids.every(id=>byid.has(id)));
 const previous=i=>{assert(Number.isInteger(i)&&i>=0&&i<limit);return nodes[i];};
 if(node.kind==='resolve'){
  const clause=previous(node.clause),imp=previous(node.implication);
  assert(clause.kind!=='force'&&imp.kind==='force'&&clause.ids.includes(imp.target));
  assert.deepEqual(node.ids,canonical([...clause.ids.filter(id=>id!==imp.target),...imp.ids]));return true;
 }
 assert(['dead','force'].includes(node.kind));assert(model.required.includes(node.point));
 const selected=new Set(node.ids),totals=new Map(),marks=new Map();
 for(const id of selected){const c=byid.get(id);
  for(const x of c.t)totals.set(x.point,(totals.get(x.point)||0)+x.value);
  for(const x of c.m||[]){const key=JSON.stringify([x.point,x.channel??'0']),v=marks.get(key)||[-Infinity,Infinity];
   v[0]=Math.max(v[0],x.lo);v[1]=Math.min(v[1],x.hi);assert(v[0]<=v[1]);marks.set(key,v);}
 }
 assert([...totals.values()].every(v=>v<=model.capacity));assert((totals.get(node.point)||0)<model.capacity);
 if(node.kind==='force')assert(!selected.has(node.target)&&at.get(node.point)?.some(c=>c.id===node.target));
 const uses=node.uses.map(i=>{const p=previous(i);assert(p.kind!=='force');return p;});
 for(const c of at.get(node.point)||[]){
  if(node.kind==='force'&&c.id===node.target)continue;
  if(selected.has(c.id)||c.t.some(x=>(totals.get(x.point)||0)+x.value>model.capacity))continue;
  if((c.m||[]).some(x=>{const v=marks.get(JSON.stringify([x.point,x.channel??'0']));return v&&(x.lo>v[1]||x.hi<v[0]);}))continue;
  assert(uses.some(p=>p.ids.includes(c.id)&&p.ids.every(id=>id===c.id||selected.has(id))),'Unexplained point candidate');
 }
 return true;
}
export function composedPointProofClass(Base){
 return class ComposedPointProofSearch extends certifiedDeadPointClass(Base){
  constructor(model){super(model);this.proofNodes=[];this.assignmentProof=new Map();this.context=proofContext(model);this.proofDiagnostics={forcedImplications:0,deadClauses:0,resolutions:0,learnedClauses:0,reusedRejections:0,backjumpSkippedFrames:0};}
  emit(node){checkComposedNode(this.context,this.proofNodes,node);const index=this.proofNodes.length;this.proofNodes.push(node);return index;}
  explainPoint(point,target=null){
   const core=new Set(),uses=new Set();
   for(const c of this.positiveCandidates.get(point)||[]){
    if(c.id===target)continue;
    if(this.placed.has(c.id)){core.add(c.id);continue;}
    const overflow=c.t.find(x=>this.points.get(x.point).total+x.value>this.capacity);
    if(overflow){let total=overflow.value;
     const contributors=[...this.placed.keys()].map(id=>[id,this.candidates.get(id).t.find(x=>x.point===overflow.point)?.value||0]).filter(([,v])=>v).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
     for(const [id,value] of contributors){core.add(id);total+=value;if(total>this.capacity)break;}assert(total>this.capacity);continue;
    }
    let blocker=null;
    for(const x of c.m)for(const y of this.points.get(x.point).marks.get(x.channel)||[])if(x.lo>y.hi||x.hi<y.lo)blocker=y.owner;
    if(blocker!==null){assert(this.placed.has(blocker));core.add(blocker);continue;}
    const cert=(this.cutIndex.get(c.id)||[]).find(p=>p.ids.every(id=>id===c.id||this.placed.has(id)));
    assert(cert,'Candidate lacks a certified blocker');uses.add(cert.proof);
    for(const id of cert.ids)if(id!==c.id)core.add(id);
   }
   return this.emit({kind:target===null?'dead':'force',point,ids:canonical(core),uses:[...uses].sort((a,b)=>a-b),...(target===null?{}:{target})});
  }
  registerClause(proof){
   const node=this.proofNodes[proof],key=JSON.stringify(node.ids);assert(node.kind!=='force');
   if(this.cutKeys.has(key))return;
   const cert={ids:node.ids,proof};this.cutKeys.add(key);this.certificates.push(cert);this.proofVersion++;this.proofDiagnostics.learnedClauses++;
   const points=new Set();
   for(const id of cert.ids){if(!this.cutIndex.has(id))this.cutIndex.set(id,[]);this.cutIndex.get(id).push(cert);
    const c=this.candidates.get(id);for(const x of [...c.t,...c.m])points.add(x.point);}
   for(const point of points)for(const id of cert.ids)this.dependencies.get(point).add(id);
   this.refresh(points);
  }
  advance(){
   if(this.status==='exhausted')return {kind:'exhausted'};
   const d=this.decision();
   if(d.kind==='complete'){this.status='consistent finite patch';return d;}
   assert(d.kind!=='unknown','Immutable complete finite model required');
   if(d.kind==='dead'){
    let proof=this.explainPoint(d.point);this.proofDiagnostics.deadClauses++;
    for(const id of [...this.placed.keys()].reverse())if(this.proofNodes[proof].ids.includes(id)&&this.assignmentProof.has(id)){
     const implication=this.assignmentProof.get(id),imp=this.proofNodes[implication];
     proof=this.emit({kind:'resolve',clause:proof,implication,ids:canonical([...this.proofNodes[proof].ids.filter(x=>x!==id),...imp.ids])});this.proofDiagnostics.resolutions++;
    }
    const core=new Set(this.proofNodes[proof].ids);assert([...core].every(id=>this.stack.some(f=>f.id===id)));
    this.registerClause(proof);
    if(!core.size){this.undo(0);this.stack=[];this.status='exhausted';return {kind:'exhausted',proof};}
    let index=this.stack.length-1;while(!core.has(this.stack[index].id))index--;
    const frame=this.stack[index],popped=this.stack.length-index;
    this.stack.length=index;this.undo(frame.checkpoint);this.stats.backtracks+=popped;this.proofDiagnostics.backjumpSkippedFrames+=popped-1;
    assert(this.reason(this.candidates.get(frame.id)));this.status='searching';return {kind:'proved-backtrack',id:frame.id,proof,frames:popped};
   }
   const id=d.ids[0];let implication=null;
   if(d.kind==='forced'){implication=this.explainPoint(d.point,id);this.proofDiagnostics.forcedImplications++;this.stats.forced++;}
   else {assert.equal(d.kind,'branch');this.stack.push({checkpoint:this.trail.length,id,point:d.point});this.stats.branches++;}
   this.stats.attempts++;this.apply(id);this.stats.accepted++;
   if(implication!==null){this.assignmentProof.set(id,implication);this.trail.push(Object.assign(()=>this.assignmentProof.delete(id),{points:[]}));}
   this.status='searching';return {...d,id};
  }
  clearCertificates(){super.clearCertificates();this.proofNodes=[];this.assignmentProof.clear();}
 };
}
