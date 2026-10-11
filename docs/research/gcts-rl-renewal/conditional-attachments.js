'use strict';
const $=id=>document.getElementById(id);
const canonical=value=>JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const equal=(a,b)=>canonical(a)===canonical(b);
const need=(yes,why)=>{if(!yes)throw Error(why);};
const key=k=>JSON.stringify(k);
const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const math=s=>'\\('+s+'\\)';
const word=(slot,channel,value)=>[...new TextEncoder().encode(canonical(value)),256].map((v,i)=>[[4*slot+(channel==='command'?1:0),100+i],v]);
const count=rows=>rows.reduce((a,r)=>(a[r.label]=(a[r.label]||0)+1,a),{});
const hasWord=(marks,entries)=>{const m=new Map(marks.map(([p,v])=>[key(p),v]));return entries.every(([p,v])=>m.get(key(p))===v);};
const texName=name=>/^[A-Za-z]$/.test(name)?name:'\\mathsf{'+String(name).replace(/[^A-Za-z0-9]/g,'')+'}';
function term(t){return t[0]==='var'?texName(t[1]):texName(t[1])+(t[2].length?'('+t[2].map(term).join(',')+')':'');}
function formula(f){
  if(f[0]==='pred')return texName(f[1])+(f[2].length?'('+f[2].map(term).join(',')+')':'');
  if(f[0]==='eq')return term(f[1])+'='+term(f[2]);
  if(f[0]==='all')return '\\forall '+texName(f[1])+'\\,'+formula(f[2]);
  if(f[0]==='not')return '\\neg('+formula(f[1])+')';
  if(f[0]==='bot')return '\\bot';
  const op={imp:'\\Rightarrow',and:'\\land',or:'\\lor'}[f[0]];
  need(op,'unsupported displayed formula');return '('+formula(f[1])+op+' '+formula(f[2])+')';
}
function validateProof(c,p,native,conditionalAssignments){
  const q=native.get(p.native_query);need(q&&q.status==='accepted','proof has no accepted global native query');
  need(equal(q.request.proof,p.proof)&&equal(q.request.target,c.spec.target)&&equal(q.request.theory,c.spec.theory),'native query does not bind displayed proof');
  const defs=new Map(c.registry.definitions.map(d=>[d.name,d.definition]));
  for(const b of q.request.blocks)need(defs.has(b.name)&&equal(defs.get(b.name),b),'native lemma definition differs');
  const values=new Map(),totals=new Map(),selected=new Map();
  const withUnary=['unary','combined'].includes(p.layer),withPair=['conditional','combined'].includes(p.layer);
  need(['original','unary','conditional','combined'].includes(p.layer),'unknown proof layer');
  const expectedInitial=new Map(word(c.spec.length-1,'formula',c.spec.target).map(([p,v])=>[key(p),v]));
  if(withUnary)for(const x of c.unary_probes.filter(x=>x.label==='negative'))expectedInitial.set(key([4*x.slot+3,100000+c.basis.findIndex(f=>equal(f,x.formula))]),0);
  if(withPair)for(const f of c.failures)if(f.joint_keys.length)expectedInitial.set(key(f.single_point),0);
  need(equal([...expectedInitial].sort(),p.initial_marks.map(([point,v])=>[key(point),v]).sort()),'complete selected fixed marking boundary differs');
  for(const [point,v] of p.initial_marks){need(!values.has(key(point))||values.get(key(point))===v,'fixed point disagreement');values.set(key(point),v);}
  need(hasWord(p.initial_marks,word(c.spec.length-1,'formula',c.spec.target)),'complete original conclusion boundary missing');
  const arity=Math.max(0,...c.registry.interfaces.map(name=>defs.get(name).premises.length));
  for(const tile of p.tiles){
    const j=tile.key[0],role=tile.key[1],center=[4*j,role];
    need(j>=0&&j<c.spec.length&&role>=0&&role<2+arity&&equal(tile.occupancy,[[center,12]]),'selected original unit tile differs');
    need(!selected.has(key(center)),'duplicate proof role');selected.set(key(center),tile);totals.set(key(center),12);
    const extra=new Map();
    if(withUnary)for(const x of c.unary_probes.filter(x=>x.label==='negative'))if(hasWord(tile.marks,word(x.slot,'formula',x.formula)))extra.set(key([4*x.slot+3,100000+c.basis.findIndex(f=>equal(f,x.formula))]),1);
    if(withPair)for(const [point,v] of conditionalAssignments.get(key(tile.key))||[])extra.set(key(point),v);
    need(equal([...extra].sort(),tile.marks.filter(([point])=>point[0]%4===3).map(([point,v])=>[key(point),v]).sort()),'selected extra marking support differs');
    for(const [point,v] of tile.marks){need(!values.has(key(point))||values.get(key(point))===v,'selected marking values disagree');values.set(key(point),v);}
  }
  need(p.proof.length===c.spec.length&&selected.size===c.spec.length*(2+arity),'incomplete proof rectangle');
  const modes=new Map(c.registry.interfaces.map((name,i)=>[name,i+1]));
  p.proof.forEach((row,j)=>{
    const skeleton={...row};delete skeleton.inputs;
    const command=selected.get(key([4*j,0])),guard=selected.get(key([4*j,1]));
    need(command&&guard&&equal(command.command,skeleton)&&equal(guard.command,skeleton),'selected command/guard words differ');
    for(const tile of [command,guard])need(hasWord(tile.marks,word(j,'command',skeleton))&&hasWord(tile.marks,word(j,'formula',row.formula)),'incomplete selected command/formula word');
    for(const [source,f] of guard.requirements)need(source<j&&source>=0&&equal(p.proof[source].formula,f)&&hasWord(guard.marks,word(source,'formula',f)),'guard premise or distant word missing');
    if(row.rule==='axiom')need(equal(c.spec.theory.axioms[row.name],row.formula),'wrong named hypothesis');
    if(row.rule==='mp')need(row.antecedent>=0&&row.implication>=0&&row.antecedent<j&&row.implication<j&&equal(p.proof[row.implication].formula,['imp',p.proof[row.antecedent].formula,row.formula]),'wrong implication attachment');
    if(row.rule==='block'){
      const d=defs.get(row.name);need(d&&equal(d.conclusion,row.formula)&&row.inputs.length===d.premises.length,'wrong lemma interface');
      row.inputs.forEach((i,r)=>need(i>=0&&i<j&&equal(p.proof[i].formula,d.premises[r]),'ordered lemma premise mismatch'));
    }
    for(let r=0;r<arity;r++){
      const tile=selected.get(key([4*j,2+r]));need(tile,'missing selected input tile');
      const d=row.rule==='block'?defs.get(row.name):null;
      const active=d&&r<d.premises.length,source=active?row.inputs[r]:null,mode=d?modes.get(row.name):0;
      need(tile.input===r&&tile.source===source&&tile.mode===mode,'input mode/source differs');
      need(hasWord(tile.marks,[[[4*j+2,90],mode],[[4*j+2,100+r],active?source:-1]]),'input field values missing');
      if(active)need(hasWord(tile.marks,word(source,'formula',d.premises[r])),'distant lemma input word missing');
    }
  });
  need(equal(p.proof.at(-1).formula,c.spec.target),'final proof formula is not the assertion');
}
function validate(data){
  need(data.version==='conditional-reader-001'&&data.audit.status==='passed'&&data.audit.native_queries===data.native.length,'missing complete audit');
  const native=new Map(data.native.map(q=>[q.id,q]));need(native.size===data.native.length&&data.native.every((q,i)=>q.id===i),'native query identifiers not globally dense');
  let observations=0;
  for(const c of data.cases){
    need(c.certificate.status==='passed'&&c.certificate.learning_sha256===c.learning_sha256&&c.certificate.context_sha256===c.context_sha256,'conditional certificate binding');
    need(equal(count(c.probes),c.pair_counts)&&equal(c.certificate.counts,c.pair_counts),'pair status counts differ');
    need(equal(count(c.unary_probes),c.unary_counts),'unary status counts differ');
    const singles=new Map(c.unary_probes.map(p=>[key([p.slot,p.formula]),p.label]));
    const formulas=[...c.basis].sort((a,b)=>canonical(a).localeCompare(canonical(b),'en'));
    // The fixed catalogs contain ASCII names, so byte lexicographic comparison
    // matches the original canonical UTF-8 sorting exactly.
    formulas.sort((a,b)=>canonical(a)<canonical(b)?-1:canonical(a)>canonical(b)?1:0);
    const expected=[];for(const [a,b] of c.row_pairs)for(const x of a===c.spec.length-1?[c.spec.target]:formulas)for(const y of b===c.spec.length-1?[c.spec.target]:formulas)expected.push({slots:[a,b],formulas:[x,y]});
    need(expected.length===c.probes.length,'complete Cartesian catalog missing');
    const probes=new Map(c.probes.map(p=>[p.id,p])),writers=new Map(c.writers.map(w=>[key([w.slot,w.formula]),w]));
    for(const w of c.writers){need(equal(w.word,word(w.slot,'formula',w.formula)),'writer word or terminator differs');need(new Set(w.keys.map(key)).size===w.keys.length,'duplicate writer candidate');}
    c.probes.forEach((p,i)=>{
      need(p.id===i&&equal(p.slots,expected[i].slots)&&equal(p.formulas,expected[i].formulas),'catalog query omitted or altered');
      const status={positive:'finite_marked_proof_region',negative:'exhausted_finite_marked_region',unknown:'unknown_search_budget'}[p.label];
      need(status&&p.teacher_status===status&&p.checked_nodes===p.teacher_metrics.nodes,'teacher label or visited-node count differs');
      need(equal(p.individual_labels,p.slots.map((j,r)=>singles.get(key([j,p.formulas[r]])))),'individual word labels differ from checked unary queries');
      need(p.genuine===(p.label==='negative'&&p.individual_labels.every(x=>x==='positive')),'conditional versus individual classification differs');
    });
    need(c.failures.length===(c.pair_counts.negative||0),'unknown or missing failure assignments');
    const allAssignments=new Map();
    for(const f of c.failures){
      const p=probes.get(f.probe);need(p&&p.label==='negative'&&equal(f.slots,p.slots)&&equal(f.formulas,p.formulas),'failure has no negative teacher');
      need(equal(f.pair_point,[3,200000+2*p.id])&&equal(f.single_point,[3,200001+2*p.id]),'private point namespace differs');
      const groups=f.slots.map((j,i)=>new Set((writers.get(key([j,f.formulas[i]]))?.keys||[]).map(key)));
      const both=[...groups[0]].filter(k=>groups[1].has(k)).sort(),left=[...groups[0]].filter(k=>!groups[1].has(k)).sort(),right=[...groups[1]].filter(k=>!groups[0].has(k)).sort();
      const sorted=ks=>ks.map(key).sort();need(equal(sorted(f.left_keys),left)&&equal(sorted(f.right_keys),right)&&equal(sorted(f.joint_keys),both),'all-writer support differs');
      const expectedAssignments=[...new Set([...groups[0],...groups[1]])].map(k=>({key:JSON.parse(k),point:both.includes(k)?f.single_point:f.pair_point,value:both.includes(k)?1:groups[0].has(k)?0:1}));
      need(equal([...f.assignments].sort((a,b)=>key(a.key).localeCompare(key(b.key))),expectedAssignments.sort((a,b)=>key(a.key).localeCompare(key(b.key)))),'missing or changed conditional value');
      for(const a of f.assignments){const k=key(a.key);if(!allAssignments.has(k))allAssignments.set(k,[]);allAssignments.get(k).push([a.point,a.value]);}
    }
    for(const f of c.failures)for(const r of f.representatives){
      need(f[r.side+'_keys'].some(k=>equal(k,r.key)),'representative outside actual group');
      const words=f.slots.map((j,i)=>word(j,'formula',f.formulas[i]));
      need(hasWord(r.original_marks,words[r.side==='right'?1:0]),'representative original word missing');
      if(r.side==='joint')need(hasWord(r.original_marks,words[1]),'joint representative second word missing');
      const expected=new Map(r.original_marks.map(([p,v])=>[key(p),v]));
      for(const [p,v] of allAssignments.get(key(r.key))||[])need(!expected.has(key(p))||expected.get(key(p))===v,'internal overlay disagreement'),expected.set(key(p),v);
      need(equal([...expected].sort(),r.marked_marks.map(([p,v])=>[key(p),v]).sort()),'representative decorated values differ');
    }
    need(c.observations.length===12,'missing paired lane');observations+=c.observations.length;
    need(new Set(c.observations.map(r=>r.layer+'-'+r.mode)).size===12,'duplicate paired lane');
    for(const p of c.proofs)validateProof(c,p,native,allAssignments);
    for(const r of c.observations){const p=c.proofs.find(p=>p.id===r.layer+'-'+r.mode);need((r.native_query===null)===(p===undefined),'proof availability differs');if(p)need(p.native_query===r.native_query,'wrong search native identifier');}
  }
  need(observations===36,'all matched observations required');return data;
}
let evidence,current;
function typeset(){if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise().catch(e=>{$('reader-status').textContent='Math rendering failed: '+e.message;});}
function drawProbe(c,p){
  const f=c.failures.find(f=>f.probe===p.id),svg=$('marking-view');
  if(!f){svg.innerHTML='<text x="40" y="80" font-size="24">'+(p.label==='positive'?'The original prefix has a completion.':'The original search is unresolved.')+'</text><text x="40" y="130" font-size="19">No added conditional marking point.</text>';return;}
  const l=f.representatives.find(r=>r.side==='left'),r=f.representatives.find(r=>r.side==='right');
  let s='<text x="35" y="40" font-size="21">Actual alternatives and their conditional point</text>';
  for(const [rep,x,color,label] of [[l,145,'#80569e','Left'],[r,610,'#377fa0','Right']]){
    if(!rep)continue;
    s+='<rect x="'+x+'" y="110" width="72" height="72" fill="#f1f4ec" stroke="'+color+'" stroke-width="4"/><text x="'+(x+36)+'" y="151" text-anchor="middle" font-size="19">'+label+'</text><text x="'+(x+36)+'" y="214" text-anchor="middle" font-size="17">'+escapeHtml(rep.kind.replaceAll('_',' '))+'</text>';
    s+='<path d="M '+(x+36)+' 184 Q '+(x+36)+' 320 410 333" fill="none" stroke="'+color+'" stroke-width="3"/><text x="'+(x+36)+'" y="264" text-anchor="middle" font-size="17">assigned '+(label==='Left'?'zero':'one')+'</text>';
  }
  s+='<circle cx="410" cy="333" r="13" fill="#b34851"/><text x="410" y="383" text-anchor="middle" font-size="20">Both attachments cannot agree here.</text>';
  if(f.joint_keys.length)s+='<text x="410" y="423" text-anchor="middle" font-size="16">Single candidates writing both words have a separate fixed exclusion.</text>';
  svg.innerHTML=s;
}
function showProbe(){
  const p=current.probes[Number($('probe-control').value)],f=current.failures.find(f=>f.probe===p.id);
  $('pair-formulas').innerHTML=p.slots.map((j,i)=>'<p>'+math('F_{'+(j+1)+'}='+formula(p.formulas[i]))+'</p>').join('');
  const notice=$('label-status');notice.className='notice '+p.label;
  notice.innerHTML='<strong>'+({positive:'Witnessed prefix completion',negative:'Certified forbidden row combination',unknown:'Unresolved teacher'}[p.label])+'</strong><p>'+math(String(p.teacher_metrics.nodes))+' visited nodes; '+math(String(p.teacher_metrics.attempts||0))+' attempted placements.</p><p>Individual prefix tests: '+p.individual_labels.map(x=>({positive:'completable',negative:'excluded',unknown:'unresolved'}[x])).join(' / ')+'.</p>'+(p.genuine?'<p>Each word has a prefix witness at its own row; the two fixed row assignments cannot share a prefix completion.</p>':'')+(f?'<p>'+math(String(f.left_keys.length))+' left-only, '+math(String(f.right_keys.length))+' right-only and '+math(String(f.joint_keys.length))+' joint writers.</p>':'<p>This pair supplies no extra assigned value.</p>');
  drawProbe(current,p);$('exact-data').textContent=JSON.stringify({probe:p,failure:f||null},null,2);typeset();
}
function explanation(c,row){
  if(row.rule==='axiom')return 'Use the given hypothesis named '+escapeHtml(row.name)+'.';
  if(row.rule==='mp')return 'Apply the implication on line '+(row.implication+1)+' to the fact on line '+(row.antecedent+1)+'.';
  if(row.rule==='block'){const d=c.registry.definitions.find(d=>d.name===row.name);return row.inputs.length?'Apply the checked lemma at level '+d.level+' to the ordered hypotheses on lines '+row.inputs.map(i=>i+1).join(', ')+'.':'Apply the checked closed lemma; it has no local hypotheses.';}
  if(row.rule==='generalize')return 'Universally generalize line '+(row.source+1)+', with the scope conditions checked by the native certificate.';
  if(row.rule==='refl')return 'Use equality reflexivity.';
  return 'Use the native-checked tautology rule.';
}
function showProof(){
  const p=current.proofs.find(p=>p.id===$('proof-control').value);
  if(!p){$('proof-context').textContent='No recorded search found a checked proof within its budget.';$('proof-lines').innerHTML='';return;}
  $('proof-context').innerHTML='<p>'+escapeHtml(p.source==='z3'?'The separate Z3 control found this proof.':'The '+p.layer+' layer with '+p.mode+' ordering found this proof.')+' Fresh global native query '+math(String(p.native_query))+' accepted the exact certificate with search markings erased.</p><p>Given hypotheses: '+Object.values(current.spec.theory.axioms).map(f=>math(formula(f))).join('; ')+'. Conclusion: '+math(formula(current.spec.target))+'.</p>';
  $('proof-lines').innerHTML=p.proof.map((row,j)=>{
    const tiles=p.tiles.filter(t=>t.slot===j).sort((a,b)=>a.key[1]-b.key[1]);
    const glyphs=tiles.map(t=>'<span class="role-tile '+t.kind+'" title="'+escapeHtml(t.kind+' '+key(t.key))+'">'+(t.kind==='command'?'C':t.kind==='guard'?'G':'I'+t.input)+'</span>').join('');
    let interfaceText='';if(row.rule==='block'){const d=current.registry.definitions.find(d=>d.name===row.name).definition;interfaceText='<details><summary>Exact lemma hypotheses and conclusion</summary><p>'+math(d.premises.map(formula).join(',')+'\\;\\vdash\\;'+formula(d.conclusion))+'</p></details>';}
    return '<div class="proof-line"><div class="line-number">Line '+(j+1)+'</div><div><div class="role-tiles">'+glyphs+'</div><div class="formula">'+math(formula(row.formula))+'</div><p>'+explanation(current,row)+'</p>'+interfaceText+'<details><summary>Selected tile point data</summary><pre>'+escapeHtml(JSON.stringify(tiles,null,2))+'</pre></details></div></div>';
  }).join('');typeset();
}
function showCase(){
  current=evidence.cases.find(c=>c.id===$('case-control').value);
  $('probe-control').innerHTML=current.probes.map(p=>'<option value="'+p.id+'">Lines '+p.slots.map(j=>j+1).join(' / ')+' · '+p.label+(p.genuine?' · individually possible':'')+' · pair '+p.id+'</option>').join('');
  const selected=current.probes.find(p=>p.genuine)||current.probes.find(p=>p.label==='negative')||current.probes[0];$('probe-control').value=String(selected.id);
  $('proof-control').innerHTML=current.proofs.map(p=>'<option value="'+p.id+'">'+p.layer+' · '+p.mode+(p.source==='z3'?' · separate control':'')+'</option>').join('');
  const proof=current.proofs.find(p=>p.id==='combined-fixed')||current.proofs.find(p=>p.id==='conditional-fixed')||current.proofs[0];if(proof)$('proof-control').value=proof.id;
  const domains=current.root_domains;$('root-diagnosis').innerHTML='<strong>Initial complete point domains</strong><p>'+Object.entries(domains).map(([layer,d])=>escapeHtml(layer)+': '+math(String(d.incidences))+' incidences, '+math(String(d.forced))+' forced roots').join('; ')+'.</p><p>Conditional constraints can become active after an attachment even when the initial domains do not change.</p>';
  showProbe();showProof();
}
async function main(){
  try{
    const response=await fetch('conditional-reader-001.json?v=20261011-ca1');need(response.ok,'reader evidence unavailable');evidence=validate(await response.json());
    $('case-control').innerHTML=evidence.cases.map(c=>'<option value="'+c.id+'">'+escapeHtml(c.title)+'</option>').join('');
    if(window.location.hash==='#reader'&&evidence.cases.some(c=>c.id==='shared-premise-join'))$('case-control').value='shared-premise-join';
    const improvements=[];
    $('results-body').innerHTML=evidence.cases.flatMap(c=>['base','fixed','learned'].map(mode=>{
      const rows=['original','unary','conditional','combined'].map(layer=>c.observations.find(r=>r.layer===layer&&r.mode===mode));
      if(rows[0].status==='finite_marked_proof_region'&&rows[2].status==='finite_marked_proof_region'&&rows[2].metrics.attempts<rows[0].metrics.attempts)improvements.push(c.id+' '+mode);
      return '<tr><td>'+escapeHtml(c.title)+'</td><td>'+mode+'</td>'+rows.map(r=>'<td>'+math(String(r.metrics.attempts||0))+(r.status==='unknown_search_budget'?' · unknown':'')+'</td>').join('')+'</tr>';
    })).join('');
    $('result-heading').textContent=improvements.length?'Conditional markings change some search paths.':'Four marking layers, no observed placement saving.';
    $('result-assessment').innerHTML='<p>'+math(String(improvements.length))+' lanes show fewer attempts with conditional markings than their original counterpart. The difficult five-link fixed-order control instead needs '+math(String(evidence.cases.find(c=>c.id==='renamed-five').observations.find(r=>r.layer==='conditional'&&r.mode==='fixed').metrics.attempts))+' attempts, compared with '+math(String(evidence.cases.find(c=>c.id==='renamed-five').observations.find(r=>r.layer==='original'&&r.mode==='fixed').metrics.attempts))+'. These are placement counts in the recorded paired runs, with both gains and regressions retained. They do not establish a cold timing advantage or a generally better learned policy.</p>';
    $('all-results').textContent=JSON.stringify(evidence.cases.map(c=>({case:c.id,observations:c.observations,overlays:c.overlay_checks,smt_control:c.smt_control})),null,2);
    $('learning-costs').innerHTML='<div class="scroll-table"><table><thead><tr><th>Declaration</th><th>Pair catalog</th><th>Genuine conditional negatives</th><th>Unary collection</th><th>Pair collection</th><th>Fresh native checks</th></tr></thead><tbody>'+evidence.cases.map(c=>'<tr><td>'+escapeHtml(c.title)+'</td><td>'+math(String(c.probes.length))+' queries</td><td>'+math(String(c.probes.filter(p=>p.genuine).length))+'</td><td>'+math(c.unary_learning_seconds.toFixed(3))+' seconds</td><td>'+math(c.pair_learning_seconds.toFixed(3))+' seconds</td><td>'+math(c.fresh_native_seconds.toFixed(3))+' seconds</td></tr>').join('')+'</tbody></table></div><p>Collection times include immediate independent teacher replay. The complete pilot pipeline took '+math(evidence.pilot_seconds.toFixed(3))+' seconds, including repeated pre-activation checks, model construction, native work and artifact output. The later independent study audit took '+math(evidence.audit.seconds.toFixed(3))+' seconds in addition. These are recorded research-pipeline costs, not a matched cold timing benchmark.</p>';
    const a=evidence.audit;$('audit-summary').innerHTML='Independent replay covers '+math(String(a.teacher_nodes))+' teacher nodes, '+math(String(a.point_nodes))+' search nodes, '+math(String(a.events))+' policy decisions, '+math(String(a.hints))+' hints and '+math(String(a.native_queries))+' fresh native computations.';
    $('artifact-links').innerHTML=evidence.artifacts.map(f=>'<p><a href="'+escapeHtml(f.path)+'">'+escapeHtml(f.path)+'</a> · <code>'+escapeHtml(f.sha256)+'</code></p>').join('');
    $('case-control').addEventListener('change',showCase);$('probe-control').addEventListener('change',showProbe);$('proof-control').addEventListener('change',showProof);showCase();
    $('reader-status').textContent='Loaded: complete declared pair catalogs, exact conditional values, representative words and every displayed selected proof checked against the audited projection. Native computations were independently replayed outside the browser.';
  }catch(e){$('reader-status').textContent='Evidence rejected: '+e.message;throw e;}
}
main();
