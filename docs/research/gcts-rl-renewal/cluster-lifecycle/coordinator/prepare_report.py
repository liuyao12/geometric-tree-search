"""Report only frozen sources and terminal observations; never runs research."""
import hashlib
import html
import json
import re
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load, project

HERE = Path(__file__).resolve().parent
GEO = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'
ARITH = ROOT / '.gcts-active/stochastic-replay-memory-v5-20261011'
GI = ROOT / '.gcts-active/hilbert-cluster-independent-20261011'
AI = ROOT / '.gcts-active/stochastic-replay-v5-independent-20261011'


def math(value):
    return r'\(' + html.escape(str(value)) + r'\)'


def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>' + ''.join('<th>'+h+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'


def main():
    # Root fills this after actual owned handles terminate and independent reviews
    # are pinned. The file is a projection selection, not scientific authority.
    selection = load(HERE / 'terminal-selection.json')
    assert selection['all_owned_handles_terminal'] is True
    ar = load(ROOT / selection['arithmetic_phase'])
    gl = load(ROOT / selection['geometry_lifetime'])
    go = load(ROOT / selection['geometry_outcome']) if selection.get('geometry_outcome') else None
    gir = load(ROOT / selection['geometry_independent_result']) if selection.get('geometry_independent_result') else None
    gil = load(ROOT / selection['geometry_independent_lifetime']) if selection.get('geometry_independent_lifetime') else None
    ar_review = load(ROOT / selection['arithmetic_terminal_review'])
    assert ar_review['status'].startswith('passed')
    a_pass = ar['status'] == 'passed_complete_loading_only_six_evaluation_replays'
    if a_pass:
        assert len(ar['observations']) == 6 and not ar['failed'] and not ar['unexecuted']
    g_pass = gl['status'] == 'passed_authored_tiny_lifecycle_full_lifetime'
    g_independent = bool(gil and gil['status'].startswith('passed'))
    if g_pass:
        assert go and go['status'] == 'passed_authored_synthetic_whole_cluster_lifecycle_pending_independent_gate'
    exclusions = {'publication.json','publication-staging.json','turn-result.json','task-files.json','local-validation.json','live-hash-checks.json','browser-validation.json','staged-whitespace-check.json'}
    files, origins, bindings = project([
        (str(GEO.relative_to(ROOT)), 'geometry', set()),
        (str(ARITH.relative_to(ROOT)), 'arithmetic', set()),
        (str(GI.relative_to(ROOT)), 'geometry-independent', set()),
        (str(AI.relative_to(ROOT)), 'arithmetic-independent', set()),
        (str(HERE.relative_to(ROOT)), 'coordinator', exclusions),
    ])
    def save(name, data):
        p=DEST/name;p.write_text(json.dumps(data,indent=2)+'\n');files.add(str(p.relative_to(ROOT)))
    def href(origin, label):
        found=next(e for e in origins if e['origin']==origin)
        return '<a href="'+html.escape(str(Path(found['path']).relative_to(Path(PREFIX))))+'">'+label+'</a>'
    lanes=[]
    original=ROOT/'.gcts-active/arithmetic-stochastic-clusters-20261011/execution-v2/evaluation'
    for job in ('base-r1','untrained-r1','trained-r1','trained-r2','untrained-r2','base-r2'):
        summary=load(original/(job+'-summary.json'))
        obs=next((x for x in ar['observations'] if x['lifetime']['job']==job),None)
        accepted=bool(obs and obs['lifetime']['status']=='passed_owned_loading_worker_lifetime')
        replay='Complete replay passed' if accepted else ('Resource UNKNOWN' if obs else 'Unexecuted')
        receipt=obs.get('receipt') if obs else None
        changed=receipt.get('tree',{}).get('executed_changed_first_branches') if receipt and accepted else None
        lanes.append([html.escape(job),'Unknown; no proof',math(summary['metrics']['attempts']),math(summary['metrics']['max_satisfied_points']),math(changed) if changed is not None else 'Not accepted',math(round(summary['search_seconds'],3)),replay,math(obs['lifetime']['conservative_owner_plus_worker_peak_bytes']) if obs else '—'])
    ar_table=table(['Original run','Search result','Attempts','Peak obligations','Changed first moves','Search seconds','Replay gate','Owned peak bytes'],lanes)
    history=[]
    for path,label in [(ARITH/'helpers-v5/phase-receipt.json','V5 helpers'),(ARITH/'evaluation-v5/phase-receipt.json','V5 missing-activation attempt'),(ROOT/selection['arithmetic_phase'],'V5 corrected owner')]:
        d=load(path);history.append([label,html.escape(d['status']),math(round(d['seconds_before_phase_receipt_write'],6)),math(d['conservative_owner_plus_worker_peak_bytes'])])
    history_table=table(['Arithmetic phase','Terminal disposition','Phase seconds','Owned peak bytes'],history)
    geometry_costs=[]
    for path in [GEO/'fixtures-lifetime-v1.json',GEO/'attempt-02/fixtures-lifetime-v1.json',ROOT/selection['geometry_lifetime']]:
        if not path.exists():continue
        d=load(path);geometry_costs.append([html.escape(str(path.relative_to(GEO))),html.escape(d['status']),math(round(d['full_supervisor_process_seconds_including_receipt_write'],6)),math(d['conservative_host_peak_bytes'])])
    if gil:
        geometry_costs.append(['Separate independent audit',html.escape(gil['status']),math(round(gil['full_owner_and_worker_seconds_before_receipt_write'],9)),math(gil['conservative_combined_peak_bytes'])])
    geometry_cost_table=table(['Geometry attempt','Terminal disposition','Owned seconds','Conservative peak bytes'],geometry_costs)
    g_states=[]
    if go:
        g_states=[s for s in go['states'] if not s['name'].startswith('exhaustive-formula-state-')]
    save('visual-states.json', g_states)
    controls=''
    if g_states:
        controls='<p><label for="snapshot">Checked state </label><select id="snapshot">'+''.join('<option value="'+str(i)+'">'+html.escape(s['name'])+'</option>' for i,s in enumerate(g_states))+'</select></p><p><label><input id="formula-layer" type="checkbox" checked> Blue formula layer</label> <label><input id="reference-layer" type="checkbox" checked> Purple ordered-reference layer</label></p><div id="state-view" aria-live="polite"></div>'
    else:
        controls='<p>No completed fixture outcome is available to draw. A failed monitor is not a checked tile configuration.</p>'
    g_rows=[]
    if go:
        for r in go['records']:
            g_rows.append([html.escape(r['name'].replace('_',' ')),html.escape(r['status'])])
    independent_text=('The separately owned independent artifact check passed. It reconstructs the literal bodies, point domains, complete identities, hint views and recorded transactions without importing the producer for acceptance. It rejects '+math(24)+' independently constructed corruptions and checks '+math(4)+' separate positive controls; those differ from the producer’s '+math(11)+' named fixture groups. Unsaved producer calls for nonfinite budgets and public-metadata mutation have source review only; their pass labels are not independently replayed calls.' if g_independent else 'Independent actual lifecycle acceptance remains pending. A source review or producer fixture pass is not a substitute for this check.')
    benchmark=load(ARITH/'next-discovery-benchmark-source-only-v1.json')
    target_table=table(['Proposed target','Symbolic statement','Prospective role'],[[html.escape(t['id']),html.escape(t['latex']),html.escape(t['role'])] for t in benchmark['targets']])
    targets_panel='<section class="panel" id="next-targets"><h2>Concrete next targets, with a frozen split before search.</h2><p>This is a source-only benchmark plan. The theory fragment contains the two recursive addition equations and natural-number induction. Cancellation and multiplication are outside this initial language. Each new target needs a separately audited complete point model; these statements have not been executed in the current commutativity region.</p>'+target_table+'<p>The defining equations calibrate admission. One-left and double-successor exercise composition with existing checked inventory. Commutativity has already been exposed. Associativity and the three-term permutation family are prospectively held out from donor training, proposals and teacher proofs before new model generation. Renaming variables does not create an independent theorem.</p><p>Match base GCTS, fixed cluster ordering, untrained stochastic ordering and trained stochastic ordering with equal models, admitted inventories, complete fallback and resource caps. Count success only after automatic discovery, independent trajectory/certificate checking and whole native acceptance. Charge inventory preparation, training, search, failed gates and replay; report cold costs and the reuse break-even point separately. A streaming full replay is a future prerequisite, not an implemented repair.</p><p><a href="arithmetic/next-discovery-benchmark-source-only-v1.json">Read the exact proposed split, controls and acceptance gates</a>. No new experiment or theorem discovery is reported by this plan.</p><p>The separate <a href="arithmetic/next-discovery-inventory-provenance-v1.json">inventory provenance note</a> binds historical GCTS discovery of zero-left and ordinary forward discovery of left-successor, with their source words, native admissions, audits and retained unknowns. Those are inherited checked lemmas, not discoveries by this new RL phase.</p></section>'
    g_summary=('The tiny producer completed '+math(go['fixture_groups'])+' fixture groups and '+math(go['controlled_states'])+' saved controlled states, with '+math(go['complete_raw_candidate_comparisons'])+' accepted-placement comparisons. The bounded formula-state sweep contains '+math(64)+' states.' if g_pass else 'The tiny producer remains unknown or failed under its owned gate; inspect the retained lifetime receipt.')
    evidence='<p>'+href(selection['arithmetic_phase'],'Arithmetic phase')+' · '+href(selection['arithmetic_terminal_review'],'Independent terminal review')+' · '+href(selection['geometry_lifetime'],'Geometry owned lifetime')
    if selection.get('geometry_outcome'):evidence+=' · '+href(selection['geometry_outcome'],'Saved geometry states')
    if selection.get('geometry_independent_result'):evidence+=' · '+href(selection['geometry_independent_result'],'Independent reconstruction')
    if selection.get('geometry_independent_lifetime'):evidence+=' · '+href(selection['geometry_independent_lifetime'],'Independent owned lifetime')
    evidence+='</p>'
    result={'goal_status':'active','arithmetic_full_six_replay_pass':a_pass,'arithmetic_all_original_searches':'unknown; no proof','arithmetic_terminal_phase':selection['arithmetic_phase'],'arithmetic_cumulative_audit_seconds':ar['cumulative_audit_seconds_before_phase_receipt_write'],'geometry_tiny_producer_pass':g_pass,'geometry_tiny_independent_pass':g_independent,'geometry_full_actual_lifecycle_execution':selection.get('full_actual_lifecycle_execution',False),'geometry_new_target_searches':0,'new_RL_training':False,'new_native_queries':0,'proof_search_gain':'not demonstrated','scope':'Cluster lifecycle conformance and unchanged-trace arithmetic verification; neither is new mathematical theorem discovery.'}
    save('result-summary.json',result)
    config={'tex':{'inlineMath':[[r'\(',r'\)']],'displayMath':[[r'\[',r'\]']]},'options':{'skipHtmlTags':['script','style','pre','code']}}
    content='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GCTS cluster lifecycle · research notebook</title><link rel="stylesheet" href="../report.css"><script>window.MathJax='''+json.dumps(config)+''';</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>
main{max-width:1200px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:24px 0}.cards>div{background:#edf2e8;padding:20px;border-radius:8px}.cards strong{display:block;font-size:24px;margin-bottom:10px}.note{padding:18px;border-left:4px solid #a57334;background:#fff4e3}.cluster{border:2px solid #6d7c6b;border-radius:8px;margin:15px 0;padding:16px}.cluster.ready{border-color:#2c7852}.cluster.waiting{border-color:#a57334}.cluster.retired{border-color:#984d4d;background:#f9eeee}.cluster.consumed{border-color:#405f92}.tile-row{display:grid;grid-template-columns:74px minmax(0,1fr);gap:15px;margin:12px 0;padding:12px;background:#f3f6f1;border-radius:6px}.tile{width:70px;height:70px;background:#fff;border:2px solid #6d7c6b;display:flex;align-items:center;justify-content:center;flex-direction:column}.tile small{font-size:11px}.marks{display:flex;flex-wrap:wrap;gap:7px}.mark{padding:6px 9px;border-radius:5px}.formula-mark{background:#d7e9ff;color:#173b78}.reference-mark{background:#e6d9ff;color:#503180}.hide-formulas .formula-mark,.hide-references .reference-mark{display:none}select{max-width:100%;padding:8px;font:inherit}td{font-size:13px}h2{scroll-margin-top:20px}@media(max-width:650px){.cards{grid-template-columns:1fr}.tile-row{grid-template-columns:60px minmax(0,1fr);gap:10px}.tile{width:56px;height:56px}}
</style></head><body><header class="masthead"><a href="../#cluster-lifecycle">Research report</a><span>NOTEBOOK 104</span><a href="#assessment">Assessment</a></header><main><section class="intro"><p class="eyebrow">PARALLEL IMPLEMENTATION · INDEPENDENT CHECKS · EXACT RECEIPTS</p><h1>Clusters wait, retire and return.</h1><p class="deck">A cluster can guide later placements only while its entire checked body still fits. Parallel work now tests that lifecycle, and checks the unchanged arithmetic search traces under their original limits.</p><p><a href="#lifecycle">Cluster checks</a> · <a href="#markings">Colored tile states</a> · <a href="#arithmetic">Arithmetic replay</a> · <a href="#assessment">Research judgment</a> · <a href="#evidence">Exact evidence</a></p></section><section class="panel"><h2>Parallel agents help when their results meet at a checkable interface.</h2><div class="cards"><div><strong>Arithmetic</strong>Repair memory use while preserving every original observation and independent replay check.</div><div><strong>Geometry</strong>Implement whole cluster validity, exact member sharing, complete fallback and paired rollback.</div><div><strong>Independent checking</strong>Reconstruct bodies and states separately, challenge corrupted inputs and reject unsupported conclusions.</div></div><p>The coordinator owns bounded dispatch and integrates terminal receipts. This division has exposed infrastructure and cost-accounting errors while implementation continued. No multiagent-versus-single-agent speed experiment has been run, so there is no quantified parallel speedup claim.</p></section><section class="panel" id="lifecycle"><h2>Whole cluster validity is a search contract.</h2><p>A ready cluster can change candidate order at the graph-selected branch. A valid cluster aimed at a later generation waits. If any pending member or distant marking conflicts, the entire cluster retires: its legal siblings stop receiving preference. Retirement lasts within that branch; exact paired rollback restores the parent graph and hint state. A selected member is shared only by its full identity, once.</p><p>Global dead ends and forced moves precede the earliest-generation branch. Hints do not change degrees or point choice. Ready preferred keys are followed by every remaining legal base candidate, once. Only a fully exhausted child justifies its exclusion in the restored parent. A budget-unknown child contributes no exclusion.</p><p>'''+g_summary+'</p><p>'+independent_text+'</p>'+table(['Fixture group','Producer result'],g_rows)+'''<p class="note">These are authored synthetic conformance probes, including an opaque two-premise fixture. They are not a mathematical theorem corpus, learned clusters or a native certificate. The separately pinned guarded Hilbert incidence model has '''+math(229)+' recipes, '+math(217)+' formula codes and '+math(24)+''' rows. The current lifecycle checkpoint does not establish a new proof in that model. Source-ready actual-model work is labeled separately in the exported plans.</p></section><section class="panel" id="markings"><h2>Examine the actual saved cluster states.</h2><p>Squares carry unit occupancy and translate without rotation. Blue markings encode formula values, including expected formulas at distant source rows; purple markings encode ordered source offsets. The surrounding border shows the whole descriptor state. A retired cluster can contain a still-legal member; it supplies no preference. The viewer reads completed fixture states. This is a point-marking adaptation; a literal universal Wang compiler with local edge matching remains open.</p>'''+controls+'''<p>The formula symbols describe synthetic propositions. They are separate from the spatial coordinates of their proof encoding. <a href="../wang-proofs.html#tile-row-translation">Earlier mathematical proof reader</a> · <a href="../stochastic-clusters/reader.html#reader">Guarded incidence formula/English reader</a></p></section><section class="panel" id="arithmetic"><h2>Arithmetic: verify the behavior before claiming a gain.</h2><p>The target remains '''+math(r'\forall x\,\forall y\,(x+y=y+x)')+' over the unchanged scalar point adaptation with '+math(19848)+' placements and '+math(52)+' obligations. All six original searches ended at '+math(5000)+' attempts without a proof, at the same peak of '+math(45)+''' satisfied obligations. This checkpoint launches no new searches or training.</p>'''+ar_table+'<p><strong>Complete six-replay phase: '+('passed' if a_pass else 'unknown or failed')+'''</strong>. The new loader shares repeated two-integer plain lists only in the frozen read-only saved-trace consumer. Before replay it compares every reconstructed compact JSON byte with the original compressed trace. The consumer restriction is essential: sharing mutable lists does not preserve arbitrary future mutation semantics. Negative fixtures demonstrate that limitation.</p><p>The independent graph, scheduler, whole-hint fallback, RNG and policy-update checks remain unchanged. The previously audited pilot and training trajectories showed changed legal choices. This V5 full phase has yet to qualify a stochastic evaluation lane; it establishes no faster or more successful proof search. The original learned and untrained lanes cost more search time and found no additional proof. These are two seeds for one theorem, without held-out theorem evaluation or an external-prover speed comparison.</p></section><section class="panel" id="cost"><h2>Preserve failures and measure the actual owned phase.</h2>'''+history_table+geometry_cost_table+'<p>The original arithmetic audit allowance remains '+math(780)+' seconds and '+math(512)+' MiB. All retained earlier failures, helpers, the missing-activation launch and this corrected phase consume '+math(round(ar['cumulative_audit_seconds_before_phase_receipt_write'],6))+''' seconds before the final receipt write; no budget was reset. Overlapping component clocks are not added twice. Root initially used the wrong activation filename; the owner stopped before any child, all six jobs remained unexecuted, and that cost stays charged.</p><p>The first geometry attempt could not read its own child process RSS because the sandbox denied the monitor. It failed closed, killed and reaped the child, and supplied no completed fixture result. The second attempt reached a failing combined assertion. Source review traced its expectation to an inspection that had advanced the hint revision before the old baseline was reused. A separate immutable successor captures the call-entry baseline after inspection and retains the same exact restoration check; the failed assertion is preserved, and no rollback pass is credited to it. Successors keep the same ceilings and charge both failures. The producer cumulative clock is '''+math(gl.get('cumulative_tiny_seconds',gl['full_supervisor_process_seconds_including_receipt_write']))+''' seconds; the separate independent audit cost is shown separately above. The geometry authoring clock also used an invalid cross-process monotonic subtraction; the preserved clarification replaces that claim with a calendar interval, including review and idle time. CPU effort remains unmeasured.</p><p>V1 tiny output charges compile, scan, ordering and rollback work inside the owned total but does not export separate timers for those subphases. There is no separate saved subphase-cost claim. Kernel peak gates and receipt-write exclusions are explicit in each lifetime receipt; no OS memory soft-limit enforcement is claimed.</p></section><section class="panel" id="assessment"><h2>Research judgment and the next gates.</h2><p>The useful contribution under test is a complete geometric candidate graph coupled to receptor-adapted checked cluster bodies. It gives learned or fixed proposals a precise validity and rollback interface. The current evidence advances that implementation contract. Existing theorem provers already reuse lemmas; having an inventory alone is not a new advantage.</p><p>For finite first-success DFS, complete fallback and sound child exhaustion preserve the existence of a solution. Different ordering may return a different proof. Equality of all visited solution sets would require exhaustive enumeration and is not established by first-success termination. The exported ordering argument is a host-level argument, not a tile-discovered theorem.</p><p>Next: run the lifecycle on the actual complete symbolic model and audit it independently; close primitive-to-logical/native certificate correspondence; then freeze a fresh discovery task and matched budgets. Broader arithmetic tasks and held-out theorem families are needed before a search contribution claim. Fixed priorities here are a control, not reinforcement learning.</p><p>The full research program remains active, including practical finite/movable-boundary tiling, learned markings, multiscale clusters and the turtle/Penrose tracks. This checkpoint establishes neither plane tiling nor a universal sound proof tile set. Finite unknown runs are not impossibility proofs.</p></section><section class="panel" id="evidence"><h2>Inspect the exact sources, states and receipts.</h2>'''+evidence+'''<p><a href="result-summary.json">Outcome summary</a> · <a href="visual-states.json">Viewer data</a> · <a href="origins.json">Every exported origin</a> · <a href="source-input-bindings.json">Exact source/input routes</a> · <a href="sources-and-inputs.zip">Additional required files</a></p><p>Each required file resolves to its exact public file or ZIP member. Existing large traces keep their original public endpoints. Failed attempts, authoring clarifications and source-only plans remain alongside successful gates. A frozen plan is not an execution receipt.</p></section></main>'''
    visual=json.dumps(g_states,separators=(',',':')).replace('</','<\/')
    script=r'''
const checkedStates=__DATA__;
const viewer=document.getElementById('state-view');
const tex=x=>'\\('+x+'\\)';
function formula(x){if(x[0]==='pred')return x[1];if(x[0]==='imp')return '('+formula(x[1])+'\\to '+formula(x[2])+')';return '\\text{fixture}';}
function renderState(){
 if(!viewer)return;
 if(window.MathJax&&MathJax.typesetClear)MathJax.typesetClear([viewer]);
 const s=checkedStates[Number(document.getElementById('snapshot').value)];
 viewer.replaceChildren();
 const intro=document.createElement('p');intro.textContent='Saved check: '+s.name+'. Selected primitive members: '+tex(s.state.graph.order.length)+'.';viewer.append(intro);
 const current=document.createElement('p');current.className='marks';
 const label=document.createElement('strong');label.textContent='Current assigned markings';current.append(label);
 s.state.graph.marks.filter(v=>v[1]>=0).forEach(([x,y,v])=>{const tag=document.createElement('span');tag.className='mark '+(x===1?'formula-mark':'reference-mark');tag.textContent=tex('m('+x+','+y+')='+v);current.append(tag);});viewer.append(current);
 s.descriptors.forEach((d,i)=>{
  const status=s.state.hint_states[i];const article=document.createElement('article');article.className='cluster '+status.status;
  const h=document.createElement('h3');h.textContent=d.body_name+' — '+status.status;article.append(h);
  const p=document.createElement('p');p.textContent=status.reason?'Whole retirement reason: '+status.reason+'.':'Whole descriptor is '+status.status+'.';article.append(p);
  d.members.forEach(k=>{
   const row=document.createElement('div');row.className='tile-row';
   const tile=document.createElement('div');tile.className='tile';tile.textContent=tex('r='+k[1]);const small=document.createElement('small');small.textContent='translation only';tile.append(small);row.append(tile);
   const detail=document.createElement('div');const output=document.createElement('p');const rec=s.recipes[k[0]];output.textContent=tex(formula(rec.primitive_witness.formula));detail.append(output);
   const occupancy=document.createElement('p');const selected=s.state.graph.order.some(v=>JSON.stringify(v)===JSON.stringify(k));const legal=s.complete_domains[k[1]].some(v=>JSON.stringify(v)===JSON.stringify(k));occupancy.textContent=tex('t(0,'+k[1]+')=1')+' · recipe '+k[0]+' · '+(selected?'exact member already selected once':(legal?'pending member · currently legal':'pending member · incompatible'));detail.append(occupancy);
   const marks=document.createElement('p');marks.className='marks';
   let vals=[[1,k[1],s.formulas.findIndex(f=>JSON.stringify(f)===JSON.stringify(rec.primitive_witness.formula))]];
   k[2].forEach((src,j)=>{vals.push([1,src,s.formulas.findIndex(f=>JSON.stringify(f)===JSON.stringify(rec.ordered_premise_formulas[j]))]);vals.push([2+j,k[1],src-k[1]]);});
   vals.forEach(([x,y,v])=>{const tag=document.createElement('span');tag.className='mark '+(x===1?'formula-mark':'reference-mark');tag.textContent=tex('m('+x+','+y+')='+v);marks.append(tag);});detail.append(marks);row.append(detail);article.append(row);
  });viewer.append(article);
 });
 if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([viewer]);
}
if(viewer){document.getElementById('snapshot').addEventListener('change',renderState);for(const [id,cls] of [['formula-layer','hide-formulas'],['reference-layer','hide-references']])document.getElementById(id).addEventListener('change',e=>document.getElementById('markings').classList.toggle(cls,!e.target.checked));if(window.MathJax&&MathJax.startup&&MathJax.startup.promise)MathJax.startup.promise.then(renderState);else window.addEventListener('load',renderState);}
'''.replace('__DATA__',visual)
    # JavaScript needs two source backslashes to emit one LaTeX backslash.
    script=script.replace(chr(92)*4,chr(92)*2)
    assert content.count('<section class="panel" id="assessment">')==1
    content=content.replace('<section class="panel" id="assessment">',targets_panel+'<section class="panel" id="assessment">',1)
    content+='<script>'+script+'</script></body></html>'
    reader=DEST/'reader.html';reader.write_text(content);files.add(str(reader.relative_to(ROOT)))
    baseline=PUB/'docs/research/gcts-rl-renewal/index.html'
    assert pin(baseline)['sha256']==selection['main_baseline_sha256']
    previous=baseline.read_text();assert 'RESEARCH NOTEBOOK · 103' in previous
    panel='<section class="panel" id="cluster-lifecycle"><h2>Checkpoint 104 · Whole cluster continuation and independent replay</h2><p>Parallel agents implement cluster waiting, whole retirement, exact sharing and rollback while independent checks reconstruct the results. Arithmetic verifies the unchanged search traces; all six original searches still found no proof. <a href="cluster-lifecycle/reader.html?v=20261011-cl1#lifecycle">Read the actual terminal gates and inspect colored cluster states</a>.</p><p>Geometry tiny producer: <strong>'+('passed' if g_pass else 'unknown')+'</strong>; independent lifecycle gate: <strong>'+('passed' if g_independent else 'pending')+'</strong>. Complete arithmetic replay: <strong>'+('passed' if a_pass else 'unknown')+'</strong>. No new theorem discovery or proof-search advantage is claimed. Failed launches, limits and the next actual-model gate remain explicit.</p></section>\n'
    # Add only one panel before the prior checkpoint; preserve historical content.
    anchor='<section class="panel" id="parallel-execution">';assert previous.count(anchor)==1
    updated=previous.replace('RESEARCH NOTEBOOK · 103','RESEARCH NOTEBOOK · 104',1).replace(anchor,panel+anchor,1)
    mainpath=ROOT/'docs/research/gcts-rl-renewal/index.html'
    if pin(mainpath)!=pin(baseline):
        old_manifest=load(HERE/'task-files.json')
        previous_own=next(e for e in old_manifest if e['path']==str(mainpath.relative_to(ROOT)))
        assert pin(mainpath)=={k:previous_own[k] for k in ('sha256','bytes')},'unrelated report change'
    mainpath.write_text(updated);files.add(str(mainpath.relative_to(ROOT)))
    manifest=[{'path':f,**pin(ROOT/f)} for f in sorted(files)]
    (HERE/'task-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'task_files':len(manifest),'source_input_bindings':len(bindings),'exported_origins':len(origins),'reader_bytes':reader.stat().st_size,'visual_saved_states':len(g_states),'arithmetic_complete_pass':a_pass,'geometry_tiny_pass':g_pass,'independent_tiny_pass':g_independent}))


if __name__=='__main__':main()
