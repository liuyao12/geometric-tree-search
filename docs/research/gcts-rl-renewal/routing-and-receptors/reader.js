'use strict';
(async()=>{
  const response=await fetch('report-data.json?v=4300ecf0cd4f',{cache:'no-cache'});
  if(!response.ok)throw new Error('Report data unavailable');
  const data=await response.json();
  const math=value=>'\\('+value+'\\)';
  document.querySelector('#duration').textContent=math((data.native_launch_to_postprobe_ns/1e9).toFixed(3)+'\\,\\mathrm{s}');
  document.querySelector('#markers').textContent=math(data.complete_marker_line_count+'/16');
  const max=Math.max(...data.intervals.map(x=>x.inclusive_native_ns));
  for(const interval of data.intervals){
    const row=document.createElement('div');row.className='phase-row';
    const label=document.createElement('div');
    const code=document.createElement('code');code.textContent=interval.from_label+' → '+interval.to_label;
    const bar=document.createElement('div');bar.className='bar';bar.style.width=(100*interval.inclusive_native_ns/max)+'%';
    label.append(code,bar);
    const time=document.createElement('div');time.className='time';time.textContent=math((interval.inclusive_native_ns/1e6).toFixed(2)+'\\,\\mathrm{ms}');
    row.append(label,time);document.querySelector('#phase-list').append(row);
  }
  for(const entry of data.evidence){const item=document.createElement('li');const a=document.createElement('a');a.href=entry.href;a.textContent=entry.label;item.append(a);document.querySelector('#evidence-list').append(item);}
  if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise();}
  document.body.dataset.ready='true';
})().catch(error=>{document.body.dataset.error=error.message;document.querySelector('#duration').textContent='Report failed to load';});
