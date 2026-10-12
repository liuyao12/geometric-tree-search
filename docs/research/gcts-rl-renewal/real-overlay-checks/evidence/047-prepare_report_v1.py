"""Metadata-only export of accepted saved observations; no scientific imports."""
import hashlib
import html
import json
from pathlib import Path
import time

ROOT = Path.cwd()
PROGRESS = ROOT / '.gcts-active/real-overlay-fixture-progress-20261012'
PRODUCER = ROOT / '.gcts-active/family-proposal-real-overlay-source-20261012'
INDEPENDENT = ROOT / '.gcts-active/family-rl-independent-review-20261012'
PUBLIC = ROOT / 'docs/research/gcts-rl-renewal/real-overlay-checks'


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    start = time.monotonic()
    accepted = json.loads((PROGRESS / 'accepted-disposition-v1.json').read_text())
    assert accepted['status'] == 'accepted_complete_real_engine_synthetic_overlay_gate'
    assert not PUBLIC.exists()
    PUBLIC.mkdir(parents=True)
    evidence = PUBLIC / 'evidence'
    evidence.mkdir()
    paths = set()
    for folder, names in [
        (PRODUCER, ['family_learned_overlay_v2.py', 'real_overlay_fixture_worker_v1.py',
            'owned_real_overlay_fixture_v1.py', 'freeze_real_overlay_fixture_v1.py',
            'overlay_successor_author_v2.py', 'overlay-v1-to-v2.diff', 'protocol-v1.json',
            'real_overlay_fixture_corpus_v1.json', 'fixture-plan-v1.json', 'fixture-plan-v2.json',
            'source-archive-v1.zip', 'root-fixture-activation-v1.json', 'root-fixture-activation-v2.json',
            'owned-output-v1/fixture-lifetime-v1.json', 'owned-output-v2/fixture-result-v1.json',
            'owned-output-v2/fixture-lifetime-v1.json']),
        (INDEPENDENT, ['independent_features_v1.py', 'independent_policy_v1.py',
            'independent_fixture_points_v1.py', 'independent_fixture_whole_v1.py',
            'independent_fixture_replay_v1.py', 'independent_fixture_worker_v1.py',
            'owned_independent_fixture_replay_v1.py', 'finalize_actual_fixture_replay_plan_v1.py',
            'finalize_actual_fixture_replay_plan_v2.py', 'freeze_independent_source_v1.py',
            'source-plan-v1.json', 'source-review-v1.json', 'source-v1.zip', 'protocol-v1.json',
            'actual-replay-plan-v1.json', 'root-actual-replay-activation-v1.json',
            'owned-output-v1/independent-result-v1.json', 'owned-output-v1/independent-lifetime-v1.json']),
        (PROGRESS, ['accepted-disposition-v1.json', 'producer-source-review-v1.json',
            'producer-source-review-v2.json', 'independent-source-review-v2.json',
            'producer-terminal-v1.json', 'producer-terminal-v2.json', 'independent-terminal-v2.json',
            'run_owned_once_v1.py', 'run_owned_once_v2.py', 'preflight-failure-disposition-v1.json',
            'metadata-preflight-failure-v1.json', 'prepare_report_v1.py']),
    ]:
        paths.update(folder / name for name in names)
    producer_plan = json.loads((PRODUCER / 'fixture-plan-v2.json').read_text())
    for record in producer_plan['inputs']:
        if record['path'].endswith('.py') or record['role'] in ('frozen_curriculum_split', 'frozen_RL_protocol', 'AGENTS', 'master_contract'):
            paths.add(ROOT / record['path'])
    paths.add(ROOT / '.gcts-active/family-proposal-rl-small-source-20261012/family_learned_overlay_v1.py')
    origins = []
    links = {}
    for index, path in enumerate(sorted(paths)):
        target = evidence / ('%03d-' % index + path.name)
        data = path.read_bytes()
        with target.open('xb') as stream:
            stream.write(data)
        assert target.read_bytes() == data
        origins.append(dict(origin=pin(path), published=pin(target)))
        links[str(path.relative_to(ROOT))] = 'evidence/' + target.name
    write_new(PUBLIC / 'origins.json', origins)
    raw = json.loads((ROOT / accepted['raw_result']['path']).read_text())
    corpus = json.loads((PRODUCER / 'real_overlay_fixture_corpus_v1.json').read_text())
    cases = []
    for case in raw['scenarios']:
        views = []
        for event in case['events']:
            snapshot = event['after']
            controller = snapshot['overlay']['controller']
            graph = controller['graph']
            views.append(dict(index=event['index'], op=event['op'], error=event.get('error'),
                payload=event['payload'], totals=graph['totals'], marks=graph['marks'],
                order=graph['order'], selected_generations=graph['selected_generations'],
                roots=graph['roots'], domains=[d['count'] for d in graph['domains']],
                decision=snapshot['decision'], hints=controller['hint_states'],
                active_id=snapshot['overlay']['active_descriptor_id'],
                overlay_revision=snapshot['overlay']['overlay_revision'],
                trails=snapshot['trail_lengths'],
                recorded_fact_sample=event['result'] if event['op'] == 'available_facts' else None,
                policy_record=event['result'][1] if event['op'] == 'choose' and event.get('error') is None else None))
        cases.append(dict(id=case['id'], descriptors=case['descriptors'], events=views))
    write_new(PUBLIC / 'trace-view.json', dict(schema='display_excerpt_of_saved_accepted_fixture_v1',
        raw_result_pin=accepted['raw_result'], source='Display-only projection; full raw record remains acceptance evidence.',
        formulas=corpus['formulas'], recipes=corpus['recipes'], cases=cases))
    def link(path, label):
        return '<a href="' + links[str(path.relative_to(ROOT))] + '">' + html.escape(label) + '</a>'
    heading = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Real-engine proposal checks · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>
main{max-width:1200px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.stat{background:#eef3ed;border:1px solid #ced9cd;border-radius:6px;padding:18px}.stat strong{display:block;font-size:30px;margin-bottom:8px}.scope-note{border-left:5px solid #a67534;background:#fbf4e8;padding:20px}.controls{display:flex;flex-wrap:wrap;gap:15px;align-items:center;margin:18px 0}select,button{font:inherit;padding:8px;border:1px solid #8b9a8d;border-radius:4px;background:#fff}input[type=range]{width:300px}.board-wrap{overflow:auto;padding:18px 0}.board{position:relative;min-width:900px;padding-top:8px}.rows{display:grid;grid-template-columns:repeat(6,1fr);gap:16px}.row-card{border:1px solid #ced5ca;border-radius:5px;padding:9px;text-align:center;background:#fafbf7}.tile{height:108px;border:2px solid #adb9a6;display:flex;flex-direction:column;justify-content:center;margin:12px 0;position:relative;background:#fff}.tile.filled{background:#e4eef8;border-color:#4476ad}.tile.empty{border-style:dashed}.formula-mark{color:#715196;font-weight:600;min-height:30px}.port{position:absolute;width:12px;height:12px;border-radius:50%;bottom:-7px}.port-a{left:28%;background:#c58530}.port-b{right:28%;background:#438c78}.row-label{font-size:14px;color:#5b665c}.key-label{font-size:11px;overflow-wrap:anywhere;min-height:32px}.wires{display:block;width:100%;height:105px;overflow:visible}.legend{display:flex;gap:25px;flex-wrap:wrap;font-size:14px}.swatch{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:5px}.hint-line{padding:12px;background:#f0eaf7;border-radius:4px}.event-note{padding:16px;background:#f4f6ef}.table-wrap{overflow:auto}th,td{white-space:nowrap}details{margin:18px 0}pre{overflow:auto;font-size:12px}.status-ready{color:#277449}.status-waiting{color:#886314}.status-retired{color:#a84135}.status-consumed{color:#5d6571}.mutants{columns:2}mjx-container{max-width:100%}@media(max-width:800px){.summary-grid{grid-template-columns:repeat(2,1fr)}.mutants{columns:1}input[type=range]{width:190px}}</style></head><body><header class="masthead"><a href="../#real-overlay-checks">Research report</a><span>NOTEBOOK 113</span><a href="#explorer">Inspect actual steps</a></header><main>
<section class="intro"><p class="eyebrow">REAL POINT ENGINE · PROPOSAL SELECTION · COMPLETE INDEPENDENT REPLAY</p><h1>The repaired proposal interface passes its engine checks.</h1><p class="deck">All declared cases run through the unchanged point graph and cluster controller. A separate implementation reconstructs the complete saved record and rejects altered records.</p><p><a href="#explorer">Interactive steps</a> · <a href="#audit">Independent checks</a> · <a href="#costs">Full costs</a> · <a href="#next">Research assessment</a> · <a href="#evidence">Sources and records</a></p></section>
<section class="panel"><div class="summary-grid"><div class="stat"><strong>\(24\)</strong>Cases accepted</div><div class="stat"><strong>\(122\)</strong>Complete events</div><div class="stat"><strong>\(12\)</strong>Altered saved records rejected</div><div class="stat"><strong>\(0\)</strong>New proofs or training episodes</div></div><p class="scope-note">This is a small synthetic engine fixture, with \(6\) rows, \(8\) recipes and \(4\) formulas. Some fixture recipes deliberately supply arbitrary outputs. They are test infrastructure, not admitted logical rules. The result establishes interface behavior on these cases; it does not establish theorem validity, learned-policy benefit or unrestricted cluster synthesis.</p></section>
<section class="panel" id="explorer"><h2>See occupancy, distant markings and proposal state separately.</h2><p>The square cards display unit occupancy at required points. Violet labels are assigned formula markings, including on empty rows; amber and green links are the two ordered source-port layers. A marking on an empty row is a constraint, not a proved fact. Translation is allowed and rotation is not.</p><div class="controls"><label for="case-select">Case</label><select id="case-select" aria-label="Fixture case"></select></div><div class="controls"><button id="previous" type="button">Previous step</button><input id="event-range" aria-label="Recorded event" type="range" min="0" value="4"><button id="next-step" type="button">Next step</button><span id="event-position"></span></div><div id="event-note" class="event-note" aria-live="polite">Loading the saved display excerpt…</div><div class="board-wrap"><div class="board"><div class="rows" id="rows"></div><svg class="wires" id="wires" viewBox="0 0 900 105" role="img" aria-label="Ordered source marking links"></svg></div></div><div class="legend"><span><i class="swatch" style="background:#4476ad"></i>Selected unit occupancy</span><span><i class="swatch" style="background:#715196"></i>Assigned formula mark</span><span><i class="swatch" style="background:#c58530"></i>First source port</span><span><i class="swatch" style="background:#438c78"></i>Second source port</span></div><p id="hint-line" class="hint-line"></p><p id="fact-line"></p><details><summary>Literal saved event fields</summary><pre id="raw-event"></pre></details><p>This is a display projection of accepted observations, not another search or proof checker. The full record retains every before, result, after and terminal state. The default case shows an occupied output whose sources are still pending, then the steps that make its dependency-complete output available.</p></section>
<section class="panel" id="audit"><h2>Independent reconstruction checks more than pass flags.</h2><p>The auditor reconstructs every complete row domain by literal enumeration, source body and full constituent identity, all assigned markings and reference counts, global dead/forced/earliest-generation decisions, controller hints, active proposal, checkpoints, features, distributions and choice gradients. It examines \(244\) snapshot observations and \(21602\) candidate-key observations, including repetitions; these are not counts of distinct graph states or inventory types.</p><p>The actual tape contains \(14\) successful ordering operations, \(9\) fresh policy selections and \(11\) primitive placements. The draws are explicitly authored uniform-menu test draws, with frozen zero weights. There is no sampled RNG stream or learned update. Waiting continuation and forced propagation consume no new draw.</p><p>The engine actually rejects \(5\) corrupt whole registrations and \(12\) invalid preparation/selection operations. These counts differ from the auditor's \(12\) altered saved-record controls below: each saved-record control calls the full independent audit, although rejection may occur at the first changed field. They are not fresh producer process runs.</p><ul class="mutants">'''
    mutants = json.loads((ROOT / accepted['independent_result']['path']).read_text())['actual_mutation_controls']
    descriptions = {
        'missing-scenario':'Missing case', 'missing-terminal-operation':'Missing operation',
        'wrong-whole-aggregate':'Changed whole marking union', 'lost-complete-domain-key':'Lost primitive alternative',
        'changed-controller-hint':'Changed cluster status', 'changed-menu-vector':'Changed feature vector',
        'disabled-draw-flag':'Disabled draw requirement', 'wrong-policy-probability':'Changed action probability',
        'wrong-mixture-gradient':'Changed mixture gradient', 'pending-output-as-fact':'Pending output counted as a fact',
        'broken-paired-overlay-rollback':'Broken proposal rollback', 'unknown-creates-exclusion':'Unknown creates an exclusion',
    }
    body = heading + ''.join('<li>' + html.escape(descriptions[x['id']]) + ': rejected</li>' for x in mutants)
    body += r'''</ul><p>The original overlay trusted a caller-owned prepared menu after checking a state digest. That gap was found by source review; no original-version failing fixture was executed. The repaired version rebuilds and compares the complete canonical menu and literal draw requirement before changing state. The original source is preserved. All \(31\) features, policy mathematics, donor split and hyperparameters remain unchanged.</p></section><section class="panel" id="costs"><h2>Include validation and the failed launch.</h2><div class="table-wrap"><table><thead><tr><th>Owned phase</th><th>Full dispatched seconds</th><th>Owned peak estimate, bytes</th></tr></thead><tbody>'''
    for label, seconds, peak in [
        ('Environment preflight; no worker', accepted['pre_scientific_environment_failure_seconds'], 120930304),
        ('Producer engine fixture', accepted['producer_full_owned_seconds'], accepted['producer_peak_estimate_bytes']),
        ('Independent replay and mutations', accepted['independent_full_owned_seconds'], accepted['independent_peak_estimate_bytes']),
    ]:
        body += '<tr><th>' + label + r'</th><td>\(' + '%.9f' % seconds + r'\)</td><td>\(' + str(peak) + r'\)</td></tr>'
    body += r'''</tbody></table></div><p>The two actual phases total \(5.463634625\) dispatched seconds, including source hashing, imports, observers, output decoding, final owner serialization, exit and reaping. The earlier \(0.373626625\) second sandboxed launch stopped before creating a scientific worker because process accounting was unavailable. A fresh plan successor preserved that failure and ran with the required accounting access; no executed scientific result was retried.</p><p>Source authoring, manual review, metadata work, reporting and deployment are additional, unmeasured research costs. Memory values are conservative owned peak estimates including the accounting observer; they are retrospective acceptance gates, not hard OS caps. Both actual owners and workers are terminal and reaped. An additional metadata-only external-path serialization failure was corrected and preserved.</p></section><section class="panel" id="next"><h2>A prerequisite for learning is now tested; learning remains open.</h2><p>This closes an actual interface gate: whole-proposal selection can change continuation order while retaining every primitive alternative, distant marking agreement, global scheduling and exact paired rollback on the declared cases. The <a href="../context-transfer/reader.html#comparison">changed-context theorem searches</a> still all have unknown outcomes. This fixture does not change those results or establish acceleration.</p><p>Parallel source work is developing the exact donor-context compiler gate and the complete scientific search/RNG/trajectory adapter. Before training, the adapter must bind the raw episode to independently rebuilt choices and gradients, freeze weights throughout failed branches, count chronological commits and retirements once across rollback, and observe dependency-complete fact potential after every primitive step. The frozen donor sequence, held-out split and final checkpoint remain fixed.</p><p>Actual donor/recipient licenses and complete pools, full scientific DFS/RNG/reward/update replay, a request-independent first-order/Wang compiler, arbitrary cluster synthesis, certified learned failure markings, turtle substitution or plane tiling, and exact Penrose extension remain unfinished. Fractional occupancy, multi-point positive support and general transformations are outside this fixture.</p></section><section class="panel" id="evidence"><h2>Inspect the exact sources and complete records.</h2><p>'''
    body += ' · '.join([
        link(ROOT / accepted['raw_result']['path'], 'Complete producer record'),
        link(ROOT / accepted['independent_result']['path'], 'Independent replay and mutation results'),
        link(PROGRESS / 'accepted-disposition-v1.json', 'ROOT acceptance and scope'),
    ]) + '</p><p>' + ' · '.join([
        link(PRODUCER / 'fixture-plan-v2.json', 'Exact producer plan'),
        link(INDEPENDENT / 'actual-replay-plan-v1.json', 'Exact independent plan'),
        link(PROGRESS / 'producer-terminal-v2.json', 'Producer terminal receipt'),
        link(PROGRESS / 'independent-terminal-v2.json', 'Independent terminal receipt'),
    ]) + r'''</p><p><a href="origins.json">Published source origins and byte hashes</a> · <a href="trace-view.json">Display excerpt</a>. Current-stage sources, raw records and receipts are exact copies. Plans retain historical prerequisite bindings; this export does not bundle every historical file or runtime binary. Process-list streams are excluded.</p></section></main><script src="reader.js"></script></body></html>'''
    (PUBLIC / 'reader.html').write_text(body)
    parent = ROOT / 'docs/research/gcts-rl-renewal/index.html'
    baseline = parent.read_bytes()
    assert baseline.decode().count('RESEARCH NOTEBOOK · 112') == 1
    with (PROGRESS / 'parent-baseline-v1.bin').open('xb') as stream:
        stream.write(baseline)
    panel = r'''<section class="panel" id="real-overlay-checks"><p class="eyebrow">NOTEBOOK 113 · ACTUAL REAL-ENGINE INTERFACE GATE</p><h2>The repaired proposal interface passes independent engine checks.</h2><p>All \(24\) synthetic cases and \(122\) events are reconstructed independently; all \(12\) altered saved records reject. Inspect occupancy, distant marking layers and paired rollback in the <a href="real-overlay-checks/reader.html#explorer">interactive saved-step reader</a>. This is interface evidence, with no new theorem, training episode or RL advantage.</p></section>'''
    text = baseline.decode().replace('RESEARCH NOTEBOOK · 112', 'RESEARCH NOTEBOOK · 113')
    assert text.count('</main>') == 1
    parent.write_text(text.replace('</main>', panel + '</main>'))
    write_new(PROGRESS / 'parent-change-v1.json', dict(baseline_sha256=hashlib.sha256(baseline).hexdigest(),
        old_counter='RESEARCH NOTEBOOK · 112', new_counter='RESEARCH NOTEBOOK · 113', added_panel=panel,
        rule='Counter plus one additive panel only; exact reversal required'))
    print(json.dumps(dict(status='prepared_reader_and_exact_evidence_pending_JS_and_validation',
        exact_copies=len(origins), report_generation_seconds_before_final_files=time.monotonic()-start,
        scientific_calls=0)))


if __name__ == '__main__':
    main()
