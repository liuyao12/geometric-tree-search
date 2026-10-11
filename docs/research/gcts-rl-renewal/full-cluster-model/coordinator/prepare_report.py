"""Project frozen observations into a reader; never execute scientific helpers."""
import copy
import html
import json
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load, project

HERE = Path(__file__).resolve().parent
GEO = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'
GI = ROOT / '.gcts-active/hilbert-cluster-full-independent-20261011'
BASE = 'f713603b4c3766f7e729a1ee4bc4c4ec8c00f9aa'
MAIN = 'docs/research/gcts-rl-renewal/index.html'


def math(value):
    return r'\(' + html.escape(str(value)) + r'\)'


def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>' + ''.join('<th>'+v+'</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows) + '</tbody></table></div>'


def main():
    selected = load(HERE/'terminal-selection.json')
    assert selected['all_owned_handles_terminal'] is True
    baseline = subprocess.check_output(['git','show',BASE+':'+MAIN],cwd=PUB)
    assert __import__('hashlib').sha256(baseline).hexdigest() == selected['main_baseline_sha256']
    baseline_file=HERE/'baseline-index.html'
    if baseline_file.exists():
        assert baseline_file.read_bytes()==baseline
    else:
        baseline_file.write_bytes(baseline)
    outcome = load(GEO/'full-language-outcome-v3.json')
    lifetime = load(GEO/'full-language-lifetime-v3.json')
    audit = load(GI/'audit-result-v1.json')
    audit_lifetime = load(GI/'audit-lifetime-v1.json')
    assert lifetime['status'] == 'passed_authored_full_language_lifecycle_full_lifetime'
    assert audit_lifetime['status'] == 'passed_owned_independent_full_language_lifecycle_audit'
    assert audit['every_key_t_m_comparisons'] == outcome['all_state_candidate_key_t_m_comparisons'] == 2979447
    assert audit['complete_state_count'] == outcome['controlled_states'] == 11
    assert len(audit['independent_actual_corruptions']) == 24
    assert audit['target_searches'] == outcome['actual_target_DFS_searches'] == 0
    exclusions = {'publication.json','publication-staging.json','turn-result.json','task-files.json','local-validation.json','live-hash-checks.json','browser-validation.json','staged-whitespace-check.json','verify_live_files.py','baseline-index.html'}
    folders = [(str(GEO.relative_to(ROOT)), 'geometry', set()), (str(GI.relative_to(ROOT)), 'geometry-independent', set())]
    folders += selected.get('additional_frozen_folders', [])
    folders.append((str(HERE.relative_to(ROOT)), 'coordinator', exclusions))
    files, origins, bindings = project(folders, {(MAIN,selected['main_baseline_sha256']):baseline_file})

    def save(name, value):
        path=DEST/name;path.write_text(json.dumps(value,indent=2)+'\n');files.add(str(path.relative_to(ROOT)))

    def href(origin, label):
        route = next((e for e in origins if e['origin']==origin), None)
        if route:
            destination=route['path']
        else:
            route=next(e for e in bindings if e['path']==origin)
            destination=route['published_path']
            assert route.get('archive_member') is None, 'HTML direct link requires direct public file'
        relative = __import__('os').path.relpath(destination, PREFIX)
        return '<a href="'+html.escape(relative)+'">'+label+'</a>'

    model_pin = next(e for e in load(GEO/'full-language-plan-v3.json')['inputs'] if e['role']=='primitive_model')
    import gzip
    with gzip.open(ROOT/model_pin['path'],'rt') as stream:
        model=json.load(stream)
    visual=dict(scope='Display projection of terminal saved states, not an acceptance checker or proof search.',
        source_outcome=dict(path=str((GEO/'full-language-outcome-v3.json').relative_to(ROOT)),**pin(GEO/'full-language-outcome-v3.json')),
        source_model=model_pin, states=copy.deepcopy(outcome['states']), descriptors=outcome['descriptors'],
        formulas=model['formula_codes'],recipes=[{k:r[k] for k in ('id','primitive_witness','ordered_premise_formulas')} for r in model['recipes']],default_state=8,default_cluster=4)
    for state in visual['states']:
        # All exact point values and identities remain; domain factors are not drawn.
        for domain in state['state']['graph']['domains']:
            domain.pop('factors',None)
    save('visual-data.json',visual)
    source=HERE/'viewer.js';target=DEST/'viewer.js';shutil.copyfile(source,target)
    files.add(str(target.relative_to(ROOT)))
    origins.append(dict(origin=str(source.relative_to(ROOT)),path=str(target.relative_to(ROOT)),**pin(source)))
    bindings.append(dict(path=str(source.relative_to(ROOT)),**pin(source),published_path=str(target.relative_to(ROOT)),archive_member=None))
    save('origins.json',origins);save('source-input-bindings.json',bindings)

    new_cost=Decimal(str(lifetime['full_supervisor_process_seconds_including_receipt_write']))+Decimal(str(audit_lifetime['full_owner_and_worker_seconds_before_receipt_write']))
    costs=table(['Gate','Owned seconds','Conservative peak bytes','Result'],[
        ['Full geometry producer',math(lifetime['full_supervisor_process_seconds_including_receipt_write']),math(lifetime['conservative_host_peak_bytes']),'Passed; all owned processes reaped'],
        ['Separate independent reconstruction',math(audit_lifetime['full_owner_and_worker_seconds_before_receipt_write']),math(audit_lifetime['conservative_combined_peak_bytes']),'Passed; direct child reaped'],
        ['Two separate new phases',math(new_cost),'Peaks are not summed','Source authoring and earlier inventory preparation are additional'],
    ])
    ar=load(ROOT/selected['arithmetic_phase'])
    ar_pass=ar['status']=='passed_complete_loading_only_six_evaluation_replays'
    ar_table=[]
    for obs in ar['observations']:
        life=obs['lifetime']; receipt=obs.get('receipt')
        accepted=life['status']=='passed_owned_loading_worker_lifetime'
        changed=receipt.get('tree',{}).get('executed_changed_first_branches') if accepted and receipt else None
        ar_table.append([html.escape(life['job']), 'Complete replay passed' if accepted else 'Resource UNKNOWN', math(life['conservative_owner_plus_worker_peak_bytes']), math(changed) if changed is not None else 'Not qualified'])
    for job in ar.get('unexecuted',[]):
        ar_table.append([html.escape(job if isinstance(job,str) else job['job']),'Unexecuted','—','Not qualified'])
    arithmetic=table(['Saved evaluation','Replay disposition','Owned peak bytes','Changed first moves accepted by this gate'],ar_table)
    arithmetic += '<p>Complete six-replay phase: <strong>'+('passed' if ar_pass else 'unknown or failed')+'</strong>. All six original searches stopped after '+math(5000)+' attempts without a proof. A replay verifies their saved behavior; it discovers no theorem. The unchanged original arithmetic allowance is '+math(780)+' seconds; cumulative charged auditing is '+math(ar['cumulative_audit_seconds_before_phase_receipt_write'])+' seconds. Failed earlier versions, helpers and the missing-activation attempt remain charged.</p>'
    if selected.get('arithmetic_successor_source_only'):
        arithmetic += '<p>A separately versioned disk-backed replay repair is being prepared. Its indexing may reduce retained memory, but it has not passed the full fresh-worker gates. A source freeze or incomplete helper attempt is not a complete memory or correctness result.</p>'
    arithmetic += '<p>'+href(selected['arithmetic_phase'],'Exact arithmetic phase receipt')+' · '+href(selected['arithmetic_terminal_review'],'Independent arithmetic terminal review')+'</p>'
    if selected.get('arithmetic_current_helper_phase'):
        helper=load(ROOT/selected['arithmetic_current_helper_phase'])
        arithmetic += '<p>The latest loading-helper gate, which preceded this replay phase: <strong>'+html.escape(helper['status'])+'</strong>. Its separately owned phase took '+math(helper['seconds_before_phase_receipt_write'])+' seconds; charged auditing at that point was '+math(helper['cumulative_audit_seconds_before_phase_receipt_write'])+' seconds. '+href(selected['arithmetic_current_helper_phase'],'Read the exact latest helper disposition')+'. Complete loading helpers must pass before any new full replay.</p>'
    if ar['status']=='unknown_phase_reservation_budget':
        remaining=Decimal(str(ar['original_cumulative_audit_seconds']))-Decimal(str(ar['cumulative_audit_seconds_before_phase_receipt_write']))
        arithmetic += '<p>All '+math(len(ar['observations']))+' attempted fresh full replays passed both mathematical and owned-memory gates. The remaining '+math(remaining)+' seconds could not reserve the required '+math(120)+'-second worker ceiling for another job, so the last '+math(len(ar['unexecuted']))+' jobs were unexecuted. The disk-backed loading repair reduced retained memory in these actual runs; no proof-search speedup follows from a replay-memory result.</p>'
    arithmetic += '<p>The retained V7 synthetic test stopped on an incorrect omission-fixture field path, before the mutant byte check. The actual gate caught a defect missed in source review. No complete helper pass is credited. Its temporary synthetic directory was automatically erased, so its broad spool-retention label is inaccurate; the immutable source, receipt and independent causal correction remain. A separately versioned repair preserves synthetic files and retains the same full byte and scientific checks.</p>'
    records=table(['Independent check','Actual scope'],[
        ['Source family expansion',math(171)+' declarations; '+math(1845)+' primitive leaves, '+math(630)+' local aliases and '+math(216)+' recursive calls'],
        ['Registry and transports',math(175)+' registered bodies, including '+math(4)+' fixed primitive controls; '+math(5)+' descriptors'],
        ['Complete candidate graph',math(11)+' saved states; '+math(2979447)+' complete key / occupancy / marking comparisons'],
        ['Transactions',math(9)+' controlled operations, including paired graph/hint rollback'],
        ['Independent corruptions',math(24)+' rejected body, identity, epoch, point-state and fallback mutants'],
    ])
    config={'tex':{'inlineMath':[[r'\(',r'\)']],'displayMath':[[r'\[',r'\]']]},'options':{'skipHtmlTags':['script','style','pre','code']}}
    content='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Full symbolic cluster model · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax='''+json.dumps(config)+''';</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>
main{max-width:1200px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:24px 0}.cards>div{background:#edf2e8;padding:20px;border-radius:8px}.cards strong{display:block;font-size:24px;margin-bottom:8px}.note{padding:18px;border-left:4px solid #a57334;background:#fff4e3}.cluster{border:2px solid #6d7c6b;border-radius:8px;margin:15px 0;padding:16px}.cluster.ready{border-color:#2c7852}.cluster.waiting{border-color:#a57334}.cluster.retired{border-color:#984d4d;background:#f9eeee}.cluster.consumed{border-color:#405f92}.tile-row{display:grid;grid-template-columns:96px minmax(0,1fr);gap:15px;margin:12px 0;padding:12px;background:#f3f6f1;border-radius:6px}.tile{width:90px;height:90px;background:#fff;border:2px solid #6d7c6b;display:flex;align-items:center;justify-content:center;flex-direction:column}.tile small{font-size:11px}.tile-layer{width:100%;text-align:center;font-size:13px}.marks{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}.mark{padding:6px 9px;border-radius:5px}.formula-mark{background:#d7e9ff;color:#173b78}.reference-mark{background:#e6d9ff;color:#503180}.hide-formulas .formula-mark,.hide-references .reference-mark{display:none}select{max-width:100%;padding:8px;font:inherit}.controls{display:flex;flex-wrap:wrap;gap:14px}.formula{overflow:auto;padding:12px}td{font-size:14px}h2{scroll-margin-top:20px}@media(max-width:650px){.cards{grid-template-columns:1fr}.tile-row{grid-template-columns:60px minmax(0,1fr);gap:10px}.tile{width:56px;height:56px}}
</style></head><body><header class="masthead"><a href="../#full-cluster-model">Research report</a><span>NOTEBOOK 105</span><a href="#assessment">Assessment</a></header><main><section class="intro"><p class="eyebrow">FULL FINITE INVENTORY · INDEPENDENT RECONSTRUCTION · COLORED MARKINGS</p><h1>Families have a checked boundary.</h1><p class="deck">Whole cluster behavior now passes on the declared symbolic geometry model. The independent check rebuilds its bodies and every saved candidate domain. Automatic theorem discovery is the next scientific gate.</p><p><a href="#results">Actual results</a> · <a href="#reader">Examine tile rows</a> · <a href="#cost">Costs</a> · <a href="#arithmetic">Arithmetic</a> · <a href="#assessment">Research judgment</a></p></section><section class="panel" id="results"><h2>From tiny fixtures to the actual symbolic inventory.</h2><div class="cards"><div><strong>'''+math(171)+'''</strong>Literal source families rebuilt independently</div><div><strong>'''+math(11)+'''</strong>Saved full-model states reconstructed</div><div><strong>'''+math(2979447)+'''</strong>Complete candidate key and point-value comparisons</div></div><p>The model contains '''+math(229)+' primitive recipes, '+math(217)+' formula values and '+math(24)+''' required proof rows. Its three original hypotheses keep generation zero. The independent auditor uses separate symbolic, expansion and point-state code; it imports neither the producer nor the production graph or lifecycle controller for acceptance.</p>'''+records+'''<p>Whole descriptors wait when valid but aimed at a later decision. A conflict in any pending member retires the whole cluster, including its still-compatible siblings. Full-identity sharing adds a selected member once; equal conclusions do not make two placements identical. Paired rollback restores both graph and hint state.</p><p>Dead points and globally forced placements precede the earliest-generation branch. A ready cluster only changes order within the selected branch; every remaining legal base candidate follows. The full controlled phase has no exhausted-child exclusion or target DFS. Dead-end, exhaustion and budget-unknown adversaries retain their separately checked tiny-fixture scope.</p><p class="note">This is the complete current finite inventory for a guarded Hilbert incidence fragment. It is not all of Hilbert geometry, all reachable states, or a universal proof-language benchmark. The families are source-authored controls with independently reconstructed bodies. This checkpoint contains no new target proof, native acceptance or reinforcement-learning training.</p></section><section class="panel" id="reader"><h2>Read the saved symbolic tiles and their colored markings.</h2><p>Blue marks encode formula values, including expected formulas at distant source rows. Purple marks encode ordered negative source offsets. The square placements translate without rotation. The border describes the whole cluster; the point values inside are exact saved descriptor data. Open each formula to read its full symbolic statement.</p><div class="controls"><label>Saved state <select id="saved-state"></select></label><label>Cluster family <select id="cluster"></select></label></div><p><label><input id="formula-layer" type="checkbox" checked> Blue formula layer</label> <label><input id="reference-layer" type="checkbox" checked> Purple ordered-reference layer</label></p><div id="cluster-view" aria-live="polite"></div><p>The current viewer displays controlled fragments, not a finished discovered proof. The spatial coordinates encode statements; the statements themselves refer to abstract points, lines and incidence. Instantiation and equality-substitution recipes introduce logical implication axioms with no input ports; subsequent modus ponens uses their ordered premises.</p><p><a href="../stochastic-clusters/reader.html#reader">Earlier symbolic geometry formula/English reader</a> · <a href="../wang-proofs.html#tile-row-translation">Arithmetic proof-row reader</a></p></section><section class="panel" id="cost"><h2>Charge each owned phase and preserve earlier failures.</h2>'''+costs+'<p>The producer used a '+math(180)+'-second outer lifetime, '+math(175)+'-second supervised phase and '+math(170)+'-second child ceiling. The independent phase used a sole '+math(180)+'-second owner and '+math(170)+'-second child alarm. Both use a '+math(512)+''' MiB conservative kernel-peak acceptance gate. The producer additionally sampled child RSS; the independent owner makes no live RSS claim. These are measured and retrospective gates, without a hard operating-system memory cap.</p><p>Inside the producer, family-registry setup took '''+math(outcome['preparation_costs']['family_registry_seconds'])+' seconds and descriptor/controller setup took '+math(outcome['preparation_costs']['root_descriptor_registry_and_controller_seconds'])+' seconds. Validation took '+math(outcome['lifecycle_metrics']['validation_seconds'])+' seconds, ordering '+math(outcome['lifecycle_metrics']['ordering_seconds'])+' seconds and rollback '+math(outcome['lifecycle_metrics']['rollback_seconds'])+''' seconds. Ordering includes resynchronization: component clocks overlap and must not be summed.</p><p>The earlier tiny producer’s retained attempts total '''+math('1.019903957')+' seconds, including monitor-permission and stale-baseline fixture failures. Its separate independent audit took '+math('0.314626667')+''' seconds. Those costs remain additional. Previously prepared symbolic models and source bodies are reused here; a full cold-start cost, source-authoring CPU time and reuse break-even point remain unmeasured. None of these gate timings measures proof-search speed.</p></section><section class="panel" id="arithmetic"><h2>Arithmetic keeps its separate search and memory result.</h2>'''+arithmetic+'''<p>No RL advantage is demonstrated. Existing saved stochastic searches changed some legal branch choices but found no additional proof. Memory-qualified auditing is needed before their complete evaluation trajectories can support a behavior comparison.</p></section><section class="panel" id="assessment"><h2>What the parallel program has established.</h2><p>Three agents separate arithmetic memory work, geometry cluster implementation, and independent reconstruction. The coordinator checks exact interfaces, owns bounded scientific dispatch and publishes terminal evidence. This has exposed mistakes in accounting and report labels while implementation continued. There is no measured multiagent speedup.</p><p>The GCTS contribution under test is a complete geometric candidate graph with a precise interface for receptor-adapted reusable bodies, distant marks and rollback. Lemma inventories are already common in theorem proving; they alone do not establish a new search advantage. This checkpoint strengthens the correctness interface needed to test that advantage.</p><p>A request-independent finite Wang palette already exists in the project’s shared FOL-machine adapter. The current formula-code/recipe model is a more compact, finite symbolic search adaptation. Its automatic proof certificate still needs an exact bridge to that shared machine encoding. Passing its point-state checks does not activate the universal palette or establish native/compiler correspondence. <a href="../shared-wang.html">Inspect the existing shared palette</a>.</p><p>The next gate must discover a target from hypotheses with complete fallback, then reconstruct the symbolic proof line by line and obtain independent certificate acceptance. It must not load an authored target proof as a proposal. Fixed family priorities are a control; trained policies need matched models, resource budgets and held-out theorem families. Failed and unknown runs remain unknown.</p><p>The full research goal remains active, including practical fixed/movable-boundary tiling, learned failure markings, multiscale clusters and the turtle/Penrose experiments. This checkpoint establishes neither a new mathematical theorem nor whole-plane tiling.</p></section><section class="panel" id="evidence"><h2>Exact sources, states and independent receipts.</h2><p>'''+href(str((GEO/'full-language-outcome-v3.json').relative_to(ROOT)),'Full producer outcome')+' · '+href(str((GEO/'full-language-lifetime-v3.json').relative_to(ROOT)),'Producer lifetime')+' · '+href(str((GI/'audit-result-v1.json').relative_to(ROOT)),'Independent reconstruction')+' · '+href(str((GI/'audit-lifetime-v1.json').relative_to(ROOT)),'Independent lifetime')+'''</p><p><a href="visual-data.json">Viewer projection</a> · <a href="result-summary.json">Outcome summary</a> · <a href="origins.json">Exported origins</a> · <a href="source-input-bindings.json">Exact source/input routes</a> · <a href="sources-and-inputs.zip">Additional bound files</a></p><p>The independent result’s literal field <code>authored24_words_read=0</code> is overbroad: the family projection JSON was decoded and its example discarded. The verified claim is that an authored target word supplied neither hints nor acceptance authority. A separate source-only label revision was never executed and does not replace this immutable actual result. The source-bound clarification and original result are both preserved.</p><p>Each required file resolves to its exact public bytes or ZIP member. The visual projection omits undrawn domain factors and duplicate recipe metadata; the full outcome and model retain them. Failed histories and prospective designs remain separate from actual acceptance receipts.</p></section></main><script defer src="viewer.js"></script></body></html>'''
    if selected.get('bridge_proposal'):
        bridge=load(ROOT/selected['bridge_proposal'])
        panel='<section class="panel" id="next-theorem"><h2>A concrete next automatic geometry target.</h2><p>The frozen source-only proposal uses the same guarded incidence hypotheses and target:</p><div class="formula">'+math(bridge['problem_latex'])+'</div><p>The guard expands to:</p><div class="formula">'+math(bridge['guard_latex'])+'</div><p>The two controls are ordinary complete primitive order and an explicitly authored generic forward/novelty order. Both use the unchanged full inventory and empty active descriptors, with '+math(128)+' attempts and '+math(20)+' seconds per search. There is no authored target-proof hint. This is a proposal; no such search has run in this checkpoint.</p><p>A discovered certificate must keep every proof row and ordered reference. The bridge maps the three local hypotheses to three explicitly retained closed hypothesis axioms in the flat shared-checker request. That establishes the same ground sequent relative to its hypotheses; it does not discharge those hypotheses or establish a universally closed theorem. Independent point, logical and wire-boundary checks precede any later native request. '+href(selected['bridge_proposal'],'Read the exact certificate bridge')+' · '+href(selected['bridge_gate'],'Read the prospective search gate')+'.</p></section>'
        content=content.replace('<section class="panel" id="assessment">',panel+'<section class="panel" id="assessment">',1)
    reader=DEST/'reader.html';reader.write_text(content);files.add(str(reader.relative_to(ROOT)))
    summary=dict(goal_status='active',geometry_full_producer_pass=True,geometry_full_independent_pass=True,source_families=171,formulas=217,recipes=229,required_rows=24,controlled_states=11,complete_key_t_m_comparisons=2979447,independent_mutants=24,geometry_full_new_owned_seconds=str(new_cost),arithmetic_complete_six_replay_pass=ar_pass,arithmetic_phase=selected['arithmetic_phase'],arithmetic_original_searches='unknown; no proof',new_target_searches=0,new_native_queries=0,new_RL_training=False,proof_search_gain='not demonstrated',scope='Full current finite cluster lifecycle controls, not target proof discovery or native/shared-palette correspondence.')
    save('result-summary.json',summary)
    previous=baseline.decode();assert 'RESEARCH NOTEBOOK · 104' in previous
    panel='<section class="panel" id="full-cluster-model"><h2>Checkpoint 105 · Full symbolic cluster inventory, independently reconstructed</h2><p>The geometry lifecycle now passes on the declared guarded incidence model: '+math(171)+' source families, '+math(11)+' saved states and '+math(2979447)+' complete placement comparisons. A separate auditor reconstructs bodies, ordered receptors, distant markings and rollback. <a href="full-cluster-model/reader.html?v=20261011-fc1#reader">Inspect the colored symbolic tile rows and exact terminal receipts</a>.</p><p>These are controlled full-inventory checks. No new theorem discovery, native activation or RL search advantage is claimed. Arithmetic keeps its separately qualified replay status, and the shared Wang proof bridge remains a next gate.</p></section>\n'
    anchor='<section class="panel" id="cluster-lifecycle">';assert previous.count(anchor)==1
    updated=previous.replace('RESEARCH NOTEBOOK · 104','RESEARCH NOTEBOOK · 105',1).replace(anchor,panel+anchor,1)
    mainpath=ROOT/MAIN
    if mainpath.read_bytes()!=baseline:
        old=load(HERE/'task-files.json');record=next(e for e in old if e['path']==MAIN)
        assert pin(mainpath)=={k:record[k] for k in ('sha256','bytes')},'unrelated main-report edit'
    mainpath.write_text(updated);files.add(MAIN)
    manifest=[dict(path=f,**pin(ROOT/f)) for f in sorted(files)]
    (HERE/'task-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(task_files=len(manifest),origins=len(origins),bindings=len(bindings),reader_bytes=reader.stat().st_size,visual_states=11,geometry_full_independent_pass=True,arithmetic_complete_pass=ar_pass)))


if __name__ == '__main__':
    main()
