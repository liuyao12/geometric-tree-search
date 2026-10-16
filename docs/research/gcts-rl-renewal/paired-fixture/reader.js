'use strict';
(async()=>{
 const r=await fetch('report-data.json');if(!r.ok)throw Error('Saved report unavailable');const d=await r.json();
 for(const [id,key] of [['lead','lead'],['outcome','outcome'],['observation-text','observation_text'],['assessment-text','assessment'],['next-step','next_step'],['trace','trace']])document.getElementById(id).textContent=d[key];
 const seconds=x=>'\\('+(x/1e9).toFixed(6)+'\\,\\mathrm{s}\\)';
 function row(parent,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td)}document.getElementById(parent).append(tr)}
 const max=Math.max(...d.stages.map(x=>x.native_ns),20e9);
 for(const x of d.stages){row('metrics',[x.label,x.outcome,seconds(x.native_ns),'\\('+(x.peak_bytes/1048576).toFixed(2)+'\\,\\mathrm{MiB}\\)']);const wrapper=document.createElement('div');wrapper.className='time-row';const label=document.createElement('div');label.className='time-label';const a=document.createElement('span');a.textContent=x.label;const b=document.createElement('span');b.textContent=seconds(x.native_ns);label.append(a,b);const track=document.createElement('div');track.className='track';const bar=document.createElement('div');bar.className='bar'+(x.qualified?'':' unknown');bar.style.width=(100*x.native_ns/max)+'%';track.append(bar);wrapper.append(label,track);document.getElementById('time-bars').append(wrapper)}
 const number=x=>x==null?'Unavailable':'\\('+x+'\\)';
 for(const x of d.roles)row('roles',[x.role,number(x.row),number(x.selected_count),x.elapsed_ns==null?'Unavailable':seconds(x.elapsed_ns)]);
 for(const x of d.links){const li=document.createElement('li');const a=document.createElement('a');a.textContent=x.label;a.href=x.href;li.append(a);document.getElementById('links').append(li)}
 if(window.MathJax?.typesetPromise)await MathJax.typesetPromise();document.body.dataset.savedReaderReady='true';
})().catch(e=>{document.body.dataset.savedReaderFailed='true';document.getElementById('lead').textContent=e.message;});
