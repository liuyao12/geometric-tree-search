'use strict';
const captions=[
 ['Joint interface','One binding fits the ordered receptors and complete two-MP expansion.'],
 ['Wrong bindings','Port order and inconsistent repeated parameters are rejected.'],
 ['Capture avoidance','Typed abstractions retain free variables through binder renaming.'],
 ['Context and scope','Eigenvariable and undeclared symbol violations are rejected.'],
 ['Nested composition','Exposed outputs and original hypothesis occurrences remain explicit.'],
 ['Identity and forgery','A forged expansion and invalid dependency identity are rejected.'],
 ['Native local cluster','Pending inputs stay obligations under original marked point checks.'],
 ['Original rule forms','Five positive native paths; empty-context assumption is rejected.'],
 ['Host provenance','Wrong epoch and wrong physical port source are rejected.'],
 ['Physical interfaces','Exact sharing, remote conflicts, unused inputs and nested distinctness.'],
 ['Unknown and interruption','Incomplete work stays unknown; declared interruption propagates.'],
 ['State and costs','Input state and cumulative checking costs remain inspectable.']];
async function typeset(){if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise();}}
// Display formatting of retained syntax only; no inference or rule admission.
function tex(ast){const k=ast[0];if(k==='var')return ast[1];if(k==='bot')return '\\bot';
 if(k==='all')return '\\forall '+ast[1]+'\\,('+tex(ast[2])+')';
 if(k==='eq')return tex(ast[1])+'='+tex(ast[2]);if(k==='imp')return '('+tex(ast[1])+'\\to '+tex(ast[2])+')';
 if(k==='fun'){const a=ast[2];if(ast[1]==='add')return '('+tex(a[0])+'+'+tex(a[1])+')';if(ast[1]==='succ')return 'S('+tex(a[0])+')';return '\\operatorname{'+ast[1]+'}'+(a.length?'('+a.map(tex).join(',')+')':'');}
 throw new Error('Unsupported display syntax');}
function showPoints(fixture){
 const wrap=document.getElementById('point-view');if(!fixture){wrap.textContent='No native point fixture qualified in this run.';return;}
 const p=document.createElement('p');p.textContent='Actual native fixture: \\(A=C='+tex(fixture.formula_A)+'\\), \\(B=\\bot\\). These are open-premise component data, not a discovered proof.';wrap.append(p);
 const cells=new Map();for(const member of fixture.members){for(const [point,value]of member.global_t_values)cells.set(point.join(','),'\\('+value+'\\)');for(const [point,value]of member.global_m_values){let label;
  if(point[0]===1){const f=value[1],A=JSON.stringify(fixture.formula_A);label=f===A?'A':f==='["bot"]'?'\\bot':f===JSON.stringify(['imp',fixture.formula_A,['bot']])?'A\\to\\bot':'\\bot\\to A';}
  else label=Array.isArray(value)?String(value[1]):String(value);cells.set(point.join(','),'\\('+label+'\\)');}}
 const table=document.createElement('table');table.className='point-table';const head=document.createElement('thead'),tr=document.createElement('tr');
 for(const label of['Row','\\(t\\)','Formula','First read','Second read','Remote']){const th=document.createElement('th');th.textContent=label;tr.append(th);}head.append(tr);table.append(head);const body=document.createElement('tbody');
 for(let row=0;row<=4;row++){const tr=document.createElement('tr'),th=document.createElement('th');th.textContent='\\('+row+'\\)';tr.append(th);for(let channel=0;channel<=4;channel++){const td=document.createElement('td');td.className='ch'+channel;td.textContent=cells.get(channel+','+row)??'\\(\\ast\\)';tr.append(td);}body.append(tr);}table.append(body);wrap.append(table);
}
async function boot(){
 const response=await fetch('report-data.json?v=bb335ce9a639',{cache:'no-cache'});if(!response.ok)throw new Error('Saved report unavailable');
 const data=await response.json();const accepted=data.component_controls_accepted===true;
 const status=document.getElementById('result');status.classList.toggle('fail',!accepted);
 status.textContent=accepted?'All twelve infrastructure assertions passed in the one frozen native run. The local lemma bridge is qualified only for these fixtures.':'The bounded component run did not qualify the new bridge. Its original failure is retained; no unchanged rerun was used to replace it.';
 document.getElementById('case-count').textContent='\\('+data.qualified_component_case_count+'/12\\)';
 document.getElementById('duration').textContent='\\('+(data.native_launch_to_postprobe_ns/1e9).toFixed(3)+'\\,\\mathrm{s}\\)';
 const cases=document.getElementById('case-list');captions.forEach(([title,scope],i)=>{
  const article=document.createElement('article');article.className='case';const h=document.createElement('strong');h.textContent=title;
  const tag=document.createElement('span');tag.className=accepted?'pass':'unknown';tag.textContent=accepted?'Passed':'Not qualified by this run';
  const p=document.createElement('span');p.textContent=scope;article.append(h,tag,p);cases.append(article);
 });
 const links=document.getElementById('evidence-list');for(const item of data.evidence){const li=document.createElement('li'),a=document.createElement('a');a.href=item.href;a.textContent=item.label;li.append(a);links.append(li);}
 if(data.expanded_result_href){const a=document.createElement('a');a.href=data.expanded_result_href;a.textContent='Inspect the complete saved component result and point packets';document.getElementById('packet-link').append(a);}
 showPoints(data.point_fixture);
 if(data.raw_error){const p=document.getElementById('error-detail');p.hidden=false;p.textContent=data.raw_error;}
 await typeset();document.body.dataset.ready='true';
}
for(const [id,show]of[['show-boundary',true],['show-members',false]])document.getElementById(id).addEventListener('click',()=>{
 document.getElementById('boundary-view').hidden=!show;document.getElementById('member-view').hidden=show;
 document.getElementById('show-boundary').setAttribute('aria-pressed',String(show));document.getElementById('show-members').setAttribute('aria-pressed',String(!show));typeset();
});
boot().catch(error=>{document.getElementById('result').textContent='The saved result could not be loaded. No result is inferred.';document.getElementById('result').classList.add('fail');console.error(error);});
