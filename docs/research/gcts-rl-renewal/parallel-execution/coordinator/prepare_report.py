"""Publishable projection of terminal receipts. Never runs a search or checker."""
import gzip
import hashlib
import html
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PUB = Path('/private/tmp/gcts-family-router-publish-20261010')
DOC = ROOT / 'docs/research/gcts-rl-renewal'
DEST = DOC / 'parallel-execution'
MEM = ROOT / '.gcts-active/stochastic-replay-memory-20261011'
GEO = ROOT / '.gcts-active/hilbert-primitive-executor-20261011'
REVIEW = ROOT / '.gcts-active/stochastic-replay-review-20261011'
RUN = ROOT / '.gcts-active/arithmetic-stochastic-clusters-20261011/execution-v2'


def load(p):
    with (gzip.open(p, 'rt') if p.suffix == '.gz' else p.open()) as f:
        return json.load(f)


def pin(p):
    b = p.read_bytes()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def math(s):
    return r'\(' + html.escape(str(s)) + r'\)'


def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>' + ''.join('<th>' + x + '</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + x + '</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def main():
    DEST.mkdir(exist_ok=True)
    files, origins, requirements = set(), [], {}
    def require(path, sha, size=None):
        p = Path(path)
        p = p if p.is_absolute() else ROOT / p
        if not p.is_file() or ROOT not in p.parents:
            raise ValueError('unresolved pinned research input: ' + str(path))
        got = pin(p)
        assert got['sha256'] == sha and (size is None or size == got['bytes']), path
        relative = str(p.relative_to(ROOT))
        if relative in requirements:
            assert requirements[relative] == got
        requirements[relative] = got
    def scan(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v and isinstance(v['path'], str):
                if (ROOT / v['path']).is_file() or Path(v['path']).is_absolute():
                    require(v['path'], v['sha256'], v.get('bytes'))
            for key in ('source_sha256', 'input_sha256'):
                if isinstance(v.get(key), dict):
                    for path, sha in v[key].items():
                        require(path, sha)
            for value in v.values():
                scan(value)
        elif isinstance(v, list):
            for value in v:
                scan(value)
    def copy(p, relative):
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        files.add(str(target.relative_to(ROOT)))
        origins.append({'path': str(target.relative_to(ROOT)), 'origin': str(p.relative_to(ROOT)), **pin(p)})
        require(p, pin(p)['sha256'])
        if p.suffix == '.json':
            scan(load(p))
    def save(name, value):
        p = DEST / name
        p.write_text(json.dumps(value, indent=2) + '\n')
        files.add(str(p.relative_to(ROOT)))
    # Every current owned scientific source/receipt, including failed attempts.
    for folder, label in ((MEM, 'arithmetic'), (GEO, 'geometry'), (REVIEW, 'independent'),
                          (ROOT / '.gcts-active/stochastic-replay-fixture-followon-20261011', 'loader-fixtures')):
        for p in sorted(folder.rglob('*')):
            if p.is_file() and p.suffix in ('.json', '.py', '.zip', '.txt') and '__pycache__' not in p.parts:
                copy(p, label + '/' + str(p.relative_to(folder)))
    for p in sorted(HERE.glob('*')):
        if p.is_file() and p.suffix in ('.json', '.py') and p.name not in ('publication.json', 'turn-result.json', 'task-files.json', 'local-validation.json', 'live-hash-checks.json'):
            copy(p, 'coordinator/' + p.name)
    collector_path = ROOT / '.gcts-active/arithmetic-stochastic-clusters-20261011/collector-v1/final-audited-v1.json'
    require(collector_path, pin(PUB / 'docs/research/gcts-rl-renewal/stochastic-clusters/arithmetic/collector/final-audited-v1.json')['sha256'])
    for p in sorted((RUN / 'evaluation').glob('*-summary.json')):
        require(p, pin(PUB / 'docs/research/gcts-rl-renewal/stochastic-clusters/arithmetic/evaluation' / p.name)['sha256'])

    # Resolve exact old bindings through the established public artifacts. Large
    # unchanged search traces remain at their original published endpoints.
    old_routes = {}
    for p in sorted((PUB / 'docs/research/gcts-rl-renewal').rglob('*.json')):
        if p.name not in ('origins.json', 'source-input-bindings.json'):
            continue
        records = load(p)
        if not isinstance(records, list):
            continue
        for e in records:
            if not isinstance(e, dict) or 'sha256' not in e:
                continue
            origin = e.get('origin') or e.get('path')
            published = e.get('path') if e.get('origin') else e.get('published_path')
            member = e.get('archive_member')
            if published and (PUB / published).is_file() and pin(PUB / published)['sha256'] == e['sha256']:
                old_routes[(origin, e['sha256'])] = {'published_path': published, 'archive_member': None}
            elif member:
                archive = p.parent / 'sources-and-inputs.zip'
                if archive.exists():
                    with zipfile.ZipFile(archive) as z:
                        if member in z.namelist():
                            b = z.read(member)
                            if hashlib.sha256(b).hexdigest() == e['sha256']:
                                old_routes[(origin, e['sha256'])] = {'published_path': str(archive.relative_to(PUB)), 'archive_member': member}
    new_routes = {e['origin']: {'published_path': e['path'], 'archive_member': None} for e in origins}
    records = []
    archive = DEST / 'sources-and-inputs.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path, expected in sorted(requirements.items()):
            route = new_routes.get(path) or old_routes.get((path, expected['sha256']))
            if route is None and (PUB / path).is_file() and pin(PUB / path) == expected:
                route = {'published_path': path, 'archive_member': None}
            if route is None:
                z.write(ROOT / path, path)
                route = {'published_path': str(archive.relative_to(ROOT)), 'archive_member': path}
            records.append({'path': path, **expected, **route})
    files.add(str(archive.relative_to(ROOT)))
    save('source-input-bindings.json', records)
    save('origins.json', origins)

    versions = sorted(MEM.glob('evaluation-v*/phase-receipt.json'))
    latest_path = versions[-1]
    evaluation = load(latest_path)
    passed_arithmetic = evaluation['status'] == 'passed_complete_loading_only_six_evaluation_replays'
    # Unknown/failure status cannot become a pass merely because a worker passes.
    if passed_arithmetic:
        assert len(evaluation['observations']) == 6 and not evaluation['failed'] and not evaluation['unexecuted']
    audit_by_id = {x['lifetime']['job']: x for x in evaluation['observations']}
    collector = load(collector_path)
    old_observations = {x['id']: x for phase in collector['phases'] if phase['phase'] == 'evaluation' for x in phase['observations']}
    rows, means = [], {}
    for job in ('base-r1', 'untrained-r1', 'trained-r1', 'trained-r2', 'untrained-r2', 'base-r2'):
        s = load(RUN / 'evaluation' / (job + '-summary.json'))
        assert s['search_status']=='unknown_search_budget' and s['metrics']['attempts']==5000 and s['metrics']['max_satisfied_points']==45
        changed = next((x['receipt'].get('tree',{}).get('executed_changed_first_branches') for x in evaluation['observations'] if x['lifetime']['job'] == job and x.get('receipt')), None)
        if changed is None:
            changed = old_observations[job]['metrics'].get('executed_changed_first_branches')
        if changed is None:
            changed = 0 if job.startswith('base-') else 'unavailable'
        accepted = job in audit_by_id and audit_by_id[job]['lifetime']['status'].startswith('passed')
        status = ('Complete replay passed' if passed_arithmetic else 'Worker replay passed; phase unknown') if accepted else ('Resource UNKNOWN' if job in audit_by_id else 'Unexecuted')
        href = 'arithmetic/' + latest_path.parent.name + '/' + job + '-audit.json'
        rows.append([html.escape(job), 'Unknown; no proof', math(5000), math(45), math(changed), math(round(s['search_seconds'], 3)), '<a href="' + href + '">' + status + '</a>' if job in audit_by_id else status])
        means.setdefault(job.split('-r')[0], []).append(s['search_seconds'])
    arithmetic_table = table(['Lane','Search result','Attempts','Peak obligations','Changed first moves','Search seconds','Current replay'], rows)
    bar_max = max(sum(values)/len(values) for values in means.values())
    bars = ''.join('<div class="barrow"><span>' + name + '</span><div class="track"><div class="bar" style="width:' + str(sum(values)/len(values)/bar_max*100) + '%"></div></div><span>' + math(round(sum(values)/len(values),3)) + ' s</span></div>' for name, values in means.items())
    history = []
    original = RUN / 'evaluation/independent-audit.json'
    history.append(['Original replay','Resource UNKNOWN',math(18.112109042),'First full replay exceeded memory'])
    for p in sorted(MEM.glob('helpers-v*/phase-receipt.json')) + versions:
        v = load(p)
        history.append([str(p.parent.name), html.escape(v['status']),math(round(v['seconds_before_phase_receipt_write'],6)), math(v['conservative_owner_plus_worker_peak_bytes']) + ' bytes'])
    history_table = table(['Phase','Terminal status','Phase seconds','Resource evidence'],history)

    lifetime_path = GEO / 'full-model-lifetime-v1.json'
    lifetime = load(lifetime_path) if lifetime_path.exists() else None
    outcome = load(GEO / 'full-model-outcome-v1.json') if (GEO / 'full-model-outcome-v1.json').exists() else None
    geometric_pass = bool(lifetime and lifetime['status'] == 'passed_authored_full_primitive_graph_full_lifetime')
    independent_full = sorted(REVIEW.glob('geometry-full-independent-lifetime-v*.json'))
    independent = load(independent_full[-1]) if independent_full else None
    geometry_summary = 'Complete-model check remains unknown or unexecuted.'
    geometry_rows, prefix_html = [], ''
    if geometric_pass:
        initial = outcome['complete_comparisons'][0]
        geometry_summary = ('The actual model passes its owned complete-graph check across ' + math(outcome['complete_state_count']) + ' controlled complete-domain states and ' + math(outcome['all_candidate_comparisons']) + ' accepted-placement comparisons. Its initial legal graph has ' + math(initial['candidate_nodes']) + ' candidate nodes and the same number of point/candidate incidence edges. These are measured legal domains, distinct from the earlier raw grammar census. This is not exhaustive enumeration of all reachable states.')
        geometry_rows = [[math(c['label'].split('_')[-1]) if c['label'].startswith('prefix_after_') else html.escape(c['label']),math(c['frontier_points']),math(c['candidate_nodes'])] for c in outcome['complete_comparisons']]
        model = load(ROOT / '.gcts-active/hilbert-aggregate-expansion-20261011/model-v2.json.gz')
        for step in outcome['generic_prefix']:
            recipe_i, row, refs = step['key']
            recipe = model['recipes'][recipe_i]
            output = model['formula_codes'].index(recipe['primitive_witness']['formula'])
            marks = '<span class="mark formula-mark">' + math('m(1,' + str(row) + ')=' + str(output)) + '</span>'
            for port, ref in enumerate(refs):
                marks += '<span class="mark reference-mark">' + math('m(' + str(2+port) + ',' + str(row) + ')=' + str(ref-row)) + '</span>'
            prefix_html += '<article class="proof-row"><div class="tile">' + math('r=' + str(row)) + '<small>' + html.escape(recipe['primitive_witness']['rule']) + '</small></div><div><p>' + math('t(0,' + str(row) + ')=1') + ' · scheduler ' + html.escape(step['decision']['kind']) + ' · complete degree ' + math(step['decision']['count']) + '</p><p class="marks">' + marks + '</p><p class="small">Generic base choice; ordered source rows ' + (', '.join(math(r) for r in refs) if refs else 'none') + '.</p></div></article>'
        prefix_html += '<p>These eight generic choices are repeated guarded incidence axioms, with no source ports. The purple layer appears in the separate distant modus-ponens catalog transaction below; this transaction is not a scheduler branch or discovered proof.</p>'
        recipe_i, row, refs = outcome['catalog_only_probes']['remote_mp_key']
        recipe = model['recipes'][recipe_i]
        marks = {(1,row):model['formula_codes'].index(recipe['primitive_witness']['formula'])}
        for port,(ref,formula) in enumerate(zip(refs,recipe['ordered_premise_formulas'])):
            marks[(1,ref)] = model['formula_codes'].index(formula)
            marks[(2+port,row)] = ref-row
        tags = ''.join('<span class="mark ' + ('formula-mark' if x==1 else 'reference-mark') + '">' + math('m(' + str(x) + ',' + str(y) + ')=' + str(v)) + '</span>' for (x,y),v in sorted(marks.items()))
        prefix_html += '<article class="proof-row"><div class="tile">' + math('r=' + str(row)) + '<small>modus ponens</small></div><div><p><strong>Distant catalog probe.</strong> ' + math('t(0,' + str(row) + ')=1') + '</p><p class="marks">' + tags + '</p><p>Formula requirements reach source rows ' + ', '.join(math(ref) for ref in refs) + '. Ordered offsets retain which row supplies the antecedent and which supplies the implication. The transaction and its exact rollback are checked.</p></div></article>'
    result_summary = {'arithmetic_latest_phase': str(latest_path.relative_to(ROOT)), 'arithmetic_full_phase_pass': passed_arithmetic,
                      'all_six_searches': 'unknown, no proof', 'arithmetic_original_cumulative_audit_seconds': evaluation['cumulative_audit_seconds_before_phase_receipt_write'],
                      'geometry_owned_full_model_pass': geometric_pass, 'geometry_independent_full_lifetime': independent,
                      'geometry_target_searches_this_checkpoint': 0, 'fresh_native_queries': 0,
                      'cluster_lifecycle_conformance':'open; fixed preference control', 'RL_advantage':'not demonstrated',
                      'goal_status':'active'}
    save('result-summary.json', result_summary)
    # Independent acceptance is shown verbatim; producer checks alone are not it.
    independent_text = ('The separately frozen full-model independent gate is <strong>' + ('passed' if independent['status']=='passed_owned_independent_full_model_audit_lifetime' else 'unknown') + '</strong>. <a href="independent/' + independent_full[-1].name + '">Read its lifetime receipt</a>.') if independent else 'A separate full-model independent audit remains pending. The two complete tiny-model checks passed; neither replaces this gate.'
    content = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GCTS parallel execution · checked progress</title><link rel="stylesheet" href="../report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>main{max-width:1200px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:24px 0}.cards>div{background:#edf2e8;padding:20px;border-radius:8px}.cards strong{display:block;font-size:26px;margin-bottom:10px}.barrow{display:grid;grid-template-columns:100px 1fr 110px;gap:15px;align-items:center;margin:14px 0}.track{background:#dde5d7;height:20px;border-radius:3px}.bar{background:#52785d;height:100%;border-radius:3px}.note{padding:18px;border-left:4px solid #a57334;background:#fff4e3}.proof-row{display:grid;grid-template-columns:85px minmax(0,1fr);gap:18px;padding:16px;margin:10px 0;background:#f1f5ef;border-radius:8px}.tile{height:80px;background:white;border:2px solid #637364;display:flex;flex-direction:column;align-items:center;justify-content:center}.tile small{font-size:11px}.marks{display:flex;flex-wrap:wrap;gap:8px}.mark{padding:6px 9px;border-radius:5px;font-size:13px}.formula-mark{background:#d7e9ff;color:#173b78}.reference-mark{background:#e6d9ff;color:#503180}.hide-formulas .formula-mark,.hide-references .reference-mark{display:none}td{font-size:13px}h2{scroll-margin-top:20px}@media(max-width:650px){.cards{grid-template-columns:1fr}.barrow{grid-template-columns:80px 1fr 90px}.proof-row{grid-template-columns:65px minmax(0,1fr);gap:10px}}</style></head><body><header class="masthead"><a href="../#parallel-execution">Research report</a><span>NOTEBOOK 103</span><a href="#assessment">Assessment</a></header><main><section class="intro"><p class="eyebrow">ARITHMETIC · SYMBOLIC GEOMETRY · INDEPENDENT CHECKING</p><h1>Parallel work, checked results.</h1><p class="deck">The agents separate implementation from checking. This checkpoint distinguishes verified search behavior, complete primitive graph tests, and the proofs still to be discovered.</p><p><a href="#arithmetic">Arithmetic</a> · <a href="#geometry">Complete geometry graph</a> · <a href="#markings">Colored placements</a> · <a href="#assessment">Assessment and next goals</a> · <a href="#evidence">Reproducible evidence</a></p></section><section class="panel"><h2>Three agents, with distinct responsibilities.</h2><div class="cards"><div><strong>Arithmetic</strong>Fresh stochastic cluster selection, training, matched controls and memory-preserving replay.</div><div><strong>Geometry</strong>Complete primitive point domains, long-range formula/reference markings, scheduler and exact rollback.</div><div><strong>Independent checking</strong>Separate enumerators and policy replay, corrupted-input controls, resource receipts and limits on conclusions.</div></div><p>The coordinator integrates terminal receipts and publishes the report. Parallel work helps isolate errors and advance independent tasks. It does not make one implementation's self-check an independent proof certificate.</p></section><section class="panel" id="arithmetic"><h2>The arithmetic policy changes moves; a search gain remains unproved.</h2><p>The unchanged target is \(\forall x\,\forall y\,(x+y=y+x)\), with the same \(19848\) base placements and \(52\) point obligations. All six original evaluation searches finished at \(5000\) attempts without a proof, reaching the same peak of \(45\) satisfied obligations. Eight fresh training episodes and the pilot already passed complete independent replay. This checkpoint repairs loading and checks the original evaluation traces; it launches no new searches or training.</p>''' + arithmetic_table + '<div aria-label="Mean search times">' + bars + '</div><p>Mean search times are shown in seconds. Changed-move counts use the current replay where available and earlier producer-collected values otherwise; a disabled baseline proposer has zero changed moves. The last column records validation separately. These are two repetitions of the same theorem, with distinct stochastic evaluation seeds. There is no held-out theorem test or external-prover performance comparison here. The learned policy changes visited moves and costs more search time in these runs; it has not improved proof finding.</p><p><strong>Current complete evaluation gate: ' + ('passed' if passed_arithmetic else 'unknown: resource limit') + '</strong>. <a href="arithmetic/' + latest_path.parent.name + '/phase-receipt.json">Exact phase receipt</a>.</p><p>The loading repairs share repeated four-integer arrays, stream nested JSON, and reuse equal dictionary keys. They have not brought the full evaluation within its memory gate. For each attempted trace, before semantic replay it compares every reconstructed compact-JSON byte against the original compressed trace. Complete point domains, graph checks, RNG draws, policy gradients, rollback and base fallback remain unchanged. Successful loading is verification progress, not a proof-search improvement.</p></section><section class="panel" id="cost"><h2>Keep failed attempts in the cost ledger.</h2>' + history_table + '<p>The original evaluation-audit allowance remains ' + math(780) + ' seconds with ' + math(512) + ' MiB. The retained original failure, all repair helper phases and full replay attempts consume ' + math(round(evaluation['cumulative_audit_seconds_before_phase_receipt_write'],6)) + ' seconds before the last receipt write. No clock or memory gate was reset. Component worker and phase clocks overlap; they are not summed again.</p><p>The original replay failed on memory. The first loading repair reproduced the pilot bytes but timed out in a redundant digest. The second passed all helper fixtures and logically checked the complete first evaluation run, but its combined owner/worker peak exceeded the memory gate. Those failures remain available alongside subsequent results. Source authorship is uninstrumented; source freeze times, test lifetimes, serialization and stated receipt-write exclusions are recorded separately.</p></section><section class="panel" id="geometry"><h2>The primitive geometry model receives an execution check.</h2><p>The symbolic Hilbert inventory has ' + math(229) + ' primitive recipe types, ' + math(217) + ' formula codes and a ' + math(24) + '-row finite boundary. Rotation is forbidden. A placement has ' + math('t(0,r)=1') + ', its formula at ' + math('m(1,r)') + ', and ordered source offsets at ' + math('m(2+j,r)') + '. Points and lines in the mathematical statement are symbols; their proof encoding supplies the spatial coordinates.</p><p>' + geometry_summary + '</p>' + table(['Checked state','Frontier points','Complete legal candidates'],geometry_rows) + '<p>' + independent_text + '</p><p>The complete check streams all raw recipe/offset alignments, then compares every accepted key, exact occupancy, all near and distant markings, degree and stable order against the implicit graph. It tests global dead/forced decisions before earliest-generation branching, rollback, a distant modus-ponens attachment and an assigned formula code of zero. Two independently authored tiny-model suites checked ' + math(1216) + ' states and ' + math(8496) + ' accepted placements apiece.</p><p class="note">The generic prefix has at most ' + math(8) + ' legal base placements and cannot fill the region. It is a conformance probe, not theorem discovery. The previously authored ' + math(24) + '-row proof is read afterward in a separate catalog verification control. Native/compiler correspondence remains open. The current fixed preference set does not retire an invalidated whole pending cluster; full GCTS cluster continuation also remains open.</p><p><a href="geometry/full-model-plan-v1.json">Frozen full-model plan</a> · <a href="geometry/full-model-lifetime-v1.json">Owned full lifetime</a> · <a href="geometry/full-model-outcome-v1.json">Complete graph measurements</a> · <a href="geometry/conformance-scope-v1.json">Explicit cluster lifecycle gap</a></p></section><section class="panel" id="markings"><h2>Actual generic placements, with colored marking layers.</h2><p>Blue encodes formula values; purple encodes ordered reference offsets. The squares show unit occupancy. These are the actual placements in the generic prefix, chosen by the complete base scheduler. They are not a supplied proof word. The detailed theorem reader remains separate.</p><p><label><input id="formula-layer" type="checkbox" checked> Formula markings</label> <label><input id="reference-layer" type="checkbox" checked> Reference markings</label></p>' + prefix_html + '<p><a href="../stochastic-clusters/reader.html#reader">Read the authored incidence proof line by line, with formulas and English</a></p></section><section class="panel" id="assessment"><h2>What the program has established, and what comes next.</h2><p>GCTS bookkeeping and stochastic proposals can drive automatically chosen legal moves, while an independent checker reconstructs the actual arithmetic trajectories. Primitive geometry domains can be represented exactly without materializing every decorated identity. These are concrete implementation results. They do not yet demonstrate improved proof search or a universal proof tile set.</p><p>The next goals are to finish full-model independent acceptance, implement and check whole-cluster invalidation/waiting/rollback, establish primitive-to-logical/native certificate correspondence, then run fresh geometry discovery with a frozen budget. Arithmetic needs broader, harder and held-out tasks with complete replay and matched baseline costs. Learned receptor families must retain their checked primitive expansions and complete fallback.</p><p>The research goal remains active. Finite unknown runs do not establish unprovability. Source-level valid authored proofs do not establish search discovery. Aperiodicity and universal computation do not substitute for an implemented sound proof encoding.</p></section><section class="panel" id="evidence"><h2>Inspect and reproduce the evidence.</h2><p><a href="result-summary.json">Current outcome summary</a> · <a href="source-input-bindings.json">Exact source/input and preservation bindings</a> · <a href="sources-and-inputs.zip">Additional bound sources and inputs</a> · <a href="origins.json">Every new exported origin</a></p><p>The binding manifest resolves each required file to an exact published file or ZIP member. Unchanged large traces keep their existing public routes. Historical guard files are preserved; they are not evidence of new execution. Source-ready and activation notes authorize no broader proof or deployment claims.</p></section></main><script>for(const [id,cls] of [["formula-layer","hide-formulas"],["reference-layer","hide-references"]])document.getElementById(id).addEventListener("change",e=>document.getElementById("markings").classList.toggle(cls,!e.target.checked));</script></body></html>'
    corrections = {
        'The symbolic Hilbert inventory has': 'The guarded symbolic Hilbert incidence fragment has',
        'its formula at ' + math('m(1,r)') + ', and ordered source offsets at ' + math('m(2+j,r)') + '.': 'its conclusion formula at ' + math('m(1,r)') + ', expected source formulas at ' + math('m(1,s_j)') + ', and ordered source offsets ' + math('m(2+j,r)=s_j-r') + '.',
        'It tests global dead/forced decisions before earliest-generation branching, rollback, a distant modus-ponens attachment and an assigned formula code of zero.': 'The actual-model prefix exercises eight branch decisions, exact rollback, a distant modus-ponens attachment and an assigned formula code of zero. Adversarial global dead/forced decisions and generation priority are exercised by the tiny-model suites.',
    }
    for old,new in corrections.items():
        assert content.count(old)==1, old
        content = content.replace(old,new,1)
    math_config = {'tex':{'inlineMath':[[r'\(',r'\)']], 'displayMath':[[r'\[',r'\]']]}, 'options':{'skipHtmlTags':['script','style','pre','code']}}
    content = re.sub(r'window\.MathJax=\{.*?\};', lambda _: 'window.MathJax=' + json.dumps(math_config) + ';', content, count=1)
    if lifetime:
        cost = '<p>The owned full-model verification lifetime is ' + math(round(lifetime['full_supervisor_process_seconds_including_receipt_write'],6)) + ' seconds, with conservative combined peak ' + math(lifetime['conservative_host_peak_bytes']) + ' bytes. The earlier synthetic runtime failure cost ' + math(0.520595542) + ' seconds; its preserved compatibility retry cost ' + math(0.844840583) + ' seconds. These are conformance costs, not proof-search times. The outer receipt write is outside its stated clock.</p>'
        content = content.replace('<p><a href="geometry/full-model-plan-v1.json">',cost + '<p><a href="geometry/full-model-plan-v1.json">',1)
    if independent and independent['status']=='passed_owned_independent_full_model_audit_lifetime':
        old = 'finish full-model independent acceptance, implement and check'
        assert content.count(old)==1
        content = content.replace(old,'implement and check',1)
        cost = '<p>The independent full-model audit lifetime is ' + math(round(independent['full_worker_and_owner_seconds_before_receipt_write'],6)) + ' seconds, with conservative combined peak ' + math(independent['conservative_combined_peak_bytes']) + ' bytes. It independently checks all primitive logical recipes and the authored whole word, including nine explicit corrupted objects. Its own final receipt write is excluded. <a href="independent/geometry-full-independent-result-v1.json">Read the complete independent result</a>.</p>'
        content = content.replace('<p>The complete check streams',cost + '<p>The complete check streams',1)
    reader = DEST / 'reader.html'
    reader.write_text(content)
    files.add(str(reader.relative_to(ROOT)))
    baseline = PUB / 'docs/research/gcts-rl-renewal/index.html'
    assert pin(baseline)['sha256'] == '74492111dc139a10d443dbd0a684ec6abaa7cb8e88d4d39e78277ba47867ce07'
    main_text = baseline.read_text().replace('RESEARCH NOTEBOOK · 102', 'RESEARCH NOTEBOOK · 103', 1)
    panel = '<section class="panel" id="parallel-execution"><p class="eyebrow">NOTEBOOK 103 · PARALLEL IMPLEMENTATION AND INDEPENDENT CHECKING</p><h2>Complete replay and primitive geometry execution.</h2><p>The agents now separate arithmetic experiments, the primitive geometry executor, and independent checking. The new checkpoint preserves every resource failure, reports the current full evaluation gate, and measures actual complete geometry domains. Search improvement and full cluster/native conformance remain separate questions.</p><p><a class="button" href="parallel-execution/reader.html#arithmetic">Read the checked parallel progress</a> <a href="parallel-execution/reader.html#markings">Inspect colored generic placements</a></p></section>\n'
    main_text = main_text.replace('<section class="panel" id="stochastic-clusters">', panel + '<section class="panel" id="stochastic-clusters">', 1)
    (DOC / 'index.html').write_text(main_text)
    files.add(str((DOC / 'index.html').relative_to(ROOT)))
    manifest = [{'path': path, **pin(ROOT / path)} for path in sorted(files)]
    (HERE / 'task-files.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'task_files': len(files), 'bytes':sum(e['bytes'] for e in manifest), 'source_input_bindings':len(records), 'result':result_summary}))


if __name__ == '__main__':
    main()
