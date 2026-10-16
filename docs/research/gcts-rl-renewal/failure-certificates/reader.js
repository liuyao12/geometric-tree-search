'use strict';
// Saved-data renderer. No theorem prover, local checker or marking learner.
const math=s=>'\\('+s+'\\)';
const esc=s=>String(s).replace(/[\\{}_%&#$]/g,c=>'\\'+c);
function term(t){if(t[0]==='var')return esc(t[1]);const a=t[2].map(term);if(t[1]==='zero')return'0';if(t[1]==='succ')return`S(${a[0]})`;if(t[1]==='add')return`(${a[0]}+${a[1]})`;return`\\operatorname{${esc(t[1])}}(${a.join(',')})`;}
function formula(f){switch(f[0]){case'bot':return'\\bot';case'eq':return`${term(f[1])}=${term(f[2])}`;case'pred':return`\\operatorname{${esc(f[1])}}(${f[2].map(term).join(',')})`;case'not':return`\\neg\\bigl(${formula(f[1])}\\bigr)`;case'all':return`\\forall ${esc(f[1])}\\;\\bigl(${formula(f[2])}\\bigr)`;case'imp':case'and':case'or':return`\\bigl(${formula(f[1])}\\bigr)${{imp:'\\Rightarrow',and:'\\land',or:'\\lor'}[f[0]]}\\bigl(${formula(f[2])}\\bigr)`;default:throw Error('Unsupported saved formula');}}
function cellrow(parent,values,cls){const tr=document.createElement('tr');if(cls)tr.className=cls;for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td)}parent.append(tr);return tr;}
function point(label,content,cls){const d=document.createElement('div');d.className='point';const x=document.createElement('span');x.textContent=label;const box=document.createElement('span');box.className='square '+cls;box.textContent=content;d.append(x,box);return d;}
(async()=>{
 const res=await fetch('report-data.json');if(!res.ok)throw Error('Saved certification record unavailable');const d=await res.json();
 for(const [id,key] of [['lead','lead'],['outcome','outcome'],['assessment-text','assessment'],['next-step','next_step']])document.getElementById(id).textContent=d[key];
 for(const item of d.metrics){const e=document.createElement('div');e.className='metric';const title=document.createElement('strong');title.textContent=item.label;const val=document.createElement('span');val.textContent=item.value;e.append(title,val);document.getElementById('metrics').append(e);}
 for(const c of d.controls)cellrow(document.getElementById('control-rows'),[c.name,c.result,c.observed]);
 for(const l of d.links){const li=document.createElement('li');const a=document.createElement('a');a.href=l.href;a.textContent=l.label;li.append(a);document.getElementById('links').append(li);}
 if(window.MathJax?.startup?.promise)await MathJax.startup.promise;
 async function show(arm){const s=d.samples.find(x=>x.arm===arm);if(!s)throw Error('Missing saved sample');const parts=['sample-intro','point-board','sample-english','sample-rows','lemma-scope','rule-rows'];if(window.MathJax?.typesetClear)MathJax.typesetClear(parts.map(id=>document.getElementById(id)));
  document.getElementById('sample-intro').textContent=s.intro;document.getElementById('sample-english').textContent=s.english;
  const board=document.getElementById('point-board');board.replaceChildren();const path=document.createElement('div');path.className='remote-path';const wire=document.createElement('div');wire.className='wire';wire.setAttribute('aria-label','Remote formula marking from consumer to required premise');path.append(point(math('r=0'),'empty','empty dead'),wire,point(math('r=23'),s.tile_label,''));board.append(path);const offsets=document.createElement('div');offsets.className='offsets';offsets.textContent=s.state.m.filter(x=>x[0][0]>=2).map(x=>math('m('+x[0][0]+','+x[0][1]+')=\\operatorname{offset}('+x[1][1]+')')).join(' · ');board.append(offsets);
  const rows=document.getElementById('sample-rows');rows.replaceChildren();for(const r of s.visible_rows){const mark=s.state.m.find(x=>x[0][0]===1&&x[0][1]===r)?.[1];const selected=s.state.selected.find(x=>x.translation[1]===r);const tr=cellrow(rows,[math('r='+r),selected?s.tile_label:'empty',mark?.[0]==='formula'?math(formula(JSON.parse(mark[1]))):'unassigned'],r===0?'dead-row':'');tr.dataset.row=String(r);tr.lastChild.className=mark?'formula purple':'gray';}
  document.getElementById('local-certificate').textContent=JSON.stringify(s.local_certificate,null,2);document.getElementById('projection-certificate').textContent=JSON.stringify(s.projection_certificate,null,2);document.getElementById('lemma-scope').textContent=s.lemma;
  const rr=document.getElementById('rule-rows');rr.replaceChildren();for(const r of s.rule_explanations)cellrow(rr,[r.rule,r.reason]);
  for(const b of document.querySelectorAll('[data-arm]'))b.setAttribute('aria-pressed',String(b.dataset.arm===arm));document.body.dataset.sampleArm=arm;if(window.MathJax?.typesetPromise)await MathJax.typesetPromise();
 }
 for(const b of document.querySelectorAll('[data-arm]'))b.addEventListener('click',()=>show(b.dataset.arm).catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('sample-english').textContent=e.message}));
 await show('canonical-search');document.body.dataset.savedReaderReady='true';
})().catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('lead').textContent=e.message;});
