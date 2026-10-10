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
const lanes={base:'Plain GCTS',level1:'Level-one sequences',prior:'Fixed hierarchy prior',zero:'Zero-weight policy',trained:'Trained policy'};
const featureLabels=['Defer','Defer · multiplication','Defer · progress','Defer · frontier degree','Member count','Hierarchy level','Final-cell member','Direction','Context depth','Term shrinkage','Input already placed','Member degrees'];
let data,typeset=Promise.resolve();
function typesetVisible(){typeset=typeset.then(async()=>{if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise([el('learning'),el('explorer')]);}}).catch(e=>el('load').textContent=`Mathematical rendering failed: ${e.message}`);}
function svgNode(name,attrs,text){const n=document.createElementNS('http://www.w3.org/2000/svg',name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
function selectedSeed(){return data.seeds.find(s=>s.seed===Number(el('seed').value));}
function weights(){
  const s=selectedSeed(),count=Number(el('episode').value),e=count?s.episodes[count-1]:null,w=e?e.update.weights_after:Array(12).fill(0),max=Math.max(.1,...w.map(Math.abs)),svg=el('weights');svg.replaceChildren();el('episode-count').textContent=`${count} / 32`;
  const center=650,scale=280/max;svg.append(svgNode('line',{x1:center,y1:20,x2:center,y2:386,stroke:'#8c9b8b','stroke-width':1}));
  w.forEach((v,i)=>{const y=30+i*29;svg.append(svgNode('text',{x:275,y:y+14,'text-anchor':'end','font-size':13,fill:'#52645a'},featureLabels[i]));svg.append(svgNode('rect',{x:Math.min(center,center+v*scale),y:y,width:Math.max(1,Math.abs(v)*scale),height:20,rx:3,fill:v>=0?'#37775e':'#806d9b'}));svg.append(svgNode('text',{x:v>=0?center+v*scale+8:center+v*scale-8,y:y+15,'text-anchor':v>=0?'start':'end','font-size':12,fill:'#52645a'},v.toFixed(3)));});
  [-max,0,max].forEach(v=>svg.append(svgNode('text',{x:center+v*scale,y:413,'text-anchor':'middle','font-size':11,fill:'#68776c'},v.toFixed(2))));
  if(e){const p=data.training.find(x=>x.problem.id===e.problem_id).problem;el('training-target').innerHTML=math(p.target);el('training-detail').textContent=`Episode ${count} · ${p.label} · ${e.result.status==='unknown_search_budget'?'unknown; no weight or baseline update':`complete native check ${e.native.status}`} · ${e.result.base_attempts} base attempts · ${e.update.credits.length} actually reached choices credited · ${fmt(e.cold_seconds)} cold seconds. Epoch ${e.epoch+1}.`;}
  else{el('training-target').textContent='All policy coefficients are zero.';el('training-detail').textContent='No previous policy is imported. Sampling begins uniformly among eligible checked fragments and deferral.';}
  typesetVisible();
}
function current(){const row=data.cases[Number(el('statement').value)];return [row,row.runs.find(r=>r.seed===Number(el('seed').value)&&r.lane===el('lane').value)];}
function resetEvent(){const [,run]=current();el('event').replaceChildren();const events=run.result.policy_events;if(events.length){events.forEach((e,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Event ${i+1} · ${e.pool_count} fragments`;el('event').append(o);});el('event').disabled=false;}else{const o=document.createElement('option');o.value='-1';o.textContent='No policy event';el('event').append(o);el('event').disabled=true;}render();}
function render(){
  const [row,run]=current(),r=run.result,e=r.policy_events[Number(el('event').value)],order=e?e.order:r.placements,n=row.problem.length,placed=new Map(order.map((k,i)=>[k[0],{key:k,at:i+1}])),constrained=new Map([[n-1,row.target_id]]),solved=!!run.native,unknown=r.status==='unknown_search_budget';
  el('target').innerHTML=math(row.problem.target);el('result').textContent=solved?`Complete native check accepted · ${r.nodes} states · ${r.base_attempts} actual base attempts · ${fmt(run.cold_seconds)} cold seconds.`:unknown?'Unknown at the resource limit. No proof certificate or finite impossibility is inferred.':'The finite cell and term envelope is exhausted, with a complete independently replayed search tree. This is not general unprovability.';
  const svg=el('proof-state');svg.replaceChildren();const dx=920/n,x=i=>60+dx*i+dx/2,w=Math.min(dx-22,155);
  for(const key of order){const rule=row.rules[key[1]];constrained.set(key[0],rule.output);key[2].forEach((ref,i)=>constrained.set(ref,rule.inputs[i]));}
  for(const key of order)key[2].forEach(ref=>{const a=x(ref),b=x(key[0]),height=Math.min(120,40+Math.abs(b-a)/6);svg.append(svgNode('path',{d:`M ${b} 158 Q ${(a+b)/2} ${158-2*height} ${a} 158`,fill:'none',stroke:'#b28543','stroke-width':2}));});
  for(let i=0;i<n;i++){const item=placed.get(i),bound=constrained.has(i);svg.append(svgNode('rect',{x:x(i)-w/2,y:157,width:w,height:67,rx:5,fill:item?'#37775e':bound?'#f4e6c8':'#fffdf8',stroke:bound?'#ba8d44':'#cbd5c7','stroke-width':2}));svg.append(svgNode('text',{x:x(i),y:181,'text-anchor':'middle',fill:item?'white':'#52645a','font-size':13},`cell ${i+1}`));svg.append(svgNode('text',{x:x(i),y:205,'text-anchor':'middle',fill:item?'#d6e6d5':'#65716a','font-size':11},item?`${row.rules[item.key[1]].label} · placed ${item.at}`:bound?'formula required':'free output'));if(e&&e.point[0]===2*i)svg.append(svgNode('text',{x:x(i),y:248,'text-anchor':'middle',fill:'#795e92','font-size':11},'selected frontier'));}
  if(e){const trials=run.event_trials[String(e.id)],isComplete=trials!==undefined;el('decision').innerHTML=`<p>${e.pool_count} compatible fragment instances plus deferral. The complete primitive graph selects cell ${e.point[0]/2+1} before policy ordering.</p>`+e.draws.map((d,j)=>{const trial=trials?.[j],defer=d.action==='defer',reached=!!trial||defer&&isComplete&&j===trials.length&&run.event_fallbacks[String(e.id)];const label=defer?'Defer to ordinary GCTS':trial?`Level ${trial.item.level} sequence · cells ${trial.item.members.map(k=>k[0]+1).join(', ')}`:'Sampled fragment preference';return `<p class="${isComplete&&!reached?'censored':''}"><strong>${j+1}. ${esc(label)}</strong> · probability ${d.probability.toFixed(5)}${trial?`<br>${math(['eq',trial.item.instance.before,trial.item.instance.after])}<br>Validation: ${esc(trial.trace.status)} · ${trial.trace.steps.length} actual base placements${trial.continuation_solved!==null?` · ${trial.continuation_solved?'continuation reaches the checked proof':'finite continuation exhausted'}`:''}`:''}<br>${!isComplete?'Unknown run: draw and context checked; complete continuation unavailable.':reached?'Choice actually reached.':'Sampled suffix not reached; no training credit.'}</p>`;}).join('');}
  else el('decision').textContent='This lane has no learned-policy event. The plain or authored-prior control uses the same complete primitive graph.';
  el('work').innerHTML=`<p>Search: ${fmt(r.seconds)} s · cold request: ${fmt(run.cold_seconds)} s</p><p>Fresh catalog: ${fmt(run.catalog_build_seconds)} s</p><p>${r.candidate_universe.toLocaleString()} base candidate types · ${r.index_instances.toLocaleString()} checked-fragment instances</p><p>Policy inference: ${fmt(r.policy_seconds)} s · proposal trials: ${r.stats.proposal_trials||0}</p>${run.hierarchy?`<p>${run.hierarchy.original_root_lines} original root lines · ${run.hierarchy.root_lines} hierarchy root lines · ${run.hierarchy.definitions} checked definitions</p>`:''}${run.native?`<p>Native checker: ${esc(run.native.status)} · ${run.native.steps.toLocaleString()} instructions · ${fmt(run.native.wall_seconds)} s</p>`:''}`;
  el('certificate').innerHTML=run.hierarchy?run.hierarchy.proof.map((p,i)=>`<p><code>${i+1}: ${esc(p.rule)}</code><br>${math(p.formula)}</p>`).join(''):'No complete proof certificate.';typesetVisible();
}
async function start(){
  const responses=await Promise.all([fetch('proof-policy-view-001.json?v=20261009-r31.1'),fetch('proof-policy-tests-001.json?v=20261009-r31.1')]);for(const r of responses)if(!r.ok)throw Error(`HTTP ${r.status}`);const [view,tests]=await Promise.all(responses.map(r=>r.json()));data=view;
  data.cases.forEach((row,i)=>{const o=document.createElement('option');o.value=i;o.textContent=row.problem.label;el('statement').append(o);});el('statement').value='6';
  el('cost-rows').innerHTML=data.seeds.map(s=>Object.entries(data.totals[String(s.seed)]).map(([lane,t])=>{const setup=data.compile_seconds+(lane==='base'?0:data.library_seconds)+(lane==='trained'?data.training_catalog_seconds+s.training_seconds:0);return `<tr><td>${s.seed}</td><td>${esc(lanes[lane])}</td><td>${t.verified} / ${t.exhausted} / ${t.unknown}</td><td>${t.nodes} / ${t.attempts}</td><td>${fmt(t.cold_seconds)}</td><td>${fmt(t.policy_seconds)}</td><td>${fmt(t.cold_seconds+setup)}</td></tr>`;}).join('')).join('');
  el('cost-detail').textContent=`Shared native compile: ${fmt(data.compile_seconds)} s · freshly discovered library and whole-library gate: ${fmt(data.library_seconds)} s · training catalogs: ${fmt(data.training_catalog_seconds)} s. Whole producer: ${fmt(data.total_seconds)} s. Peak driver ${(data.peak_driver_memory_bytes/1048576).toFixed(2)} MiB includes accumulated artifacts and catalogs; no per-lane memory ranking.`;
  el('test-status').textContent=`All ${tests.passed} tests pass (${fmt(tests.seconds)} wall seconds). Independent audit passed in ${fmt(data.independent_audit.seconds)} seconds. The small projection pins the full artifact and exporter by SHA-256.`;
  el('load').textContent='';el('seed').addEventListener('change',()=>{weights();resetEvent();});el('episode').addEventListener('input',weights);el('statement').addEventListener('change',resetEvent);el('lane').addEventListener('change',resetEvent);el('event').addEventListener('change',render);weights();resetEvent();
}
start().catch(e=>{el('load').textContent=`Evidence could not be loaded: ${e.message}`;console.error(e);});
