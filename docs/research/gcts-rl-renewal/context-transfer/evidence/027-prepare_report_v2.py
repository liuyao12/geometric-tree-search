"""Publishable saved-result reader; no functional science imports or reruns."""
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import time

ROOT = Path.cwd()
PRODUCER = ROOT / '.gcts-active/fixed-family-transfer-source-v1-20261012'
AUDITOR = ROOT / '.gcts-active/fixed-family-transfer-independent-source-20261012'
OUT = ROOT / '.gcts-active/fixed-family-transfer-progress-20261012'
DOC = ROOT / 'docs/research/gcts-rl-renewal/context-transfer'


def read(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
        return json.load(stream)


def pin(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def esc(value):
    return html.escape(str(value), quote=True)


def math(value):
    return r'\(' + esc(value) + r'\)'


def main():
    started = time.perf_counter()
    static = read(OUT / 'static-audit-disposition-v1.json')
    trace = read(OUT / 'trace-audit-disposition-v1.json')
    outcome = read(PRODUCER / 'search-outcome-v1.json')
    assert static['status'] == 'passed_ROOT_saved_static_audit_receipt_inspection'
    assert trace['status'] == 'passed_ROOT_saved_complete_three_lane_trace_receipt_inspection'
    assert len(trace['observations']) == len(outcome['observations']) == 3
    assert all(x['status'] == 'unknown_search_budget' and x['trace_accepted'] and not x['certificate_accepted'] for x in trace['observations'])
    parent = ROOT / 'docs/research/gcts-rl-renewal/index.html'
    baseline = parent.read_bytes()
    assert hashlib.sha256(baseline).hexdigest() == 'e96e6f91cebe2450ba6d4dc35acd5d177c92c70de62568a37e875eefce48218f'
    assert not DOC.exists()
    (DOC / 'evidence').mkdir(parents=True)
    sources = set()
    for folder in (PRODUCER, AUDITOR):
        sources.update(folder.glob('*.py'))
        sources.update(p for p in folder.glob('*.json') if not p.name.endswith('result-v1.json'))
        sources.update(folder.glob('*.zip'))
    sources.update(PRODUCER.glob('*.json.gz'))
    sources.update(AUDITOR.glob('*result-v1.json'))
    # Include the actual functional kernel/library surface and source data.
    plan = read(AUDITOR / 'trace-audit-plan-v1.json')
    sources.update(Path(r['path']) for r in plan['libraries'])
    prep = read(PRODUCER / 'preparation-plan-v1.json')
    for rec in prep['inputs']:
        path = ROOT / rec['path']
        if path.suffix == '.py' or rec['role'] in ('primitive_model', 'complete_family_projection', 'context_spec',
                'old_body_closure_source_constant_transport_certificate', 'old_body_closure_exact_three_source_schemas',
                'old_complete_body_plan'):
            sources.add(path)
    sources.add(ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py')
    sources.update(OUT / name for name in ('preparation-terminal-v1.json', 'static-audit-terminal-v1.json',
        'search-terminal-v1.json', 'trace-audit-terminal-v1.json', 'static-audit-disposition-v1.json',
        'trace-audit-disposition-v1.json', 'static-audit-source-review-v1.json', 'search-source-review-v1.json',
        'trace-audit-source-review-v1.json', 'static-wrapper-preflight-failure-v1.json', 'run_static_once.py',
        'run_static_once_v2.py', 'run_trace_once.py', 'run_phase_once.py', 'review_static_audit.py',
        'review_prepare.py', 'prepare_report_v1.py', 'prepare_report_v2.py'))
    origins = []
    links = {}
    for number, path in enumerate(sorted(sources)):
        assert path.is_file() and path.is_relative_to(ROOT)
        target = DOC / 'evidence' / ('%03d-' % number + path.name)
        shutil.copyfile(path, target)
        assert path.read_bytes() == target.read_bytes()
        source_pin = pin(path); target_pin = pin(target)
        origins.append(dict(original=source_pin, published=target_pin, byte_exact=True))
        links[str(path)] = 'evidence/' + target.name
    (DOC / 'origins.json').write_text(json.dumps(dict(schema='context-transfer-exact-publication-origins-v1',
        files=origins, scope='Current-stage sources, actual inputs, full raw results and receipts. Retained historical provenance is identified in exact plans and linked lineage; runtime binaries and process streams are excluded.'), indent=2) + '\n')
    def link(path, label):
        return '<a href="' + esc(links[str(path)]) + '">' + esc(label) + '</a>'
    rows = []
    bars = []
    names = ['Primitive', 'Fixed forward', 'Whole pool']
    colors = ['#4476ad', '#9170b3', '#669672']
    lane_metrics = []
    for i, (obs, checked) in enumerate(zip(outcome['observations'], trace['observations'])):
        assert obs['id'] == checked['id'] and obs['attempts'] == checked['attempts']
        result = read(ROOT / obs['result']['path'])
        lane_metrics.append(result)
        rows.append('<tr><th>' + names[i] + '</th><td>Unknown</td><td>' + math(obs['attempts']) + '</td><td>' + math(checked['branches']) +
            '</td><td>' + math(checked['forced']) + '</td><td>' + math(checked['proved_child_exclusions']) + '</td><td>' + math(format(obs['search_seconds'], '.9f')) + '</td><td>' + math(format(obs['cold_setup_seconds'], '.9f')) + '</td><td>' + math(format(obs['serialization_seconds'], '.9f')) + '</td></tr>')
        width = obs['search_seconds'] / 25 * 100
        bars.append('<div class="time-row"><strong>' + names[i] + '</strong><div class="time-track"><div class="time-bar" style="width:' + str(width) + '%;background:' + colors[i] + '"></div><span class="deadline" title="Declared search limit"></span></div><span>' + math(format(obs['search_seconds'], '.2f')) + ' s</span></div>')
    stages = [('Preparation', OUT / 'preparation-terminal-v1.json', 'full_phase_seconds_including_outer_final_write_and_reaping'),
              ('Independent context audit', OUT / 'static-audit-terminal-v1.json', 'full_phase_seconds_including_owner_final_write_and_reaping'),
              ('Three cold search lanes', OUT / 'search-terminal-v1.json', 'full_phase_seconds_including_outer_final_write_and_reaping'),
              ('Independent full trace audit', OUT / 'trace-audit-terminal-v1.json', 'full_phase_seconds_including_owner_final_write_and_reaping')]
    costs = []; total = 0.0
    for label, path, key in stages:
        r = read(path); total += r[key]
        peak = r.get('conservative_owned_peak_bytes', r.get('conservative_owned_peak_estimate_bytes'))
        costs.append('<tr><th>' + label + '</th><td>' + math(format(r[key], '.9f')) + '</td><td>' + math(peak) + '</td><td>' + link(path, 'Terminal receipt') + '</td></tr>')
    events = sum(x['events'] for x in trace['observations'])
    graphs = sum(x['distinct_graph_states'] for x in trace['observations'])
    bindings = sum(x['complete_base_binding_checks'] for x in trace['observations'])
    exclusions = sum(x['proved_child_exclusions'] for x in trace['observations'])
    controls = sum(x['count'] for x in trace['actual_event_template_controls'])
    pool = lane_metrics[2]
    equation = r'H(P,Q,l,m),\;m=n,\;\operatorname{Incident}(R,l)\;\vdash\;\operatorname{Incident}(R,n).'
    page = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A harder context transfer · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>main{max-width:1200px}.result{border-left:5px solid #a0783a;background:#fbf4e9;padding:22px}.equation{padding:18px;background:#f5f6f0;overflow:auto}.time-row{display:grid;grid-template-columns:140px 1fr 100px;gap:20px;align-items:center;margin:24px 0}.time-track{height:32px;background:#e4e8e1;position:relative;border-radius:4px}.time-bar{height:100%;border-radius:4px}.deadline{position:absolute;left:80%;top:-7px;height:46px;border-left:2px dashed #ae5d48}.table-wrap{overflow:auto}th,td{white-space:nowrap}.tracks{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.tracks>div{padding:20px;background:#f5f6f0;border:1px solid #d4dccf;border-radius:6px}details{margin:20px 0}@media(max-width:800px){.tracks{grid-template-columns:1fr}.time-row{grid-template-columns:105px 1fr 70px;gap:8px}}</style></head><body><header class="masthead"><a href="../#context-transfer">Research report</a><span>NOTEBOOK 112</span><a href="#comparison">Actual searches</a></header><main><section class="intro"><p class="eyebrow">NEW HYPOTHESES · THREE COLD CONTROLS · INDEPENDENT COMPLETE REPLAY</p><h1>The successful cluster does not yet transfer reliably.</h1><p class="deck">A changed premise pattern passes the independent context and pool checks. All three automated searches stop with unknown outcomes. This checkpoint makes the limits and the validation cost visible.</p><p><a href="#context">Symbolic target</a> · <a href="#comparison">Search comparison</a> · <a href="#audit">What was checked</a> · <a href="#assessment">Research judgment</a> · <a href="#costs">Complete costs</a> · <a href="#evidence">Exact evidence</a></p></section><section class="panel result"><h2>No new proof is claimed.</h2><p>The primitive and fixed forward controls each reach their ''' + math(128) + ' attempt limit. The whole-pool control reaches its time limit after ' + math(22) + ''' attempts. All three complete returned traces pass independent checking and restore the original boundary exactly. Unknown means the budget ended; it is not nonprovability.</p><p>The <a href="../fixed-family-search/reader.html#reader">earlier successful incidence proof, with actual colored tile rows and line-by-line translation</a> remains available. This run changes the hypotheses and rebuilds the full context instead of reusing that proof.</p></section><section class="panel" id="context"><h2>A new symbolic receptor pattern.</h2><div class="equation">\[''' + equation + r'''\]</div><p>''' + math('H(P,Q,l,m)') + ' expands to the right-associated conjunction of point and line type guards, ' + math('P\ne Q') + ', and the four incidence statements placing ' + math('P,Q') + ' on both ' + math('l,m') + '''. The second premise is now equality, replacing a second common-points conjunction. The statement is expressed symbolically; no coordinate diagram supplies an inference.</p><p>The compiler preserves all ''' + math(226) + ' non-assumption witnesses and ' + math(217) + ' formula codes, rebuilds the ' + math(3) + ' hypothesis licenses, and retains all ' + math(171) + ' conditional source bodies. The point model has ' + math(24) + ''' required rows, with the original hypotheses at the boundary and the target marking on the last row. Translations are allowed; rotation is not.</p><p>The independent static auditor reconstructs all ''' + math(229) + ' licenses, ' + math(332510) + ' initial candidates, all ' + math(171) + ' single types and ' + math(29241) + ' ordered pair types. Exactly ' + math(4) + ''' compatible whole proposals emerge. This is the complete declared canonical single/pair grammar, which is a restricted advice inventory; the primitive fallback remains complete.</p></section><section class="panel" id="comparison"><h2>Same boundary, same primitive domain, same budgets.</h2><p>Each cold lane registers the same inventory and uses the global dead/forced/earliest-generation scheduler. Only continuation ordering differs. Each receives ''' + math(128) + ' attempts, ' + math(20) + ' search seconds and ' + math(2000) + ''' trace events. There is one observation per control, not a balanced statistical study.</p><div class="time-chart">''' + ''.join(bars) + '</div><p class="note">The dashed line marks the declared ' + math(20) + ' second search limit; the chart spans ' + math(25) + ' seconds. The whole-pool lane stops at a finite operation boundary and records a ' + math(format(pool['checked_search_deadline_overshoot_seconds'], '.9f')) + ''' second overshoot. The stricter whole-process gates pass; this does not turn the search limit into a hard operating-system cutoff.</p><div class="table-wrap"><table><thead><tr><th>Control</th><th>Outcome</th><th>Attempts</th><th>Branches</th><th>Forced</th><th>Proved child exclusions</th><th>Search seconds</th><th>Cold setup seconds</th><th>Serialization seconds</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div><p>Proved child exclusions apply only to their restored parent contexts. The unknown root receives no impossibility claim. No supplied proof word, atomic macro move, native query or new RL training is used.</p></section><section class="panel" id="audit"><h2>Rollback and failed children now have actual trace evidence.</h2><p>The independent auditor reconstructs all ''' + math(events) + ' events, ' + math(graphs) + ' distinct reached graph states and ' + math(bindings) + ' raw base bindings across the three lanes. It verifies ' + math(exclusions) + ''' justified failed-child exclusions and paired graph/hint restoration. It also rechecks complete fallback permutations, global decisions, distant markings, whole hint retirement, and current full identities. The whole-pool run contains ''' + math(trace['observations'][2]['reconstructed_hint_counts']['whole_retirements']) + ''' actual whole hint retirements.</p><p>The static gate actually rejects ''' + math(static['context_mutation_calls']) + ' altered contextual payloads and checks ' + math(static['per_group_payload_controls']) + ' changed group payloads against independently reconstructed groups. The trace gate compares ' + math(controls) + ''' changed actual event payloads against independently rebuilt templates. These event controls are not full mutated-tape or process replays. There is no positive target certificate, so no positive-proof mutation control is exercised here.</p><p>''' + link(AUDITOR / 'static-audit-result-v1.json', 'Full independent static result') + ' · ' + link(AUDITOR / 'trace-audit-result-v1.json', 'Full independent trace result') + ' · ' + link(OUT / 'trace-audit-disposition-v1.json', 'Compact ROOT disposition') + '''</p></section><section class="panel" id="assessment"><h2>The evidence points to validation overhead, not an RL advantage.</h2><p>The whole-pool search performs ''' + math(pool['lifecycle_metrics']['whole_scans']) + ' whole scans, ' + math(pool['lifecycle_metrics']['members_checked']) + ' member checks and ' + math(pool['lifecycle_metrics']['mark_checks']) + ' marking checks. Its recorded hint-validation timer is ' + math(format(pool['lifecycle_metrics']['validation_seconds'], '.9f')) + ' seconds within the ' + math(format(pool['seconds'], '.9f')) + ''' second search. These profiling categories overlap other phase timers and must not be added together.</p><p>The earlier successful target shows that cluster advice can guide a complete primitive proof. The changed-context experiment does not establish useful acceleration or reliable transfer. All controls remain unknown, and the whole-pool lane spends most of its search time validating advice. The next implementation work should reduce repeated identity and authority work while preserving full validation, and establish a real-engine learning gate before claiming any RL contribution.</p><p>Known conditional source bodies remain authored and certified infrastructure. No new lemma family is discovered in this checkpoint. A request-independent first-order/Wang compiler, unrestricted cluster topology, certified learned redundant markings, turtle substitution or plane tiling, and exact Penrose extension remain open parts of the research program.</p></section><section class="panel" id="parallel"><h2>Parallel agents are producing concrete, reviewable interfaces.</h2><div class="tracks"><div><h3>Curriculum contexts</h3><p>A source-only generic compiler freezes the four donor contexts and held-out recipient, preserving the complete witness, formula and body inventory. Separate per-context independent acceptance is required.</p></div><div><h3>Real-engine policy gate</h3><p>A source-only small fixture uses the unchanged PointGraph and Controller. A minimal overlay successor rederives its action menu and draw requirement to repair a mutable-preparation gap; the old version remains preserved. It has not been executed.</p></div><div><h3>Independent replay</h3><p>A separate reviewer reconstructs features, menu, point legality, reward and update evidence. Exact raw trajectory bindings and chronological retirement accounting are requirements for the future driver.</p></div></div><p>The frozen ''' + math(31) + ' features and donor/held-out split predate these search outcomes. This checkpoint performs no tuning, donor episodes or learned-policy evaluations. Source authoring can proceed concurrently; ROOT activates actual experiments and publishes accepted results.</p></section><section class="panel" id="costs"><h2>Charge preparation and verification too.</h2><div class="table-wrap"><table><thead><tr><th>Owned phase</th><th>Full dispatched seconds</th><th>Owned peak estimate, bytes</th><th>Evidence</th></tr></thead><tbody>''' + ''.join(costs) + '</tbody></table></div><p>The four new-context phases total ' + math(format(total, '.9f')) + ''' dispatched seconds, including owner final serialization and reaping. This is a recorded subtotal, not a complete research or end-to-end wall-time bill. Metadata work, earlier numeric checks, source authoring, reporting and publication are additional.</p><p>Preparation and search memory estimates omit accounting-observer RSS and are not strict aggregate host upper bounds. Audit estimates add owned observer/kernel peaks; all are retrospective acceptance gates, not hard OS memory caps. All actual workers and owners are terminal and reaped. One ROOT metadata wrapper failed before activation when it tried to represent an external runtime path as project-relative; the original failure and corrected successor are retained. No scientific run was retried.</p></section><section class="panel" id="evidence"><h2>Inspect the complete saved observations.</h2><p>''' + ' · '.join(link(PRODUCER / (o['id'] + '-result-v1.json.gz'), names[i] + ' raw tape') for i, o in enumerate(outcome['observations'])) + '''</p><p>''' + link(PRODUCER / 'compiled-context-v1.json.gz', 'Exact compiled context') + ' · ' + link(PRODUCER / 'preparation-evidence-v1.json.gz', 'Complete preparation evidence') + ' · ' + link(PRODUCER / 'search-plan-v1.json', 'Frozen three-lane plan') + ' · ' + link(AUDITOR / 'trace-audit-plan-v1.json', 'Frozen independent audit plan') + ''' · <a href="origins.json">Exact published sources and origins</a></p><p>Current-stage sources, source data, complete raw results and receipts are copied byte for byte. The exact plans retain historical prerequisite bindings; the <a href="../family-learning-checks/reader.html">previous learning checkpoint</a> and <a href="../fixed-family-search/reader.html">earlier successful proof checkpoint</a> supply the report lineage. This export does not bundle every historical provenance file or runtime binary. The reader displays saved evidence and runs no scientific checker.</p></section></main></body></html>'''
    assert page.count('\\(') == page.count('\\)') and page.count('\\[') == page.count('\\]')
    reader = DOC / 'reader.html'; reader.write_text(page)
    old = baseline.decode(); counter_old = 'RESEARCH NOTEBOOK · 111'; counter_new = 'RESEARCH NOTEBOOK · 112'
    assert old.count(counter_old) == 1
    panel = '<section class="panel" id="context-transfer"><p class="eyebrow">NOTEBOOK 112 · INDEPENDENTLY AUDITED CONTEXT TRANSFER</p><h2>The cluster advantage does not yet transfer reliably.</h2><p>The changed-hypothesis context and complete cluster pool pass independent reconstruction. All three cold controls finish unknown within their budgets; complete returned traces, failed-child exclusions and rollback are independently checked. Whole-cluster validation dominates the recorded hint search cost. No new proof or RL benefit is claimed.</p><p><a href="context-transfer/reader.html#comparison">Open the actual controls, full audit and cost comparison</a></p></section>'
    assert old.count('</main>') == 1
    new = old.replace(counter_old, counter_new, 1).replace('</main>', panel + '</main>', 1)
    assert new.replace(panel, '', 1).replace(counter_new, counter_old, 1) == old
    parent.write_text(new)
    (OUT / 'parent-baseline-v1.bin').write_bytes(baseline)
    (OUT / 'parent-change-v1.json').write_text(json.dumps(dict(counter_old=counter_old, counter_new=counter_new, panel=panel, baseline_sha256=hashlib.sha256(baseline).hexdigest()), indent=2) + '\n')
    files = sorted([p for p in DOC.rglob('*') if p.is_file()] + [parent])
    manifest = dict(status='prepared_actual_context_transfer_checkpoint_pending_independent_reader_review_and_publication',
        files=[pin(p) for p in files], file_count=len(files), total_bytes=sum(p.stat().st_size for p in files),
        original_copies=len(origins), reader=pin(reader), actual_events=events, actual_distinct_graphs=graphs,
        actual_base_bindings=bindings, actual_proved_child_exclusions=exclusions,
        per_event_template_controls=controls, all_three_statuses='unknown_search_budget',
        new_target_proofs=0, RL_training=0, native_queries=0, full_phase_subtotal_seconds=total,
        report_generation_seconds_before_final_manifest_write=time.perf_counter()-started,
        scientific_checker_imports_or_calls=0, broad_goal_complete=False)
    with (OUT / 'task-files-v1.json').open('x') as stream:
        json.dump(manifest, stream, indent=2); stream.write('\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))


if __name__ == '__main__':
    main()
