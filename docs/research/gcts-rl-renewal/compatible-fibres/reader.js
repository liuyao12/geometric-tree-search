'use strict';
// Saved metadata display only. No search, model, inference or scientific replay.
const byId=id=>document.getElementById(id),math=s=>`\\(${s}\\)`;
function node(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
async function main(){const r=await fetch('report-data.json');if(!r.ok)throw Error('Missing saved report data');const d=await r.json();
for(const s of d.stages){const tr=node('tr');for(const x of [s.label,s.outcome,math((s.native_launch_to_postprobe_ns/1e9).toFixed(6)+'\\,\\mathrm{s}'),math((s.peak_bytes/1048576).toFixed(3)+'\\,\\mathrm{MiB}')])tr.append(node('td',x));byId('metrics').append(tr);}
byId('worker-error').textContent=d.worker_error;
for(const x of d.evidence){const li=node('li'),a=node('a',x.label);a.href=x.href;li.append(a);byId('evidence-links').append(li);}
await MathJax.startup.promise;await MathJax.typesetPromise([byId('metrics')]);document.body.dataset.savedReaderReady='true';}
main().catch(e=>{document.body.dataset.savedReaderFailed='true';document.querySelector('.lead').textContent='Saved reader failed: '+e.message;});
