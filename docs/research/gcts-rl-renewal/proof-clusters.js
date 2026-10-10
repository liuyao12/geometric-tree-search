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
const lanes={base:'Plain GCTS',level1:'Level-one sequences',hierarchy:'Full hierarchy sequences','rank-only':'Hierarchy ranks single tiles'};
const idKey=k=>JSON.stringify(k);
let data,typeset=Promise.resolve();
function typesetVisible(){typeset=typeset.then(async()=>{if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise([el('explorer'),el('fragments')]);}}).catch(e=>{el('load').textContent=`Mathematical rendering failed: ${e.message}`;});}
function svgNode(name,attrs,text){const n=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
function templateName(name){const index=data.library.findIndex(t=>t.name===name);return index<0?name:`Fragment ${index+1}`;}
function fragment(){
  const t=data.library[Number(el('fragment').value)],expanded=el('expand').checked;
  el('interface').innerHTML=math(t.conclusion);
  el('fragment-source').innerHTML=`${esc(templateName(t.name))} · level ${t.level} · ${t.actions.length} base moves · mined from ${esc(t.source.problem)}, window ${t.source.window[0]+1}–${t.source.window[1]} · checked ${esc(t.check.status)}<br><code>${esc(t.name)}</code>`;
  const childAt=new Map(t.child_spans.map(c=>[Math.min(...c.indices),c])),html=[];
  for(let i=0;i<t.actions.length;i++){
    const child=childAt.get(i);
    if(child&&!expanded){
      const first=t.actions[Math.min(...child.indices)],last=t.actions[Math.max(...child.indices)];html.push(`<div class="fragment-card child"><h3>${esc(templateName(child.template))} · earlier checked child</h3>${math(['eq',first.before,last.after])}<p class="small">${child.indices.length} primitive moves inside this call. Context depth ${child.instance.context.length}.</p></div>`);i=Math.max(...child.indices);
    }else{
      const a=t.actions[i],inside=t.child_spans.find(c=>c.indices.includes(i));html.push(`<div class="fragment-card ${inside?'child':''}"><h3>Move ${i+1} · ${esc(a.rule)}${inside?` · inside ${esc(templateName(inside.template))}`:''}</h3>${math(['eq',a.before,a.after])}<p class="small">Actual rewrite context depth ${a.path.length}.</p></div>`);
    }
  }
  el('fragment-chain').innerHTML=html.join('');el('fragment-detail').textContent=t.children.length?'This source proof actually used the earlier child. The promoted parent definition retains that checked call. The diagram displays its recorded contextual move span.':'This level-one definition calls no earlier learned fragment. Its moves were selected by GCTS from the bounded axiom grammar.';typesetVisible();
}
function current(){const row=data.cases[Number(el('statement').value)];return [row,row.runs.find(r=>r.lane===el('lane').value&&r.replica===Number(el('replica').value))];}
function render(){
  const [row,run]=current(),r=run.result,n=row.problem.length,order=r.placements||[],step=Math.min(Number(el('step').value),order.length),placed=order.slice(0,step),selected=new Map(placed.map((k,i)=>[k[0],{key:k,at:i+1}]));
  el('step').max=String(order.length);el('step').value=String(step);el('step-count').textContent=`${step} / ${order.length}`;el('step').disabled=!order.length;
  el('target').innerHTML=math(row.problem.target);
  el('theory').innerHTML=`${Object.entries(row.problem.theory.axioms).map(([name,a])=>`<code>${esc(name)}</code>: ${math(a)}`).join(' · ')}<br>Same ${n} proof cells and term-node bound ${row.problem.term_bound} in every lane. No induction schema.`;
  const svg=el('proof-tiles');svg.replaceChildren();const dx=920/n,x=i=>60+dx*i+dx/2,w=Math.min(dx-22,155),constrained=new Map([[n-1,row.catalog.target_id]]),txs=r.solution_transactions;
  for(const k of placed){const rule=row.rules[k[1]];constrained.set(k[0],rule.output);k[2].forEach((ref,i)=>constrained.set(ref,rule.inputs[i]));}
  for(const key of placed)key[2].forEach((ref,i)=>{const a=x(ref),b=x(key[0]),height=Math.min(120,40+Math.abs(b-a)/6+i*9);svg.append(svgNode('path',{d:`M ${b} 164 Q ${(a+b)/2} ${164-height*2} ${a} 164`,fill:'none',stroke:'#b28543','stroke-width':2,'stroke-opacity':.75}));svg.append(svgNode('circle',{cx:a,cy:164,r:4,fill:'#b28543'}));});
  for(let i=0;i<n;i++){
    const entry=selected.get(i),bound=constrained.has(i),rule=entry?row.rules[entry.key[1]]:null;
    svg.append(svgNode('rect',{x:x(i)-w/2,y:163,width:w,height:66,rx:5,fill:entry?'#37775e':bound?'#f4e6c8':'#fffdf8',stroke:bound?'#ba8d44':'#cbd5c7','stroke-width':bound?2:1}));
    svg.append(svgNode('text',{x:x(i),y:186,'text-anchor':'middle',fill:entry?'#fff':'#54665b','font-size':13,'font-weight':600},`cell ${i+1}`));
    svg.append(svgNode('text',{x:x(i),y:208,'text-anchor':'middle',fill:entry?'#d6e6d5':'#65716a','font-size':11},entry?`${rule.label} · placed ${entry.at}`:bound?'formula required':'free output'));
    if(i===n-1)svg.append(svgNode('text',{x:x(i),y:245,'text-anchor':'middle',fill:'#91682f','font-size':10},'target boundary'));
  }
  txs.forEach((tx,i)=>{const slots=tx.members.map(k=>k[0]),a=x(Math.min(...slots))-w/2,b=x(Math.max(...slots))+w/2,color=tx.level===2?'#796496':'#347f8b',done=tx.members.every(k=>placed.some(p=>idKey(p)===idKey(k))),y=264+i%2*21;
    svg.append(svgNode('path',{d:`M ${a} ${y-6} V ${y} H ${b} V ${y-6}`,fill:'none',stroke:color,'stroke-width':2,'stroke-opacity':done?1:.3}));svg.append(svgNode('text',{x:(a+b)/2,y:y+14,'text-anchor':'middle',fill:color,'font-size':11,opacity:done?1:.5},`${templateName(tx.template)} · level ${tx.level}`));});
  const solved=!!run.hierarchy,unknown=r.status==='unknown_search_budget';
  el('placement-story').textContent=solved?(txs.length?`${txs.length} actual checked sequence transactions compose this solution. Their constituents remain ordinary base tiles; all global forced and branch decisions are validated. The base placement order is ${order.map(k=>k[0]+1).join(', ')}.`:'This solution uses only individual base placements. Logical cell order yields the separately checked certificate.'):unknown?'The search reached its wall or attempt budget. This compatible partial placement is not a proof, and no finite impossibility is inferred.':'The complete finite search tree is independently replayed. This cell and term envelope is exhausted; this is not a general unprovability claim. The diagram shows the best compatible partial placement.';
  el('commands').innerHTML=solved?run.hierarchy.proof.map((line,i)=>`<p><strong>Root line ${i+1}</strong> · <code>${esc(line.rule)}</code>${line.inputs?.length?` · earlier inputs ${line.inputs.map(j=>j+1).join(', ')}`:''}<br>${math(line.formula)}</p>`).join(''):'No complete checked certificate was found.';
  el('transactions').innerHTML=txs.length?txs.map(tx=>`<p><strong>${esc(templateName(tx.template))}</strong> · level ${tx.level} · cells ${tx.members.map(k=>k[0]+1).join(', ')}<br>${math(['eq',tx.instance.before,tx.instance.after])}<br>Actual step order: ${tx.steps.map(s=>`${s.key[0]+1} (${s.kind}, ${s.role})`).join(', ')}.</p>`).join(''):'No learned fragment was used in the saved solution.';
  const h=run.hierarchy;
  el('work').innerHTML=`<p class="result-state ${solved?'':'unproved'}">${solved?'Proof found; complete native check accepted':unknown?'Unknown; search resource limit':'Finite envelope exhausted'}</p><p>${r.nodes.toLocaleString()} visited states; ${r.base_attempts.toLocaleString()} base-placement attempts.</p><p>Search: ${fmt(r.seconds)} s · cold request: ${fmt(run.cold_seconds)} s</p><p>Fresh catalog: ${fmt(run.catalog_build_seconds)} s (validation ${fmt(run.catalog_validation_seconds)} s)</p><p>Model / graph / proposal index: ${fmt(r.build_seconds)} / ${fmt(r.graph_seconds)} / ${fmt(r.index_seconds)} s</p><p>${r.candidate_universe.toLocaleString()} base candidate types · ${r.index_instances.toLocaleString()} proposal instances${r.index_complete?'':' (proposal index truncated)'}</p><p>Proposal trials: ${r.stats.proposal_trials||0}; accepted transactions across visited branches: ${r.stats.accepted_proposal_trials||0}.</p>${h?`<p>${n} base cells · ${h.original_root_lines} original root lines · ${h.root_lines} hierarchical root lines · ${h.definitions} definitions · ${h.expanded_lines} fully expanded root lines.</p><p>Hierarchy build and host checking: ${fmt(h.seconds)} s</p>`:''}${run.native?`<p>Fixed checker: ${esc(run.native.status)} · ${run.native.steps.toLocaleString()} instructions · ${fmt(run.native.wall_seconds)} s</p>`:''}`;
  typesetVisible();
}
async function start(){
  const responses=await Promise.all([fetch('proof-cluster-view-001.json?v=20261009-r30.1'),fetch('proof-cluster-tests-001.json?v=20261009-r30.1')]);for(const r of responses)if(!r.ok)throw Error(`HTTP ${r.status}`);
  const [view,tests]=await Promise.all(responses.map(r=>r.json()));data=view;
  data.library.forEach((t,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Fragment ${i+1} · level ${t.level} · ${t.actions.length} base moves`;el('fragment').append(o);});el('fragment').value='2';
  data.cases.forEach((row,i)=>{const o=document.createElement('option');o.value=i;o.textContent=row.problem.label;el('statement').append(o);});el('statement').value='6';
  el('totals').innerHTML=Object.entries(data.totals).map(([lane,t])=>`<tr><td>${esc(lanes[lane])}</td><td>${t.found} / ${t.exhausted} / ${t.unknown}</td><td>${t.nodes.toLocaleString()} / ${t.attempts.toLocaleString()}</td><td>${fmt(t.search_seconds)}</td><td>${fmt(t.cold_seconds)}</td><td>${fmt(t.index_seconds)} / ${fmt(t.native_seconds)}</td></tr>`).join('');
  el('case-costs').innerHTML=data.cases.map(row=>`<tr><td>${esc(row.problem.label)}</td>${Object.keys(lanes).map(lane=>`<td>${[0,1].map(replica=>{const r=row.runs.find(r=>r.lane===lane&&r.replica===replica);return `${r.result.status==='unknown_search_budget'?'unknown · ':''}${r.result.nodes} · ${r.cold_seconds.toFixed(3)}`;}).join('<br>')}</td>`).join('')}</tr>`).join('');
  el('costs').textContent=`Shared learning and whole-library validation: ${fmt(data.learning_seconds)} s. Shared native compilation: ${fmt(data.compile_seconds)} s. Full family producer: ${fmt(data.total_seconds)} s. Peak driver memory: ${(data.peak_driver_memory_bytes/1048576).toFixed(2)} MiB, including accumulated artifacts; this is not a per-lane memory comparison.`;
  el('test-status').textContent=`All ${tests.passed} research tests pass (${fmt(tests.seconds)} wall seconds). Independent audit: ${data.independent_audit.status}; ${fmt(data.independent_audit.seconds)} seconds. The browser projection carries the full artifact's SHA-256 and the exporter source SHA.`;
  el('load').textContent='';for(const id of ['statement','lane','replica'])el(id).addEventListener('change',()=>{el('step').value=String(current()[1].result.placements.length);render();});el('step').addEventListener('input',render);el('fragment').addEventListener('change',fragment);el('expand').addEventListener('change',fragment);fragment();render();
}
start().catch(e=>{el('load').textContent=`Evidence could not be loaded: ${e.message}`;console.error(e);});
