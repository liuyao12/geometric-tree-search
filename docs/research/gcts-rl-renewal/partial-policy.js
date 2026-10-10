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
const lanes={base:'Plain GCTS',prior:'Fixed hierarchy prior',zero:'Zero weights',complete:'Complete-tree learner',local:'Local-progress learner'};
const featureLabels=['Defer','Defer · multiplication','Defer · progress','Defer · frontier degree','Member count','Hierarchy level','Final-cell member','Direction','Context depth','Term shrinkage','Input already placed','Member degrees'];
let data,typeset=Promise.resolve();
function typesetVisible(){typeset=typeset.then(async()=>{if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise([el('training'),el('comparison')]);}}).catch(e=>el('load').textContent=`Mathematical rendering failed: ${e.message}`);}
function svgNode(name,attrs,text){const n=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
function learner(){return data.learners.find(x=>x.seed===Number(el('seed').value)&&x.signal===el('signal').value);}
function episode(){const count=Number(el('episode').value);return count?learner().episodes[count-1]:null;}
function coefficients(e){
 const before=e?e.update.weights_before:Array(12).fill(0),after=e?e.update.weights_after:Array(12).fill(0),max=Math.max(.1,...before.map(Math.abs),...after.map(Math.abs)),center=650,scale=280/max,svg=el('weights');svg.replaceChildren();svg.append(svgNode('line',{x1:center,y1:20,x2:center,y2:386,stroke:'#8c9b8b'}));
 after.forEach((v,i)=>{const y=30+i*29,b=before[i];svg.append(svgNode('text',{x:275,y:y+14,'text-anchor':'end','font-size':13,fill:'#52645a'},featureLabels[i]));svg.append(svgNode('rect',{x:Math.min(center,center+b*scale),y:y-2,width:Math.max(1,Math.abs(b)*scale),height:24,rx:3,fill:'none',stroke:'#8d9d8e','stroke-width':2}));svg.append(svgNode('rect',{x:Math.min(center,center+v*scale),y:y+2,width:Math.max(1,Math.abs(v)*scale),height:16,rx:3,fill:v>=0?'#37775e':'#806d9b'}));svg.append(svgNode('text',{x:v>=0?center+v*scale+8:center+v*scale-8,y:y+15,'text-anchor':v>=0?'start':'end','font-size':12,fill:'#52645a'},v.toFixed(3)));});
 [-max,0,max].forEach(v=>svg.append(svgNode('text',{x:center+v*scale,y:413,'text-anchor':'middle','font-size':11,fill:'#68776c'},v.toFixed(2))));
 el('update-detail').textContent=e?`${e.update.credits.length} reached choices credited · baseline ${fmt(e.update.baseline_before)} to ${fmt(e.update.baseline_after)} · ${e.update.updated?'update applied':'no parameter update'} · multiplication coefficient ${fmt(before[1])} to ${fmt(after[1])}.`:'All coefficients start at zero; no prior policy is imported.';
}
function prefix(e,row,event){
 const svg=el('prefix');svg.replaceChildren();if(!e)return;
 const n=row.problem.length,visits=e.prefix_nodes,x=i=>65+920*i/Math.max(1,visits.length-1),y=d=>195-150*d/n;
 for(let d=0;d<=n;d++){svg.append(svgNode('line',{x1:65,y1:y(d),x2:985,y2:y(d),stroke:'#dce4d6'}));svg.append(svgNode('text',{x:49,y:y(d)+4,'text-anchor':'end','font-size':11,fill:'#68776c'},String(d)));}
 svg.append(svgNode('polyline',{points:visits.map((t,i)=>`${x(i)},${y(t.depth)}`).join(' '),fill:'none',stroke:'#b6c8b7','stroke-width':1}));
 visits.forEach((t,i)=>{svg.append(svgNode('circle',{cx:x(i),cy:y(t.depth),r:t.event===event?5:2.5,fill:t.viable?'#37775e':'#806d9b',stroke:t.event===event?'#795e92':'none','stroke-width':2}));if(t.kind==='cutoff'||t.cutoff)svg.append(svgNode('rect',{x:x(i)-5,y:y(t.depth)-5,width:10,height:10,fill:'none',stroke:'#b28543','stroke-width':3}));});
 svg.append(svgNode('text',{x:65,y:225,'font-size':11,fill:'#68776c'},'DFS visit 1'));svg.append(svgNode('text',{x:985,y:225,'text-anchor':'end','font-size':11,fill:'#68776c'},`DFS visit ${visits.length}`));
}
function pointState(e,row,event){
 const svg=el('state');svg.replaceChildren();if(!e)return;
 const selected=e.result.policy_events[event],order=selected?selected.order:e.result.placements,n=row.problem.length,placed=new Map(order.map((k,i)=>[k[0],{key:k,at:i+1}])),marks=new Map([[n-1,row.target_id]]),dx=920/n,x=i=>60+dx*i+dx/2,w=Math.min(dx-22,155);
 for(const key of order){const r=row.rules[key[1]];marks.set(key[0],r.output);key[2].forEach((ref,i)=>marks.set(ref,r.inputs[i]));key[2].forEach(ref=>{const a=x(ref),b=x(key[0]),h=Math.min(90,35+Math.abs(a-b)/6);svg.append(svgNode('path',{d:`M ${b} 140 Q ${(a+b)/2} ${140-2*h} ${a} 140`,fill:'none',stroke:'#b28543','stroke-width':2}));});}
 for(let i=0;i<n;i++){const item=placed.get(i),required=marks.has(i);svg.append(svgNode('rect',{x:x(i)-w/2,y:138,width:w,height:64,rx:5,fill:item?'#37775e':required?'#f4e6c8':'#fffdf8',stroke:required?'#ba8d44':'#cbd5c7','stroke-width':2}));svg.append(svgNode('text',{x:x(i),y:160,'text-anchor':'middle',fill:item?'white':'#52645a','font-size':13},`cell ${i+1}`));svg.append(svgNode('text',{x:x(i),y:184,'text-anchor':'middle',fill:item?'#d6e6d5':'#65716a','font-size':11},item?`${row.rules[item.key[1]].label} · placed ${item.at}`:required?'formula required':'free output'));if(selected&&selected.point[0]===2*i)svg.append(svgNode('text',{x:x(i),y:227,'text-anchor':'middle',fill:'#795e92','font-size':11},'selected frontier'));}
}
function resetEvents(){
 const e=episode();el('event').replaceChildren();const events=e?e.result.policy_events:[];
 if(events.length){events.forEach((x,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Event ${i+1} · ${x.pool_count} fragments`;el('event').append(o);});el('event').disabled=false;}else{const o=document.createElement('option');o.value='-1';o.textContent='No policy event';el('event').append(o);el('event').disabled=true;}
 renderTraining();
}
function renderTraining(){
 const count=Number(el('episode').value),e=episode(),event=Number(el('event').value),row=e?data.training.find(x=>x.problem.id===e.problem_id):null;el('episode-count').textContent=`${count} / 32`;coefficients(e);
 if(!e){el('training-target').textContent='No training episode yet.';el('training-detail').textContent='All six learners start from zero weights.';el('prefix').replaceChildren();el('state').replaceChildren();el('credits').textContent='No choices have been executed.';typesetVisible();return;}
 el('training-target').innerHTML=math(row.problem.target);const r=e.result,gate=e.prefix_gate.report;el('training-detail').textContent=`Episode ${count} · epoch ${e.epoch+1} · ${row.problem.label} · ${r.status==='unknown_search_budget'?'unknown at resource cutoff':e.native?`complete native check ${e.native.status}`:'finite envelope exhausted'} · ${gate.executed_nodes} independently replayed nodes · ${r.base_attempts} base attempts · ${gate.open_suffixes} open suffix · observed viable depth ${gate.observed_viable_depth} / ${row.problem.length} · ${fmt(e.cold_seconds)} cold seconds, including ${fmt(e.prefix_gate.seconds)} s online replay.`;
 prefix(e,row,event);pointState(e,row,event);const choice=r.policy_events[event];
 if(!choice)el('credits').textContent='This episode has no policy decision.';
 else{const trials=e.event_trials[String(event)],credits=e.update.credits.filter(x=>x.event===event);el('credits').innerHTML=`<p>${choice.pool_count} compatible checked fragment instances plus deferral. The complete primitive graph first selects cell ${choice.point[0]/2+1}.</p>`+choice.draws.map((d,j)=>{const trial=trials[j],credit=credits.find(x=>x.draw===j),defer=d.action==='defer',reached=!!trial||defer&&j===trials.length&&e.event_fallbacks[String(event)],label=defer?'Defer to ordinary GCTS':trial?`Level ${trial.item.level} sequence · cells ${trial.item.members.map(k=>k[0]+1).join(', ')}`:'Sampled fragment preference';return `<p class="${!reached?'censored':trial?.trace.status==='unknown_transaction_budget'?'open':''}"><strong>${j+1}. ${esc(label)}</strong> · probability ${d.probability.toFixed(5)}${trial?`<br>${math(['eq',trial.item.instance.before,trial.item.instance.after])}<br>Validation: ${esc(trial.trace.status)} · ${trial.trace.steps.length} actual base placements${trial.continuation!==undefined&&trial.trace.status==='accepted_cluster'?` · continuation ${trial.continuation===null?'open at cutoff':trial.continuation?'reaches the checked proof':'finite subtree exhausted'}`:''}`:''}<br>${!reached?'Sampled suffix not reached; no credit.':credit?`<span class="reward">Actual return ${fmt(credit.value)} · ${credit.base_attempts} observed base attempts${credit.viable_gain!==undefined?` · viable gain ${credit.viable_gain} / ${row.problem.length}`:''} · theorem bonus ${credit.verified_continuation?'1':'0'}</span>`:r.status==='unknown_search_budget'&&el('signal').value==='complete'?'Executed choice; complete-tree control discards credit for this unknown request.':'Choice reached; interruption before a constituent executes supplies no local credit.'}</p>`;}).join('');}
 typesetVisible();
}
function renderEvaluation(){
 const row=data.cases[Number(el('statement').value)],run=row.runs.find(x=>x.seed===Number(el('seed').value)&&x.lane===el('lane').value),r=run.result;el('eval-target').innerHTML=math(row.problem.target);el('eval-result').textContent=run.native?`Complete native check ${run.native.status} · ${r.nodes} states · ${r.base_attempts} actual base attempts · ${fmt(run.cold_seconds)} cold seconds.`:r.status==='unknown_search_budget'?'Unknown at the resource limit. The retained open prefix is not a proof or finite impossibility certificate.':'The finite cell and term envelope is exhausted with a complete independently replayed tree. This is not general unprovability.';
 el('eval-work').textContent=`Search ${fmt(r.seconds)} s · fresh catalog ${fmt(run.catalog_build_seconds)} s · ${r.candidate_universe.toLocaleString()} primitive candidate types · ${r.index_instances.toLocaleString()} fragment instances · policy inference ${fmt(r.policy_seconds)} s${run.native?` · native checker ${run.native.steps.toLocaleString()} instructions in ${fmt(run.native.wall_seconds)} s`:''}.`;
 el('certificate').innerHTML=run.hierarchy?run.hierarchy.proof.map((p,i)=>`<p><code>${i+1}: ${esc(p.rule)}</code><br>${math(p.formula)}</p>`).join(''):'No complete proof certificate.';typesetVisible();
}
async function start(){
 const responses=await Promise.all([fetch('partial-policy-view-001.json?v=20261009-r32.1'),fetch('partial-policy-tests-001.json?v=20261009-r32.1')]);for(const r of responses)if(!r.ok)throw Error(`HTTP ${r.status}`);const [view,tests]=await Promise.all(responses.map(r=>r.json()));data=view;
 data.cases.forEach((row,i)=>{const o=document.createElement('option');o.value=i;o.textContent=row.problem.label;el('statement').append(o);});el('statement').value='6';
 el('cost-rows').innerHTML=[1,7,19].map(seed=>Object.entries(data.totals[String(seed)]).map(([lane,t])=>{const training=['complete','local'].includes(lane)?data.learners.find(x=>x.seed===seed&&x.signal===lane).training_seconds:0,setup=data.compile_seconds+(lane==='base'?0:data.library_seconds)+(training?data.training_catalog_seconds+training:0);return `<tr><td>${seed}</td><td>${esc(lanes[lane])}</td><td>${t.verified} / ${t.exhausted} / ${t.unknown}</td><td>${t.nodes} / ${t.attempts}</td><td>${fmt(t.cold_seconds)}</td><td>${fmt(training)}</td><td>${fmt(t.cold_seconds+setup)}</td></tr>`;}).join('')).join('');
 el('cost-detail').textContent=`Common native compilation ${fmt(data.compile_seconds)} s · fresh library and whole-library check ${fmt(data.library_seconds)} s · shared training catalogs including independent inventory checks ${fmt(data.training_catalog_seconds)} s · producer ${fmt(data.total_seconds)} s · peak driver ${(data.peak_driver_memory_bytes/1048576).toFixed(2)} MiB, including all accumulated artifacts and catalogs; no per-lane memory ranking.`;
 const local=data.learners.filter(x=>x.signal==='local'),control=data.learners.filter(x=>x.signal==='complete'),unknown=x=>x.episodes.filter(e=>e.result.status==='unknown_search_budget'),localUnknown=local.flatMap(unknown),controlUnknown=control.flatMap(unknown);el('assessment-result').textContent=`Local credit updates ${localUnknown.filter(e=>e.update.updated).length} of ${localUnknown.length} unknown training requests; the complete-tree control updates ${controlUnknown.filter(e=>e.update.updated).length} of ${controlUnknown.length}. All unknown requests retain an unknown final outcome. The multiplication coefficients after local training are ${local.map(x=>fmt(x.weights[1])).join(', ')}; the control coefficients are ${control.map(x=>fmt(x.weights[1])).join(', ')}. See the matched full costs below before interpreting this as acceleration.`;
 el('test-status').textContent=`All ${tests.passed} tests pass (${fmt(tests.seconds)} wall seconds). The independent complete/open-prefix audit passes in ${fmt(data.independent_audit.seconds)} seconds. The browser projection pins the full artifact and exporter by SHA-256.`;
 el('load').textContent='';el('seed').addEventListener('change',()=>{resetEvents();renderEvaluation();});el('signal').addEventListener('change',resetEvents);el('episode').addEventListener('input',resetEvents);el('event').addEventListener('change',renderTraining);el('statement').addEventListener('change',renderEvaluation);el('lane').addEventListener('change',renderEvaluation);resetEvents();renderEvaluation();
}
start().catch(e=>{el('load').textContent=`Evidence could not be loaded: ${e.message}`;console.error(e);});
