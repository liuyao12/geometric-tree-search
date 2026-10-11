/* Independent reader-to-raw binding and mutation checks; no UI automation. */
'use strict';
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),DOC=path.join(ROOT,'docs/research/gcts-rl-renewal');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),gz=p=>JSON.parse(zlib.gunzipSync(fs.readFileSync(p))),clone=x=>JSON.parse(JSON.stringify(x));
const normalize=x=>Array.isArray(x)?x.map(normalize):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,normalize(x[k])])):x;
const same=(a,b)=>JSON.stringify(normalize(a))===JSON.stringify(normalize(b));
function need(ok,text){if(!ok)throw Error(text);}
function term(t){return t[0]==='var'?t[1]:'\\mathrm{'+t[1]+'}';}
function formula(f){
 const k=f[0];if(k==='pred')return '\\operatorname{'+f[1]+'}\\!\\left('+f[2].map(term).join(',')+'\\right)';
 if(k==='eq')return term(f[1])+'='+term(f[2]);if(k==='not')return '\\neg\\left('+formula(f[1])+'\\right)';
 if(k==='all')return '\\forall '+f[1]+'\\, '+formula(f[2]);if(k==='bot')return '\\bot';
 return '\\left('+formula(f[1])+({imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k])+formula(f[2])+'\\right)';
}
function english(c,inventory){
 if(c.rule==='axiom')return 'Given: '+(c.name==='common-distinct-points'?'the nine conditions abbreviated by H.':c.name==='extra-incidence'?'C is incident with u.':'the universally quantified uniqueness axiom.');
 if(c.rule==='block'){const d=inventory.definitions.find(d=>d.name===c.name);return d.family==='universal-uniqueness'?'Apply the uniqueness axiom to the earlier common-point conditions.':'Use the earlier line equality to replace the line argument of the earlier incidence statement.';}
 return {refl:'Equality is reflexive.',tautology:'This formula is a propositional tautology.',mp:'Apply the earlier implication to its antecedent.',generalize:'Universally quantify the earlier formula.'}[c.rule]||c.rule;
}
function verify(data){
 need(data.version==='hilbert-receptors-001'&&data.audit.status==='passed'&&data.summary.status==='complete','finished audited pilot');
 const rawPlan=read(path.join(DOC,'hilbert_receptors_plan.json')),rawAudit=read(path.join(DOC,'hilbert_receptors_audit.json')),rawSummary=read(path.join(DOC,'hilbert_receptors_summary.json')),native=gz(path.join(DOC,'hilbert_receptors_native.json.gz'));
 need(same(data.plan,rawPlan)&&same(data.audit,rawAudit)&&same(data.summary,rawSummary),'exact audit, plan and summary');
 for(const artifact of data.artifacts){const file=fs.readFileSync(path.join(DOC,artifact.path));need(file.length===artifact.bytes&&crypto.createHash('sha256').update(file).digest('hex')===artifact.sha256,'artifact hash '+artifact.path);}
 need(data.cases.length===rawPlan.cases.length,'all cases');let rows=0,tiles=0,accepted=0,unknown=0,exhausted=0;
 for(const [key,file] of [['plan','closure_plan.json'],['result','closure_result.json'],['audit','closure_audit.json'],['heap','closure_heap_diagnosis.json'],['candidate','closure_input.json']])need(same(data.closure[key],read(path.join(DOC,'hilbert_receptors_'+file))),'exact closure diagnostic '+key);
 need(same(data.closure.native,gz(path.join(DOC,'hilbert_receptors_closure_native.json.gz')))&&data.closure.result.status==='unknown_space_budget'&&data.closure.audit.status==='passed'&&data.closure.audit.native_outcome==='unknown_space_budget','independently replayed unknown closure outcome');
 for(let i=0;i<data.cases.length;i++){
  const item=data.cases[i],raw=gz(path.join(DOC,'hilbert_receptors_'+item.spec.id.replaceAll('-','_')+'.json.gz'));
  need(same(item.spec,rawPlan.cases[i])&&same(item.spec,raw.case)&&same(item.compiled,raw.compiled)&&same(item.inventory,raw.inventory),'theory and complete admitted inventory');need(item.observations.length===raw.observations.length,'all runs');
  const hypothesis=item.spec.theory.axioms['common-distinct-points'];need(item.hypothesis_tex===formula(hypothesis)&&item.target_tex===formula(item.spec.target),'exact displayed hypotheses and goal');
  for(let j=0;j<item.observations.length;j++){
   const o=item.observations[j],actual=raw.observations[j],proof=actual.search.proof,selected=new Map(actual.model.placements.map(p=>[JSON.stringify(p.key),p]));
   need(o.lane===actual.lane&&o.repetition===actual.repetition&&o.status===actual.search.status&&same(o.metrics,actual.search.metrics)&&o.seconds===actual.search.seconds&&o.setup_seconds===actual.setup_seconds&&o.peak_rss_bytes===actual.peak_rss_bytes&&o.root_restored===actual.search.root_restored,'actual measured observation');
   need(o.native_query===actual.native_query&&o.cached_native_acceptance===actual.cached_native_acceptance,'actual native provenance');
   if(!proof){need(o.rows.length===0&&o.native===null&&o.native_query===null,'unresolved has no proof');if(o.status==='unknown_search_budget')unknown++;else if(o.status==='exhausted_finite_marked_region')exhausted++;else throw Error('wrong unfinished label');continue;}
   accepted++;need(o.rows.length===proof.length,'all proof rows');const q=native[o.native_query];need(q.result.status==='accepted'&&same(o.native,{request:q.request,request_sha256:q.request_sha256,result:q.result,seconds:q.seconds}),'whole actual native certificate');need(same(q.request.proof,proof)&&same(q.request.theory,item.spec.theory)&&same(q.request.target,item.spec.target),'native assertion and command sequence');
   for(let k=0;k<proof.length;k++){
    const row=o.rows[k];need(row.index===k+1&&same(row.command,proof[k])&&row.english===english(proof[k],raw.inventory)&&row.tex===(same(proof[k].formula,hypothesis)?'H':formula(proof[k].formula)),'formula-to-human row correspondence');
    const keys=actual.search.placements.filter(key=>key[0]===k).sort((a,b)=>a[1]-b[1]);need(row.tiles.length===4&&keys.length===4,'every C/G/I1/I2 role');
    for(let n=0;n<4;n++){
     const t=row.tiles[n],p=selected.get(JSON.stringify(keys[n]));need(same(t.key,p.key)&&t.role===['C','G','I1','I2'][n]&&same(t.occupancy,p.occupancy)&&same(t.marks,p.marks)&&t.kind===p.kind&&t.source===p.source,'every displayed exact point placement');
     const words=p.marks.filter(([point])=>point[0]%4===2&&(point[1]===0||point[1]===1)).map(([point,value])=>{const kind=point[1]===0?'formula':'command';return {point,value,kind,word:actual.model.catalog[kind][value].value};});need(same(t.words,words),'actual injective word catalog values');tiles++;
    }rows++;
   }
  }
 }
 need(data.audit.accepted_observations===accepted,'accepted observation audit count');return {status:'passed',cases:data.cases.length,observations:accepted+unknown+exhausted,accepted,unknown,exhausted,rows,tiles};
}
const data=read(path.join(DOC,'hilbert_receptors_reader_001.json')),result=verify(data),mutations=[];
const found=data.cases.flatMap((c,ci)=>c.observations.map((o,oi)=>({ci,oi,o}))).find(x=>x.o.rows.length);
need(found,'a checked proof exists');const {ci,oi}=found;
const tests=[['omit proof row',d=>d.cases[ci].observations[oi].rows.pop()],['wrong rule',d=>d.cases[ci].observations[oi].rows[0].command.rule='tautology'],['wrong scalar word value',d=>d.cases[ci].observations[oi].rows[0].tiles[0].words[0].value++],['wrong distant point value',d=>d.cases[ci].observations[oi].rows[0].tiles[0].marks[0][1]++],['wrong tile occupancy',d=>d.cases[ci].observations[oi].rows[0].tiles[0].occupancy[0][1]=1],['missing input role',d=>d.cases[ci].observations[oi].rows[0].tiles.pop()],['wrong native query',d=>d.cases[ci].observations[oi].native_query=0],['missing native definition',d=>d.cases[ci].observations[oi].native.request.blocks.pop()],['wrong theory',d=>d.cases[ci].spec.theory.axioms['I.2-uniqueness']=['bot']],['wrong audit',d=>d.audit.status='pending'],['wrong source hash',d=>d.artifacts[0].sha256='0'.repeat(64)],['wrong attempt count',d=>d.cases[ci].observations[oi].metrics.attempts++],['wrong human formula',d=>d.cases[ci].observations[oi].rows[0].tex='\\bot'],['wrong English translation',d=>d.cases[ci].observations[oi].rows[0].english='This proves all of Euclidean geometry.'],['unknown closure claimed accepted',d=>d.closure.result.status='accepted']];
for(const [name,mutate] of tests){const d=clone(data);mutate(d);let rejected=false;try{verify(d);}catch{rejected=true;}need(rejected,'mutation escaped: '+name);mutations.push(name);}
console.log(JSON.stringify({...result,rejected_mutations:mutations.length,mutations},null,2));
