'use strict';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function familyOf(r){
 if(r.kind==='copy')return {kind:'copy'};
 if(r.kind==='primitive')return {kind:'primitive',operation:r.witness.rule};
 const f={kind:'block',operation:r.operation};if(r.operation.endsWith('rewrite'))Object.assign(f,{axiom:r.axiom,direction:r.move.direction});return f;
}
function equalEntries(a,b){return a.length===b.length&&a.every(([p,v])=>b.some(([q,w])=>same(p,q)&&same(v,w)));}
function validateClusterRow(p,library){
 if(p.tiles.length!==p.length||!p.groups.length)throw Error('Incomplete row');
 const bySlot=new Map(),globalMarks=new Map();
 p.tiles.forEach((t,j)=>{
  if(t.slot!==j||!same(t.formula,p.formulas[t.formula_id]))throw Error('Changed formula or position');
  if(!same(t.weights,[[[2*j,0],12]]))throw Error('Changed base occupancy');
  if(t.refs.length!==t.input_ids.length||t.refs.some((k,i)=>!Number.isInteger(k)||k<0||k>=j||p.tiles[k].formula_id!==t.input_ids[i]))throw Error('Changed premise receptor');
  const expected=new Map([[`${2*j},1`,t.formula_id],[`${2*j},2`,t.candidate],[`${2*j},4`,0]]);
  t.refs.forEach((k,i)=>{expected.set(`${2*k},1`,t.input_ids[i]);expected.set(`${2*k},4`,0);});
  const actual=new Map(t.marks.map(([q,v])=>[q.join(','),v]));
  if(actual.size!==t.marks.length||actual.size!==expected.size||[...expected].some(([q,v])=>actual.get(q)!==v))throw Error('Changed marking layer');
  t.marks.forEach(([q,v])=>{const k=q.join(',');if(globalMarks.has(k)&&globalMarks.get(k)!==v)throw Error('Disagreeing marks');globalMarks.set(k,v);});
  if(!same(p.request.proof[t.root_line]?.formula,t.formula))throw Error('Changed certificate binding');
  bySlot.set(j,t);
 });
 const covered=new Set(),owners=new Set();
 for(const g of p.groups){
  if(owners.has(g.candidate)||!g.members.length)throw Error('Duplicate owner');owners.add(g.candidate);
  const slots=new Set(g.members.map(k=>k[0])),weights=[],marks=new Map(),incoming=new Map(),outgoing=[];
  const outsideRefs=new Set(p.tiles.filter(t=>!slots.has(t.slot)).flatMap(t=>t.refs));
  for(const [slot,rid,refs] of g.members){
   const t=bySlot.get(slot);if(!t||covered.has(slot)||t.candidate!==g.candidate||t.rule_id!==rid||!same(t.refs,refs))throw Error('Changed cluster member');covered.add(slot);
   weights.push(...t.weights);t.marks.forEach(([q,v])=>{const k=q.join(',');if(marks.has(k)&&marks.get(k)[1]!==v)throw Error('Internal conflict');marks.set(k,[q,v]);});
   t.refs.forEach((ref,i)=>{if(!slots.has(ref))incoming.set(ref,t.input_ids[i]);});
   if(outsideRefs.has(slot)||slot===p.length-1)outgoing.push([slot,t.formula_id]);
  }
  if(!equalEntries(weights,g.weights)||!equalEntries([...marks.values()],g.marks)||!equalEntries([...incoming],g.incoming)||!equalEntries(outgoing,g.outgoing))throw Error('Changed aggregate or exposed receptors');
  if(g.item){
   if(!same(g.item.members,g.members)||!g.item.patterns.length)throw Error('Changed family instance');
   for(const name of g.item.patterns){
    const f=library.find(x=>x.name===name);if(!f||f.nodes.length!==g.members.length)throw Error('Unknown family');
    f.nodes.forEach((node,i)=>{const [slot,rid,refs]=g.members[i],t=bySlot.get(slot);if(slot!==g.item.start+node.offset||!same(refs,node.refs.map(k=>g.item.start+k))||!same(familyOf(t.recipe),node.family))throw Error('Changed translated family');});
   }
  }else if(g.members.length!==1)throw Error('Missing family provenance');
 }
 if(covered.size!==p.length||!same(p.tiles.at(-1).formula[2],p.goal)||!same(p.request.proof.at(-1).formula,p.target)||!same(p.primitive.at(-1).formula,p.target)||p.native.status!=='accepted')throw Error('Changed conclusion/acceptance');
 return true;
}
function hilbertName(x){
 if(x==='u')return '\\ell';if(x==='v')return 'm';if(x==='equalityHole')return 'z';
 if(/^l[0-9]+$/.test(x))return '\\ell_{'+x.slice(1)+'}';
 if(/^p[0-9]+$/.test(x))return 'P_{'+x.slice(1)+'}';
 return /^(fresh|[a-zA-Z]+)([0-9]+)$/.test(x)?'\\operatorname{'+x.replace(/[0-9]+$/,'')+'}_{'+x.match(/[0-9]+$/)[0]+'}':x.replace(/[^a-zA-Z0-9]/g,'');
}
function hilbertFormula(a){
 const k=a[0];
 if(k==='var')return hilbertName(a[1]);
 if(k==='bot')return '\\bot';
 if(k==='eq')return hilbertFormula(a[1])+'='+hilbertFormula(a[2]);
 if(k==='all')return '\\forall '+hilbertName(a[1])+'\\;('+hilbertFormula(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+hilbertName(a[1][1])+'\\;('+hilbertFormula(a[1][2][1])+')';
 if(k==='not')return '\\neg('+hilbertFormula(a[1])+')';
 if(k==='pred')return '\\operatorname{'+a[1].replace(/[^a-zA-Z]/g,'')+'}('+a[2].map(hilbertFormula).join(',')+')';
 if(['imp','and','or'].includes(k))return '('+hilbertFormula(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+hilbertFormula(a[2])+')';
 throw Error('Unsupported formula');
}
function hilbertEnglish(a){
 const name=x=>x==='u'?'the first line':x==='v'?'the second line':x.toUpperCase();
 if(a[0]==='var')return name(a[1]);
 if(a[0]==='bot')return 'a contradiction';
 if(a[0]==='eq')return name(a[1][1])+' and '+name(a[2][1])+' are the same object';
 if(a[0]==='all')return 'for every object assigned to '+name(a[1])+', ['+hilbertEnglish(a[2])+']';
 if(a[0]==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return 'there is an object '+name(a[1][1])+' such that ['+hilbertEnglish(a[1][2][1])+']';
 if(a[0]==='not'&&a[1][0]==='eq')return name(a[1][1][1])+' and '+name(a[1][2][1])+' are distinct objects';
 if(a[0]==='not')return 'it is false that ['+hilbertEnglish(a[1])+']';
 if(a[0]==='and')return hilbertEnglish(a[1])+'; and '+hilbertEnglish(a[2]);
 if(a[0]==='or')return '['+hilbertEnglish(a[1])+'] or ['+hilbertEnglish(a[2])+']';
 if(a[0]==='imp')return 'if ['+hilbertEnglish(a[1])+'], then ['+hilbertEnglish(a[2])+']';
 const xs=a[2].map(x=>name(x[1]));
 if(a[1]==='Point')return xs[0]+' is a point';
 if(a[1]==='Line')return xs[0]+' is a line';
 if(a[1]==='Inc')return xs[0]+' lies on '+xs[1];
 return 'relation '+a[1]+' holds of '+xs.join(', ');
}
if(typeof module!=='undefined')module.exports={validateClusterRow,hilbertFormula,hilbertEnglish};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const math=a=>'\\('+hilbertFormula(a)+'\\)',number=x=>Number(x).toFixed(3);
 const titles={'line-has-point':'Source: every line contains a point','unique-joining-line':'Recipient: two distinct points have a unique joining line','joining-exists-reordered':'Recipient: a joining line, with reordered conditions'};
 let data,p,selected=0;
 const typeset=nodes=>{if(window.MathJax?.typesetPromise)MathJax.typesetPromise(nodes).catch(e=>{el('load').textContent=e.message;});};
 function reason(t){
  const r=t.recipe,refs=t.refs.map(j=>'cell '+(j+1)).join(' and ');
  if(r.kind==='copy')return 'Repeat '+refs+'.';
  if(r.kind==='primitive')return r.witness.rule==='generalize'?'Universally generalize the free parameter '+r.witness.variable+' in '+refs+'. Temporary witness conditions stay inside the formula.':'Propositional logic establishes the complete conditional formula.';
  const q=r.inference;
  if(r.operation==='exists-introduce')return 'Introduce an existential quantifier from '+refs+' using the free parameter '+q.variable+'.';
  if(r.operation==='exists-eliminate')return 'Discharge the witness '+q.variable+' from '+refs+'. It is absent from the outer context and conclusion; the input is already universally quantified.';
  if(r.operation==='forall-scope')return 'Move the quantified conditional in '+refs+' into a context that does not contain its quantified variable.';
  if(r.operation==='forall-distribute')return 'Distribute the universal quantifier from '+refs+' through a context without that variable.';
  if(r.operation==='propositional')return 'Combine or rearrange the complete conditional formulas from '+refs+' by propositional logic.';
  if(r.operation==='axiom-clause')return 'Apply '+q.row.axiom+' with '+refs+'. Source binders are instantiated with capture avoidance.';
  throw Error('Unsupported inference '+r.operation);
 }
 function svg(){
  const width=Math.max(960,p.length*100+80),left=(width-100*p.length)/2,xy=q=>[left+50+q[0]*50,280-q[1]*50],active=p.tiles[selected],group=p.groups.find(g=>g.candidate===active.candidate);
  const shown=el('view').value==='cluster'?p.tiles.filter(t=>t.candidate===group.candidate):p.tiles;
  const text=(x,y,s)=>`<text x="${x}" y="${y}" text-anchor="middle">${esc(s)}</text>`;
  let shapes='',paths='',ports='',outlines='';
  p.tiles.forEach((t,j)=>{const [x,y]=xy([2*j,0]);shapes+=`<rect x="${x-50}" y="${y-50}" width="100" height="100" fill="${j===selected?'#e2ecf5':'#f0f4ee'}" stroke="${j===selected?'#246aa2':'#a7b8aa'}" stroke-width="${j===selected?3:1}"/>`+text(x,y+24,'Cell '+(j+1));if(shown.includes(t))shapes+=`<circle cx="${x}" cy="${y}" r="4" fill="#303d38"/>`;});
  p.groups.filter(g=>g.item&&(el('view').value==='row'||g.candidate===group.candidate)).forEach(g=>{const slots=g.members.map(k=>k[0]),x1=xy([2*Math.min(...slots),0])[0]-45,x2=xy([2*Math.max(...slots),0])[0]+45;
   outlines+=`<path d="M${x1} 355 H${x2}" stroke="#8450a0" stroke-width="2" stroke-dasharray="5 4"/>`;
   slots.forEach(j=>{const [x,y]=xy([2*j,0]);outlines+=`<rect x="${x-45}" y="${y-45}" width="90" height="90" rx="5" fill="none" stroke="#8450a0" stroke-width="${g.candidate===group.candidate?3:1.5}"/>`;});
  });
  const guides=shown.filter(t=>t.candidate===group.candidate);guides.forEach(t=>{const [ox,oy]=xy([2*t.slot,0]);t.refs.forEach(j=>{const [x,y]=xy([2*j,1]);paths+=`<path d="M${ox} ${oy-8} C${ox} 145 ${x} 145 ${x} ${y}" fill="none" stroke="#246aa2" stroke-width="2" stroke-dasharray="6 4"/>`;});});
  const union=new Map();shown.forEach(t=>t.marks.forEach(([q,v])=>union.set(q.join(','),{q,v})));
  union.forEach(({q,v})=>{const [x,y]=xy(q),w=group.marks.some(([r])=>same(q,r))?3:1.5;
   if(q[1]===1)ports+=`<circle cx="${x}" cy="${y}" r="12" fill="#e3eff8" stroke="#246aa2" stroke-width="${w}"/>`+text(x,y+30,'F'+v);
   if(q[1]===2)ports+=`<rect x="${x-8}" y="${y-8}" width="16" height="16" fill="#e0ede5" stroke="#28745c" stroke-width="${w}"/>`+text(x,y-16,'O'+v);
   if(q[1]===4)ports+=`<path d="M${x} ${y-10} l10 10 -10 10 -10 -10 Z" fill="#fff2cd" stroke="#aa7418" stroke-width="${w}"/>`+text(x,y-17,'R'+v);
  });
  return `<svg viewBox="0 0 ${width} 410" role="img" aria-label="Actual directed proof cells and learned clusters with exact colored point markings"><style>text{font:12px system-ui;fill:#30423a}</style>${shapes}${paths}${ports}${outlines}${text(width/2,393,'Translation only. Gaps are not occupied by a spanning cluster; its contacts can reach them.')}</svg>`;
 }
 function select(j){
  selected=j;el('cell').value=String(j);el('tile-svg').innerHTML=svg();const t=p.tiles[j],g=p.groups.find(x=>x.candidate===t.candidate);
  el('selected-reading').innerHTML=`<strong>Cell ${j+1} · formula ID F${t.formula_id}</strong><div class="equation">${math(t.formula)}</div><p>${esc(hilbertEnglish(t.formula))}.</p><p>${reason(t)}</p>`;
  const ports=(xs)=>xs.length?xs.map(([slot,f])=>`<div><strong>Cell ${slot+1} · F${f}</strong><div class="equation">${math(p.formulas[f])}</div></div>`).join(''):'<p>None.</p>';
  el('selected-cluster').innerHTML=`<strong>${g.item?'Learned cluster':'Base tile'} · owner O${g.candidate}</strong><p>Occupies cells ${g.members.map(k=>k[0]+1).join(', ')}.</p><h4>Incoming receptors</h4>${ports(g.incoming)}<h4>Outgoing receptors used by this proof</h4>${ports(g.outgoing)}${g.item?'<p>Learned family: '+g.item.patterns.map(esc).join(', ')+'. All constituents are original checked inference tiles.</p>':''}`;
  el('tile-values').textContent=JSON.stringify({t_values:g.weights.map(([q,v])=>[q,v/12]),m_values:g.marks,expansion:g.members,family_instance:g.item},null,2);typeset([el('selected-reading'),el('selected-cluster')]);
 }
 function proofLines(){
  const lines=el('proof-level').value==='primitive'?p.primitive:p.request.proof;
  el('proof-count').textContent=lines.length+' checked lines. References point to earlier lines; full formulas and English are shown.';
  const ref=j=>`<button class="reference" data-ref="${j}" type="button">line ${j+1}</button>`;
  el('proof-lines').innerHTML=lines.map((l,i)=>{
   const why=l.rule==='mp'?'Modus ponens: '+ref(l.antecedent)+' and '+ref(l.implication):l.rule==='generalize'?'Universal generalization from '+ref(l.source):l.rule==='block'?'Checked compiled inference'+(l.inputs.length?' using '+l.inputs.map(ref).join(', '):''):l.rule==='axiom'?'Declared axiom '+esc(l.name):l.rule==='eq_subst'?'Logical equality substitution':l.rule==='instantiate'?'Universal instantiation':l.rule==='tautology'?'Propositional tautology':esc(l.rule);
   return `<div class="proof-line" id="proof-line-${i}"><span>${i+1}</span><div><div class="equation">${math(l.formula)}</div><p>${esc(hilbertEnglish(l.formula))}.</p><p class="small">${why}.</p></div></div>`;
  }).join('');
  el('proof-lines').querySelectorAll('[data-ref]').forEach(b=>b.addEventListener('click',()=>{const row=el('proof-line-'+b.dataset.ref);document.querySelectorAll('.proof-line.flash').forEach(x=>x.classList.remove('flash'));row.classList.add('flash');row.scrollIntoView({behavior:'smooth',block:'nearest'});}));typeset([el('proof-lines')]);
 }
 function choose(i){
  p=data.proofs[i];el('theorem').value=String(i);validateClusterRow(p,data.library);el('theorem-title').textContent=titles[p.id];el('target').innerHTML=math(p.target);el('hypotheses').innerHTML='\\(\\Gamma:='+hilbertFormula(p.hypothesis)+'\\)';
  el('proof-origin').textContent=p.length+' proof cells selected by '+p.lane+'; '+p.groups.filter(g=>g.item).length+' actual learned clusters; '+p.primitive_lines+' primitive lines; complete native acceptance. No coordinates or witness oracle enter search.';
  el('cell').innerHTML=p.tiles.map((t,j)=>`<option value="${j}">Cell ${j+1} · F${t.formula_id}${p.groups.find(g=>g.candidate===t.candidate).item?' · learned cluster':''}</option>`).join('');
  el('row-reading').innerHTML=p.tiles.map((t,j)=>`<article class="reading"><button type="button" data-cell="${j}">Cell ${j+1}</button><div><div class="equation">${math(t.formula)}</div><p>${esc(hilbertEnglish(t.formula))}.</p><p class="small">${reason(t)}</p></div></article>`).join('');
  el('row-reading').querySelectorAll('[data-cell]').forEach(b=>b.addEventListener('click',()=>select(Number(b.dataset.cell))));el('closure').textContent=p.variables.length+' checked universal generalizations close the theorem after the row. These closure steps do not fill additional occupancy cells.';
  el('axioms').innerHTML=Object.entries(p.theory.axioms).map(([n,a])=>`<div class="axiom"><strong>${esc(n)}</strong><div class="equation">${math(a)}</div></div>`).join('');el('certificate').textContent=JSON.stringify(p.request,null,2);select(0);proofLines();typeset([el('target'),el('hypotheses'),el('row-reading'),el('axioms')]);
 }
 function sketch(){
  const separated=el('receptor-layout').value==='spaced',xs=separated?[80,260,540,760]:[120,280,440,600],names=['Existence fact','Local witness proof','Discharge family','Conclusion'];
  const text=(x,y,s)=>`<text x="${x}" y="${y}" text-anchor="middle">${s}</text>`;
  el('receptor-sketch').innerHTML='<svg class="diagram-sketch" viewBox="0 0 900 240" role="img" aria-label="Proposed receptor family layouts, a design sketch"><style>text{font:13px system-ui;fill:#30423a}</style>'+xs.map((x,i)=>`<rect x="${x-55}" y="135" width="110" height="65" fill="${i===2?'#f3edfa':'#edf2e9'}" stroke="${i===2?'#8450a0':'#a7b8aa'}"/>${text(x,176,names[i])}<circle cx="${x}" cy="105" r="11" fill="#e3eff8" stroke="#246aa2" stroke-width="2"/><rect x="${x-7}" y="66" width="14" height="14" fill="#e0ede5" stroke="#28745c"/><path d="M${x} 24 l9 9 -9 9 -9 -9 Z" fill="#fff2cd" stroke="#aa7418"/>`).join('')+`<path d="M${xs[0]} 105 Q${(xs[0]+xs[2])/2} 10 ${xs[2]} 105 M${xs[1]} 105 Q${(xs[1]+xs[2])/2} 60 ${xs[2]} 105 M${xs[2]} 105 Q${(xs[2]+xs[3])/2} 55 ${xs[3]} 105" fill="none" stroke="#246aa2" stroke-width="2" stroke-dasharray="5 4"/>`+text(450,229,'Same typed interface; different positions and marking reach. Proposed, not measured.')+'</svg>';
 }
 const status=s=>s==='finite_exact_proof_tiling'?'Checked proof':s==='unknown_search_budget'?'Budget cutoff':'Finite grammar exhausted';
 async function main(){
  const response=await fetch('hilbert-cluster-reader-001.json?v=20261010-c1.1');if(!response.ok)throw Error('Dataset HTTP '+response.status);data=await response.json();
  if(data.audit.status!=='passed')throw Error('Complete independent audit required');data.proofs.forEach(p=>validateClusterRow(p,data.library));
  el('load').textContent='Three audited GCTS proofs · '+data.library.length+' learned families · 29 fully audited source/recipient records.';
  el('theorem').innerHTML=data.proofs.map((p,i)=>`<option value="${i}">${esc(titles[p.id])}</option>`).join('');
  el('theorem').addEventListener('change',()=>choose(Number(el('theorem').value)));el('cell').addEventListener('change',()=>select(Number(el('cell').value)));el('view').addEventListener('change',()=>select(selected));el('proof-level').addEventListener('change',proofLines);el('receptor-layout').addEventListener('change',sketch);el('previous').addEventListener('click',()=>select(Math.max(0,selected-1)));el('next').addEventListener('click',()=>select(Math.min(p.length-1,selected+1)));
  const unique=data.results.filter(r=>r.id==='unique-joining-line'),reordered=data.results.filter(r=>r.id==='joining-exists-reordered');
  el('finding').textContent='Both joining-line replicas: GCTS with learned families finds the proof in 19 states and 22 expanded placement attempts; GCTS without them reaches its 30-second search budget. CSP uses 12 states without families and 7 with them. On reordered existence, GCTS falls from 901 to 195 states; CSP from 22 to 3. These are two selected transfer statements within a calibrated bounded grammar.';
  el('library-summary').textContent=data.library.length+' family schemas, '+data.audit.library.source_occurrences+' connected source occurrences, mined after complete native acceptance of one freshly discovered 10-cell line/point proof. No earlier proof or library was read.';
  el('family-list').innerHTML=data.library.map(f=>`<article><strong>${f.size} cells · span ${f.span}</strong><p>${f.nodes.map(n=>esc(n.family.operation||n.family.kind)).join(' → ')}</p><code>${esc(f.name)}</code><p class="small">Source cells: ${f.sources.map(s=>s.members.map(k=>k[0]+1).join(', ')).join('; ')}.</p><details><summary>Exact receptor offsets and provenance</summary><pre>${esc(JSON.stringify(f,null,2))}</pre></details></article>`).join('');
  el('training-cost').textContent='Fresh source discovery, checking, mining and storage: '+number(data.training_seconds)+' s, charged once to either cluster lane. Native compiler: '+number(data.compile_seconds)+' s; subsequent independent audit: '+number(data.audit.seconds)+' s, both separate shared costs. Query cold time includes catalog, search, decode, primitive replay and native checking. The first-query column adds fresh learning to cluster lanes.';
  el('comparison-table').innerHTML='<table><thead><tr><th>Statement/control</th><th>Replica</th><th>Lane</th><th>Result</th><th>States</th><th>Expanded attempts</th><th>Family instances</th><th>Join (s)</th><th>Search (s)</th><th>Native (s)</th><th>Cold query (s)</th><th>First query (s)</th></tr></thead><tbody>'+data.results.map(r=>`<tr><td>${esc(r.id)}</td><td>${r.replica+1}</td><td>${esc(r.lane)}</td><td>${status(r.status)}</td><td>${r.states}</td><td>${r.attempts}</td><td>${r.motif_instances}</td><td>${number(r.instantiation_seconds)}</td><td>${number(r.search_seconds)}</td><td>${number(r.native_seconds)}</td><td>${number(r.cold_seconds)}</td><td>${number(r.first_query_seconds)}</td></tr>`).join('')+'</tbody></table>';
  el('experiment-scope').textContent=data.scope;
  const a=data.arithmetic;el('arithmetic-comparison').innerHTML='<p>Fresh source discovery/mining: '+number(a.discovery_seconds)+' s; additional RL learning: '+number(a.rl_learning_seconds)+' s.</p><table><thead><tr><th>Replica</th><th>Lane</th><th>Successor-addition result</th><th>States</th><th>Cold query (s)</th></tr></thead><tbody>'+a.runs.map(r=>`<tr><td>${r.replica+1}</td><td>${esc(r.lane)}</td><td>${status(r.status)}</td><td>${r.states}</td><td>${number(r.cold_seconds)}</td></tr>`).join('')+'</tbody></table>';
  el('archives').innerHTML='<ul>'+data.archive_descriptors.map(d=>`<li><a href="${esc(d.file)}">${esc(d.id)}: full catalog and lossless traces</a> (${(d.bytes/1048576).toFixed(2)} MiB compressed)</li>`).join('')+'</ul>';
  sketch();choose(1);select(p.groups.find(g=>g.item).members[0][0]);
 }
 main().catch(e=>{el('load').textContent='Reader stopped: '+e.message;});
}
