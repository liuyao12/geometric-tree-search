'use strict';
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);
const equal=(a,b)=>canonical(a)===canonical(b);
const need=(v,s)=>{if(!v)throw Error(s);};
const key=v=>JSON.stringify(v);
const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const math=s=>'\\('+s+'\\)';
const word=(j,channel,value)=>[...new TextEncoder().encode(canonical(value)),256].map((v,i)=>[[4*j+(channel==='command'?1:0),100+i],v]);
const hasWord=(marks,entries)=>{const m=new Map(marks.map(([p,v])=>[key(p),v]));return entries.every(([p,v])=>m.get(key(p))===v);};
const texName=n=>/^[A-Za-z]$/.test(n)?n:'\\mathsf{'+String(n).replace(/[_%&#{}$]/g,c=>'\\'+c)+'}';
const term=t=>t[0]==='var'?texName(t[1]):texName(t[1])+(t[2].length?'('+t[2].map(term).join(',')+')':'');
function formula(f){
  if(f[0]==='pred')return texName(f[1])+(f[2].length?'('+f[2].map(term).join(',')+')':'');
  if(f[0]==='eq')return term(f[1])+'='+term(f[2]);
  if(f[0]==='all')return '\\forall '+texName(f[1])+'\\,'+formula(f[2]);
  if(f[0]==='not')return '\\neg('+formula(f[1])+')';
  if(f[0]==='bot')return '\\bot';
  const op={imp:'\\Rightarrow',and:'\\land',or:'\\lor'}[f[0]];need(op,'unsupported formula');
  return '('+formula(f[1])+op+' '+formula(f[2])+')';
}
const sortedKeys=ks=>ks.map(key).sort();
function groups(c){
  const writers=new Map(),failures=new Map(),fast=[];
  for(const w of c.writers){
    need(equal(w.word,word(w.slot,'formula',w.formula)),'changed complete formula word or terminator');
    need(new Set(w.keys.map(key)).size===w.keys.length,'duplicate writer identity');
    const id=key([w.slot,w.formula]);need(!writers.has(id),'duplicate word table');writers.set(id,w);
  }
  for(const f of c.failures){
    need(!failures.has(f.probe)&&f.slots.length===2&&0<=f.slots[0]&&f.slots[0]<f.slots[1]&&f.slots[1]<c.spec.length,'invalid row conjunction');
    need(equal(f.pair_point,[3,200000+2*f.probe])&&equal(f.single_point,[3,200001+2*f.probe]),'changed private point namespace');
    const a=writers.get(key([f.slots[0],f.formulas[0]])),b=writers.get(key([f.slots[1],f.formulas[1]]));
    need(a&&b,'missing original word writer table');
    const left=new Set(a.keys.map(key)),right=new Set(b.keys.map(key));
    need(equal(sortedKeys(f.left_keys),[...left].filter(k=>!right.has(k)).sort())&&
         equal(sortedKeys(f.right_keys),[...right].filter(k=>!left.has(k)).sort())&&
         equal(sortedKeys(f.joint_keys),[...left].filter(k=>right.has(k)).sort()),'incomplete opposing or shared writer incidence');
    failures.set(f.probe,f);
    fast.push({f,aw:a.word.map(([p,v])=>[key(p),v]),bw:b.word.map(([p,v])=>[key(p),v]),
      left:new Set(f.left_keys.map(key)),right:new Set(f.right_keys.map(key)),joint:new Set(f.joint_keys.map(key))});
  }
  need(failures.size===(c.source_counts.negative||0),'omitted certified negative');
  const domains=[];
  for(let j=0;j<c.spec.length;j++){
    const rows=[];
    for(const f of j===c.spec.length-1?[c.spec.target]:c.basis){
      for(const name of Object.keys(c.spec.theory.axioms).sort())rows.push({rule:'axiom',formula:f,name});
      for(const variable of c.variables)for(let source=0;source<j;source++)rows.push({rule:'generalize',formula:f,variable,source});
      for(let antecedent=0;antecedent<j;antecedent++)for(let implication=0;implication<j;implication++)rows.push({rule:'mp',formula:f,antecedent,implication});
      rows.push({rule:'refl',formula:f},{rule:'tautology',formula:f});
      for(const name of c.registry.interfaces)rows.push({rule:'block',formula:f,name});
    }
    const compare=(a,b)=>a<b?-1:a>b?1:0;
    rows.sort((a,b)=>compare(a.rule,b.rule)||compare(canonical(a.formula),canonical(b.formula))||compare(canonical(a),canonical(b)));
    domains.push(rows);
  }
  return {writers,failures,fast,domains};
}
function validateProof(c,p,native,g){
  if(p.proof===null){need(!p.tiles.length&&p.native_query===null&&!p.cached_native_acceptance&&['unknown_search_budget','exhausted_finite_marked_region'].includes(p.status),'unfinished or exhausted search has proof authority');return;}
  const q=native.get(p.native_query);need(q&&q.status==='accepted','missing accepted native computation');
  need(equal(q.request.proof,p.proof)&&equal(q.request.target,c.spec.target)&&equal(q.request.theory,c.spec.theory),'native query does not bind exact proof');
  need(['original','point','direct'].includes(p.layer),'invalid representation');
  const definitions=new Map(c.registry.definitions.map(d=>[d.name,d]));
  const wanted=new Set(),pending=p.proof.filter(r=>r.rule==='block').map(r=>r.name);
  while(pending.length){const n=pending.pop();if(wanted.has(n))continue;need(definitions.has(n),'unregistered lemma');wanted.add(n);pending.push(...definitions.get(n).definition.proof.filter(r=>r.rule==='block').map(r=>r.name));}
  need(equal(q.request.blocks,c.registry.native_blocks.filter(d=>wanted.has(d.name))),'wrong native dependency closure');
  const arity=Math.max(0,...c.registry.interfaces.map(n=>definitions.get(n).definition.premises.length));
  const modes=new Map(c.registry.interfaces.map((n,i)=>[n,i+1])),selected=new Map(),values=new Map();
  const expectedBoundary=word(c.spec.length-1,'formula',c.spec.target);
  if(p.layer==='point')for(const f of g.failures.values())if(f.joint_keys.length)expectedBoundary.push([f.single_point,0]);
  const sortMarks=m=>m.map(([pt,v])=>[key(pt),v]).sort((a,b)=>a[0].localeCompare(b[0]));
  need(equal(sortMarks(p.initial_marks),sortMarks(expectedBoundary)),'incorrect fixed target or exclusion boundary');
  for(const [point,v] of p.initial_marks){need(!values.has(key(point))||values.get(key(point))===v,'boundary value conflict');values.set(key(point),v);}
  for(const tile of p.tiles){
    const j=tile.key[0],role=tile.key[1],center=[4*j,role];
    need(j>=0&&j<c.spec.length&&role>=0&&role<2+arity&&equal(tile.occupancy,[[center,12]]),'wrong original unit occupancy');
    need(!selected.has(key(center)),'duplicate role in proof');selected.set(key(center),tile);
    const extra=[],markValues=new Map(tile.marks.map(([p,v])=>[key(p),v])),tileKey=key(tile.key);
    for(const {f,aw,bw,left,right,joint} of g.fast){
      const a=aw.every(([p,v])=>markValues.get(p)===v),b=bw.every(([p,v])=>markValues.get(p)===v);
      need(left.has(tileKey)===(a&&!b)&&right.has(tileKey)===(b&&!a)&&
           joint.has(tileKey)===(a&&b),'selected distant writer incidence differs from full word');
      if(p.layer==='point'&&(a||b))extra.push([a&&b?f.single_point:f.pair_point,a&&b?1:a?0:1]);
    }
    need(equal(sortMarks(extra),sortMarks(tile.marks.filter(([pt])=>pt[0]%4===3))),'wrong selected extra point values');
    for(const [point,v] of tile.marks){need(!values.has(key(point))||values.get(key(point))===v,'selected t/m region disagrees');values.set(key(point),v);}
  }
  need(p.proof.length===c.spec.length&&selected.size===c.spec.length*(2+arity),'incomplete rectangle');
  for(const f of g.failures.values()){
    const keys=new Set(p.tiles.map(t=>key(t.key)));
    need(!f.joint_keys.some(k=>keys.has(key(k)))&&!(f.left_keys.some(k=>keys.has(key(k)))&&f.right_keys.some(k=>keys.has(key(k)))),'selected direct conjunction is forbidden');
  }
  p.proof.forEach((row,j)=>{
    const skeleton=Object.fromEntries(Object.entries(row).filter(([k])=>k!=='inputs'));
    const C=selected.get(key([4*j,0])),G=selected.get(key([4*j,1]));
    need(C.kind==='command'&&G.kind==='guard'&&equal(C.command,skeleton)&&equal(G.command,skeleton),'selected command/guard does not decode row');
    const index=g.domains[j].findIndex(r=>equal(r,skeleton));
    need(index>=0&&equal(C.key,[j,0,index,0])&&G.key[2]===index,'wrong original positional command identity');
    const mode=row.rule==='block'?modes.get(row.name):0;need(mode!==undefined,'missing lemma mode');
    const entries=word(j,'command',skeleton).concat(word(j,'formula',row.formula),[[[4*j+2,90],mode]]);let requirements=[];
    if(row.rule==='axiom')need(equal(c.spec.theory.axioms[row.name],row.formula),'wrong axiom row');
    else if(row.rule==='block')need(equal(definitions.get(row.name).definition.conclusion,row.formula),'wrong lemma conclusion');
    else if(row.rule==='refl')need(row.formula[0]==='eq'&&equal(row.formula[1],row.formula[2]),'wrong reflexivity');
    else if(row.rule==='tautology')need(c.tautologies.some(f=>equal(f,row.formula)),'unadmitted tautology');
    else if(row.rule==='generalize'){
      need(row.formula[0]==='all'&&row.formula[1]===row.variable&&0<=row.source&&row.source<j&&equal(p.proof[row.source].formula,row.formula[2]),'bad earlier generalization');
      requirements=[[row.source,row.formula[2]]];
    }else if(row.rule==='mp'){
      need(0<=row.antecedent&&row.antecedent<j&&0<=row.implication&&row.implication<j,'later modus ponens input');
      const imp=p.proof[row.implication].formula;need(imp[0]==='imp'&&equal(imp[1],p.proof[row.antecedent].formula)&&equal(imp[2],row.formula),'modus ponens formula mismatch');
      requirements=[[row.antecedent,imp[1]],[row.implication,imp]];
    }else need(false,'unknown displayed rule');
    need(G.key[3]===(row.rule==='mp'?c.basis.findIndex(f=>equal(f,p.proof[row.implication].formula)):0),'wrong original guard variant');
    const originalMarks=t=>t.marks.filter(([pt])=>pt[0]%4!==3);
    need(equal(sortMarks(originalMarks(C)),sortMarks(entries))&&equal(C.requirements,[]),'command has incomplete full words');
    need(equal(G.requirements,requirements)&&equal(sortMarks(originalMarks(G)),sortMarks(entries.concat(requirements.flatMap(([i,f])=>word(i,'formula',f))))),'guard has incorrect original word values');
    const premises=row.rule==='block'?definitions.get(row.name).definition.premises:[];
    if(row.rule==='block')need(Array.isArray(row.inputs)&&row.inputs.length===premises.length,'missing lemma tuple');
    for(let r=0;r<arity;r++){
      const I=selected.get(key([4*j,2+r])),source=r<premises.length?row.inputs[r]:-1;
      const expected=[[[4*j+2,90],mode],[[4*j+2,100+r],source]];
      if(r<premises.length){need(source>=0&&source<j&&equal(p.proof[source].formula,premises[r]),'incorrect strict earlier lemma receptor');expected.push(...word(source,'formula',premises[r]));}
      need(I.input===r&&I.mode===mode&&I.source===(source===-1?null:source)&&I.kind===(source===-1?'unused_input':'lemma_input'), 'wrong premise field');
      need(equal(I.key,[j,2+r,mode,source===-1?0:source+1]),'wrong original premise placement identity');
      need(equal(I.requirements,source===-1?[]:[[source,premises[r]]])&&equal(sortMarks(originalMarks(I)),sortMarks(expected)),'premise field has incorrect point values');
    }
  });
  need(equal(p.proof.at(-1).formula,c.spec.target),'wrong final conclusion');
}
function validate(data){
  need(data.version==='boundary-reuse-reader-001'&&data.audit.status==='passed','missing independent audit');
  const native=new Map();data.native.forEach((q,i)=>{need(q.id===i&&q.status==='accepted','incorrect global native identity');native.set(q.id,q);});
  let proofs=0,observations=0;
  for(const c of data.cases){
    need(c.transfer_certificate.status==='passed'&&c.transfer_certificate.target_length===c.spec.length,'wrong transferred boundary');
    const g=groups(c);need(c.observations.length===14,'missing measured lane');
    const ids=new Set();for(const p of c.observations){need(!ids.has(p.id),'duplicate observation');ids.add(p.id);validateProof(c,p,native,g);proofs+=p.proof!==null;observations++;}
    for(const e of c.equivalence){
      const a=c.observations.find(p=>p.layer==='point'&&p.mode==='base'&&p.repetition===e.repetition),b=c.observations.find(p=>p.layer==='direct'&&p.repetition===e.repetition);
      need(a&&b&&a.semantic_tree_sha256===e.sha256&&b.semantic_tree_sha256===e.sha256&&equal(a.metrics,b.metrics)&&equal(a.proof,b.proof)&&a.metrics.nodes===e.nodes,'incorrect declared representation equivalence');
    }
  }
  need(observations===data.audit.observations,'audit observation count differs');return {cases:data.cases.length,observations,proofs};
}
const median=a=>{a=[...a].sort((x,y)=>x-y);return (a[Math.floor((a.length-1)/2)]+a[Math.floor(a.length/2)])/2;};
if(typeof window!=='undefined')window.GCTSBoundaryReuse={validate,formula};
if(typeof document!=='undefined'){
  const $=id=>document.getElementById(id);let evidence,current;let mathQueue=Promise.resolve();
  function clearMath(ids){if(window.MathJax?.typesetClear)MathJax.typesetClear(ids.map($));}
  function typeset(){mathQueue=mathQueue.then(async()=>{if(window.MathJax?.startup)await MathJax.startup.promise;if(window.MathJax?.typesetPromise)await MathJax.typesetPromise();}).catch(e=>{$('reader-status').textContent='Math rendering error: '+e.message;});}
  const format=v=>math(Number(v).toFixed(3));
  function comparisons(){
    clearMath(['statement','bars','cost-table','reuse-cost','equivalence']);
    $('statement').innerHTML='Given '+Object.values(current.spec.theory.axioms).map(f=>math(formula(f))).join('; ')+'. Seek '+math(formula(current.spec.target))+' in a boundary with '+math(String(current.spec.length))+' proof rows.';
    const grouped=[];for(const mode of ['base','fixed','learned'])for(const layer of ['original','point','direct']){
      const rows=current.observations.filter(p=>p.layer===layer&&p.mode===mode);if(!rows.length)continue;
      grouped.push({layer,mode,rows,attempts:median(rows.map(r=>r.metrics.attempts||0))});
    }
    const maximum=Math.max(...grouped.map(g=>g.attempts),1);
    $('bars').innerHTML=grouped.map(g=>'<div class="bar-row"><span>'+escapeHtml(g.mode+' · '+g.layer)+'</span><div class="bar-track"><div class="bar '+g.layer+'" style="width:'+g.attempts/maximum*100+'%"></div></div><span>'+math(String(g.attempts))+(g.rows.every(r=>r.proof===null)?' · unknown':'')+'</span></div>').join('');
    $('cost-table').innerHTML='<div class="scroll-table"><table><thead><tr><th>Ordering / representation</th><th>Attempts, both observations</th><th>Search seconds, both observations</th><th>Worker seconds, both observations</th><th>Peak worker MiB</th></tr></thead><tbody>'+grouped.map(g=>'<tr><td>'+escapeHtml(g.mode+' / '+g.layer)+'</td><td>'+g.rows.map(r=>math(String(r.metrics.attempts||0))).join(' / ')+'</td><td>'+g.rows.map(r=>format(r.seconds)).join(' / ')+'</td><td>'+g.rows.map(r=>format(r.worker_wall_seconds)).join(' / ')+'</td><td>'+g.rows.map(r=>format(r.peak_rss_bytes/1048576)).join(' / ')+'</td></tr>').join('')+'</tbody></table></div>';
    $('reuse-cost').innerHTML='The source pair collection took '+format(current.source_collection_seconds)+' seconds, including its immediate independent replay. Admitting this boundary took '+format(current.transfer_seconds)+' seconds and rechecked '+math(String(current.transfer_certificate.pairs))+' source pairs. Both constraint representations share these certification costs. They reuse '+math(String(current.source_counts.negative||0))+' negatives; '+math(String(current.source_counts.unknown||0))+' unresolved source pairs impose no constraint.';
    $('equivalence').innerHTML='Point and direct base searches have the same complete censuses, decisions, alternatives, results and decoded proof in both repetitions: '+current.equivalence.map(x=>math(String(x.nodes))+' visited nodes').join(' / ')+'. <details><summary>Exact certified equivalence data</summary><pre>'+escapeHtml(JSON.stringify(current.equivalence,null,2))+'</pre></details>';
  }
  function readProof(){
    clearMath(['proof-context','proof-lines']);
    const p=current.observations.find(x=>x.id===$('proof-control').value);const root=$('proof-lines');
    if(!p.proof){$('proof-context').innerHTML=p.status==='exhausted_finite_marked_region'?'The declared finite grammar was exhausted at this boundary. This does not establish mathematical unprovability.':'This search reached its placement budget with no proof. Its result is unknown.';root.innerHTML='';typeset();return;}
    const q=evidence.native.find(x=>x.id===p.native_query);
    $('proof-context').innerHTML='The '+escapeHtml(p.layer)+' representation with '+escapeHtml(p.mode)+' ordering found this '+math(String(p.proof.length))+'-row proof. Native computation '+math(String(q.id))+' accepted the exact symbolic certificate. '+(p.cached_native_acceptance?'This observation reuses an earlier identical acceptance within this experiment.':'This observation caused a fresh whole native check.')+'<p>Conclusion: '+math(formula(current.spec.target))+'.</p>';
    const definitions=new Map(current.registry.definitions.map(d=>[d.name,d]));
    root.innerHTML=p.proof.map((row,j)=>{
      const tiles=p.tiles.filter(t=>t.key[0]===j).sort((a,b)=>a.key[1]-b.key[1]);let words,contract='';
      if(row.rule==='axiom')words='Use the given hypothesis named <code>'+escapeHtml(row.name)+'</code>.';
      else if(row.rule==='mp')words='Apply modus ponens to lines '+math(String(row.antecedent+1))+' and '+math(String(row.implication+1))+'.';
      else if(row.rule==='block'){
        const d=definitions.get(row.name);words='Apply the checked lemma at inventory level '+math(String(d.level))+' to the ordered hypotheses on lines '+math(row.inputs.map(i=>i+1).join(','))+'.';
        contract='<details><summary>Exact lemma hypotheses and conclusion</summary><p>Ordered hypotheses: '+d.definition.premises.map(f=>math(formula(f))).join('; ')+'. Conclusion: '+math(formula(d.definition.conclusion))+'.</p><pre>'+escapeHtml(JSON.stringify(d.definition,null,2))+'</pre></details>';
      }else if(row.rule==='generalize')words='Generalize line '+math(String(row.source+1))+' over '+math(texName(row.variable))+'.';
      else if(row.rule==='refl')words='Use equality reflexivity.';else words='Use a native-admitted logical tautology.';
      return '<div class="proof-line"><span class="line-number">Line '+math(String(j+1))+'</span><div><div class="role-tiles">'+tiles.map(t=>'<span class="role-tile '+escapeHtml(t.kind)+'" title="'+escapeHtml(t.kind)+'">'+(t.key[1]===0?'C':t.key[1]===1?'G':'I'+(t.key[1]-2))+'</span>').join('')+'</div><p class="formula">'+math(formula(row.formula))+'</p><p>'+words+'</p>'+contract+'<details><summary>Selected tile point data</summary><pre>'+escapeHtml(JSON.stringify(tiles,null,2))+'</pre></details></div></div>';
    }).join('');typeset();
  }
  function chooseCase(){
    current=evidence.cases.find(c=>c.id===$('case-control').value);comparisons();
    $('proof-control').innerHTML=current.observations.map(p=>'<option value="'+p.id+'">'+escapeHtml(p.layer+' · '+p.mode+' · repetition '+p.repetition+(p.proof?'':' · unknown'))+'</option>').join('');
    const preferred=current.observations.find(p=>p.layer==='point'&&p.mode==='fixed'&&p.repetition===1&&p.proof);if(preferred)$('proof-control').value=preferred.id;
    readProof();typeset();
  }
  async function start(){
    try{
      const response=await fetch('boundary-reuse-reader-001.json?v=20261011-br1');need(response.ok,'evidence download failed');evidence=await response.json();const checked=validate(evidence);
      $('reader-status').textContent='Loaded: '+checked.cases+' admitted boundaries, '+checked.observations+' observations and '+checked.proofs+' selected proof regions checked against the audited projection. Native computations and full tree replay were verified outside the browser.';
      $('case-control').innerHTML=evidence.cases.map(c=>'<option value="'+c.id+'">'+escapeHtml(c.title+' · '+c.spec.length+' rows')+'</option>').join('');
      $('case-control').value=evidence.cases.find(c=>c.id==='join-boundary-6').id;
      $('case-control').addEventListener('change',chooseCase);$('proof-control').addEventListener('change',readProof);chooseCase();
      $('audit-summary').innerHTML='Independent replay covers '+math(String(evidence.audit.point_nodes))+' search nodes, '+math(String(evidence.audit.events))+' policy decisions and '+math(String(evidence.audit.native_queries))+' fresh distinct native computations. The full pipeline took '+format(evidence.pilot_seconds)+' seconds; the later complete audit took '+format(evidence.audit.seconds)+' additional seconds. These are research-pipeline costs, not a cold timing benchmark.';
      $('artifact-links').innerHTML=evidence.artifacts.map(a=>'<p><a href="'+a.path+'">'+escapeHtml(a.path)+'</a> · <code>'+a.sha256+'</code></p>').join('');typeset();
    }catch(e){$('reader-status').textContent='Reader rejected this projection: '+e.message;}
  }
  start();
}
