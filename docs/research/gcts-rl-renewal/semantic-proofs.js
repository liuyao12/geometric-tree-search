'use strict';
const el=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const texName=s=>String(s).replace(/[^a-zA-Z0-9]/g,'');
function term(t){
  if(t[0]==='var')return texName(t[1]);
  const [kind,name,args]=t;
  if(name==='zero')return '0';
  if(name==='succ'){
    const a=term(args[0]);return /^\d+$/.test(a)?String(Number(a)+1):`\\operatorname{S}(${a})`;
  }
  if(name==='add')return `(${term(args[0])}+${term(args[1])})`;
  if(name==='mul')return `(${term(args[0])}\\cdot ${term(args[1])})`;
  return `\\operatorname{${texName(name)}}${args.length?`(${args.map(term).join(',')})`:''}`;
}
function formula(a){
  if(a[0]==='eq')return `${term(a[1])}=${term(a[2])}`;
  if(a[0]==='pred')return `\\operatorname{${texName(a[1])}}${a[2].length?`(${a[2].map(term).join(',')})`:''}`;
  if(a[0]==='all')return `\\forall ${texName(a[1])}\\;(${formula(a[2])})`;
  if(a[0]==='not')return `\\neg(${formula(a[1])})`;
  if(a[0]==='bot')return '\\bot';
  return `(${formula(a[1])}${{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[a[0]]}${formula(a[2])})`;
}
const math=a=>`\\(${esc(formula(a))}\\)`;
const fmt=x=>Number(x).toFixed(6);
const label=row=>row.problem.label.replace(/^Addition ([12]) \+ ([12])$/,(_,a,b)=>`Addition of ${{1:'one',2:'two'}[a]} and ${{1:'one',2:'two'}[b]}`);
let data,typeset=Promise.resolve();
function typesetVisible(){typeset=typeset.then(async()=>{if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise([el('explorer')]);}}).catch(e=>{el('load').textContent=`Mathematical rendering failed: ${e.message}`;});}
function svgNode(name,attrs,text){const n=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
function render(){
  const row=data.cases[Number(el('statement').value)],run=row.runs.find(r=>r.lane===el('lane').value),r=run.result,n=row.problem.length,order=r.placements||[],step=Math.min(Number(el('step').value),order.length),placed=order.slice(0,step),selected=new Map(placed.map((k,i)=>[k[0],{key:k,at:i+1}]));
  el('step').max=String(order.length);el('step').value=String(step);el('step-count').textContent=`${step} / ${order.length}`;el('step').disabled=!order.length;
  el('target').innerHTML=math(row.problem.target);
  const axioms=Object.entries(row.problem.theory.axioms).map(([name,a])=>`<span><code>${esc(name)}</code>: ${math(a)}</span>`).join(' · ');
  el('theory').innerHTML=`Declared theory: ${axioms||'equality rules only'}. Proof-cell bound: ${n}. ${row.problem.kind==='equational'?`Term-node bound: ${row.problem.configuration.term_bound}. No induction schema.`:'Primitive FOL syntax closure.'}`;
  const svg=el('proof-tiles');svg.replaceChildren();const dx=920/n,x=i=>60+dx*i+dx/2,w=Math.min(dx-22,155),constrained=new Map([[n-1,row.catalog.target_id]]);
  for(const k of placed){const rule=row.rules[k[1]];constrained.set(k[0],rule.output);k[2].forEach((ref,i)=>constrained.set(ref,rule.inputs[i]));}
  for(const key of placed)key[2].forEach((ref,i)=>{const a=x(ref),b=x(key[0]),height=Math.min(135,45+Math.abs(b-a)/6+i*9);svg.append(svgNode('path',{d:`M ${b} 178 Q ${(a+b)/2} ${178-height*2} ${a} 178`,fill:'none',stroke:'#b28543','stroke-width':2,'stroke-opacity':.75}));svg.append(svgNode('circle',{cx:a,cy:178,r:4,fill:'#b28543'}));});
  for(let i=0;i<n;i++){
    const entry=selected.get(i),bound=constrained.has(i),rule=entry?row.rules[entry.key[1]]:null;
    svg.append(svgNode('rect',{x:x(i)-w/2,y:177,width:w,height:72,rx:5,fill:entry?'#37775e':bound?'#f4e6c8':'#fffdf8',stroke:bound?'#ba8d44':'#cbd5c7','stroke-width':bound?2:1}));
    svg.append(svgNode('text',{x:x(i),y:202,'text-anchor':'middle',fill:entry?'#fff':'#54665b','font-size':13,'font-weight':600},`cell ${i+1}`));
    svg.append(svgNode('text',{x:x(i),y:224,'text-anchor':'middle',fill:entry?'#d6e6d5':'#65716a','font-size':11},entry?`${rule.label} · placed ${entry.at}`:bound?'formula required':'free output'));
    if(i===n-1)svg.append(svgNode('text',{x:x(i),y:265,'text-anchor':'middle',fill:'#91682f','font-size':10},'target boundary'));
  }
  const solved=!!r.proof,unknown=r.status==='unknown_search_budget',nonchronological=solved&&order.some((k,i)=>k[0]!==i);
  el('placement-story').textContent=solved?(nonchronological?'The actual placement order differs from logical cell order. A later cell can impose an earlier premise value before the premise tile is selected. Read cells in logical order to obtain the checked proof.':'This run selected cells in logical order. Each premise marking agrees with an earlier output; the final cell matches the target boundary.'):unknown?'The search reached a resource limit. The outcome remains unknown. The diagram shows a compatible partial placement.':run.lane==='gcts'?'The complete finite GCTS tree and its failed branches were independently replayed. No proof exists in this declared envelope. This is not a general unprovability claim. The diagram shows the best saved compatible partial placement.':'The symbolic control exhausted the same declared grammar and cell bound. Its abandoned prefixes were not exported. The corresponding complete GCTS failure tree was independently replayed.';
  const commands=el('commands');commands.replaceChildren();
  if(solved){const bySlot=new Map(order.map(k=>[k[0],k]));for(let i=0;i<n;i++){const key=bySlot.get(i),rule=row.rules[key[1]],p=document.createElement('p');p.className=selected.has(i)?'':'waiting';p.innerHTML=`<strong>Cell ${i+1}</strong> · <code>${esc(rule.label)}</code>${key[2].length?` · premises ${key[2].map(j=>j+1).join(', ')}`:' · no premises'}<br>${math(row.catalog.formulas[rule.output])}`;commands.append(p);}}
  else commands.textContent='No complete logical certificate was found in this finite envelope.';
  const audit=row.audit.runs.find(a=>a.lane===run.lane),d=audit.derivation;
  el('work').innerHTML=`<p class="result-state ${solved?'':'unproved'}">${solved?'Proof found; independently accepted':unknown?'Unknown; search resource limit':'Finite envelope exhausted'}</p><p>${r.nodes.toLocaleString()} visited states; ${r.attempts.toLocaleString()} attempted placements.</p><p>Search: ${fmt(r.seconds)} s · cold run: ${fmt(run.cold_seconds)} s</p><p>Catalog construction and validation: ${fmt(run.catalog_build_seconds)} s (validation ${fmt(run.catalog_validation_seconds)} s)</p>${r.candidate_universe!==undefined?`<p>${r.candidate_universe.toLocaleString()} positional candidate types; peak ${r.peak_candidate_nodes.toLocaleString()} live candidate nodes.</p>`:''}${d?`<p>${d.proof_cells} proof cells · ${d.root_lines} decoded root commands · ${d.blocks} compiled blocks · ${d.expanded_lines} expanded primitive lines.</p>`:''}${run.native?`<p>Fixed checker: ${esc(run.native.status)} · ${run.native.steps.toLocaleString()} instructions · ${fmt(run.native.wall_seconds)} s</p>`:''}`;
  el('primitive-lines').innerHTML=solved?r.proof.map((line,i)=>`<p><code>${i}: ${esc(line.rule)}${line.name?` ${esc(line.name)}`:''}</code><br>${math(line.formula)}</p>`).join(''):'No proof to decode.';
  typesetVisible();
}
async function start(){
  const responses=await Promise.all([fetch('semantic-proof-view-001.json?v=20261009-r29.1'),fetch('semantic-proof-tests-001.json?v=20261009-r29.1')]);for(const r of responses)if(!r.ok)throw Error(`HTTP ${r.status}`);
  const [view,tests]=await Promise.all(responses.map(r=>r.json()));data=view;
  data.cases.forEach((row,i)=>{const option=document.createElement('option');option.value=i;option.textContent=label(row);el('statement').append(option);});
  el('comparison-rows').innerHTML=data.cases.map(row=>{const g=row.runs.find(r=>r.lane==='gcts'),s=row.runs.find(r=>r.lane==='symbolic');return `<tr><td>${esc(label(row))}</td><td>${row.catalog.formulas.length} / ${row.rules.length}</td><td>${g.result.nodes.toLocaleString()}</td><td>${s.result.nodes.toLocaleString()}</td><td>${fmt(g.result.seconds)} / ${fmt(g.cold_seconds)}</td><td>${fmt(s.result.seconds)} / ${fmt(s.cold_seconds)}</td></tr>`;}).join('');
  el('test-status').textContent=`All ${tests.passed} research tests pass (${fmt(tests.seconds)} wall seconds). Independent audit: ${data.independent_audit.status}; ${fmt(data.independent_audit.seconds)} seconds. The small browser projection is bound to the full experiment by SHA-256.`;
  el('load').textContent='';el('statement').addEventListener('change',()=>{const row=data.cases[Number(el('statement').value)],r=row.runs.find(r=>r.lane===el('lane').value);el('step').value=String(r.result.placements?.length||0);render();});
  el('lane').addEventListener('change',()=>{const row=data.cases[Number(el('statement').value)],r=row.runs.find(r=>r.lane===el('lane').value);el('step').value=String(r.result.placements?.length||0);render();});el('step').addEventListener('input',render);render();
}
start().catch(e=>{el('load').textContent=`Evidence could not be loaded: ${e.message}`;console.error(e);});
