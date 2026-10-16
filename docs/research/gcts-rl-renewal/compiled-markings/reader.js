'use strict';
const math=s=>'\\('+s+'\\)';
function row(parent,values,cls){const tr=document.createElement('tr');if(cls)tr.className=cls;for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td)}parent.append(tr);return tr;}
(async()=>{
 const res=await fetch('report-data.json');if(!res.ok)throw Error('Saved marking report unavailable');const d=await res.json();
 for(const[id,key]of[['lead','lead'],['outcome','outcome'],['scope-text','scope_text'],['assessment-text','assessment'],['next-step','next_step']])document.getElementById(id).textContent=d[key];
 for(const m of d.metrics){const e=document.createElement('div');e.className='metric';const label=document.createElement('strong');label.textContent=m.label;const value=document.createElement('span');value.textContent=m.value;e.append(label,value);document.getElementById('metrics').append(e)}
 for(const c of d.controls)row(document.getElementById('control-rows'),[c.name,c.status,c.observed]);
 for(const l of d.links){const li=document.createElement('li');const a=document.createElement('a');a.href=l.href;a.textContent=l.label;li.append(a);document.getElementById('links').append(li)}
 document.getElementById('marking').textContent=JSON.stringify(d.marking,null,2);let chosen=d.fixtures[0].id,phase='marked';
 if(window.MathJax?.startup?.promise)await MathJax.startup.promise;
 async function render(){const f=d.fixtures.find(x=>x.id===chosen),view=f[phase];const ids=['fixture-intro','verdict','match-display','point-rows','fixture-english'];if(window.MathJax?.typesetClear)MathJax.typesetClear(ids.map(id=>document.getElementById(id)));
  document.getElementById('fixture-intro').textContent=f.intro;document.getElementById('fixture-english').textContent=f.english;
  const verdict=document.getElementById('verdict');verdict.textContent=view.summary;verdict.className='callout '+(view.compatible?'accepted':'rejected');
  const display=document.getElementById('match-display');display.replaceChildren();const tile=document.createElement('span');tile.className='square';tile.textContent=f.tile_label;const arrow=document.createElement('span');arrow.className='match-wire';arrow.textContent=phase==='marked'?'added point markings':'original point markings';const outcome=document.createElement('span');outcome.className='point-result '+(view.compatible?'pass':'fail');outcome.textContent=view.compatible?'compatible':'conflict';display.append(tile,arrow,outcome);
  const rows=document.getElementById('point-rows');rows.replaceChildren();for(const p of view.points)row(rows,[math('('+p.point.join(',')+')'),p.state_present?math(String(p.state_value)):'absent',p.candidate_present?math(String(p.candidate_value)):'absent'],p.conflict?'dead-row':'');if(!view.points.length)row(rows,['No auxiliary marking points','absent','absent']);
  document.getElementById('prototype').textContent=JSON.stringify(f.prototype,null,2);document.getElementById('comparison').textContent=JSON.stringify(view.records,null,2);
  for(const b of document.querySelectorAll('[data-fixture]'))b.setAttribute('aria-pressed',String(b.dataset.fixture===chosen));for(const b of document.querySelectorAll('[data-phase]'))b.setAttribute('aria-pressed',String(b.dataset.phase===phase));document.body.dataset.fixture=chosen;document.body.dataset.markPhase=phase;document.body.dataset.compatible=String(view.compatible);if(window.MathJax?.typesetPromise)await MathJax.typesetPromise();
 }
 function failed(e){document.body.dataset.savedReaderFailed='true';document.getElementById('verdict').textContent=e.message}
 for(const f of d.fixtures){const b=document.createElement('button');b.type='button';b.dataset.fixture=f.id;b.textContent=f.label;b.addEventListener('click',()=>{chosen=f.id;render().catch(failed)});document.getElementById('fixtures').append(b)}
 for(const b of document.querySelectorAll('[data-phase]'))b.addEventListener('click',()=>{phase=b.dataset.phase;render().catch(failed)});
 await render();document.body.dataset.savedReaderReady='true';
})().catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('lead').textContent=e.message});
