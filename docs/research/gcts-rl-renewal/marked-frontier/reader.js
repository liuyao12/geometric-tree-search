'use strict';
// Saved-state rendering only. No model, search, proof checker or failure labeler.
const math=s=>'\\('+s+'\\)',esc=s=>String(s).replace(/[\\{}_%&#$]/g,c=>'\\'+c);
function term(t){if(t[0]==='var')return esc(t[1]);const a=t[2].map(term);if(t[1]==='zero')return'0';if(t[1]==='succ')return`S(${a[0]})`;if(t[1]==='add')return`(${a[0]}+${a[1]})`;return`\\operatorname{${esc(t[1])}}(${a.join(',')})`;}
function formula(f){switch(f[0]){case'bot':return'\\bot';case'eq':return`${term(f[1])}=${term(f[2])}`;case'pred':return`\\operatorname{${esc(f[1])}}(${f[2].map(term).join(',')})`;case'not':return`\\neg\\bigl(${formula(f[1])}\\bigr)`;case'all':return`\\forall ${esc(f[1])}\\;\\bigl(${formula(f[2])}\\bigr)`;case'imp':case'and':case'or':return`\\bigl(${formula(f[1])}\\bigr)${{imp:'\\Rightarrow',and:'\\land',or:'\\lor'}[f[0]]}\\bigl(${formula(f[2])}\\bigr)`;default:throw Error('Unsupported saved formula');}}
function row(parent,values){const tr=document.createElement('tr');for(const v of values){const td=document.createElement('td');td.textContent=v;tr.append(td)}document.getElementById(parent).append(tr);return tr}
(async()=>{
 const response=await fetch('report-data.json');if(!response.ok)throw Error('Saved report unavailable');const d=await response.json();
 for(const [id,key] of [['lead','lead'],['outcome','outcome'],['target-text','target_text'],['assessment-text','assessment'],['next-step','next_step']])document.getElementById(id).textContent=d[key];
 document.getElementById('target-formula').textContent=math(formula(d.target));document.getElementById('pending-formula').textContent=math(formula(d.pending_formula));
 const max=Math.max(20e9,...d.stages.map(x=>x.native_ns));
 for(const s of d.stages){const seconds=math((s.native_ns/1e9).toFixed(6)+'\\,\\mathrm{s}');row('metrics',[s.label,s.outcome,seconds,math((s.peak_bytes/1048576).toFixed(2)+'\\,\\mathrm{MiB}')]);const wrapper=document.createElement('div');wrapper.className='time-row';const label=document.createElement('div');label.className='time-label';label.textContent=s.label+' '+seconds;const track=document.createElement('div');track.className='track';const bar=document.createElement('div');bar.className='bar'+(s.qualified?'':' unknown');bar.style.width=100*s.native_ns/max+'%';track.append(bar);wrapper.append(label,track);document.getElementById('time-bars').append(wrapper)}
 for(const c of d.cases)row('case-rows',[c.case,c.status,c.status==='SKIPPED'?c.observed.reason:c.scope]);
 for(const t of d.target_diagnostics)row('target-diagnostics',[t.arm,...['nodes','branches','backtracks','advice_selected','forced'].map(k=>math(String(t[k])))]);
 for(const l of d.links){const li=document.createElement('li');const a=document.createElement('a');a.textContent=l.label;a.href=l.href;li.append(a);document.getElementById('links').append(li)}
 if(window.MathJax?.startup?.promise)await MathJax.startup.promise;
 async function phase(name){const p=d.phases[name],board=document.getElementById('boundary-rows');if(window.MathJax?.typesetClear)MathJax.typesetClear([board,document.getElementById('phase-explanation')]);board.replaceChildren();document.getElementById('phase-explanation').textContent=p.explanation;
  const selected=new Map(p.state.selected.map(x=>[x.translation[1],x.type_preimage.primitive_witness.rule]));const marks=new Map(p.state.m.filter(x=>x[0][0]===1).map(x=>[x[0][1],x[1]]));
  for(const r of [0,1,2,3,4,5,6,7,23]){const tr=row('boundary-rows',[math('r='+r),'','']);tr.dataset.row=String(r);const tile=document.createElement('span');tile.className='tile '+(selected.has(r)?'blue':'pending');tile.textContent=selected.has(r)?({axiom:'AX',generalize:'UG'}[selected.get(r)]||selected.get(r)):'empty';tr.children[1].append(tile);const mark=document.createElement('span');mark.className='mark '+(marks.has(r)?'assigned':'absent');mark.textContent=marks.has(r)?'assigned formula':'unassigned';tr.children[2].append(mark);if(r===p.mark_row){tr.classList.add('chosen');const label=document.createElement('small');label.textContent='MARK selects';tr.children[0].append(label)}}
  for(const b of document.querySelectorAll('[data-phase]'))b.setAttribute('aria-pressed',String(b.dataset.phase===name));document.body.dataset.controlPhase=name;if(window.MathJax?.typesetPromise)await MathJax.typesetPromise();
 }
 for(const b of document.querySelectorAll('[data-phase]'))b.addEventListener('click',()=>phase(b.dataset.phase).catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('phase-explanation').textContent=e.message}));
 await phase('initial');document.body.dataset.savedReaderReady='true';
})().catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('lead').textContent=e.message});
