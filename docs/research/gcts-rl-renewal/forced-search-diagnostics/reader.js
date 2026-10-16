'use strict';
// Literal saved metadata only. The mathematical search never executes here.
const $=id=>document.getElementById(id);
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const math=s=>'\\('+s+'\\)';
const seconds=ns=>math((ns/1e9).toFixed(6)+'\\,\\mathrm{s}');
async function main(){
  const response=await fetch('report-data.json?v=7e08e35e4d25');
  if(!response.ok)throw Error('Saved diagnostic data unavailable');
  const data=await response.json();
  $('lead').textContent=data.lead;
  for(const value of data.metrics){const box=el('div');box.className='metric';box.append(el('span',value.label),el('strong',value.text));$('metrics').append(box);}
  $('outcome-note').textContent=data.outcome;
  for(const row of data.markers){
    const tr=el('tr'),label=el('td');label.append(el('code',row.label));tr.append(label,el('td',seconds(row.fromLaunchNs)),el('td',row.fromPreviousMarkerNs===null?'First saved marker':seconds(row.fromPreviousMarkerNs)));$('marker-rows').append(tr);
  }
  for(const row of data.intervals){const box=el('div');if(row.unobserved)box.className='tail';const label=el('div');label.append(el(row.label.startsWith('GF_')?'code':'span',row.label));label.className='group-label';const track=el('div');track.className='track';const bar=el('div');bar.className='bar';bar.style.width=String(100*row.durationNs/data.nativeLifetimeNs)+'%';track.append(bar);box.append(label,track);$('group-chart').append(box);}
  $('tail-note').textContent=data.tail;
  $('marker-wire').textContent=data.markerWire;
  for(const row of data.callbacks){const tr=el('tr');tr.append(el('td',row.role),el('td',row.row===null?'Unavailable':math(String(row.row))),el('td',row.selectedCount===null?'Unavailable':math(String(row.selectedCount))),el('td',row.fromLaunchNs===null?'Unavailable':seconds(row.fromLaunchNs)));$('callback-rows').append(tr);}
  $('interpretation').textContent=data.interpretation;$('next-action').textContent=data.nextAction;
  $('saved-record').textContent=JSON.stringify(data.record,null,2);$('source-scope').textContent=JSON.stringify(data.sourceScope,null,2);
  for(const ref of data.links){const a=el('a',ref.label);a.href=ref.href;const li=el('li');li.append(a);$('evidence-links').append(li);}
  if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise();}
  document.body.dataset.savedDiagnosticReady='true';
}
main().catch(error=>{$('lead').textContent=error.message;document.body.dataset.savedDiagnosticFailed='true';});
