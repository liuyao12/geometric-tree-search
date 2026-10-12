(() => {
  'use strict';
  const data=JSON.parse(document.getElementById('saved-data').textContent);
  const selector=document.getElementById('event-selector');
  const summary=document.getElementById('event-summary');
  const counters=document.getElementById('event-counters');
  const math=value=>'\\('+String(value)+'\\)';
  function update(){
    const item=data.events[Number(selector.value)], event=item.event;
    if(window.MathJax?.typesetClear)window.MathJax.typesetClear([summary,counters]);
    summary.innerHTML='Observation '+math(item.index)+', at '+math(item.worker_elapsed_seconds)+' seconds on the worker clock. <code>'+event.phase+'</code> / <code>'+event.milestone+'</code>.';
    counters.replaceChildren();
    for(const [key,value] of Object.entries(event.counters)){
      const term=document.createElement('dt'),definition=document.createElement('dd'),code=document.createElement('code');
      code.textContent=key;term.append(code);definition.textContent='\\('+String(value)+'\\)';counters.append(term,definition);
    }
    if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([summary,counters]);
  }
  selector.addEventListener('input',update);
})();
