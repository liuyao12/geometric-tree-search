/* Independent reader-to-checkpoint binding, including searched source provenance. */
'use strict';
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),DOC=path.join(ROOT,'docs/research/gcts-rl-renewal');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),gz=p=>JSON.parse(zlib.gunzipSync(fs.readFileSync(p))),clone=x=>JSON.parse(JSON.stringify(x));
const normalized=x=>Array.isArray(x)?x.map(normalized):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,normalized(x[k])])):x;
const same=(a,b)=>JSON.stringify(normalized(a))===JSON.stringify(normalized(b));
function need(ok,why){if(!ok)throw Error(why);}
function verify(d){
 need(d.version==='hilbert-promotion-family-001','correct reader');const prefix='hilbert_promotion_family_';
 for(const a of d.artifacts){const v=fs.readFileSync(path.join(DOC,a.path));need(v.length===a.bytes&&crypto.createHash('sha256').update(v).digest('hex')===a.sha256,'exact artifact '+a.path);}
 const plan=read(path.join(DOC,prefix+'plan.json')),progress=read(path.join(DOC,prefix+'progress.json')),catalog=gz(path.join(DOC,prefix+'catalog.json.gz')),native=gz(path.join(DOC,prefix+'native.json.gz'));
 need(same(d.plan,plan)&&same(d.progress,progress)&&same(d.catalog,catalog),'exact declared complete catalog/progress/plan');
 need(same(d.native,native.map(r=>Object.fromEntries(Object.entries(r).filter(([k])=>!['request','boundary_words'].includes(k))))),'every displayed native admission/certification outcome');
 const source=gz(path.join(DOC,prefix+'source_native.json.gz'))[0],audit=read(path.join(DOC,prefix+'source_audit.json')),ground=read(path.join(DOC,prefix+'source_ground.json'));
 need(same(d.source,{native:source,audit,ground})&&source.result.status==='accepted'&&audit.status==='passed'&&audit.native_outcome==='accepted'&&audit.request_sha256===source.request_sha256&&audit.source_native_query===56&&audit.source_request_sha256===ground.request_sha256&&ground.native_query===56&&ground.result.status==='accepted','actual independently replayed searched source');
 const names=ground.hypothesis_axioms,premises=names.map(n=>ground.request.theory.axioms[n]);const proof=ground.request.proof.map(c=>c.rule==='axiom'&&names.includes(c.name)?{rule:'assumption',index:names.indexOf(c.name),formula:c.formula}:c);
 const upper=source.request.blocks.at(-1);need(same(upper.premises,premises)&&same(upper.proof,proof)&&same(upper.conclusion,ground.request.target)&&same(source.request.blocks.slice(0,-1),ground.request.blocks)&&same(source.request.theory.axioms,{'I.2-uniqueness':ground.request.theory.axioms['I.2-uniqueness']}),'whole searched proof converted only to two local inputs, dependencies unchanged');
 need(same(plan.parameter_domains,{A:['P','Q'],B:['P','Q'],C:['P','Q','R'],u:['l','m'],v:['l','m']})&&catalog.binding_records.length===48&&catalog.promoted_definitions.length===48&&catalog.base_definitions.length===28,'complete declared domain and languages');
 const bindings=[];for(const A of ['P','Q'])for(const B of ['P','Q'])for(const C of ['P','Q','R'])for(const u of ['l','m'])for(const v of ['l','m'])bindings.push({A,B,C,u,v});need(same(catalog.binding_records.map(x=>x.binding),bindings),'all sorted bindings shown, no sample');
 const auditPath=path.join(DOC,prefix+'audit.json'),nativeAuditPath=path.join(DOC,prefix+'native_audit_progress.json');need(same(d.audit,fs.existsSync(auditPath)?read(auditPath):null)&&same(d.native_audit,fs.existsSync(nativeAuditPath)?read(nativeAuditPath):null),'exact independent audit evidence');
 const invPath=path.join(DOC,prefix+'inventories.json.gz'),compiledPath=path.join(DOC,prefix+'compiled.json.gz');need(same(d.inventories,fs.existsSync(invPath)?gz(invPath):null)&&same(d.compiled,fs.existsSync(compiledPath)?gz(compiledPath):null),'exact complete admitted inventories/guards');
 need(d.cases.length===plan.cases.length,'all recipients');let observations=0,rows=0,tiles=0;
 for(let i=0;i<d.cases.length;i++){
  const item=d.cases[i];need(same(item.spec,plan.cases[i]),'actual recipient');const summaries=progress.observations.filter(o=>o.case_id===item.spec.id);need(item.observations.length===summaries.length,'all recorded runs');
  for(let j=0;j<summaries.length;j++){
   const o=item.observations[j],s=summaries[j],raw=gz(path.join(DOC,prefix+s.tag.replaceAll('-','_')+'_final.json.gz')),checkpointFile=path.join(DOC,prefix+s.tag.replaceAll('-','_')+'.json.gz'),checkpoint=gz(checkpointFile),r=raw.search;observations++;
   need(same(o.summary,s)&&same(o.metrics,r.metrics)&&o.root_restored===r.root_restored&&o.pre_certification_checkpoint_sha256===raw.pre_certification_checkpoint_sha256,'measured run and complete rollback');need(crypto.createHash('sha256').update(fs.readFileSync(checkpointFile)).digest('hex')===raw.pre_certification_checkpoint_sha256&&same(checkpoint.search,r)&&same(checkpoint.model,raw.model),'whole tree saved before native certification');
   if(!r.proof){need(o.rows.length===0&&o.native===null&&raw.native_query===null,'no proof from unresolved search');continue;}
   const q=native[raw.native_query];need(same(o.native,{request:q.request,request_sha256:q.request_sha256,result:q.result,seconds:q.seconds})&&s.certification===q.result.status&&same(q.request.proof,r.proof)&&same(q.request.theory,item.spec.theory)&&same(q.request.target,item.spec.target),'actual whole target certificate and native outcome');
   need(o.rows.length===r.proof.length,'all proof rows');const placed=new Map(raw.model.placements.map(p=>[JSON.stringify(p.key),p]));
   for(let k=0;k<r.proof.length;k++){
    const row=o.rows[k];need(row.index===k+1&&same(row.command,r.proof[k]),'actual human formula row');const keys=r.placements.filter(key=>key[0]===k).sort((a,b)=>a[1]-b[1]);need(keys.length===4&&row.tiles.length===4,'all point roles');
    for(let n=0;n<4;n++){const t=row.tiles[n],p=placed.get(JSON.stringify(keys[n]));need(same(t.key,p.key)&&t.role===['C','G','I1','I2'][n]&&same(t.occupancy,p.occupancy)&&same(t.marks,p.marks)&&t.kind===p.kind&&t.source===p.source,'exact point placement');const words=p.marks.filter(([point])=>point[0]%4===2&&[0,1].includes(point[1])).map(([point,value])=>{const kind=point[1]===0?'formula':'command';return {point,value,kind,word:raw.model.catalog[kind][value].value};});need(same(t.words,words),'all displayed injective distant values');tiles++;}rows++;
   }
  }
 }
 if(progress.status==='complete')need(observations===64&&progress.base_admissions.length===28&&progress.promoted_admissions.length===48,'complete declared experiment');
 return {status:'passed',production_outcome:progress.status,full_audit:d.audit?.status||'pending',bindings:48,observations,rows,tiles};
}
const data=read(path.join(DOC,'hilbert_promotion_family_reader_001.json')),result=verify(data),tests=[['missing binding',d=>d.catalog.binding_records.pop()],['wrong domain',d=>d.plan.parameter_domains.A.pop()],['missing source dependency',d=>d.source.native.request.blocks.shift()],['authored replacement of source proof',d=>d.source.native.request.blocks.at(-1).proof.pop()],['wrong audit',d=>{d.native_audit.native_queries++;}],['wrong native outcome',d=>d.native[0].result.status='rejected'],['wrong file hash',d=>d.artifacts[0].sha256='0'.repeat(64)]];
const first=data.cases.flatMap((c,ci)=>c.observations.map((o,oi)=>({ci,oi,o}))).find(x=>x.o.rows.length);
if(first){const {ci,oi}=first;tests.push(['omit proof row',d=>d.cases[ci].observations[oi].rows.pop()],['wrong point marking',d=>d.cases[ci].observations[oi].rows[0].tiles[0].marks[0][1]++],['wrong occupancy',d=>d.cases[ci].observations[oi].rows[0].tiles[0].occupancy[0][1]=1],['wrong word ID',d=>d.cases[ci].observations[oi].rows[0].tiles[0].words[0].value++],['wrong checkpoint',d=>d.cases[ci].observations[oi].pre_certification_checkpoint_sha256='0'.repeat(64)]);}
const mutations=[];for(const [label,change] of tests){const d=clone(data);change(d);let rejected=false;try{verify(d);}catch{rejected=true;}need(rejected,'mutation escaped '+label);mutations.push(label);}console.log(JSON.stringify({...result,rejected_mutations:mutations.length,mutations},null,2));
