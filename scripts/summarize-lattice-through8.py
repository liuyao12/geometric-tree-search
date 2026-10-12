"""Publish measured coverage and costs without dropping unknown cases."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'research/knot-classifier/lattice-through8-benchmark.json'
report = json.loads(path.read_text())
cases = report['cases']
lanes = report['lanes']
assert len(cases) == 105 and len({c['evaluatorKnot'] for c in cases}) == 35
assert all(len(l['runs']) == 105 for l in lanes)


def summarize(runs):
    stats = [r['stats'] for r in runs]
    complete = sum(s['branches'] + s['forced'] + s['deadEnds'] for s in stats)
    return {
        'cases': len(runs), 'success': sum(bool(r['certificate']) for r in runs),
        'unknown': sum(not r['certificate'] for r in runs),
        'unknownReasons': dict(Counter(r.get('reason', r['status']) for r in runs if not r['certificate'])),
        'totalMs': sum(r['totalMs'] for r in runs),
        'nodes': sum(s['nodes'] for s in stats),
        'branches': sum(s['branches'] for s in stats),
        'forced': sum(s['forced'] for s in stats),
        'completeStateDomains': complete,
        'availableCandidates': sum(s['availableCandidates'] for s in stats),
        'meanAvailableCandidates': sum(s['availableCandidates'] for s in stats)/complete if complete else None,
        'extensionEliminations': sum(s['extensionEliminations'] for s in stats),
        'extensionCandidateCount': sum(s['extensionCandidateCount'] for s in stats),
        'newExtensionPrototypes': sum(len((r.get('extensions') or {}).get('eventsThisRun', [])) for r in runs),
        'unresolvedProbeSamples': sum(s['outcome']=='unresolved' for r in runs for e in (r.get('extensions') or {}).get('eventsThisRun', []) for s in e['samples']),
        'cacheHits': sum((r.get('extensions') or {}).get('cacheHitsThisRun', 0) for r in runs),
        'rawCandidates': sum(s['rawCandidates'] for s in stats),
        'generatedStates': sum(s['generatedStates'] for s in stats),
        'verificationMs': sum(r['verificationMs'] for r in runs),
        'probeNodes': sum((r.get('extensions') or {}).get('probeNodesThisRun', 0)+(r.get('learning') or {}).get('probeNodesThisRun', 0) for r in runs),
        'probeMs': sum((r.get('extensions') or {}).get('probeMsThisRun', 0)+(r.get('learning') or {}).get('probeMsThisRun', 0) for r in runs),
        'transferValidationMs': sum((r.get('extensions') or {}).get('transferValidationMsThisRun', 0)+(r.get('learning') or {}).get('transferValidationMsThisRun', 0) for r in runs),
        'maxRSSKiB': max(r['maxRSSKiB'] for r in runs),
        'overruns': sum(r['totalMs'] > report['bounds']['maxMs'] for r in runs),
        'maxOverrunMs': max(max(0, r['totalMs']-report['bounds']['maxMs']) for r in runs),
    }


report['summary'] = [dict(lane=l['lane'], **summarize(l['runs'])) for l in lanes]
report['coverageByCrossings'] = [
    dict(crossings=n, types=len({c['evaluatorKnot'] for c in cases if c['crossings']==n}), lanes=[
        dict(lane=l['lane'], **summarize([r for r in l['runs'] if cases[r['caseIndex']]['crossings']==n])) for l in lanes])
    for n in range(3, 9)
]
report['coverageByType'] = [
    dict(knot=knot, lanes=[dict(lane=l['lane'], outcomes=[
        dict(seedPair=cases[r['caseIndex']]['seedPair'], status=r['knotEquivalence'], reason=r.get('reason'), moves=len(r['certificate']['steps']) if r['certificate'] else None, totalMs=r['totalMs'])
        for r in l['runs'] if cases[r['caseIndex']]['evaluatorKnot']==knot]) for l in lanes])
    for knot in dict.fromkeys(c['evaluatorKnot'] for c in cases)
]
a,b=lanes
common = [i for i in range(len(cases)) if a['runs'][i]['certificate'] and b['runs'][i]['certificate']]
report['equalSuccessComparison'] = dict(cases=common, unmarkedTotalMs=sum(a['runs'][i]['totalMs'] for i in common), markedTotalMs=sum(b['runs'][i]['totalMs'] for i in common))
report['samplingAudit'] = dict(identicalEndpoints=sum(c['source']==c['target'] for c in cases), sameProjectedDiagram=sum(c['sourceDiagram']==c['targetDiagram'] for c in cases), discardedCases=0)
path.write_text(json.dumps(report,separators=(',', ':'))+'\n')
u,m=report['summary']
rows=[]
for entry in report['coverageByCrossings']:
    x,y=entry['lanes']
    rows.append(f"<tr><td>\\({entry['crossings']}\\)</td><td>{entry['types']}</td><td>{x['cases']}</td><td>{x['success']} / {x['unknown']}</td><td>{y['success']} / {y['unknown']}</td><td>{x['totalMs']/1000:.2f} / {y['totalMs']/1000:.2f}</td></tr>")
type_rows=[]
for entry in report['coverageByType']:
    n,j=entry['knot'].split('_')
    outcomes=['; '.join(f"seed {r['seedPair']}: "+(f"identified ({r['moves']} moves)" if r['status']=='equivalent' else f"unknown ({r['reason']})") for r in l['outcomes']) for l in entry['lanes']]
    type_rows.append(f"<tr><td>\\({n}_{{{j}}}\\)</td><td>{outcomes[0]}</td><td>{outcomes[1]}</td></tr>")
check=report['independentVerification']
timing_claim=(f"Both lanes identify {len(common)} of the same cases; their summed times on that subset are {report['equalSuccessComparison']['unmarkedTotalMs']/1000:.2f} and {report['equalSuccessComparison']['markedTotalMs']/1000:.2f} seconds." if common else "No case produces a certificate in both lanes, so this experiment establishes no equal-success timing speedup.")
section=f'''<section id="through8-results">
<h2>Prime knots through eight crossings: deeper independent scrambles</h2>
<p>All 35 corpus prime types through eight crossings were tested with three predetermined seed pairs per type: 105 queries, five independent lattice moves per endpoint, and no discarded cases. Walk length is not minimum move distance. Every incident lattice face remains available throughout both knots; no move-support patch is imposed. The search receives only endpoint vertices. Labels, common ancestors and scramble histories stay in the evaluator.</p>
<table><thead><tr><th>Minimal crossings</th><th>Prime types</th><th>Queries</th><th>Brute force: success / unknown</th><th>Reused markings: success / unknown</th><th>Total seconds: brute / marked</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p><strong>Measured result:</strong> brute force identifies {u['success']} queries and leaves {u['unknown']} unknown; the marking lane identifies {m['success']} and leaves {m['unknown']} unknown. {timing_claim} Each query has the same bounds: ten moves, 240 unit edges, 200 expanded nodes, 30,000 stored states and six seconds including learning and transfer replay. Local probes have a 512-node limit; unfinished probes remain unresolved. Atomic operations may overrun the deadline; the maximum measured overrun is {max(u['maxOverrunMs'],m['maxOverrunMs']):.2f} milliseconds.</p>
<p>The marked lane starts with an empty model, then retains its in-memory local proof catalog across all seeds and knot types. Full incident-face alphabets, every resolved proof label and assigned stencil values are checked before transfer. No archived assignments are loaded. Time-interrupted samples remain unconstrained; interrupted transfer validation leaves the whole query unknown.</p>
<p>Actual marked candidate graphs remove {m['extensionEliminations']:,} of {m['extensionCandidateCount']:,} legal candidates ({100*m['extensionEliminations']/m['extensionCandidateCount']:.2f}%). Across completed state domains, mean available choices are {u['meanAvailableCandidates']:.2f} for brute force and {m['meanAvailableCandidates']:.2f} with markings. These averages cover different visited states. Expanded nodes are {u['nodes']:,} / {m['nodes']:,}; branching states are {u['branches']:,} / {m['branches']:,}. At a fixed time limit, fewer processed branches can also reflect learning overhead; candidate elimination is evidence of pruning, not by itself a speedup.</p>
<p>Total query cost is {u['totalMs']/1000:.2f} seconds unmarked and {m['totalMs']/1000:.2f} seconds marked. The latter includes {m['probeMs']/1000:.3f} seconds of local proof searches and {m['transferValidationMs']/1000:.3f} seconds of transfer replay. Peak resident memory is {u['maxRSSKiB']/1024:.1f} / {m['maxRSSKiB']/1024:.1f} MiB. Common input generation took {report['preparationMs']/1000:.2f} seconds; independent archive verification took {check['wallMs']/1000:.2f} seconds and replayed {check['movies']} spatial movies plus {check['resolvedLabels']:,} resolved proof labels. Both extra costs are reported separately from query times.</p>
<p><strong>Classification scope:</strong> this tests positive equivalence of supplied endpoint pairs across every prime reference type through eight crossings. It does not test blind reference-bank selection or negative pairs. Composite knots, separate mirror cases, the unknot, RL and a complete decision procedure remain open. The fixed regular projection and single-Reidemeister endpoint grammar remain declared restrictions; only move locations are unrestricted. An unknown query is never reported as inequivalent. All 105 construction witnesses are independently checked, even when the search cannot recover a movie.</p>
<details><summary>Every knot type and seed result</summary><table><thead><tr><th>Knot</th><th>Brute force</th><th>Reused markings</th></tr></thead><tbody>{''.join(type_rows)}</tbody></table></details>
<p><a href="lattice-through8-benchmark.json">Every input, seed, outcome, cost, new proof and certificate</a> · <a href="lattice-through8-contract.json">Benchmark bounds and conformance scope</a> · <a href="../../scripts/benchmark-lattice-through8.mjs">Reproduction harness</a> · <a href="../../scripts/verify-lattice-through8.py">Independent verifier</a>.</p>
<pre>node scripts/benchmark-lattice-through8.mjs
node tests/test_knot_lattice_budgets.mjs
python3 scripts/verify-lattice-through8.py research/knot-classifier/lattice-through8-benchmark.json</pre>
</section>
'''
html=root/'research/knot-classifier/lattice-classifier.html'
text=html.read_text()
if '<section id="through8-results">' in text:
    start=text.index('<section id="through8-results">');end=text.index('</section>',start)+len('</section>');text=text[:start]+text[end:].lstrip('\n')
old_heading='<h2>New: learned local extension failures reduce branching</h2>'
if old_heading not in text: old_heading='<h2>Earlier comparison: learned local extension failures reduce branching</h2>'
text=text.replace(old_heading,section+'<h2>Earlier comparison: learned local extension failures reduce branching</h2>',1)
text=text.replace('Independent three- and four-move scrambles of three reference types identified with spatial replay. Broad coverage, mirror/composite scoring and 12-crossing scaling remain pending.', 'All 35 prime types through eight crossings tested on three five-move independent seed pairs each, with success/unknown outcomes and full costs published above. Complete recognition, reference-bank selection, mirror/composite scoring and twelve-crossing scaling remain pending.')
html.write_text(text)
readme=root/'research/knot-classifier/README.md'
notice=f"> **Through-eight benchmark:** All 35 prime types through eight crossings, three independent seed pairs each, five scramble moves per endpoint. Brute force: {u['success']} identified / {u['unknown']} unknown; reused local markings: {m['success']} identified / {m['unknown']} unknown, under identical six-second and node/state/edge/depth bounds. Marked proofs start empty and transfer across types. Complete outcomes, total costs and limits appear in the [live research report](lattice-classifier.html#through8-results) and [raw evidence](lattice-through8-benchmark.json). Reproduce with `node scripts/benchmark-lattice-through8.mjs`; verify with `python3 scripts/verify-lattice-through8.py research/knot-classifier/lattice-through8-benchmark.json`. This is positive pair identification, not a complete through-eight decision procedure.\n\n"
old=readme.read_text()
if old.startswith('> **Through-eight benchmark:**'): old=old.split('\n\n',1)[1]
readme.write_text(notice+old)
print(json.dumps(dict(summary=report['summary'],verification=check)))
