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
  if(a[1]==='zero')return '0';if(a[1]==='succ')return 'S('+f(a[2][0])+')';
  if(a[1]==='add'||a[1]==='mul')return '('+f(a[2][0])+(a[1]==='add'?'+':'\\cdot ')+f(a[2][1])+')';
  return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 }
 if(k==='pred')return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 if(k==='eq')return f(a[1])+'='+f(a[2]);
 if(k==='all')return '\\forall '+name(a[1])+'\\;('+f(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+name(a[1][1])+'\\;('+f(a[1][2][1])+')';
 if(k==='not')return '\\neg('+f(a[1])+')';
 if(['imp','and','or'].includes(k))return '('+f(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+f(a[2])+')';
 throw Error('Unknown syntax');
}
const reason={axiom:'Use the named axiom from the input theory.',refl:'A term equals itself.',tautology:'This formula is a checked propositional tautology.',instantiate:'Instantiate a universal formula using capture-avoiding substitution.',mp:'Apply the earlier implication to its earlier antecedent.',generalize:'Universally quantify the variable; it is absent from every open premise.',eq_subst:'Substitute equal terms in the indicated formula.',distribute:'Move the quantifier across an implication with the variable condition checked.',induction:'Use the explicitly authorized natural-number induction schema.',assumption:'Use an input premise of this local block.',block:'Apply a previously checked lemma to the matching earlier premises.'};
const FIXED_CORE='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455';
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function validateClusters(v){
 if(v.version!=='logical-wang-clusters-reader-001'||v.audit.status!=='passed'||v.inventory.fingerprint!==FIXED_CORE||v.cases.length!==6)throw Error('Changed experiment identity');
 if(v.inventory.symbols!==60||v.inventory.states!==462276)throw Error('Changed base set');
 const kinds=new Set();
 for(const p of v.cases){
  if(!equal(p.target,p.request.target)||p.provenance.kind!=='reused certificate'||p.builder.micro_steps!==p.checker.micro_steps||p.builder.physical_steps!==p.checker.physical_steps||p.checker.result!==p.result)throw Error('Changed case');
  const seen=new Set();
  for(const l of p.lines){
   const b=p.request.blocks.find(b=>b.name===l.label.scope),proof=l.label.scope==='root'?p.request.proof:b?.proof,j=l.label.line;
   const key=l.label.scope+':'+j;if(seen.has(key)||!proof||!Number.isInteger(j)||j<0||j>=proof.length)throw Error('Changed line placement');seen.add(key);
   if(!equal(proof[j].formula,l.label.formula)||proof[j].rule!==l.label.rule||!equal(l.input.pending,proof.slice(j))||!equal(l.input.proved,proof.slice(0,j).map(x=>x.formula)))throw Error('Changed line context');
   if(!equal(l.input.theory,p.request.theory)||!equal(l.input.target,b?b.conclusion:p.target)||!equal(l.input.assumptions,b?b.premises:[]))throw Error('Changed theory or open premises');
   if(l.q!==1688||!Number.isInteger(l.node)||l.node<0||l.physical_height<1||l.literal_width<1||l.micro_steps<1)throw Error('Changed response dimensions');
   if(l.outcome==='line-checked'){
    kinds.add(l.label.rule);
    if(l.out!==1688||!l.output||!equal(l.output.proved,[...l.input.proved,l.label.formula])||!equal(l.output.pending,l.input.pending.slice(1)))throw Error('Changed checked result');
    for(const k of ['theory','target','assumptions','registry','forbidden'])if(!equal(l.input[k],l.output[k]))throw Error('Changed scope frame');
   }else if(l.outcome!=='line-rejected'||l.output!==null||p.result!=='rejected'||l.out!==1)throw Error('Changed rejection');
   const patch=l.patch;if(patch.width!==9||patch.height!==3||patch.rows.length!==4||patch.tiles.length!==27||patch.trajectory[0][0]!==6746||patch.prefix_physical_steps!==l.input_head+patch.marker+1||patch.prefix_physical_steps+3>l.physical_height)throw Error('Changed crop binding');
   const occupied=new Set();
   patch.tiles.forEach(t=>{
    const at=t.x+','+t.y;if(occupied.has(at)||!Number.isInteger(t.x)||!Number.isInteger(t.y)||t.x<0||t.x>=9||t.y<0||t.y>=3)throw Error('Changed occupancy');occupied.add(at);
    const triple=patch.rows[t.y].slice(t.x,t.x+3),n=coreOutput(v,triple);
    if(!equal(t.triple,triple)||t.identity!==triple.join(':')||t.S!==triple[1]||t.N!==n||patch.rows[t.y+1][t.x+1]!==n||!equal(t.W,triple.slice(0,2))||!equal(t.E,triple.slice(1)))throw Error('Changed literal tile');
   });
  }
 }
 if(!equal([...kinds].sort(),v.audit.checked_rules))throw Error('Changed command coverage');return true;
}
if(typeof module!=='undefined')module.exports={validateClusters,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const math=a=>'\\('+formula(a)+'\\)';let view,chosen=0,index=0;
 const labels={arithmetic:'Arithmetic · adding one gives successor',geometry:'Hilbert incidence · incident object is a point','universal-distribution':'Logical control · quantifier distribution','addition-induction':'Arithmetic control · addition induction','generalization-of-open-premise':'Rejected control · open-premise generalization','captured-instantiation':'Rejected control · variable capture'};
 const list=xs=>xs.length?xs.map((a,j)=>`<div class="lineitem"><span class="tiny">Fact ${j+1}</span><div class="formula">${math(a)}</div></div>`).join(''):'<p class="tiny">No earlier facts.</p>';
 const symbol=s=>s<view.inventory.symbols?view.inventory.alphabet[s]:`${Math.floor((s-60)/60)}:${view.inventory.alphabet[(s-60)%60]}`;
 const color=(v,layer)=>{let n=17;for(const a of Array.isArray(v)?v:[v])n=(Math.imul(n,31)+a)>>>0;return `hsl(${(layer==='vertical'?205:140)+n%30} 58% ${38+n%24}%)`;};
 function draw(){
  const p=view.cases[chosen].lines[index].patch,mode=el('layer').value,s=75,ox=38,oy=22;
  let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ox+p.width*s+15} ${oy+p.height*s+20}" role="img" aria-label="Three actual literal Wang transitions at this proof-line entry, time upward"><text x="4" y="14" font-size="12">time ↑</text>`;
  for(const t of p.tiles){const x=ox+t.x*s,y=oy+(p.height-1-t.y)*s;const c=(v,l)=>mode==='all'||mode===l?color(v,l):'#dfe5df';
   svg+=`<g><rect x="${x+1}" y="${y+1}" width="${s-2}" height="${s-2}" fill="${t.triple.some(v=>v>=60)?'#fff3d9':'#f8faf5'}" stroke="#acb9ad"/><rect x="${x+8}" y="${y+2}" width="${s-16}" height="7" fill="${c(t.N,'vertical')}"/><rect x="${x+8}" y="${y+s-9}" width="${s-16}" height="7" fill="${c(t.S,'vertical')}"/><rect x="${x+2}" y="${y+10}" width="7" height="${s-20}" fill="${c(t.W,'horizontal')}"/><rect x="${x+s-9}" y="${y+10}" width="7" height="${s-20}" fill="${c(t.E,'horizontal')}"/><circle cx="${x+s/2}" cy="${y+s/2}" r="3" fill="#242a28"/><text x="${x+s/2}" y="${y+26}" text-anchor="middle" font-size="10" font-family="monospace">${esc(symbol(t.N))}</text><text x="${x+s/2}" y="${y+s-19}" text-anchor="middle" font-size="10" font-family="monospace">${esc(symbol(t.S))}</text></g>`;
  }el('literal').innerHTML=svg+'</svg>';
 }
 function read(){
  const p=view.cases[chosen],l=p.lines[index],cmd=l.input.pending[0];
  el('scope').textContent=`${l.label.scope==='root'?'Root proof':'Lemma definition '+l.label.scope} · local line ${l.label.line+1} · ${l.outcome==='line-checked'?'checked':'rejected'} · ${p.provenance.kind}`;
  const refs=cmd.rule==='mp'?` Earlier lines ${cmd.antecedent+1} and ${cmd.implication+1}.`:cmd.rule==='generalize'?` Earlier line ${cmd.source+1}.`:cmd.rule==='block'?` Earlier lines ${cmd.inputs.map(i=>i+1).join(', ')}.`:'';
  el('reading').innerHTML=`<div class="formula">${math(l.label.formula)}</div><p><code>${esc(l.label.rule)}</code> · ${esc(l.outcome==='line-checked'?reason[l.label.rule]:l.label.rule==='generalize'?'Attempt universal generalization; the chosen variable occurs in an open premise, so this step is forbidden.':'Attempt universal instantiation; the proposed substitution captures a variable, so this step is forbidden.')}${esc(refs)}</p>${l.outcome==='line-rejected'?'<p class="fail">This supplied command fails its rule or variable-scope check. It creates no new proven fact.</p>':''}`;
  el('input').innerHTML=`<p>${l.input.proved.length} earlier facts; ${l.input.assumptions.length} open premises; ${l.input.registry.length} previously checked lemmas.</p><p class="tiny">Variables forbidden for generalization: ${l.input.forbidden.length?l.input.forbidden.map(x=>'\\('+esc(x)+'\\)').join(', '):'none'}.</p><details><summary>Open premises</summary>${list(l.input.assumptions)}</details><details><summary>Earlier facts</summary>${list(l.input.proved)}</details>`;
  el('output').innerHTML=l.output?`<p>Append one checked formula; ${l.output.proved.length} facts are now available.</p><div class="formula">${math(l.output.proved.at(-1))}</div><p class="tiny">${l.output.pending.length} local commands remain. Hypotheses, theory, checked inventory and variable restrictions match the incoming context.</p>`:'<p class="fail">The fixed checker rejects this command. No accepting outgoing logical receptor is exported.</p>';
  el('expansion').textContent=`Cluster node ${l.node.toLocaleString()} expands to ${l.micro_steps.toLocaleString()} selected-symbol operations and a literal rectangle ${l.literal_width.toLocaleString()} columns wide by ${l.physical_height.toLocaleString()} transitions high, including side guards. Full counts are exact; the rectangle is not drawn to scale.`;
  el('crop-note').textContent=`A 9-column × 3-transition crop, beginning ${l.patch.prefix_physical_steps.toLocaleString()} physical steps into this cluster, at its first entry-stub symbol read. This entry sample illustrates the fixed core; most checking occurs later. Exact integer and ordered-pair values decide matching; colors are a display map.`;
  el('context').textContent=JSON.stringify({command:cmd,input:l.input,output:l.output,fragment:{node:l.node,q:l.q,out:l.out,input_head:l.input_head,output_head:l.output_head,pre_intervals:l.pre_intervals,write_intervals:l.write_intervals}},null,2);
  el('bands').innerHTML='<table><thead><tr><th>Band</th><th>Cursor shift</th><th>Visited offsets</th><th>Input intervals</th><th>Write intervals</th></tr></thead><tbody>'+l.bands.map(b=>`<tr><td>${b.tape}</td><td>${b.shift}</td><td><code>${b.extent.join(' … ')}</code></td><td>${b.pre}</td><td>${b.writes}</td></tr>`).join('')+'</tbody></table>';
  el('artifacts').innerHTML=`Complete case: <a href="${p.grammar.name}">compression grammar</a> · <a href="${p.events.name}">actual checkpoints</a> · <a href="${p.responses.name}">derived responses</a>. The whole certificate includes constructor, scope-bridge and final-target fragments as well as the selected inference.`;
  draw();window.MathJax?.typesetPromise?.([el('reading'),el('input'),el('output')]).catch(e=>{el('load').textContent='Math rendering error: '+e.message;});
 }
 function show(){
  const p=view.cases[chosen];index=0;el('line').innerHTML=p.lines.map((l,j)=>`<option value="${j}">${l.label.scope==='root'?'Root':'Lemma '+(p.request.blocks.findIndex(b=>b.name===l.label.scope)+1)} · line ${l.label.line+1} · ${l.label.rule}${l.outcome==='line-rejected'?' · REJECTED':''}</option>`).join('');
  el('theorem').textContent=math(p.target);read();window.MathJax?.typesetPromise?.([el('theorem')]).catch(e=>{el('load').textContent='Math rendering error: '+e.message;});
 }
 async function boot(){try{
  const r=await fetch('logical-wang-clusters-reader-001.json?v=20261010-l1');if(!r.ok)throw Error('Reader HTTP '+r.status);view=await r.json();validateClusters(view);
  el('load').innerHTML='<span class="badge">Independent audit passed · all 11 commands · one unchanged core</span>';
  el('case').innerHTML=view.cases.map((p,j)=>`<option value="${j}">${labels[p.name]}</option>`).join('');
  el('results').innerHTML='<table><thead><tr><th>Reused certificate</th><th>Line clusters</th><th>Result</th><th>Build + derive</th><th>Grammar nodes</th></tr></thead><tbody>'+view.cases.map(p=>`<tr><td>${labels[p.name]}</td><td>${p.lines.length}</td><td>${p.result}</td><td>${(p.builder.wall_seconds+p.checker.wall_seconds).toFixed(3)} s</td><td>${p.builder.nodes.toLocaleString()}</td></tr>`).join('')+'</tbody></table>';
  el('audit').textContent=`Production: ${view.production_seconds.toFixed(3)} s. Independent audit: ${view.audit.seconds.toFixed(3)} s; ${view.audit.mutations} changed contexts, boundary claims or fragment bindings rejected. Each proof context was reconstructed from actual symbol data. These are reused compiler controls, not new proof-discovery timings.`;
  el('case').addEventListener('change',()=>{chosen=Number(el('case').value);show();});el('line').addEventListener('change',()=>{index=Number(el('line').value);read();});el('layer').addEventListener('change',draw);show();
 }catch(e){el('load').textContent='Validation failed: '+e.message;console.error(e);}}boot();
}
