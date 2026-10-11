"""Render frozen actual observations; never import a search or proof checker."""
import copy
import gzip
import hashlib
import html
import json
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load, project

HERE=Path(__file__).resolve().parent
BASE='f41da478a4a16b4c91eabe20aa8255ebdfc30830'
MAIN='docs/research/gcts-rl-renewal/index.html'


def math(value):
    return r'\('+html.escape(str(value))+r'\)'


def prose(value):
    return re.sub(r'(?<![\w])([0-9][0-9,]*(?:\.[0-9]+)?)(?![\w])', lambda match: math(match.group(1).replace(',', '')), html.escape(value))


def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+html.escape(v)+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def main():
    selected=load(HERE/'terminal-selection-v3.json')
    assert selected['all_owned_handles_terminal'] is True
    phase=ROOT/selected['producer_folder']
    outcome=load(phase/'search-outcome-v1.json')
    life=load(phase/'search-lifetime-v1.json')
    assert life['status']=='passed_automatic_primitive_geometry_full_lifetime'
    plan=load(phase/'search-plan-v1.json')
    acceptance=load(ROOT/selected['independent_result'])
    assert acceptance['status']==selected['independent_result_status']
    baseline=subprocess.check_output(['git','show',BASE+':'+MAIN],cwd=PUB)
    assert hashlib.sha256(baseline).hexdigest()==selected['main_baseline_sha256']
    baseline_file=HERE/'baseline-index.html'
    if baseline_file.exists():assert baseline_file.read_bytes()==baseline
    else:baseline_file.write_bytes(baseline)
    exclusions={'publication.json','publication-staging.json','task-files.json','turn-result.json','local-validation.json','live-hash-checks.json','browser-validation.json','staged-whitespace-check.json','verify_live_files.py','baseline-index.html','actual-display-data-validation.json'}
    folders=selected['frozen_folders']+[(str(HERE.relative_to(ROOT)),'coordinator',exclusions)]
    files,origins,bindings=project(folders,{(MAIN,selected['main_baseline_sha256']):baseline_file})
    def save(name,value):
        options={'separators':(',',':')} if name=='visual-data.json' else {'indent':2}
        p=DEST/name;p.write_text(json.dumps(value,**options)+'\n');files.add(str(p.relative_to(ROOT)))
    def link(origin,label):
        row=next((e for e in origins if e['origin']==origin),None)
        if row:target=row['path']
        else:
            row=next(e for e in bindings if e['path']==origin)
            target=row['published_path'];assert row.get('archive_member') is None
        return '<a href="'+html.escape(__import__('os').path.relpath(target,PREFIX))+'">'+label+'</a>'
    model_pin=next(e for e in plan['inputs'] if e['role']=='primitive_model')
    with gzip.open(ROOT/model_pin['path'],'rt') as s:model=json.load(s)
    observations=[]
    for observation in outcome['observations']:
        source=ROOT/observation['result']['path'];assert pin(source)=={k:observation['result'][k] for k in ('sha256','bytes')}
        with gzip.open(source,'rt') as s:result=json.load(s)
        verdict=selected['observation_verdicts'][observation['id']]
        visual=copy.deepcopy(result)
        visual.update(id=observation['id'],independent_certificate_accepted=verdict['certificate_accepted'],independent_trace_accepted=verdict['trace_accepted'],independent_scope=verdict['scope'])
        observations.append(visual)
    recipient_models=[entry for entry in model['models'] if entry['height']==24]
    assert len(recipient_models)==1
    context=recipient_models[0]['context']
    visual=dict(scope='Actual partial search states and any supplied certificates. Independent whole-trace checks are distinct from theorem acceptance; native authority and RL are inactive.',formula_codes=model['formula_codes'],recipes=[{k:r[k] for k in ('id','primitive_witness','ordered_premise_formulas')} for r in model['recipes']],hypotheses=context['ordered_local_premises'],target=model['formula_codes'][54],observations=observations,producer_result=dict(path=str((phase/'search-outcome-v1.json').relative_to(ROOT)),**pin(phase/'search-outcome-v1.json')))
    save('visual-data.json',visual)
    viewer=ROOT/selected['viewer_source'];target=DEST/'viewer.js';shutil.copyfile(viewer,target);files.add(str(target.relative_to(ROOT)))
    origins.append(dict(origin=str(viewer.relative_to(ROOT)),path=str(target.relative_to(ROOT)),**pin(viewer)))
    bindings.append(dict(path=str(viewer.relative_to(ROOT)),**pin(viewer),published_path=str(target.relative_to(ROOT)),archive_member=None))
    save('origins.json',origins);save('source-input-bindings.json',bindings)
    passed=[o['id'] for o in observations if o['independent_certificate_accepted']]
    result_rows=[]
    for o in observations:
        result_rows.append([html.escape(o['id']),html.escape(o['status']),math(o['attempts']),math(o['graph_metrics']['forced']),math(round(o['seconds'],6)),'Accepted ground certificate' if o['independent_certificate_accepted'] else 'No accepted proof', 'Passed' if o['independent_trace_accepted'] else html.escape(o['independent_scope'])])
    results=table(['Control','Actual outcome','Attempts','Forced moves','Search seconds','Proof check','Complete trace check'],result_rows)
    failure=load(ROOT/'.gcts-active/shared-symbolic-geometry-search-source-20261011/search-lifetime-v1.json')
    auditlife=load(ROOT/selected['independent_lifetime'])
    failed_cost=Decimal(str(failure['full_supervisor_process_seconds_including_receipt_write']))
    producer_cost=Decimal(str(life['full_supervisor_process_seconds_including_receipt_write']))
    audit_cost=Decimal(str(selected['independent_owned_seconds']))
    costs=table(['Owned phase','Seconds','Conservative peak bytes','Scope'],[
        ['Preserved first adapter failure',math(failed_cost),math(failure['conservative_host_peak_bytes']),'Model constructed; no target search began'],
        ['Corrected producer',math(producer_cost),math(life['conservative_host_peak_bytes']),'Preparation, two search observations, serialization and reap'],
        ['Separate independent audit',math(audit_cost),math(selected['independent_peak_bytes']),html.escape(selected['independent_gate_scope'])],
        ['Additional owned total',math(failed_cost+producer_cost+audit_cost),'Peaks are not summed','Inventory preparation, source authoring, metadata, terminal review and publication are additional']])
    bridge=load(ROOT/'.gcts-active/shared-symbolic-native-bridge-20261011/bridge-design-v1.json')
    config={'tex':{'inlineMath':[[r'\(',r'\)']],'displayMath':[[r'\[',r'\]']]},'options':{'skipHtmlTags':['script','style','pre','code']}}
    verdict='<p class="note">'+prose(selected['assessment'])+'</p>'
    diagnosis='<section class="panel" id="next"><h2>The next search-policy experiment.</h2><p>'+html.escape(selected['diagnosis_summary'])+'</p><p>This is a source-bound proposal from the saved traces. It has not been run or validated as an improvement. Any matching score changes only the complete-domain order, while checked global dead points, forced moves and earliest generation retain priority.</p><p>'+link(selected['diagnosis_result'],'Saved-trace diagnosis')+' · '+link(selected['next_search_plan'],'Prospective generic receptor-ranking plan')+'</p></section>'
    content='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Automatic symbolic geometry search · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax='''+json.dumps(config)+''';</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>
main{max-width:1240px}#reader .gcts-math{display:inline-block;max-width:100%;overflow:auto;vertical-align:middle}#reader .gcts-proof-row>div:last-child{min-width:0;overflow:auto}.note{padding:18px;border-left:4px solid #a57334;background:#fff4e3}.controls{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0}select{max-width:100%;font:inherit;padding:8px}.tile-row{display:grid;grid-template-columns:94px minmax(0,1fr);gap:16px;padding:16px;margin:12px 0;background:#f3f6f1;border-radius:7px}.tile{width:88px;height:88px;background:#fff;border:2px solid #6d7c6b;display:flex;align-items:center;justify-content:center;flex-direction:column}.tile small{font-size:11px}.tile-layer{width:100%;text-align:center}.marks{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}.mark{padding:6px 9px;border-radius:5px}.formula-mark{background:#d7e9ff;color:#173b78}.reference-mark{background:#e6d9ff;color:#503180}.hide-formulas .formula-mark,.hide-references .reference-mark{display:none}.formula{overflow:auto;padding:12px}td{font-size:14px}pre{overflow:auto;max-height:420px}h2{scroll-margin-top:20px}@media(max-width:650px){.tile-row{grid-template-columns:60px minmax(0,1fr)}.tile{width:56px;height:56px}}
</style></head><body><header class="masthead"><a href="../#automatic-geometry">Research report</a><span>NOTEBOOK 106</span><a href="#assessment">Assessment</a></header><main><section class="intro"><p class="eyebrow">HYPOTHESES → AUTOMATIC SEARCH → SEPARATE CHECKING</p><h1>Search from the hypotheses.</h1><p class="deck">Two fixed ordering controls search the same finite symbolic geometry language. No authored proof word or active cluster descriptor is supplied.</p><p><a href="#problem">The statement</a> · <a href="#results">Actual outcomes</a> · <a href="#reader">Read the tiles or trace</a> · <a href="#cost">Costs</a></p></section><section class="panel" id="problem"><h2>The exact guarded incidence problem.</h2><div class="formula">'''+math(bridge['problem_latex'])+'''</div><p>The guard abbreviates the original predicates:</p><div class="formula">'''+math(bridge['guard_latex'])+'''</div><p>In words: the first two hypotheses describe distinct points incident with the indicated pairs of lines. The guarded uniqueness axiom identifies those lines. The third hypothesis says the indicated point is incident with the first line; the target asserts incidence with the last. These are abstract symbolic predicates, without drawn points, lengths or angles.</p><p>The claim is a ground sequent relative to all three hypotheses and the retained guarded incidence axiom. The designed decoder would retain the hypotheses as three named axioms in a flat shared-checker request. Neither recorded run produced a proof or that request. Such a request would preserve these assumptions rather than establish a universally closed theorem.</p></section><section class="panel" id="results"><h2>Actual automatic search observations.</h2>'''+results+verdict+'''<p>Both controls retain '''+math(229)+' recipes, '+math(217)+' formula values, '+math(24)+' required proof rows and all '+math(171)+''' checked source bodies. This finite grammar was previously prepared for this ground incidence problem; it is not the full request-independent native palette. Their active descriptor lists are empty. Ordinary base order is compared with a fixed generic forward/readiness/novelty permutation; neither is reinforcement learning. The source bodies are not proposed as target-proof hints in either run.</p><p>Global dead points and forced moves precede the earliest-generation branch. Every legal candidate in the chosen domain remains in fallback. A child is excluded only after finite exhaustion and exact parent restoration. Attempt, deadline or trace cutoff returns unknown and restores the whole paired root.</p><p>The '''+math(20)+'''-second lane value is a checked deadline. In-flight ordering, state hashing, propagation and rollback may finish later; actual elapsed time is shown. Any overshoot cannot support a strict equal-wall-time success or speed claim. The separately enforced whole-worker/owner gates remain distinct.</p></section><section class="panel" id="reader"><h2>Examine the actual tile rows or search trace.</h2><p>Blue markings encode formula values. Purple markings encode ordered offsets to earlier source rows. Placements translate without rotation. When a finite certificate exists, its exact rows translate into formulas and the stated inference. The selected trace also shows its actual occupied squares and formula constraints. A purple offset can point to an earlier row that is still empty: that is a pending receptor, not a derived proof line. The default view is the first saved state with the largest occupied-row count.</p><div class="controls"><label>Observation <select id="observation"></select></label><label>Trace event <select id="trace-event"></select></label></div><p><label><input id="formula-layer" type="checkbox" checked> Blue formula layer</label> <label><input id="reference-layer" type="checkbox" checked> Purple ordered-reference layer</label></p><div id="proof-view" aria-live="polite"></div><div id="trace-view" aria-live="polite"></div></section><section class="panel" id="cost"><h2>Count preparation, failures and independent checking.</h2>'''+costs+'''<p>The first actual run stopped on repeated file-path aliases in the phase metadata passed to the body-registry factory. Both source reviews missed that caller precondition. Its model construction, traceback, terminal/reaped processes and cost remain preserved. The corrected adapter passes the accepted original '''+math(56)+'''-input body-registry plan and keeps all '''+math(118)+''' broader phase prerequisites. No recipe, premise, proof row or fallback candidate was deduplicated.</p><p>The corrected phase retains its '''+math(180)+'-second outer, '+math(175)+'-second supervisor, '+math(170)+'-second child alarm and '+math(512)+''' MiB conservative peak gate. The failed phase is additional; the two phases do not claim a joint '''+math(180)+'''-second bound. These are monitored and retrospective memory checks, not a hard operating-system memory cap.</p><p>Historical source-body/native admission, finite model preparation and earlier audits are additional dependencies. Metadata preparation, independent terminal review and report/publication work are additional to the displayed three-owner total. Source-authoring CPU time remains unmeasured. Component clocks overlap; do not add ordering, tracing and rollback clocks as disjoint costs. A speed comparison must include preparation, proposal validation and checking for the same accepted result. The new observations use the small attempt budget from the frozen plan; both stop on attempts rather than time. Their forced-move counts and partial occupancies cannot establish proof-search superiority.</p></section><section class="panel" id="assessment"><h2>What this says about GCTS proof search.</h2>'''+verdict+'''<p>This experiment uses the finite scalar-point proof adaptation. Its geometric occupancy and distant markings enforce the declared row/interface constraints. A request-independent Wang palette exists, but no shared native machine query or compiler correspondence is activated here. A checked symbolic certificate and a checked native Wang-machine execution are separate claims.</p><p>The recorded runs execute global occupancy/mark compatibility, complete candidate bookkeeping, forced propagation and search rollback. These are operational constraint-search contributions, with no new theorem discovered here. A ground proof in this finite grammar would establish actual automated discovery under the declared assumptions. It would not establish unrestricted first-order completeness, general Hilbert geometry, an RL advantage or superiority to existing provers. Matching or surpassing proof-search methods still needs matched theorem families and full costs.</p><p>The full program remains active: learned failure markings, receptor-adapted reusable clusters, multiscale and finite/movable-boundary tiling, arithmetic, turtle and Penrose remain research goals.</p></section>'''+diagnosis+'''<section class="panel" id="evidence"><h2>Exact source and terminal evidence.</h2><p>'''+link(str((phase/'search-outcome-v1.json').relative_to(ROOT)),'Actual producer outcome')+' · '+link(str((phase/'search-lifetime-v1.json').relative_to(ROOT)),'Full producer lifetime')+' · '+link(selected['independent_result'],'Independent result')+' · '+link(selected['independent_lifetime'],'Independent owned lifetime')+'''</p><p><a href="visual-data.json">Viewer projection</a> · <a href="result-summary.json">Result summary</a> · <a href="origins.json">Exported origins</a> · <a href="source-input-bindings.json">Exact source/input routes</a> · <a href="sources-and-inputs.zip">Additional bound files</a></p><p>Raw results and failed history retain their exact bytes. The reader is a display projection and cannot establish proof validity by itself.</p></section></main><script defer src="viewer.js"></script></body></html>'''
    reader=DEST/'reader.html';reader.write_text(content);files.add(str(reader.relative_to(ROOT)))
    save('result-summary.json',dict(goal_status='active',accepted_ground_certificates=passed,assessment=selected['assessment'],controls=[dict(id=o['id'],status=o['status'],attempts=o['attempts'],seconds=o['seconds'],independent_certificate_accepted=o['independent_certificate_accepted'],independent_trace_accepted=o['independent_trace_accepted']) for o in observations],source_authored_target_hints=0,active_cluster_descriptors=0,new_native_queries=0,new_RL_training=False,additional_owned_seconds=str(failed_cost+producer_cost+audit_cost),scope='Finite symbolic ground-sequent search; full proof and whole-search trace scope remain distinct.'))
    previous=baseline.decode();assert 'RESEARCH NOTEBOOK · 105' in previous
    panel='<section class="panel" id="automatic-geometry"><h2>Checkpoint 106 · Automatic geometry search from hypotheses</h2><p>Two ordering controls now have actual bounded observations in the unchanged finite symbolic language. '+prose(selected['main_assessment'])+' <a href="automatic-geometry/reader.html?v=20261011-ag1#reader">Inspect the exact tile rows, formulas or search trace</a>.</p><p>No authored target-proof hint, shared native query or new RL training is supplied. Adapter failures, unknowns and independent-check scope remain explicit.</p></section>\n'
    anchor='<section class="panel" id="full-cluster-model">';assert previous.count(anchor)==1
    updated=previous.replace('RESEARCH NOTEBOOK · 105','RESEARCH NOTEBOOK · 106',1).replace(anchor,panel+anchor,1)
    mainpath=ROOT/MAIN
    if mainpath.read_bytes()!=baseline:
        old=load(HERE/'task-files.json');record=next(e for e in old if e['path']==MAIN);assert pin(mainpath)=={k:record[k] for k in ('sha256','bytes')},'unrelated main-report edit'
    mainpath.write_text(updated);files.add(MAIN)
    manifest=[dict(path=f,**pin(ROOT/f)) for f in sorted(files)];(HERE/'task-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(files=len(manifest),origins=len(origins),bindings=len(bindings),accepted_ground_certificates=passed,science_executed_by_report=False)))


if __name__=='__main__':main()
