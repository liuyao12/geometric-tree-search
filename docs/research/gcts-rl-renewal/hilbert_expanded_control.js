/* Exact audited fixed/learned comparison; no proof search in the reader. */
'use strict';
(() => {
  const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),num=x=>Number(x).toLocaleString(undefined,{maximumFractionDigits:3});
  const name=s=>String(s).replace(/([_{}%&#$])/g,'\\$1');
  const term=t=>t[0]==='var'?'\\mathit{'+name(t[1])+'}':t[2].length?'\\operatorname{'+name(t[1])+'}('+t[2].map(term).join(',')+')':'\\mathit{'+name(t[1])+'}';
  function formula(f){
    switch(f[0]){
      case 'bot':return '\\bot';case 'top':return '\\top';
      case 'pred':return '\\operatorname{'+name(f[1])+'}('+f[2].map(term).join(',')+')';
      case 'eq':return term(f[1])+'='+term(f[2]);
      case 'not':return '\\neg\\bigl('+formula(f[1])+'\\bigr)';
      case 'and':case 'or':case 'imp':return '\\bigl('+formula(f[1])+({'and':'\\land ','or':'\\lor ','imp':'\\Rightarrow '})[f[0]]+formula(f[2])+'\\bigr)';
      case 'all':case 'ex':return (f[0]==='all'?'\\forall ':'\\exists ')+'\\mathit{'+name(f[1])+'}.\\;'+formula(f[2]);
      default:throw new Error('Unknown exact formula tag '+f[0]);
    }
  }
  const math=f=>'\\('+formula(f)+'\\)';
  const typeset=()=>{if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise().catch(e=>console.error(e));};
  function explanation(c,defs){
    const lines=(c.inputs||[]).map(x=>x+1).join(', ');
    if(c.rule==='axiom')return c.name==='common-distinct-points'?'Use the given common distinct-point hypothesis.':c.name==='extra-incidence'?'Use the given extra incidence fact.':c.name==='extra-incidence-trigger'?'Use the given implication yielding the extra incidence fact.':'Use the declared theory axiom '+c.name+'.';
    if(c.rule==='mp')return 'Apply modus ponens to lines '+(c.antecedent+1)+' and '+(c.implication+1)+'.';
    if(c.rule==='block')return (defs[c.name]?.level===2?'Apply the searched incidence-transport receptor':'Apply the admitted '+(defs[c.name]?.family||'logical')+' interface')+' using lines '+lines+'.';
    if(c.rule==='assume')return 'Use a declared local input assumption.';
    if(c.rule==='refl')return 'Use reflexivity of equality: the named object is equal to itself.';
    if(c.rule==='tautology')return 'Use a propositional tautology checked by the kernel.';
    if(c.rule==='generalize')return 'Apply the checked generalization rule to line '+(c.source+1)+'.';
    return 'Apply the native '+c.rule+' rule.';
  }
  function tile(t){
    const marks=t.marks.map(([p,v])=>{const kind=p[1]===0?'formula':p[1]===1?'command':p[1]===90?'mode':'source';return '<span class="mark-'+kind+'"><code>'+esc(JSON.stringify(p))+' : '+esc(v)+'</code></span>';}).join('<br>');
    return '<div class="tile"><strong>\\('+({I1:'I_1',I2:'I_2'}[t.role]||t.role)+'\\)</strong><div>\\(t('+t.occupancy[0][0].join(',')+')=1\\)</div><div class="marks">'+marks+'</div></div>';
  }
  function show(data,index){
    const o=data.observations[index],a=o.audit,spec=data.plan.cases.find(c=>c.id===o.item.case_id),defs=Object.fromEntries(data.inventories[o.item.language].definitions.map(d=>[d.name,d]));
    $('run').value=String(index);
    $('proof-status').textContent=o.native?'Whole native '+o.native.result.status+'; '+a.fixed_attempts+' fixed attempts versus '+a.learned_attempts+' learned attempts. Certificate '+o.native.binding.origin+' query '+o.native.binding.query+'.':'Complete finite marked boundary exhausted. This is not a refutation of the assertion; no proof rows or native proof are claimed.';
    $('proof-target').innerHTML=math(spec.target);
    $('proof').innerHTML=o.rows.map(row=>'<article class="proof-row"><p><strong>Line '+row.index+'.</strong> '+esc(explanation(row.command,defs))+'</p><div class="tile-scroll"><div class="tile-line">'+row.tiles.map(tile).join('')+'</div></div><div class="formula">'+math(row.command.formula)+'</div><details><summary>Decoded command and marking words</summary><pre>'+esc(JSON.stringify({command:row.command,tiles:row.tiles},null,2))+'</pre></details></article>').join('');
    $('native-proof').innerHTML=o.native?'<p>The actual accepted request contains '+o.native.request.blocks.length+' definitions and '+o.native.request.proof.length+' top-level commands. Every dependent definition below is part of the native certificate.</p>'+o.native.request.blocks.map(d=>'<details><summary><code>'+esc(d.name)+'</code> · '+d.proof.length+' actual commands</summary>'+d.proof.map((c,i)=>'<p>Native line '+(i+1)+': <code>'+esc(c.rule)+'</code></p><div class="formula">'+math(c.formula)+'</div>').join('')+'<pre>'+esc(JSON.stringify(d,null,2))+'</pre></details>').join(''):'<p>No whole proof certificate.</p>';
    typeset();
  }
  function costs(s){
    const inc=s.incremental_costs,old=s.frozen_paired_costs,shared=s.historical_shared_costs,feature=s.feature_cost_accounting;
    const rows=[['New production elapsed',inc.production_seconds],['New preparation (includes native setup)',inc.preparation_seconds],['New fixed searches',inc.fixed_search_seconds],['New fixed model setup',inc.fixed_model_setup_seconds],['New worker elapsed (includes setup/search/serialization)',inc.fixed_worker_wall_seconds],['New certification elapsed (includes replay waiting)',inc.certification_wall_seconds],['Fresh native production',inc.fresh_native_production_seconds],['New independent audit elapsed',inc.independent_audit_seconds],['Fresh native independent replay',inc.independent_fresh_native_replay_seconds],['Prior input binding reconstruction',inc.independent_prior_input_binding_seconds],['Frozen paired learned searches',old.search_seconds],['Frozen paired learned model setup',old.model_setup_seconds],['Historical shared production',shared.production_seconds],['Historical shared native production',shared.native_production_seconds],['Historical shared native replay',shared.native_replay_seconds]];
    $('cost-table').innerHTML='<div class="table-scroll"><table><thead><tr><th>Measured component</th><th>Seconds</th></tr></thead><tbody>'+rows.map(([l,v])=>'<tr><td>'+l+'</td><td>'+num(v)+'</td></tr>').join('')+'</tbody></table></div><p>'+inc.fresh_native_queries+' fresh native computations; '+num(inc.fresh_native_micro_steps)+' fresh microsteps. Peak fixed worker RSS: '+num(inc.peak_worker_rss_bytes/1048576)+' MiB. Exact acceptance reuse: '+s.native_prior_reuse_observations+' prior-study observations and '+s.native_new_reuse_observations+' independently replayed new-study observations.</p><p>Inclusive proposal time, which charges feature construction and scoring: fixed '+num(feature.fixed_proposal_seconds)+' seconds; paired learned '+num(feature.paired_learned_proposal_seconds)+' seconds. Scored feature vectors: '+num(feature.fixed_feature_vectors)+' fixed versus '+num(feature.paired_learned_feature_vectors)+' learned; expanded marking positions assessed: '+num(feature.fixed_expanded_mark_positions)+' versus '+num(feature.paired_learned_expanded_mark_positions)+'.</p><p>'+esc(feature.scope)+'</p>';
  }
  function render(data){
    const s=data.summary,rows=data.observations;
    $('assessment').textContent=s.directions.learned_fewer+' paired observations use fewer attempts with learned weights; '+s.directions.equal+' tie; '+s.directions.learned_more+' use more. The two deterministic repetitions duplicate each case’s attempt count. These differences isolate the weight vector on this finite benchmark, while keeping the limits of frozen transfer and total costs visible.';
    $('metrics').innerHTML=[['Audited control runs',s.observations],['Native accepted proof observations',s.proof_observations],['Finite-boundary exhaustions',s.finite_exhaustions],['Search or native unknowns',s.search_unknowns+s.native_whole_unknowns]].map(([label,v])=>'<div class="metric"><strong>'+num(v)+'</strong>'+label+'</div>').join('');
    $('pairs').innerHTML=rows.map(o=>'<tr><td>'+esc(o.item.case_id)+'</td><td>'+esc(o.item.language)+'</td><td>'+o.item.repetition+'</td><td>'+o.audit.fixed_attempts+'</td><td>'+o.audit.learned_attempts+'</td><td>'+esc(o.audit.certification)+'</td><td>'+(o.audit.identical_structural_tree?'Yes':'No')+'</td></tr>').join('');
    const chart=rows.filter(o=>o.item.repetition===1),max=Math.max(...chart.flatMap(o=>[o.audit.fixed_attempts,o.audit.learned_attempts])),scale=450/max;
    $('chart').innerHTML='<svg class="chart" viewBox="0 0 880 '+(chart.length*48+28)+'" role="img" aria-label="Fixed versus learned attempts with equal word-expanded features"><rect width="880" height="'+(chart.length*48+28)+'" fill="white"/>'+chart.map((o,i)=>{const y=i*48+15;return '<text x="0" y="'+(y+13)+'" font-size="12">'+esc(o.item.case_id.replace('fresh-','')+' / '+o.item.language)+'</text><rect class="bar-fixed" x="305" y="'+y+'" width="'+o.audit.fixed_attempts*scale+'" height="12"/><text x="'+(310+o.audit.fixed_attempts*scale)+'" y="'+(y+11)+'" font-size="11">'+o.audit.fixed_attempts+'</text><rect class="bar-learned" x="305" y="'+(y+15)+'" width="'+o.audit.learned_attempts*scale+'" height="12"/><text x="'+(310+o.audit.learned_attempts*scale)+'" y="'+(y+26)+'" font-size="11">'+o.audit.learned_attempts+'</text>';}).join('')+'</svg>';
    $('weights').innerHTML='<p>Fixed weights:</p><div class="formula">\\(('+data.plan.fixed_weights.map(x=>Number(x).toFixed(5)).join(',')+')\\)</div><p>Frozen learned weights:</p><div class="formula">\\(('+data.plan.paired_weights.map(x=>Number(x).toFixed(5)).join(',')+')\\)</div>';
    $('run').innerHTML=rows.map((o,i)=>'<option value="'+i+'">'+esc(o.item.tag)+'</option>').join('');$('run').onchange=e=>show(data,Number(e.target.value));
    const spec=data.plan.cases[0],H=spec.theory.axioms['common-distinct-points'];$('axiom').innerHTML=math(spec.theory.axioms['I.2-uniqueness']);$('hypothesis').innerHTML='\\(H='+formula(H)+'\\)';$('sequent').innerHTML='\\(H,\\;'+formula(spec.theory.axioms['extra-incidence'])+'\\;\\vdash\\;'+formula(spec.target)+'\\)';
    costs(s);$('audit-summary').textContent='Independent audit: '+s.audit.complete_models+' complete models, '+num(s.audit.nodes)+' new tree nodes, '+s.audit.events+' policy events and '+s.audit.hints+' hints. All 16 paired learned trees were also freshly replayed. Prior native reuse: '+s.native_prior_reuse_observations+' observations.';
    $('artifact-list').innerHTML=data.artifacts.map(a=>'<li><a href="'+esc(a.path.split('/').pop())+'">'+esc(a.path.split('/').pop())+'</a> · '+num(a.bytes)+' bytes · <code>'+a.sha256+'</code></li>').join('');
    show(data,rows.findIndex(o=>o.native));typeset();
  }
  fetch('hilbert_expanded_control_reader_001.json?v=20261011-hec1').then(r=>{if(!r.ok)throw new Error('Reader fetch failed');return r.json();}).then(render).catch(e=>{$('assessment').textContent='Reader unavailable: '+e.message;console.error(e);});
})();
