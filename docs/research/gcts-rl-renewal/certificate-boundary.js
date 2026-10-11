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
const SAME=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function validateBoundary(v){
 if(v.version!=='certificate-boundary-reader-001'||v.audit.status!=='passed'||v.inventory.fingerprint!=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455'||v.inventory.symbols!==60||v.inventory.states!==462276)throw Error('Fixed palette/audit changed');
 if(v.cases.length!==7||v.observations.length!==28||v.proofs.length!==4)throw Error('Experiment coverage changed');
 for(const p of v.proofs){
  const c=v.cases.find(c=>c.id===p.case);if(!c||!SAME(c.target,p.request.target)||!SAME(c.theory,p.request.theory)||p.request.blocks.length||p.request.proof.length!==c.length||p.lines.length!==c.length)throw Error('Assertion/proof binding changed');
  if(p.builder.status!=='accepted'||p.literal.status!=='accepted'||p.checker.result!=='accepted'||p.builder.micro_steps!==p.literal.micro_steps||p.builder.micro_steps!==p.checker.micro_steps||p.builder.physical_steps!==p.literal.physical_steps||p.builder.physical_steps!==p.checker.physical_steps)throw Error('Full native acceptance changed');
  const tr=p.trace;if(tr.status!=='native_proof_discovered'||tr.case.id!==p.case||!SAME(tr.found.proof,p.request.proof)||!SAME(tr.records[tr.found.query].request,p.request)||tr.records[tr.found.query].query_target!=='fixed_assertion'||tr.records[tr.found.query].result.status!=='accepted'||!tr.root_path_restored)throw Error('Discovered certificate source changed');
  p.lines.forEach((l,j)=>{
   const cmd=p.request.proof[j];if(l.outcome!=='line-checked'||l.label.scope!=='root'||l.label.line!==j||l.label.rule!==cmd.rule||!SAME(l.label.formula,cmd.formula)||!SAME(l.input.pending,p.request.proof.slice(j))||!SAME(l.input.proved,p.request.proof.slice(0,j).map(c=>c.formula))||!SAME(l.output.proved,p.request.proof.slice(0,j+1).map(c=>c.formula))||!SAME(l.output.pending,p.request.proof.slice(j+1)))throw Error('Actual line context changed');
   for(const ctx of [l.input,l.output])if(!SAME(ctx.theory,p.request.theory)||!SAME(ctx.target,p.request.target)||ctx.assumptions.length||ctx.registry.length||ctx.forbidden.length)throw Error('Actual theory/scope changed');
   if(l.q!==1688||l.out!==1688||l.micro_steps<=0||l.physical_height<=0||l.literal_width<=0)throw Error('Fragment receptor changed');
   const patch=l.patch;if(patch.width!==9||patch.height!==3||patch.rows.length!==4||patch.tiles.length!==27||patch.trajectory[0][0]!==6746||patch.prefix_physical_steps!==l.input_head+patch.marker+1||patch.prefix_physical_steps+3>l.physical_height)throw Error('Native crop changed');
   const seen=new Set();for(const t of patch.tiles){const at=t.x+','+t.y;if(seen.has(at)||t.x<0||t.x>=9||t.y<0||t.y>=3)throw Error('Tile occupancy changed');seen.add(at);const triple=patch.rows[t.y].slice(t.x,t.x+3),n=coreOutput(v,triple);if(!SAME(t.triple,triple)||t.identity!==triple.join(':')||t.S!==triple[1]||t.N!==n||n!==patch.rows[t.y+1][t.x+1]||!SAME(t.W,triple.slice(0,2))||!SAME(t.E,triple.slice(1)))throw Error('Native point values changed');}
  });
 }
 return {proofs:v.proofs.length,lines:v.proofs.reduce((n,p)=>n+p.lines.length,0),tiles:v.proofs.reduce((n,p)=>n+p.lines.length*27,0),queries:v.audit.queries,observations:v.observations.length};
}
if(typeof module!=='undefined')module.exports={validateBoundary,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),math=a=>'\\('+formula(a)+'\\)';let view,chosen=2,index=0;
 const refs=c=>c.rule==='mp'?[c.antecedent,c.implication]:c.rule==='generalize'?[c.source]:[];
 const english=c=>reason[c.rule]+(c.rule==='axiom'?` Input premise “${c.name}”.`:refs(c).length?` Earlier ${refs(c).length===1?'line':'lines'} ${refs(c).map(i=>i+1).join(' and ')}.`:'');
 function colors(v,layer){let n=0;for(const x of Array.isArray(v)?v:[v])n=(Math.imul(n,31)+x)>>>0;return `hsl(${(layer==='vertical'?205:140)+n%30} 58% ${38+n%24}%)`;}
 function draw(){
  const p=view.proofs[chosen].lines[index].patch,mode=el('layer').value,s=75,ox=38,oy=22;let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ox+p.width*s+15} ${oy+p.height*s+20}" role="img" aria-label="Actual native square tiles at the discovered proof line"><text x="4" y="14" font-size="12">time ↑</text>`;
  for(const t of p.tiles){const x=ox+t.x*s,y=oy+(p.height-1-t.y)*s,c=(v,l)=>mode==='all'||mode===l?colors(v,l):'#dfe5df';svg+=`<g><rect x="${x+1}" y="${y+1}" width="73" height="73" fill="${t.triple.some(v=>v>=60)?'#fff3d9':'#f8faf5'}" stroke="#acb9ad"/><rect x="${x+8}" y="${y+2}" width="59" height="7" fill="${c(t.N,'vertical')}"/><rect x="${x+8}" y="${y+66}" width="59" height="7" fill="${c(t.S,'vertical')}"/><rect x="${x+2}" y="${y+10}" width="7" height="55" fill="${c(t.W,'horizontal')}"/><rect x="${x+66}" y="${y+10}" width="7" height="55" fill="${c(t.E,'horizontal')}"/><circle cx="${x+37.5}" cy="${y+37.5}" r="3" fill="#242a28"/><text x="${x+37.5}" y="${y+25}" text-anchor="middle" font-size="9" font-family="monospace">N ${t.N}</text><text x="${x+37.5}" y="${y+57}" text-anchor="middle" font-size="9" font-family="monospace">S ${t.S}</text></g>`;}el('literal').innerHTML=svg+'</svg>';
 }
 function dependencies(p){
  let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 430 '+(p.lines.length*75+25)+'" role="img" aria-label="Symbolic proof dependency receptors">';p.request.proof.forEach((c,j)=>{const y=20+j*75;svg+=`<rect x="18" y="${y}" width="280" height="48" rx="5" fill="${j===index?'#e8dcef':'#f3f6ef'}" stroke="#ccd4c7"/><text x="35" y="${y+20}" font-size="14">Line ${j+1} · ${esc(c.rule)}</text><text x="35" y="${y+37}" font-size="11">${esc(c.rule==='axiom'?'Input premise '+c.name:refs(c).length?'Earlier lines '+refs(c).map(i=>i+1).join(' and '):reason[c.rule])}</text>`;refs(c).forEach((i,k)=>{const x=340+k*28;svg+=`<path d="M 298 ${44+i*75} H ${x} V ${44+j*75} H 300" stroke="#8654a0" stroke-width="3" fill="none"/><circle cx="298" cy="${44+i*75}" r="4" fill="#8654a0"/><circle cx="298" cy="${44+j*75}" r="4" fill="#8654a0"/>`;});});el('dependencies').innerHTML=svg+'</svg>';
 }
 function read(){
  const p=view.proofs[chosen],l=p.lines[index],cmd=p.request.proof[index];el('reading').innerHTML=`<p class="small">Actual native checkpoint · root line ${index+1} · checked</p><div class="formula">${math(cmd.formula)}</div><p>${esc(english(cmd))}</p>`;el('input').innerHTML=`<p>${l.input.proved.length} earlier facts.</p>`+l.input.proved.map(a=>`<div class="formula">${math(a)}</div>`).join('');el('output').innerHTML=`<p>Append the checked formula. ${l.output.proved.length} facts are available.</p><div class="formula">${math(cmd.formula)}</div>`;el('expansion').textContent=`The complete line fragment expands to ${l.micro_steps.toLocaleString()} selected-symbol operations and ${l.physical_height.toLocaleString()} literal transitions, across ${l.literal_width.toLocaleString()} columns. The compression checker derives that entire expansion.`;el('context').textContent=JSON.stringify({command:cmd,input:l.input,output:l.output,node:l.node,native_entry_state:l.q,native_exit_state:l.out},null,2);el('artifacts').innerHTML=`Whole accepting certificate: <a href="${p.grammar.name}">response grammar</a> · <a href="${p.events.name}">native checkpoints</a> · <a href="${p.responses.name}">derived interfaces</a>.`;draw();dependencies(p);window.MathJax?.typesetPromise?.([el('reading'),el('input'),el('output')]).catch(e=>el('load').textContent=e.message);
 }
 function show(){
  const p=view.proofs[chosen],c=view.cases.find(c=>c.id===p.case);index=0;el('theorem').innerHTML=`<div class="formula">${math(p.request.target)}</div><p>${esc(c.scope)}</p>`;el('premises').innerHTML=Object.entries(p.request.theory.axioms).map(([n,a])=>`<p><code>${esc(n)}</code> ${math(a)}</p>`).join('')||'<p>No input axioms.</p>';el('lines').innerHTML=p.request.proof.map((cmd,j)=>`<div class="proof-line"><span>Line ${j+1}</span><div class="formula">${math(cmd.formula)}</div><p>${esc(english(cmd))}</p></div>`).join('');el('proof-line-control').innerHTML=p.lines.map((l,j)=>`<option value="${j}">Line ${j+1} · ${l.label.rule}</option>`).join('');const tr=p.trace;el('trace-summary').textContent=`Prefix control tried ${tr.nodes} command assignments and requested ${tr.queries} complete native computations. The chosen command path is ${tr.found.path.map(i=>i+1).join(', ')} in the declared per-slot domains.`;el('query-table').innerHTML=tr.records.map(r=>`<tr><td>${r.id+1}</td><td>${r.request.proof.length}</td><td>${r.query_target==='fixed_assertion'?'Final assertion':'Prefix last formula'}</td><td>${r.result.status}</td><td>${r.result.micro_steps.toLocaleString()}</td></tr>`).join('');el('trace').textContent=JSON.stringify({grammar:tr.grammar,events:tr.events,records:tr.records},null,2);read();window.MathJax?.typesetPromise?.([el('theorem'),el('premises'),el('lines')]).catch(e=>el('load').textContent=e.message);
 }
 async function boot(){try{
  const r=await fetch('certificate-boundary-reader-001.json?v=20261010-cb2');if(!r.ok)throw Error('HTTP '+r.status);view=await r.json();const checked=validateBoundary(view);el('load').textContent=`Independent audit passed · ${checked.proofs} discovered proofs · ${checked.lines} native proof lines · ${checked.tiles} checked displayed squares`;el('case').innerHTML=view.proofs.map((p,j)=>`<option value="${j}">${esc(view.cases.find(c=>c.id===p.case).title)}</option>`).join('');el('results').innerHTML=view.observations.map(o=>`<tr><td>${esc(o.case)}</td><td>${o.mode}</td><td>${o.repetition}</td><td>${o.status.replaceAll('_',' ')}</td><td>${o.queries}</td><td>${o.cold_seconds.toFixed(3)}</td><td>${o.worker_stage_seconds.toFixed(3)}</td><td><a href="${o.artifact.name}">Trace</a></td></tr>`).join('');el('costs').textContent=`Compilation ${view.costs.compile_seconds.toFixed(3)} s; complete production ${view.costs.production_seconds.toFixed(3)} s; independent audit ${view.costs.audit_seconds.toFixed(3)} s. The independent interpreter reran every one of ${view.audit.queries} native queries, including failed attempts and repeated observations; ${view.audit.mutations} tree/binding corruptions were rejected.`;el('case').addEventListener('change',()=>{chosen=Number(el('case').value);show();});el('proof-line-control').addEventListener('change',()=>{index=Number(el('proof-line-control').value);read();});el('layer').addEventListener('change',draw);el('case').value=String(chosen);show();
 }catch(e){el('load').textContent='Validation failed: '+e.message;console.error(e);}}boot();
}
