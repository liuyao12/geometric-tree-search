'use strict';
function coreOutput(v,triple){
 const A=v.inventory.symbols,Q=v.inventory.states;
 const decode=s=>{if(!Number.isInteger(s)||s<0||s>=A*(Q+1))throw Error('Bad symbol');return s<A?null:[Math.floor((s-A)/A),(s-A)%A];};
 const [a,b,c]=triple,h=triple.map(decode);
 if(h.filter(Boolean).length>1)throw Error('Multiple heads');
 const delta=x=>{const row=v.transition_rows[x[0]];if(!row)throw Error('Unbound table row');return row[x[1]];};
 if(h[1]){
  if(h[1][0]===v.inventory.accept)return b;
  const action=delta(h[1]);if(!action)throw Error('Undefined central action');
  return action[2]===0?A+A*action[0]+action[1]:action[1];
 }
 for(const [i,d] of [[0,1],[2,-1]])if(h[i]&&h[i][0]!==v.inventory.accept){const action=delta(h[i]);if(action&&action[2]===d)return A+A*action[0]+b;}
 return b;
}
function formula(a){
 const f=formula,k=a[0],name=s=>String(s).replace(/[^A-Za-z0-9]/g,'');
 if(k==='var')return name(a[1]);
 if(k==='bot')return '\\bot';
 if(k==='fun'){
  if(a[1]==='zero')return '0';if(a[1]==='succ')return 'S('+f(a[2][0])+')';if(!a[2].length)return a[1]==='l'?'\\ell':name(a[1]);
  if(a[1]==='add'||a[1]==='mul')return '('+f(a[2][0])+(a[1]==='add'?'+':'\\cdot ')+f(a[2][1])+')';
  return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 }
 if(k==='pred')return '\\operatorname{'+name(a[1])+'}'+(a[2].length?'('+a[2].map(f).join(',')+')':'');
 if(k==='eq')return f(a[1])+'='+f(a[2]);
 if(k==='all')return '\\forall '+name(a[1])+'\\;('+f(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+name(a[1][1])+'\\;('+f(a[1][2][1])+')';
 if(k==='not')return '\\neg('+f(a[1])+')';
 if(['imp','and','or'].includes(k))return '('+f(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+f(a[2])+')';
 throw Error('Unknown syntax');
}
const reason={axiom:'Use the named axiom from the input theory.',refl:'A term equals itself.',tautology:'This formula is a checked propositional tautology.',instantiate:'Instantiate a universal formula using capture-avoiding substitution.',mp:'Apply the earlier implication to its earlier antecedent.',generalize:'Universally quantify the variable; it is absent from every open premise.',eq_subst:'Substitute equal terms in the indicated formula.',distribute:'Move the quantifier across an implication with the variable condition checked.',induction:'Use the explicitly authorized natural-number induction schema.',assumption:'Use an input premise of this local block.',block:'Apply a previously checked lemma to the matching earlier premises.'};
const SAME=(a,b)=>eq(a,b);
function validateReceptors(v){
 if(v.version!=='native-inventory-reader-001'||v.audit.status!=='passed'||v.inventory.fingerprint!=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455'||v.inventory.symbols!==60||v.inventory.states!==462276)throw Error('Fixed palette/audit changed');
 if(v.cases.length!==7||v.donors.length!==3||v.observations.length!==70||v.proofs.length!==8)throw Error('Experiment coverage changed');
 for(const p of v.proofs){
  const c=[...v.cases,...v.donors].find(c=>c.id===p.case);if(!c||!SAME(c.target,p.request.target)||!SAME(c.theory,p.request.theory)||p.request.blocks.length||p.request.proof.length!==c.length||p.lines.length!==c.length)throw Error('Assertion/proof binding changed');
  if(p.builder.status!=='accepted'||p.literal.status!=='accepted'||p.checker.result!=='accepted'||p.builder.micro_steps!==p.literal.micro_steps||p.builder.micro_steps!==p.checker.micro_steps||p.builder.physical_steps!==p.literal.physical_steps||p.builder.physical_steps!==p.checker.physical_steps)throw Error('Full native acceptance changed');
  const tr=p.trace;if(tr.status!=='native_proof_discovered'||tr.case.id!==p.case||!SAME(tr.proof,p.request.proof)||!SAME(tr.records[tr.verification_query].request,p.request)||tr.records[tr.verification_query].result.status!=='accepted'||!tr.search.root_restored||tr.compiled.status!=='complete')throw Error('Point discovery binding changed');
  if(p.role==='frozen_evaluation'&&(tr.mode!=='learned'||!eq(tr.search.weights,v.policy.weights)))throw Error('Frozen evaluation policy changed');
  validatePointTrace(tr,v.policy.library);
  const final=tr.records[tr.verification_query];if((p.role==='frozen_evaluation'&&tr.verification_query!==tr.compiled.basis.length)||!['new_inventory_donor','frozen_evaluation_without_search_hints'].includes(final.purpose)||final.query_target!=='fixed_assertion'||final.result.start!==88986)throw Error('Marking-erased whole-check boundary changed');
  p.lines.forEach((l,j)=>{
   const cmd=p.request.proof[j];if(l.outcome!=='line-checked'||l.label.scope!=='root'||l.label.line!==j||l.label.rule!==cmd.rule||!SAME(l.label.formula,cmd.formula)||!SAME(l.input.pending,p.request.proof.slice(j))||!SAME(l.input.proved,p.request.proof.slice(0,j).map(c=>c.formula))||!SAME(l.output.proved,p.request.proof.slice(0,j+1).map(c=>c.formula))||!SAME(l.output.pending,p.request.proof.slice(j+1)))throw Error('Actual line context changed');
   for(const ctx of [l.input,l.output])if(!SAME(ctx.theory,p.request.theory)||!SAME(ctx.target,p.request.target)||ctx.assumptions.length||ctx.registry.length||ctx.forbidden.length)throw Error('Actual theory/scope changed');
   if(l.q!==1688||l.out!==1688||l.micro_steps<=0||l.physical_height<=0||l.literal_width<=0)throw Error('Fragment receptor changed');
   const patch=l.patch;if(patch.width!==9||patch.height!==3||patch.rows.length!==4||patch.tiles.length!==27||patch.trajectory[0][0]!==6746||patch.prefix_physical_steps!==l.input_head+patch.marker+1||patch.prefix_physical_steps+3>l.physical_height)throw Error('Native crop changed');
   const seen=new Set();for(const t of patch.tiles){const at=t.x+','+t.y;if(seen.has(at)||t.x<0||t.x>=9||t.y<0||t.y>=3)throw Error('Tile occupancy changed');seen.add(at);const triple=patch.rows[t.y].slice(t.x,t.x+3),n=coreOutput(v,triple);if(!SAME(t.triple,triple)||t.identity!==triple.join(':')||t.S!==triple[1]||t.N!==n||n!==patch.rows[t.y+1][t.x+1]||!SAME(t.W,triple.slice(0,2))||!SAME(t.E,triple.slice(1)))throw Error('Native point values changed');}
  });
 }
 const donorRecords=v.proofs.find(p=>p.role==='inventory_donor').trace.records;for(const p of v.proofs.filter(p=>p.role==='inventory_donor'))if(!eq(p.trace.records,donorRecords))throw Error('Shared training query transcript changed');
 validateTraining(v);
 return {proofs:v.proofs.length,lines:v.proofs.reduce((n,p)=>n+p.lines.length,0),tiles:v.proofs.reduce((n,p)=>n+p.lines.length*27,0),queries:v.audit.queries,observations:v.observations.length};
}
function stable(x){if(Array.isArray(x))return x.map(stable);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])]));return x;}
const packed=x=>JSON.stringify(stable(x)),eq=(a,b)=>packed(a)===packed(b),pointKey=p=>p.join(',');
function validatePointTrace(tr,library=[]){
 const m=tr.model,spec=tr.case,formulaPort=(j,a,ch='formula')=>[...new TextEncoder().encode(packed(a)),256].map((v,k)=>[[4*j+(ch==='command'?1:0),100+k],v]);
 const all=new Map(),basis=[],seen=new Set(),variables=new Set();
 const term=t=>{if(t[0]==='var')variables.add(t[1]);else t[2].forEach(term);};
 const visit=a=>{const k=packed(a);if(seen.has(k))return;seen.add(k);basis.push(a);if(a[0]==='all'){variables.add(a[1]);visit(a[2]);}else if(['imp','and','or'].includes(a[0])){visit(a[1]);visit(a[2]);}else if(a[0]==='not')visit(a[1]);else if(a[0]==='eq'){term(a[1]);term(a[2]);}else if(a[0]==='pred')a[2].forEach(term);};visit(spec.target);Object.values(spec.theory.axioms).forEach(visit);
 // The grammar uses bytewise ordering; locale collation is not that order.
 basis.sort((a,b)=>packed(a)<packed(b)?-1:packed(a)>packed(b)?1:0);
 if(!eq(basis,tr.compiled.basis)||!eq([...variables].sort(),tr.compiled.variables))throw Error('Syntactic basis changed');
 if(tr.compiled.queries.length!==basis.length||!eq(tr.compiled.tautologies,basis.filter((f,j)=>tr.records[tr.compiled.queries[j]].result.status==='accepted')))throw Error('Native guard catalog changed');
 basis.forEach((f,j)=>{const q=tr.compiled.queries[j],r=tr.records[q];if(r.id!==q||r.purpose!=='tautology_instance'||r.basis_index!==j||r.result.start!==88986||!['accepted','rejected'].includes(r.result.status)||!eq(r.request,{protocol:'gcts-fol-1',theory:spec.theory,blocks:[],proof:[{rule:'tautology',formula:f}],target:f}))throw Error('Guard query binding changed');});
 const domains=Array.from({length:spec.length},(_,j)=>{
  const rows=[];for(const f of j+1===spec.length?[spec.target]:basis){for(const name of Object.keys(spec.theory.axioms).sort())rows.push({rule:'axiom',formula:f,name});for(const variable of [...variables].sort())for(let source=0;source<j;source++)rows.push({rule:'generalize',formula:f,variable,source});for(let antecedent=0;antecedent<j;antecedent++)for(let implication=0;implication<j;implication++)rows.push({rule:'mp',formula:f,antecedent,implication});for(const rule of ['refl','tautology'])rows.push({rule,formula:f});}rows.sort((a,b)=>{for(const [u,v] of [[a.rule,b.rule],[packed(a.formula),packed(b.formula)],[packed(a),packed(b)]])if(u!==v)return u<v?-1:1;return 0;});return rows;
 });if(!eq(domains,m.domains)||!eq(domains.map(d=>d.length),m.command_counts)||m.complete_words!==domains.reduce((n,d)=>n*d.length,1))throw Error('Original command grammar changed');
 const taut=new Set(tr.compiled.tautologies.map(packed)),expected=[];
 function add(key,c,requirements){const j=key[0],role=key[1],marks=new Map(),entries=[...formulaPort(j,c,'command'),...formulaPort(j,c.formula),...requirements.flatMap(([i,a])=>formulaPort(i,a))];for(const [p,v] of entries){const k=pointKey(p);if(marks.has(k)&&marks.get(k)!==v)return;marks.set(k,v);}expected.push({key,occupancy:[[[4*j,role],12]],marks:[...marks].map(([p,v])=>[p.split(',').map(Number),v]).sort((a,b)=>a[0][0]-b[0][0]||a[0][1]-b[0][1]),slot:j,kind:role?'guard':'command',command:c,requirements});}
 domains.forEach((rows,j)=>rows.forEach((c,k)=>{add([j,0,k,0],c,[]);const f=c.formula,r=c.rule;if(r==='axiom'&&eq(spec.theory.axioms[c.name],f)||r==='refl'&&f[0]==='eq'&&eq(f[1],f[2])||r==='tautology'&&taut.has(packed(f)))add([j,1,k,0],c,[]);if(r==='generalize'&&f[0]==='all'&&f[1]===c.variable)add([j,1,k,0],c,[[c.source,f[2]]]);if(r==='mp')basis.forEach((a,n)=>{if(a[0]==='imp'&&eq(a[2],f))add([j,1,k,n],c,[[c.antecedent,a[1]],[c.implication,a]]);});}));
 const keyCompare=(a,b)=>{for(let i=0;i<4;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;};expected.sort((a,b)=>keyCompare(a.key,b.key));if(!eq(expected,m.placements))throw Error('Complete point inventory or distant marks changed');expected.forEach(c=>all.set(pointKey(c.key),c));
 const roots=Array.from({length:spec.length},(_,j)=>[[4*j,0],[4*j,1]]).flat();if(!eq(roots,m.roots))throw Error('Untouched root obligations changed');const marks=new Map(formulaPort(spec.length-1,spec.target).map(([p,v])=>[pointKey(p),v]));let nodes=0,accepted=null;
 const legal=(c,selected,values)=>!selected.has(pointKey(c.key))&&!selected.has('root:'+pointKey(c.occupancy[0][0]))&&c.marks.every(([p,v])=>!values.has(pointKey(p))||values.get(pointKey(p))===v);

 function walk(t,selected,values,path,hint=null){
  nodes++;const census=roots.filter(p=>!selected.has('root:'+pointKey(p))).map(p=>({point:p,generation:0,keys:expected.filter(c=>eq(c.occupancy[0][0],p)&&legal(c,selected,values)).map(c=>c.key)}));if(!eq(census,t.census))throw Error('Complete displayed graph changed');
  const dead=census.find(p=>!p.keys.length),forced=census.find(p=>p.keys.length===1),branch=[...census].sort((a,b)=>a.keys.length-b.keys.length||a.point[0]-b.point[0]||a.point[1]-b.point[1])[0],choice=dead||forced||branch,kind=dead?'dead':forced?'forced':choice?'branch':'empty';
  if(t.kind!==kind||!eq(t.point,choice?.point??null))throw Error('Scheduler changed');
  const guided=Array.isArray(tr.search.events);let preferred=[],active=hint;
  function review(h){
   if(!h)return {phase:'absent',pending:[],eligible:[]};
   const pending=h.item.members.filter(k=>!selected.has(pointKey(k)));if(!pending.length)return {phase:'completed',pending:[],eligible:[]};
   const illegal=pending.filter(k=>!legal(all.get(pointKey(k)),selected,values));if(illegal.length)return {phase:'invalid',pending,illegal,eligible:[]};
   const eligible=pending.filter(k=>choice?.keys.some(x=>eq(x,k)));return {phase:eligible.length?'eligible':'waiting',pending,eligible};
  }
  if(guided){
   if(t.hint_in!==(hint?.id??null))throw Error('Hint inherited incorrectly');const r=review(hint);if(!eq(r,t.review))throw Error('Hint review changed');
   if(['completed','invalid'].includes(r.phase))active=null;preferred=active?r.eligible:[];
  }
  if(kind==='dead'){if(t.children.length)throw Error('Dead child');return false;}
  if(kind==='empty'){accepted=path;if(t.children.length)throw Error('Extra finished child');return true;}
  if(guided&&Object.hasOwn(t,'policy_event')){
   if(kind!=='branch'||active)throw Error('Policy bypassed scheduler');
   const e=tr.search.events[t.policy_event];if(!e||e.id!==t.policy_event||!eq(e.point,t.point)||!eq(e.chosen,path)||!eq(e.weights,tr.search.weights))throw Error('Policy receptor changed');
   validateEvent(e,tr,all,selected,values,library);
   const item=e.items[e.index];
   if(item){const h=tr.search.hints[t.hint_start];if(!h||h.id!==t.hint_start||!eq(h.chosen,path)||!eq(h.point,t.point)||!eq(h.item,item))throw Error('Cluster expansion changed');active=h;const r=review(h);if(!eq(r,t.start_review)||r.phase!=='eligible')throw Error('New hint lacks receptor');preferred=r.eligible;}
   else if(Object.hasOwn(t,'hint_start'))throw Error('Deferred action started hint');
  }else if(guided&&kind==='branch'&&!active&&tr.mode!=='base')throw Error('Missing policy action');
  const alternatives=kind==='forced'?choice.keys:[...choice.keys.filter(k=>preferred.some(p=>eq(p,k))),...choice.keys.filter(k=>!preferred.some(p=>eq(p,k)))];
  if(guided&&!eq(t.alternatives,alternatives))throw Error('Complete original fallback changed');
  for(let i=0;i<t.children.length;i++){
   const child=t.children[i];if(!eq(child.key,alternatives[i]))throw Error('Original alternative removed');if(guided&&child.role!==(preferred.some(p=>eq(p,child.key))?'member':'base'))throw Error('Hint role changed');
   const c=all.get(pointKey(child.key)),ss=new Set(selected),vv=new Map(values);ss.add(pointKey(c.key));ss.add('root:'+pointKey(c.occupancy[0][0]));c.marks.forEach(([p,x])=>vv.set(pointKey(p),x));
   const ok=walk(child.tree,ss,vv,[...path,c.key],active);if(ok){if(i+1!==t.children.length)throw Error('Choices after acceptance');return true;}
  }
  if(t.children.length!==alternatives.length)throw Error('Incomplete successful tree');return false;
 }
 if(!walk(tr.search.tree,new Set(),marks,[])||!eq(accepted,tr.search.placements)||nodes!==tr.search.metrics.nodes)throw Error('Point solution changed');
 const decoded=accepted.filter(k=>k[1]===0).sort(keyCompare).map(k=>all.get(pointKey(k)).command);if(!eq(decoded,tr.proof))throw Error('Point-to-command decoding changed');
 return {nodes,placements:expected.length};
}

const FEATURES=['family','base_growth','internal_refs','already_justified_inputs','target_output','mark_extension','shape_density','completed_pairs','level','defer'];
const close=(a,b)=>Math.abs(a-b)<1e-11;
function validateEvent(e,tr,all,selected,values,library){
 const n=e.items.length;if(!n||e.items[0]!==null||e.features.length!==n||e.scores.length!==n||e.probabilities.length!==n||e.weights.length!==10)throw Error('Policy pool changed');
 const known=new Set(),guards=new Map(),commands=new Map();
 for(const c of all.values())if(selected.has(pointKey(c.key)))(c.kind==='guard'?guards:commands).set(c.slot,c);
 for(const [j,c] of [...guards].sort((a,b)=>a[0]-b[0]))if(commands.get(j)?.key[2]===c.key[2]&&c.requirements.every(([i])=>known.has(i)))known.add(j);
 e.items.forEach((item,z)=>{
  let phi=[0,0,0,0,0,0,0,0,0,1];
  if(item){
   if(!item.members.length||new Set(item.members.map(pointKey)).size!==item.members.length)throw Error('Duplicate constituent');
   const pending=item.members.filter(k=>!selected.has(pointKey(k))),totals=new Set(),marks=new Map();
   pending.forEach(k=>{const c=all.get(pointKey(k));if(!c)throw Error('Invented cluster tile');const p=pointKey(c.occupancy[0][0]);if(totals.has(p)||selected.has('root:'+p))throw Error('Invalid cluster capacity');totals.add(p);c.marks.forEach(([p,v])=>{const k=pointKey(p);if(marks.has(k)&&marks.get(k)!==v||values.has(k)&&values.get(k)!==v)throw Error('Invalid aggregate markings');marks.set(k,v);});});
   const fresh=[...marks].filter(([p])=>!values.has(p)).length;
   if(!eq(pending,item.pending)||item.new_occupancy!==12*pending.length||item.new_marks!==fresh||!pending.some(k=>all.get(pointKey(k)).occupancy.some(([p])=>eq(p,e.point))))throw Error('Ground aggregate changed');
   const slots=new Set(item.members.map(k=>k[0])),gs=item.members.filter(k=>k[1]===1).map(k=>all.get(pointKey(k))),refs=gs.flatMap(c=>c.requirements.map(([j])=>j));
   if(item.kind==='family'){
    const f=library.find(f=>f.id===item.family);if(!f||item.level!==f.level)throw Error('Unknown family');
    const ns=new Map(item.bindings.nodes),hs=new Map(item.bindings.holes);
    if(ns.size!==f.template.nodes.length||hs.size!==f.template.holes||new Set([...ns.values()].map(k=>k[0]).concat([...hs.values()])).size!==ns.size+hs.size)throw Error('Family receptor alias changed');
    const members=[];
    f.template.nodes.forEach((node,j)=>{const k=ns.get(j),g=all.get(pointKey(k));if(!g||k[1]!==1||g.command.rule!==node.rule||g.requirements.length!==node.inputs.length)throw Error('Family rule changed');members.push([k[0],0,k[2],0],k);
     node.inputs.forEach((port,r)=>{const [slot,a]=g.requirements[r];if('node' in port){const src=all.get(pointKey(ns.get(port.node)));if(slot!==src.slot||!eq(a,src.command.formula))throw Error('Internal receptor changed');}else if(slot!==hs.get(port.hole))throw Error('External receptor changed');});
    });
    if(!eq([...members].sort(keySort),item.members))throw Error('Family original expansion changed');
   }else if(item.kind!=='sampled'||item.level!==0)throw Error('Proposal type changed');
   phi=[Number(item.kind==='family'),item.new_occupancy/72,refs.filter(j=>slots.has(j)).length/Math.max(1,refs.length),refs.filter(j=>known.has(j)).length/Math.max(1,refs.length),Number(gs.some(c=>eq(c.command.formula,tr.case.target))),fresh/1000,slots.size/(Math.max(...slots)-Math.min(...slots)+1),gs.length/3,item.level/2,0];
  }
  if(!phi.every((v,k)=>close(v,e.features[z][k])))throw Error('Policy feature changed');
  const score=phi.reduce((a,x,k)=>a+x*e.weights[k],0);if(!close(score,e.scores[z]))throw Error('Policy score changed');
 });
 const top=Math.max(...e.scores),raw=e.scores.map(s=>Math.exp(s-top)),sum=raw.reduce((a,b)=>a+b,0),ps=raw.map(x=>x/sum);
 if(!ps.every((p,j)=>close(p,e.probabilities[j])))throw Error('Policy probabilities changed');
 let index=0;if(tr.search.stochastic){if(!(e.uniform>=0&&e.uniform<1))throw Error('Missing stochastic action');let c=0;index=ps.length-1;for(let j=0;j<ps.length;j++){c+=ps[j];if(e.uniform<c){index=j;break;}}}
 else{if(e.uniform!==null)throw Error('Non-greedy held-out action');for(let j=1;j<n;j++)if(e.scores[j]>e.scores[index])index=j;}
 if(e.index!==index)throw Error('Chosen action changed');
}
function keySort(a,b){for(let j=0;j<4;j++)if(a[j]!==b[j])return a[j]-b[j];return 0;}
function validateTraining(v){
 const t=v.training;if(t.episodes.length!==24||t.rate!==.4||!eq(t.features,FEATURES)||!eq(v.policy.features,FEATURES)||v.policy.library.length!==12)throw Error('Training declaration changed');
 let weights=Array(10).fill(0),baseline=0;const cache=new Map(v.proofs.filter(p=>p.role==='inventory_donor').map(p=>[packed(p.request),p.trace.verification_query])),records=v.proofs.find(p=>p.role==='inventory_donor').trace.records;let nextQuery=1+Math.max(...v.proofs.filter(p=>p.role==='inventory_donor').map(p=>p.trace.verification_query));
 t.episodes.forEach((e,j)=>{
  if(e.id!==j||e.case!==v.donors[j%3].id||!eq(e.weights_before,weights)||e.search.seed!==10000+j||e.search.stochastic!==true||!eq(e.search.weights,weights))throw Error('Fresh training provenance changed');
  const donor=v.proofs.find(p=>p.role==='inventory_donor'&&p.case===e.case),tr={...donor.trace,search:e.search,proof:e.search.proof,mode:'learned'};validatePointTrace(tr,v.policy.library);
  const request={protocol:'gcts-fol-1',theory:donor.request.theory,blocks:[],proof:e.search.proof,target:donor.request.target},key=packed(request),q=e.verification_query,record=records[q];
  if(!record||!eq(record.request,request)||record.result.status!=='accepted'||!e.accepted)throw Error('Native training feedback changed');
  if(cache.has(key)){if(!e.cached_native_acceptance||q!==cache.get(key))throw Error('Training cache provenance changed');}
  else{if(e.cached_native_acceptance||q!==nextQuery||record.purpose!=='training_feedback')throw Error('Fresh training query provenance changed');nextQuery++;cache.set(key,q);}
  const r=2*(e.accepted?e.search.proof.length:0)/Math.max(1,e.search.metrics.attempts??0)-.25*Math.min(1,((e.search.metrics.validation_checks??0)+(e.search.metrics.sample_pair_tests??0))/100000),gradient=Array(10).fill(0);
  for(const a of e.search.events)for(let k=0;k<10;k++)gradient[k]+=a.features[a.index][k]-a.probabilities.reduce((s,p,i)=>s+p*a.features[i][k],0);
  gradient.forEach((g,k)=>gradient[k]=g/Math.max(1,e.search.events.length));
  if(!close(r,e.learning.reward)||!close(baseline,e.learning.baseline_before)||!close(r-baseline,e.learning.advantage)||!gradient.every((g,k)=>close(g,e.learning.gradient[k])))throw Error('Learning gradient/reward changed');
  weights=weights.map((w,k)=>w+.4*(r-baseline)*gradient[k]);baseline=.9*baseline+.1*r;
  if(!weights.every((w,k)=>close(w,e.weights_after[k]))||!close(baseline,e.baseline_after))throw Error('Learning update changed');
 });
 if(!weights.every((w,k)=>close(w,t.weights[k])&&close(w,v.policy.weights[k])&&close(w,v.audit.training.weights[k]))||!close(baseline,t.baseline))throw Error('Final frozen policy changed');
}
if(typeof module!=='undefined')module.exports={validateReceptors,validatePointTrace,validateTraining,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),math=a=>'\\('+formula(a)+'\\)';let view,chosen=3,index=0,nodes=[];
 const refs=c=>c.rule==='mp'?[c.antecedent,c.implication]:c.rule==='generalize'?[c.source]:[];
 const english=c=>reason[c.rule]+(c.rule==='axiom'?' Input premise “'+c.name+'”.':refs(c).length?' Earlier '+(refs(c).length===1?'line ':'lines ')+refs(c).map(i=>i+1).join(' and ')+'.':'');
 const nativeColor=(v,l)=>{let n=0;for(const x of Array.isArray(v)?v:[v])n=(Math.imul(n,31)+x)>>>0;return 'hsl('+((l==='vertical'?205:140)+n%30)+' 58% '+(38+n%24)+'%)';};
 function pointPicture(p){
  const mode=el('layer').value,s=78,n=p.request.proof.length;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 '+(30+s*n)+'" role="img" aria-label="Exact formula markings linking command and guard point tiles"><text x="24" y="16" font-size="12">Command</text><text x="145" y="16" font-size="12">Rule guard</text><text x="275" y="16" font-size="12">Formula port</text>';
  p.request.proof.forEach((c,j)=>{const y=30+j*s,active=j===index;
   for(const [x,kind] of [[24,'command'],[145,'guard']])svg+='<rect x="'+x+'" y="'+y+'" width="57" height="57" fill="'+(active?'#eee3f2':'#f3f6ef')+'" stroke="#c2cdbb"/><circle cx="'+(x+28)+'" cy="'+(y+28)+'" r="4" fill="#23856b"/><rect x="'+(x+2)+'" y="'+(y+2)+'" width="53" height="6" fill="'+(mode==='formula'?'#d9dfd6':'#b98528')+'"/><rect x="'+(x+2)+'" y="'+(y+49)+'" width="53" height="6" fill="'+(mode==='command'?'#d9dfd6':'#8654a0')+'"/><text x="'+(x+28)+'" y="'+(y+20)+'" text-anchor="middle" font-size="10">'+(kind==='command'?'C':'G')+(j+1)+'</text><text x="'+(x+28)+'" y="'+(y+42)+'" text-anchor="middle" font-size="9">'+esc(c.rule)+'</text>';
   svg+='<path d="M 81 '+(y+28)+' H 145" stroke="'+(mode==='formula'?'#d9dfd6':'#b98528')+'" stroke-width="3"/><path d="M 202 '+(y+28)+' H 270" stroke="'+(mode==='command'?'#d9dfd6':'#8654a0')+'" stroke-width="3"/>';const bytes=[...new TextEncoder().encode(packed(c.formula)),256],shown=bytes.slice(0,7).concat(256);
   shown.forEach((v,k)=>svg+='<rect x="'+(270+k*9)+'" y="'+(y+21)+'" width="7" height="14" fill="'+(mode==='command'?'#d9dfd6':'hsl('+(275+v%25)+' 55% '+(36+v%20)+'%)')+'"/>');
   svg+='<text x="270" y="'+(y+49)+'" font-size="10" font-family="monospace">'+bytes.length+' point values</text>';
   if(active)refs(c).forEach((i,k)=>{const x=385+20*k;svg+='<path d="M 343 '+(30+i*s+28)+' H '+x+' V '+(y+28)+' H 343" stroke="'+(mode==='command'?'#d9dfd6':'#8654a0')+'" stroke-width="3" fill="none"/><circle cx="343" cy="'+(30+i*s+28)+'" r="4" fill="#8654a0"/><circle cx="343" cy="'+(y+28)+'" r="4" fill="#8654a0"/>';});
  });el('point-picture').innerHTML=svg+'</svg>';
 }
 function nativePicture(p){
  const patch=p.lines[index].patch,s=75,ox=38,oy=22;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+(ox+patch.width*s+15)+' '+(oy+patch.height*s+20)+'" role="img" aria-label="Actual original native Wang squares at the selected proof line"><text x="4" y="14" font-size="12">time ↑</text>';
  for(const t of patch.tiles){const x=ox+t.x*s,y=oy+(patch.height-1-t.y)*s;svg+='<g><rect class="native-tile" x="'+(x+1)+'" y="'+(y+1)+'" width="73" height="73" fill="'+(t.triple.some(v=>v>=60)?'#fff3d9':'#f8faf5')+'" stroke="#acb9ad"/><rect x="'+(x+8)+'" y="'+(y+2)+'" width="59" height="7" fill="'+nativeColor(t.N,'vertical')+'"/><rect x="'+(x+8)+'" y="'+(y+66)+'" width="59" height="7" fill="'+nativeColor(t.S,'vertical')+'"/><rect x="'+(x+2)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.W,'horizontal')+'"/><rect x="'+(x+66)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.E,'horizontal')+'"/><circle cx="'+(x+37.5)+'" cy="'+(y+37.5)+'" r="3" fill="#242a28"/><text x="'+(x+37.5)+'" y="'+(y+25)+'" text-anchor="middle" font-size="9" font-family="monospace">N '+t.N+'</text><text x="'+(x+37.5)+'" y="'+(y+57)+'" text-anchor="middle" font-size="9" font-family="monospace">S '+t.S+'</text></g>';}el('literal').innerHTML=svg+'</svg>';
 }
 function showNode(){const node=nodes[Number(el('node-control').value)],t=node.tree;el('node-summary').textContent=t.kind+' · '+t.census.length+' frontier points · '+t.census.reduce((n,p)=>n+p.keys.length,0)+' complete incidences · '+node.path.length+' previous placements. Selected point: '+JSON.stringify(t.point)+'.';el('graph-table').innerHTML=t.census.map(p=>'<tr><td><code>'+JSON.stringify(p.point)+'</code></td><td>'+p.generation+'</td><td>'+p.keys.length+'</td><td>'+(eq(p.point,t.point)?t.kind:'—')+'</td></tr>').join('');}
 function read(){
  const p=view.proofs[chosen],l=p.lines[index],c=p.request.proof[index],selected=p.trace.search.placements.find(k=>k[0]===index&&k[1]===1),guard=p.trace.model.placements.find(a=>eq(a.key,selected));
  el('reading').innerHTML='<div class="formula">'+math(c.formula)+'</div><p>'+esc(english(c))+'</p><p class="small">This selected guard assigns '+guard.marks.length+' exact marking points, including '+guard.requirements.length+' earlier formula words. All are checked by point-value agreement.</p>';
  el('marks').textContent=JSON.stringify({key:guard.key,occupancy:guard.occupancy,command:guard.command,earlier_requirements:guard.requirements.map(([i,f])=>({source_line:i+1,formula:f,encoded_word:[...new TextEncoder().encode(packed(f)),256]})),all_marking_points:guard.marks},null,2);
  el('input').innerHTML='<p>'+l.input.proved.length+' earlier checked facts.</p>'+l.input.proved.map(a=>'<div class="formula">'+math(a)+'</div>').join('');el('output').innerHTML='<p>Append the formula. '+l.output.proved.length+' facts are available.</p><div class="formula">'+math(c.formula)+'</div>';el('expansion').textContent='The complete native line expands to '+l.micro_steps.toLocaleString()+' selected-symbol operations and '+l.physical_height.toLocaleString()+' literal transitions. The response checker derives the entire expansion; only the entry crop is drawn.';el('artifacts').innerHTML='Whole accepting certificate: <a href="'+p.grammar.name+'">response grammar</a> · <a href="'+p.events.name+'">actual checkpoints</a> · <a href="'+p.responses.name+'">derived interfaces</a>.';pointPicture(p);nativePicture(p);window.MathJax?.typesetPromise?.([el('reading'),el('input'),el('output')]).catch(e=>el('load').textContent=e.message);
 }
 function show(){
  const p=view.proofs[chosen],c=[...view.cases,...view.donors].find(a=>a.id===p.case);index=p.lines.length-1;el('theorem').innerHTML='<div class="formula">'+math(p.request.target)+'</div><p>'+esc(c.scope)+'</p>';el('premises').innerHTML=Object.entries(p.request.theory.axioms).map(([n,a])=>'<p><code>'+esc(n)+'</code> '+math(a)+'</p>').join('')||'<p>No input axioms.</p>';el('lines').innerHTML=p.request.proof.map((cmd,j)=>'<div class="proof-line"><span>Line '+(j+1)+'</span><div class="formula">'+math(cmd.formula)+'</div><p>'+esc(english(cmd))+'</p></div>').join('');el('proof-line-control').innerHTML=p.lines.map((l,j)=>'<option value="'+j+'">Line '+(j+1)+' · '+l.label.rule+'</option>').join('');el('proof-line-control').value=String(index);nodes=[];const collect=(t,path)=>{nodes.push({tree:t,path});t.children.forEach(c=>collect(c.tree,[...path,c.key]));};collect(p.trace.search.tree,[]);el('node-control').innerHTML=nodes.map((n,j)=>'<option value="'+j+'">Node '+(j+1)+' · '+n.tree.kind+' · '+n.path.length+' placements</option>').join('');showNode();read();showDecisionOptions(p);window.MathJax?.typesetPromise?.([el('theorem'),el('premises'),el('lines')]).catch(e=>el('load').textContent=e.message);
 }
 function showTemplate(){
  const f=view.policy.library[Number(el('family-control').value)],nodes=f.template.nodes,step=80;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 430 '+(50+step*nodes.length)+'" role="img" aria-label="Mined rule topology with external receptors">';
  nodes.forEach((n,j)=>{const y=25+j*step;svg+='<rect x="75" y="'+y+'" width="54" height="54" fill="#edf3e7" stroke="#91a382"/><rect x="149" y="'+y+'" width="54" height="54" fill="#f0e6f4" stroke="#8654a0"/><rect x="77" y="'+(y+2)+'" width="50" height="6" fill="#b98528"/><rect x="151" y="'+(y+2)+'" width="50" height="6" fill="#b98528"/><text x="102" y="'+(y+34)+'" text-anchor="middle" font-size="12">C'+(j+1)+'</text><text x="176" y="'+(y+32)+'" text-anchor="middle" font-size="11">'+n.rule+'</text><circle cx="232" cy="'+(y+27)+'" r="7" fill="#8654a0"/>';
   n.inputs.forEach((port,k)=>{if('node' in port){const sy=25+port.node*step+27,x=265+20*k;svg+='<path d="M 239 '+sy+' H '+x+' V '+(y+27)+' H 239" fill="none" stroke="#8654a0" stroke-width="3"/>';}else{const x=327+45*k;svg+='<circle cx="'+x+'" cy="'+(y+27)+'" r="15" fill="#fff4d9" stroke="#b98528"/><text x="'+x+'" y="'+(y+31)+'" text-anchor="middle" font-size="11">H'+(port.hole+1)+'</text><path d="M '+(x-16)+' '+(y+27)+' H 239" stroke="#b98528" stroke-width="2"/>';}});});
  el('template-picture').innerHTML=svg+'</svg>';el('template-reading').textContent='Level '+f.level+' · '+nodes.length+' logical nodes · '+f.template.holes+' external receptor slots. Donor fragments: '+f.donors.map(d=>d.case+' lines '+d.slots.map(j=>j+1).join(', ')).join('; ')+'. Level counts inference nodes, not a proof-theoretic hierarchy.';
 }
 function showDecisionOptions(p){
  const es=p.trace.search.events??[];el('decision-control').innerHTML=es.map((e,j)=>'<option value="'+j+'">Decision '+(j+1)+' · '+e.chosen.length+' previous placements · point '+esc(JSON.stringify(e.point))+'</option>').join('')||'<option value="">No policy decision</option>';showProposals();
 }
 function showProposals(){
  const p=view.proofs[chosen],e=p.trace.search.events?.[Number(el('decision-control').value)];
  el('proposal-control').innerHTML=e?e.items.map((a,j)=>'<option value="'+j+'">'+(j+1)+' · '+(a?a.kind+' · '+a.members.length+' tiles':'Defer')+(j===e.index?' · CHOSEN':'')+'</option>').join(''):'<option value="">No proposal</option>';
  if(e)el('proposal-control').value=String(e.index);showProposal();
 }
 function showProposal(){
  const p=view.proofs[chosen],e=p.trace.search.events?.[Number(el('decision-control').value)],z=Number(el('proposal-control').value),item=e?.items[z];
  if(!e){el('cluster-picture').innerHTML='';el('cluster-summary').textContent=p.role==='inventory_donor'?'This donor was discovered without inventory guidance.':'This proof required only forced moves; RL made no choice.';el('cluster-reading').innerHTML='';el('policy-probs').innerHTML='';el('policy-raw').textContent='';return;}
  el('policy-probs').innerHTML=e.items.map((a,j)=>'<tr class="'+(j===e.index?'chosen':'')+'"><td>'+(j+1)+'</td><td>'+(a?a.kind:'defer')+'</td><td>'+(a?a.members.length:0)+'</td><td>'+e.scores[j].toFixed(4)+'</td><td><span class="bar" style="width:'+Math.round(e.probabilities[j]*260)+'px"></span>'+(100*e.probabilities[j]).toFixed(2)+'%</td><td>'+(j===e.index?'Chosen':'')+'</td></tr>').join('');
  el('policy-raw').textContent=JSON.stringify({proposal:z+1,chosen:e.index+1,item,features:Object.fromEntries(view.policy.features.map((f,j)=>[f,e.features[z][j]])),weights:e.weights,score:e.scores[z],probability:e.probabilities[z],uniform:e.uniform},null,2);
  if(!item){el('cluster-picture').innerHTML='';el('cluster-summary').textContent='Defer to the original candidate order at this branch.';el('cluster-reading').innerHTML='';return;}
  const all=p.trace.model.placements,find=k=>all.find(c=>eq(c.key,k)),members=new Set(item.members.map(pointKey)),pending=new Set(item.pending.map(pointKey)),holes=new Set(item.bindings?.holes.map(h=>h[1])??[]),step=58;
  let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 '+(26+p.lines.length*step)+'" role="img" aria-label="Actual original cluster tiles bound to variable proof line positions">';
  for(let j=0;j<p.lines.length;j++){
   const y=12+j*step;svg+='<text x="12" y="'+(y+28)+'" font-size="11">Line '+(j+1)+'</text>';
   for(const [x,r] of [[72,0],[148,1]]){
    const key=item.members.find(k=>k[0]===j&&k[1]===r),inMember=!!key,used=inMember&&!pending.has(pointKey(key));
    svg+='<rect x="'+x+'" y="'+y+'" width="46" height="46" fill="'+(inMember?(used?'#e4f0dd':'#ede0f3'):'#f5f7f1')+'" stroke="'+(inMember?'#8654a0':'#d3dacd')+'"/><rect x="'+(x+2)+'" y="'+(y+2)+'" width="42" height="5" fill="'+(inMember?'#b98528':'#e0e5dc')+'"/><rect x="'+(x+2)+'" y="'+(y+39)+'" width="42" height="5" fill="'+(inMember?'#8654a0':'#e0e5dc')+'"/><text x="'+(x+23)+'" y="'+(y+27)+'" text-anchor="middle" font-size="11">'+(r?'G':'C')+(j+1)+'</text>';
   }
   svg+='<circle cx="229" cy="'+(y+23)+'" r="6" fill="'+(holes.has(j)?'#b98528':'#c4ccbf')+'"/>';if(holes.has(j))svg+='<text x="246" y="'+(y+27)+'" font-size="10">external receptor</text>';
  }
  item.members.filter(k=>k[1]===1).forEach((k,n)=>{const g=find(k),y=12+k[0]*step+23;g.requirements.forEach(([i],r)=>{const sy=12+i*step+23,x=326+12*(n+r);svg+='<path d="M 229 '+sy+' H '+x+' V '+y+' H 229" stroke="#8654a0" stroke-width="2" fill="none"/>';});});
  el('cluster-picture').innerHTML=svg+'</svg>';
  el('cluster-summary').textContent='Proposal '+(z+1)+(z===e.index?' was chosen.':' was compatible but not chosen.')+' '+item.members.length+' original tiles, '+item.pending.length+' still to place; '+item.new_marks+' new exact mark points. The diagram shows this recorded binding, including future ports; occupancy alone is not an already justified fact.';
  el('cluster-reading').innerHTML=item.members.filter(k=>k[1]===1).map(k=>{const c=find(k);return '<p>Line '+(k[0]+1)+' · '+esc(c.command.rule)+' '+math(c.command.formula)+'</p>';}).join('');
  if(item.family){el('family-control').value=String(view.policy.library.findIndex(f=>f.id===item.family));showTemplate();}
  window.MathJax?.typesetPromise?.([el('cluster-reading')]).catch(e=>el('load').textContent=e.message);
 }
 function showEpisode(){
  const e=view.training.episodes[Number(el('episode-control').value)];el('episode-summary').textContent='Episode '+(e.id+1)+' · '+e.case+' · '+(e.accepted?'native accepted':'unfinished')+' · '+(e.search.metrics.attempts??0)+' original placements · '+e.search.events.length+' sampled decisions · reward '+e.learning.reward.toFixed(6)+'. Native feedback '+(e.cached_native_acceptance?'reused the exact accepted training request':'was freshly executed')+'.';
  el('weights-table').innerHTML=view.policy.features.map((f,j)=>'<tr><td><code>'+esc(f)+'</code></td><td>'+e.weights_before[j].toFixed(6)+'</td><td>'+e.learning.gradient[j].toFixed(6)+'</td><td>'+e.weights_after[j].toFixed(6)+'</td></tr>').join('');
  el('episode-raw').textContent=JSON.stringify(e,null,2);
 }
 function extraBoot(){
  el('case').innerHTML=view.proofs.map((p,j)=>'<option value="'+j+'">'+(p.role==='inventory_donor'?'Donor · ':'Held out · ')+esc([...view.cases,...view.donors].find(c=>c.id===p.case).title)+'</option>').join('');el('case').value=String(chosen);
  el('family-control').innerHTML=view.policy.library.map((f,j)=>'<option value="'+j+'">Family '+(j+1)+' · level '+f.level+' · '+f.template.nodes.map(n=>n.rule).join(' / ')+'</option>').join('');showTemplate();
  el('family-control').addEventListener('change',showTemplate);el('decision-control').addEventListener('change',showProposals);el('proposal-control').addEventListener('change',showProposal);
  el('episode-control').innerHTML=view.training.episodes.map((e,j)=>'<option value="'+j+'">Episode '+(j+1)+' · '+esc(e.case)+'</option>').join('');el('episode-control').addEventListener('change',showEpisode);showEpisode();
  const es=view.training.episodes,h=150,w=800,ox=45,oy=25,maxAttempts=Math.max(...es.map(e=>e.search.metrics.attempts??0)),maxReward=Math.max(1,...es.map(e=>Math.abs(e.learning.reward)));
  let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 405" role="img" aria-label="Actual 24 training episode rewards and original placement counts"><text x="45" y="16" font-size="12">Native-accepted reward</text><text x="45" y="218" font-size="12">Original placement attempts</text>';
  for(const [base,label] of [[oy,'reward'],[225,'attempts']]){
   svg+='<path d="M 45 '+base+' V '+(base+h)+' H 845" stroke="#bac5b4" fill="none"/>';
   const ys=es.map(e=>label==='reward'?e.learning.reward:e.search.metrics.attempts??0),max=label==='reward'?maxReward:maxAttempts;
   svg+='<polyline points="'+ys.map((v,j)=>(ox+j*w/23)+','+(base+h-h*v/max)).join(' ')+'" stroke="'+(label==='reward'?'#8654a0':'#23856b')+'" stroke-width="2" fill="none"/>';
   ys.forEach((v,j)=>svg+='<circle cx="'+(ox+j*w/23)+'" cy="'+(base+h-h*v/max)+'" r="3" fill="'+(label==='reward'?'#8654a0':'#23856b')+'"/>');
   svg+='<text x="45" y="'+(base+h+19)+'" font-size="11">Episode 1</text><text x="783" y="'+(base+h+19)+'" font-size="11">Episode 24</text><text x="5" y="'+(base+12)+'" font-size="11">'+max.toFixed(label==='reward'?1:0)+'</text>';
  }el('training-picture').innerHTML=svg+'</svg>';
  el('training-costs').textContent='Fresh donor search, catalog and native feedback: '+view.training.cold_seconds.toFixed(3)+' s; 24 rollouts and training feedback: '+view.training.training_seconds.toFixed(3)+' s. All '+view.training.queries+' distinct native training-stage queries and cached acceptance sources were independently replayed. Training has '+view.audit.training.events+' actual sampled decisions.';
  el('medians').innerHTML=view.cases.flatMap(c=>['base','zero','fixed','learned','no-family'].map(mode=>{
   const rows=view.observations.filter(o=>o.case===c.id&&o.mode===mode),times=rows.map(r=>r.cold_seconds).sort((a,b)=>a-b),statuses=[...new Set(rows.map(r=>r.status.replaceAll('_',' ')))],attempts=rows.map(r=>r.metrics.attempts??0);
   return '<tr><td>'+esc(c.id)+'</td><td>'+esc(mode)+'</td><td>'+statuses.join(' / ')+'</td><td>'+[...new Set(attempts)].join(' / ')+'</td><td>'+((times[0]+times[1])/2).toFixed(3)+'</td></tr>';
  })).join('');
 }

 async function boot(){try{
  const r=await fetch('native-inventory-reader-001.json?v=20261010-nip1');if(!r.ok)throw Error('HTTP '+r.status);view=await r.json();const checked=validateReceptors(view);el('load').textContent='Independent audit passed · '+checked.proofs+' discovered proofs · '+checked.lines+' native proof lines · '+view.audit.point_nodes+' complete point nodes · '+checked.queries+' replayed native queries';el('case').innerHTML=view.proofs.map((p,j)=>'<option value="'+j+'">'+esc([...view.cases,...view.donors].find(c=>c.id===p.case).title)+'</option>').join('');el('case').value=String(chosen);
  el('results').innerHTML=view.observations.map(o=>'<tr><td>'+esc(o.case)+'</td><td>'+esc(o.mode)+' · r'+o.repetition+'</td><td>'+o.status.replaceAll('_',' ')+'</td><td>'+o.queries+'</td><td>'+(o.metrics.attempts??0)+'</td><td>'+o.cold_seconds.toFixed(3)+'</td><td>'+o.worker_stage_seconds.toFixed(3)+'</td><td><a href="'+o.artifact.name+'">Trace</a></td></tr>').join('');el('costs').textContent='Code compilation '+view.costs.compile_seconds.toFixed(3)+' s; full production and accepting certificate materialization '+view.costs.production_seconds.toFixed(3)+' s; independent audit '+view.costs.audit_seconds.toFixed(3)+' s.';

  el('comparison').textContent='Seven-line chain: base 368, fixed 18, learned 14 placements. Nine-line chain: base and no-family remain unknown at 2000; fixed finds a proof in 221, learned in 505. The fixed heuristic is better on that longer case. Two repeats are a pilot; they are not independent training seeds or a comparison with established provers.';
  el('audit-details').textContent='Independent replay checked '+view.audit.point_nodes.toLocaleString()+' point nodes, '+view.audit.policy_events.toLocaleString()+' policy decisions, all '+view.audit.queries+' native queries, all 24 training updates and all 8 full accepting response certificates. It rejected '+view.audit.mutations+' altered artifacts.';
  extraBoot();
  el('case').addEventListener('change',()=>{chosen=Number(el('case').value);show();});el('proof-line-control').addEventListener('change',()=>{index=Number(el('proof-line-control').value);read();});el('layer').addEventListener('change',()=>pointPicture(view.proofs[chosen]));el('node-control').addEventListener('change',showNode);show();
 }catch(e){el('load').textContent='Validation failed: '+e.message;console.error(e);}}boot();
}
