"""Scoped reader/export for the completed bounded cluster-search control."""
import copy
import gzip
import hashlib
import json
import resource
import shutil
import time
import zipfile
from pathlib import Path
from induction_receptors_export import math, esc, explanation
from catalog_receptor_points import Catalog
from certificate_boundary_search import canonical
from semantic_receptor_points import center, mode_point, input_point

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DOC = ROOT / 'docs/research/gcts-rl-renewal'
OUT = ROOT / '.gcts-active/commutativity-cluster-search-20261011'
PARENT = ROOT / '.gcts-active/commutativity-receptors-20261011'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def need(value, message):
    if not value:
        raise ValueError(message)


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def sec(value):
    return f'{value:,.3f}'


def words(command, inference):
    desc = inference['description']
    op = desc['operation']
    refs = command.get('inputs', [command['source']] if 'source' in command else [])
    source = ' Sources: ' + ', '.join('line ' + str(i + 1) for i in refs) + '.' if refs else ''
    if op == 'transferred-searched-theorem':
        return 'Reuse the complete earlier automatically discovered theorem certificate. It remains a derived result, with its original proof included in the expansion.'
    if op == 'reflexivity':
        return 'Start an equality path: an expression equals itself.'
    if op == 'conditional-reflexivity':
        return 'An expression equals itself under the explicit induction hypothesis. The hypothesis is inside the implication, rather than added to the theory.'
    if op == 'generalize':
        return 'The result holds for an arbitrary variable; universally quantify that variable after checking the eigenvariable condition.' + source
    if op == 'induction':
        return 'Apply natural-number induction to the checked base case and universally quantified implication step, then close the parameters.' + source
    if op in ('rewrite', 'conditional-rewrite'):
        move = desc['move']
        origin = move['rule']['origin']
        rule = 'the explicitly assumed induction equality' if origin == 'assumption' else 'the earlier discovered lemma' if origin == 'discovered-lemma' else 'recursive addition axiom ' + move['rule']['name']
        direction = 'forward' if move['direction'] == 1 else 'backward'
        conditional = ' Keep the induction hypothesis explicit in the implication.' if op == 'conditional-rewrite' else ''
        return 'Replace one expression occurrence using ' + rule + ' in the ' + direction + ' direction.' + conditional + source
    return op + source


def point_rows(catalog, forward):
    """Render only this automatic word, with the unchanged point encoding.

    This does not enumerate/search an enlarged region. Its selected point values
    are checked in full, and the 13-row display is explicitly outside the frozen
    12-row comparison. Command IDs come from the complete original dictionary.
    """
    ids = Catalog(catalog['basis'], [r['command'] for r in catalog['rules']])
    rows, marks, roots = [], {}, set()
    initial = ids.assignment(len(forward['proof']) - 1, 'formula', forward['original_request']['target'])
    for point, value in initial:
        marks[point] = value
    for index, (command, witness) in enumerate(zip(forward['proof'], forward['selected_witnesses'])):
        inference = catalog['rules'][witness['rule']]
        sources = witness['sources']
        need(command['formula'] == inference['conclusion'] and len(sources) == len(inference['premises']), 'complete selected word interface')
        mode = witness['rule'] + 1 if inference['premises'] else 0
        shared = ids.assignment(index, 'command', inference['command']) + ids.assignment(index, 'formula', inference['conclusion']) + [(mode_point(index), mode)]
        tiles = []
        for role in range(4):
            if role < 2:
                entries, source = shared, None
            else:
                field = role - 2
                source = sources[field] if field < len(sources) else None
                entries = [(mode_point(index), mode), (input_point(index, field), -1 if source is None else source)]
                if source is not None:
                    need(0 <= source < index and forward['proof'][source]['formula'] == inference['premises'][field], 'strict prior exact source receptor')
                    entries += ids.assignment(source, 'formula', inference['premises'][field])
            point = center(index, role)
            need(point not in roots, 'unique whole point occupancy')
            roots.add(point)
            for p, value in entries:
                need(p not in marks or marks[p] == value, 'all extended colored marking values agree')
                marks[p] = value
            tiles.append(dict(role=('C', 'G', 'I1', 'I2')[role], point=point, occupancy_units=12, capacity_units=12,
                              mode=mode, source=source, marks=entries))
        rows.append(dict(line=index + 1, command=command, witness=witness, inference=inference, tiles=tiles,
                         formula_id=ids.ids['formula'][canonical(command['formula'])],
                         command_id=ids.ids['command'][canonical(inference['command'])]))
    return rows, dict(status='passed_complete_selected_13row_point_display', occupied_roots=len(roots), assigned_mark_points=len(marks),
                      all_extended_values_agree=True, all_strict_prior_sources_checked=True,
                      scope='Selected ordinary word only, mechanically displayed under the same injective point encoding. This is not a 13-row GCTS search or a 12-row result, and not a primitive Wang-square occupancy embedding.')


def main():
    began = time.perf_counter()
    full = json.loads((OUT / 'search-audit-v5.json').read_text())
    need(full['status'] == 'passed_complete_four_search_graph_and_proposal_traces', 'whole four-tree audit')
    ordinary = json.loads((OUT / 'forward-audit.json').read_text())
    need(ordinary['status'] == 'passed_full_ordinary_closure_and_word_reconstruction', 'full ordinary audit')
    compact = json.loads((OUT / 'certificate-audit-v2.json').read_text())
    need(compact['status'] == 'passed_independent_automatic_candidate_selection_and_generic_whole_compaction', 'full compaction audit with actual resource receipt')
    capacity = json.loads((OUT / 'capacity-audit.json').read_text())
    need(capacity['status'] == 'passed_complete_whole_capacity_replay_with_native_unknowns' and not any(q['native_eligible'] for q in capacity['observations']), 'exact unresolved native boundary gate')
    catalog = load(PARENT / 'attempt-02/two-lemmas-retained-core.json.gz')
    forward = load(OUT / 'forward.json.gz')
    certificates = load(OUT / 'certificates.json.gz')
    candidate = certificates['candidates'][0]
    need(len(certificates['candidates']) == 1 and candidate['lane'] == 'ordinary-forward' and len(forward['proof']) == 13, 'exact sole automatic candidate')
    rows, display = point_rows(catalog, forward)
    data = dict(status='completed_bounded_controls_whole_native_unknown', rows=rows, selected_point_display=display,
                ordinary_closure=forward['closure'], original_request=candidate['original_request'],
                expanded_proof=candidate['expanded_proof'], compact_request=candidate['compact_request'],
                original_request_sha256=candidate['original_request_sha256'], compact_request_sha256=candidate['compact_request_sha256'],
                gcts_status='all_four_unknown_search_budget', whole_native_status='unknown_whole_native_heap_boundary', native_target_queries=0)
    (OUT / 'report-data.json.gz').write_bytes(gzip.compress(json.dumps(data, separators=(',', ':')).encode(), mtime=0))
    (OUT / 'report-display-audit.json').write_text(json.dumps(display, indent=2) + '\n')
    observations = [json.loads((OUT / (name + '-summary.json')).read_text()) for name in ('base-r1', 'fixed-r1', 'fixed-r2', 'base-r2')]
    doc = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Commutativity: bounded cluster search and an ordinary candidate</title><link rel="stylesheet" href="report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>main{max-width:1120px;margin:auto;padding:24px}nav{display:flex;gap:16px;flex-wrap:wrap}section{margin:38px 0}.status,.unknown{padding:18px;border-left:4px solid #348665;background:#ebf5ef}.unknown{border-color:#bc8421;background:#fff3dc}.scroll,.formula{overflow-x:auto}table{border-collapse:collapse}td,th{padding:9px;border:1px solid #ccd;vertical-align:top}details{margin:12px 0}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}ol.proof>li{padding:18px 8px;border-bottom:1px solid #ccd}.pointrow{display:flex;gap:8px;margin:12px 0;flex-wrap:wrap}.tile{width:120px;min-height:72px;border:2px solid #425163;border-radius:6px;padding:8px;color:white;background:#7454aa}.tile.g{background:#9e7520}.tile.i1{background:#287c66}.tile.i2{background:#b45733}.tile.unused{background:#f4f4f4;color:#344; border-style:dashed}.tile strong,.tile small{display:block}.pin{overflow-wrap:anywhere}.legend{display:flex;gap:18px;flex-wrap:wrap}.dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:5px}.comparison{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.comparison article{padding:18px;background:#f3f5f7;border:1px solid #ccd}</style></head><body><main><p><a href="index.html#goals">Research program</a> · <a href="commutativity_admissions.html#result">Complete admitted inventory</a> · <a href="commutativity_search_plan.html#status">Frozen experiment specification</a></p><h1>Bounded cluster search for addition commutativity</h1><nav><a href="#result">Outcome</a><a href="#searches">Four GCTS searches</a><a href="#reader">13-line ordinary candidate</a><a href="#primitive">152 primitive commands</a><a href="#costs">Complete costs</a><a href="#evidence">Exact evidence</a></nav>'''
    doc += '<section id="result"><p class="unknown">All four bounded GCTS searches remain unknown. Their complete independently reconstructed traces now pass. A separate ordinary forward-chaining control automatically produced a 13-line candidate, but this exceeds the frozen 12-row comparison. Its complete whole-native workspace estimate exceeds the fixed boundary, so no whole native target query was executed and commutativity remains native-unknown.</p><p>The exact target is ' + math(candidate['original_request']['target']) + '. The original theory contains ' + math(candidate['original_request']['theory']['axioms']['AZ']) + ' and ' + math(candidate['original_request']['theory']['axioms']['AS']) + ', with the same enabled natural-number induction scheme.</p><div class="comparison"><article><h2>GCTS result</h2><p>Two base runs reached 5,000 attempts; two fixed cluster runs reached the 60-second cap. No proof was found. All 15,679 nodes and 589 policy events/hints were independently replayed.</p></article><article><h2>Ordinary result</h2><p>The full 153-hyperedge closure produced 13 lines in 0.099 seconds internally measured before final artifact serialization. This is an ordinary discovery, with whole host/tree cross-checks, and a native workspace unknown. It is not a GCTS or RL discovery.</p></article></div><p>This is useful negative evidence about the present ordering and proposal cost. The 13-line ordinary upper bound does not establish that a 12-line proof is impossible. No speed advantage, full Peano arithmetic completeness or RL training claim follows.</p></section>'
    searchrows = []
    for row in observations:
        metric = row['metrics']
        searchrows.append((row['id'], row['status'], metric['attempts'], metric['forced'], metric['dead'], metric['backtracks'], sec(row['search_seconds']), sec(metric.get('proposal_seconds', 0)), sec(row['search_checkpoint_seconds']), f"{row['peak_rss_bytes']:,}"))
    doc += '<section id="searches"><h2>Same language and complete base fallback</h2><p>All four fresh models retain 17,158 placements, 48 initially active required points and 12 proof rows. The same complete five-node contextual grammar exposes both induction variables, all declared quantifier closures, every expression occurrence/direction/substitution and every strict-prior source binding. The preserved formula-ID dictionary has 2,069 entries; 96 formulas are active outputs or premises.</p>' + table(['Run', 'Outcome', 'Attempts', 'Forced', 'Dead', 'Backtracks', 'Search s', 'Proposal s', 'Trace serialization s', 'Peak RSS bytes'], searchrows)
    doc += '<p>The predeclared balanced order was base-r1, fixed-r1, fixed-r2, base-r2. Base runs reached the attempt ceiling in about 28 seconds. Fixed runs reached the wall ceiling after 2,832 and 2,843 attempts; the final sampler overshoots of 0.030549 and 0.154488 seconds are preserved as search-budget unknowns. These mixed caps do not establish equal work. The fixed policy spent about 44 seconds per run on proposals; complete serialization cost another 85–148 seconds per observation.</p><p>The fixed proposer uses authored weights over a bounded pool of validated continuation clusters, including open arbitrary shapes. Forty-two parameterized families backed by the two actual discovered lemmas expose 13,860 internally compatible bindings. Proposal membership only reorders original incident candidates; global dead checks, forced propagation, earliest-generation branching, every remaining base fallback and exact failed-child rollback are preserved. The 94 generic local interfaces are authored infrastructure, not learned lemmas. No compatible policy was trained and these fixed scores are not RL.</p><p>The full independent auditor reconstructed all candidate point data and every recorded graph census, decision, proposal pool, work count, feature, fixed score, continuation, fallback and rollback. The small preflight fixtures alone did not exercise failed-child backtracking; the actual target traces supply that evidence.</p></section>'
    doc += '<section id="reader"><h2>Automatically selected ordinary candidate, line by line</h2><p class="unknown">This 13-row word is the ordinary control output. The colored glyphs below mechanically translate its exact formulas and source receptors into the same fixed-orientation point encoding. This display is outside the 12-row search boundary; no larger GCTS search or primitive Wang-square embedding is claimed. The whole target has no accepted native certificate at the declared resources.</p><p>The ordinary algorithm first scans every admitted retained hyperedge synchronously to its complete fixed point: 96 reachable formulas, seven rounds, 1,224 edge scans. It chooses the first ready witness in the unchanged canonical catalog order. Only after that closure does a generic routine recursively extract the query DAG. Neither a target-proof sequence nor an induction variable was supplied.</p><div class="legend"><span><i class="dot" style="background:#7454aa"></i><code>C</code>: command/output</span><span><i class="dot" style="background:#9e7520"></i><code>G</code>: exact admitted interface</span><span><i class="dot" style="background:#287c66"></i><code>I1</code>: first source</span><span><i class="dot" style="background:#b45733"></i><code>I2</code>: second source</span></div><p>Each role fills one required point, with ' + r'\(t=1\)' + ' represented by 12 integer units. Its colored marking stores exact command/formula/mode values. Source markings reach to the named earlier formula; all overlaps agree. A dashed unused role assigns the explicit value ' + r'\(-1\)' + ', which differs from an absent marking. Translation is permitted; rotation and reflection are absent.</p><ol class="proof">'
    definitions = {d['name']: d for d in catalog['definitions']}
    for row in rows:
        command = row['command']
        doc += '<li id="line-' + str(row['line']) + '"><div class="formula">' + math(command['formula']) + '</div><p>' + esc(words(command, row['inference'])) + '</p><div class="pointrow">'
        for role, tile in enumerate(row['tiles']):
            cls = ('c', 'g', 'i1', 'i2')[role] + (' unused' if role > 1 and tile['source'] is None else '')
            label = 'formula ID ' + str(row['formula_id']) if role == 0 else 'interface ' + str(row['witness']['rule']) + ', mode ' + str(tile['mode']) if role == 1 else 'unused value −1' if tile['source'] is None else 'line ' + str(tile['source'] + 1)
            # IDs and API values are literal encodings, rather than math notation.
            label = label.replace('−1', '-1')
            doc += '<div class="tile ' + cls + '"><strong><code>' + tile['role'] + '</code></strong><small><code>' + esc(label) + '</code></small></div>'
        doc += '</div><details><summary>Exact command and extended point markings</summary><pre>' + esc(json.dumps(dict(command=command, tiles=row['tiles']), indent=2)) + '</pre></details>'
        if command['rule'] == 'block':
            definition = definitions[command['name']]
            doc += '<details><summary>Expand this independently admitted local derivation (' + str(len(definition['proof'])) + ' commands)</summary><ol>'
            for local in definition['proof']:
                doc += '<li><div class="formula">' + math(local['formula']) + '</div><p>' + esc(explanation(local, catalog['rules'])) + '</p></li>'
            doc += '</ol></details>'
        doc += '</li>'
    doc += '</ol><p>The full selected 52-point display was checked for exact occupancy, every strict-prior source and every extended marking overlap. This display check is separate from the complete original 12-row search graph audit.</p></section>'
    doc += '<section id="primitive"><h2>Generic expansion and whole-check boundary</h2><p>The exact original high-level request includes every used definition and its transitive proof-call dependencies in their original order. Generic inlining yields 169 primitive commands; context-safe formula-DAG sharing gives 152. Independent reconstruction verifies every command, original theory/target and the original and compact host proofs. The original request hash is <code class="pin">' + candidate['original_request_sha256'] + '</code>; the compact request hash is <code class="pin">' + candidate['compact_request_sha256'] + '</code>.</p><p class="unknown">Both the producer and separate stack interpreter accept the compact fixed tree-program cross-check after 7,509,732 instructions, with the complete final heap and event/profile digest matched. Its canonical native heap requires 596,873 cells, above the declared 262,144. No native input stream was constructed or byte-replayed in this over-capacity branch; the generic audit scope mentions encoding, but its exact encoding flag is false. The capacity gate therefore stops before native encoding or execution. This is a resource unknown, with zero whole native target queries; it is not a native rejection or theorem-nonprovability result.</p><details><summary>Read all 152 automatically generated compact primitive commands</summary><ol class="proof">'
    for local in candidate['compact_request']['proof']:
        doc += '<li><div class="formula">' + math(local['formula']) + '</div><p>' + esc(explanation(local, catalog['rules'])) + '</p><details><summary>Exact primitive command</summary><pre>' + esc(json.dumps(local, indent=2)) + '</pre></details></li>'
    doc += '</ol></details><details><summary>Read the full original 13-command request and used definitions</summary><pre>' + esc(json.dumps(candidate['original_request'], indent=2)) + '</pre></details></section>'
    setup = json.loads((OUT / 'preflight-summary.json').read_text())
    fixture = json.loads((OUT / 'preflight-audit.json').read_text())
    failed = json.loads((OUT / 'search-audit.json').read_text())
    decoder = json.loads((OUT / 'decoder-receipt.json').read_text())
    history = json.loads((OUT / 'decoder-receipt-v3.json').read_text())
    reconcile = json.loads((OUT / 'decoder-reconciliation.json').read_text())
    search = json.loads((OUT / 'search-summary.json').read_text())
    costs = [
        ('Complete graph/family preflight', sec(setup['seconds']), f"{setup['peak_rss_bytes']:,}", '17158 placements /13860 compatible families'),
        ('Independent full preflight', sec(fixture['seconds']), f"{fixture['peak_rss_bytes']:,}", 'Passed, limited fixture backtracking scope'),
        ('Four-search dispatcher incl. all setup/serialization', sec(search['seconds']), 'Per observation above', 'All four unknown'),
        ('Initial read-only interning pilot', sec(decoder['seconds']), f"{decoder['peak_rss_bytes']:,}", 'Full first trace resource/fixture pilot'),
        ('First full graph audit', sec(failed['seconds']), f"{failed['peak_rss_bytes']:,}", 'Unknown:35,454,976-byte memory overshoot'),
        ('Two whole-value decoder comparisons', sec(history['seconds']), '444530688 /328712192', 'Combined unknown:4.188783-second overshoot'),
        ('Fresh historical-component reconciliation', sec(reconcile['seconds']), f"{reconcile['peak_rss_bytes']:,}", 'Passed explicit reuse; earlier costs unchanged'),
        ('Complete four-tree v5 audit', sec(full['seconds']), f"{full['peak_rss_bytes']:,}", 'All15679nodes /589policy events passed'),
        ('Ordinary full closure/DAG construction', sec(forward['seconds']), f"{forward['peak_rss_bytes']:,}", '13 rows, exceeds12rowcomparison'),
        ('Independent full ordinary audit', sec(ordinary['seconds']), f"{ordinary['peak_rss_bytes']:,}", 'All edges/layers/witnesses/word passed'),
        ('Generic whole compaction', sec(certificates['seconds']), f"{certificates['peak_rss_bytes']:,}", '169 expanded /152 shared commands'),
        ('First complete compaction logical audit', '0.136 (+0.18 end-to-end sampler)', 'Unavailable', 'External time-l sampler denied sysctl; preserved'),
        ('Separately frozen compaction v2 audit', sec(compact['seconds']), f"{compact['peak_rss_bytes']:,}", 'Same reconstruction +actual internal RSS passed'),
        ('Exact whole capacity producer', sec(json.loads((OUT / 'capacity-summary.json').read_text())['seconds']), '194297856', 'Nativeheapboundaryunknown'),
        ('Complete independent whole capacity replay', sec(capacity['seconds']), f"{capacity['peak_rss_bytes']:,}", '596873requiredcells confirmed; no native query')]
    doc += '<section id="costs"><h2>All preparation, verification and failed-resource costs remain charged</h2>' + table(['Component', 'Seconds', 'Peak RSS bytes', 'Outcome/scope'], costs) + '<p>The original decoder batch remained unknown after 304.188783 seconds. Both individually complete comparisons stayed below their separate 180-second/512 MiB limits and produced the same complete 115,950,444-byte canonical JSON digest. A separately frozen fresh hash reconciliation explicitly reuses those historical components, charging the entire original run, before the unchanged 300-second/512 MiB v5 audit. No search, source model, original trace or budget was changed.</p><p>Forward extraction and generic compaction internal timings end before final artifact serialization; those final serialization costs are unmeasured separately. They are not complete process totals and do not imply an end-to-end proof-search speed claim.</p><p>Source-only decoder v1 and whole-auditor v2/v3 variants were not executed; their frozen bytes and plans are preserved. The first failed full audit and failed external RSS sampler remain separate from the passing later audits. Peak resource sampling occurs at declared checkpoints; any measured overshoot is retained as unknown.</p><p>All complete grammar/pruning, historical memory unknowns, all-94 capacity/encoding repairs, 93 fresh native admissions plus independent replay, one exact historical reuse and the two promoted theorem-discovery costs remain in the <a href="commutativity_admissions.html#costs">previous immutable ledgers</a>. They are not free inventory. Manual infrastructure development is unmeasured.</p></section>'
    exported = []
    links = []
    for name in ['report-data.json.gz', 'report-display-audit.json', 'search-summary.json', 'search-audit-plan-v5.json', 'search-audit-v5.json', 'forward-plan.json', 'forward.json.gz', 'forward-audit.json', 'certificates.json.gz', 'certificate-audit.json', 'certificate-audit-v2.json', 'capacity-plan.json', 'capacity-summary.json', 'capacity-audit.json', 'whole-capacity-000.json.gz', 'decoder-receipt-v3.json', 'decoder-reconciliation.json']:
        dest = DOC / ('commutativity_cluster_' + name.replace('-', '_'))
        need(not dest.exists(), 'fresh export path ' + dest.name)
        shutil.copyfile(OUT / name, dest)
        exported.append(dest)
        links.append('<a href="' + dest.name + '">' + esc(name) + '</a>')
    archive = DOC / 'commutativity_cluster_complete_evidence.zip'
    need(not archive.exists(), 'fresh evidence archive')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipfile_out:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.name not in ('integration.json', 'integration-receipt.json'):
                zipfile_out.write(path, path.name)
    exported.append(archive)
    links.append('<a href="' + archive.name + '">Complete original models/traces, every source/input freeze, failed and passing audits, automatic word and full final heap</a>')
    doc += '<section id="evidence"><h2>Complete reproducible evidence</h2><p>' + ' · '.join(links) + '</p><p>The complete archive preserves the exact original four producer models/traces/summaries, balanced activation and executor snapshot, all preflight and decoder versions, the earlier audit/resource failures, fresh component-reuse gate, complete four-tree replay, full ordinary closure/ranks/edges, both compaction audit attempts and the whole capacity producer/replay. Each experiment has its separately frozen exact source/input hashes. The 94-interface registry and earlier exported evidence remain byte-identical at their established links.</p><p>No target search or native batch followed the final capacity unknown. The report makes no full arithmetic completeness, trained-policy or GCTS proof-discovery claim. Parent-owned publication/live visual verification remain separate.</p></section></main></body></html>'
    page = DOC / 'commutativity_cluster_results.html'
    need(not page.exists(), 'fresh reader path')
    page.write_text(doc)
    exported.insert(0, page)
    exported.append(Path(__file__))
    manifest = dict(status='prepared-for-parent-integration', published=False, reader='commutativity_cluster_results.html?v=20261011-ccr1#reader',
                    gcts_observations=4, gcts_outcomes=['unknown_search_budget'] * 4, complete_tree_audit='passed', ordinary_rows=13,
                    same_12row_boundary_fits=False, primitive_compact_commands=152, required_heap_cells=596873, fixed_heap_cells=262144,
                    whole_native_status='unknown_whole_native_heap_boundary', native_target_queries=0, no_RL_training=True,
                    report_generation_seconds=time.perf_counter() - began, report_generation_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    files=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in exported])
    (OUT / 'integration.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(files=len(exported), html_bytes=page.stat().st_size, reader=manifest['reader'], manifest_sha256=hashlib.sha256((OUT / 'integration.json').read_bytes()).hexdigest(), report_seconds=manifest['report_generation_seconds'])), flush=True)


if __name__ == '__main__':
    main()
