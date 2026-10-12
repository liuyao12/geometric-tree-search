"""Keep all failed-stage costs when reporting larger-budget identifications."""
import json
import sys
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'research/knot-classifier/lattice-escalation-benchmark.json'
report=json.loads(path.read_text())
if len(sys.argv)>1:report['additionalStages']=[json.loads(Path(p).read_text()) for p in sys.argv[1:]]
stages=[report]+report.get('additionalStages',[])


def key(c):return c['evaluatorKnot'],c['seedPair']


def summary(runs):
    return dict(attemptedQueries=len(runs),successfulQueries=sum(bool(r['certificate']) for r in runs),unknownQueries=sum(not r['certificate'] for r in runs),totalMs=sum(r['totalMs'] for r in runs),nodes=sum(r['stats'].get('nodes',0) for r in runs),branches=sum(r['stats'].get('branches',0) for r in runs),candidateEliminations=sum(r['stats'].get('extensionEliminations',0) for r in runs),candidateCount=sum(r['stats'].get('extensionCandidateCount',0) for r in runs),probeMs=sum((r.get('extensions') or {}).get('probeMsThisRun',0) for r in runs)+sum(e['probeMs'] for r in runs for e in (r.get('learning') or {}).get('eventsThisRun',[])),activationValidationMs=sum((r.get('extensions') or {}).get('activationValidationMsThisRun',0) for r in runs),transferMs=sum((r.get('extensions') or {}).get('transferValidationMsThisRun',sum(a['transferValidationMs'] for a in r['attempts'])) for r in runs),certificateVerificationMs=sum(r['verificationMs'] for r in runs),maxRSSKiB=max(r['maxRSSKiB'] for r in runs),unknownReasons=dict(Counter(r.get('reason','finite-horizon') for r in runs if not r['certificate'])))


all_runs={name:[] for name in ['unmarked','extension-transfer']};latest={name:{} for name in all_runs}
for stage in stages:
    for lane in stage['lanes']:
        for r in lane['runs']:
            # Correct aggregate version accounting using retained per-attempt snapshots.
            for field in ['markingVersions','extensionVersions']:r['stats'][field]=max((a['stats'].get(field,0) for a in r['attempts']),default=0)
            if r.get('extensions'):
                r['extensions']['initialVersion']=r['initialVersion']
                r['extensions']['probeNodesThisRun']=sum(s['nodes'] for e in r['extensions']['eventsThisRun'] for s in e['samples'])
            all_runs[lane['lane']].append(r);latest[lane['lane']][key(stage['cases'][r['caseIndex']])]=r
report['cumulativeSummary']=[]
for name,runs in all_runs.items():
    final=list(latest[name].values());report['cumulativeSummary'].append(dict(lane=name,uniqueCases=len(final),identified=sum(bool(r['certificate']) for r in final),unknown=sum(not r['certificate'] for r in final),**summary(runs)))
report['outcomesByCase']=[]
for c in report['cases']:
    report['outcomesByCase'].append(dict(knot=c['evaluatorKnot'],seedPair=c['seedPair'],crossings=c['crossings'],lanes=[dict(lane=name,status=latest[name][key(c)]['knotEquivalence'],moves=len(latest[name][key(c)]['certificate']['steps']) if latest[name][key(c)]['certificate'] else None,cumulativeMs=sum(r['totalMs'] for stage in stages for lane in stage['lanes'] if lane['lane']==name for r in lane['runs'] if key(stage['cases'][r['caseIndex']])==key(c))) for name in all_runs]))
report['accounting']='Time/node counts include every horizon and every retry, including failed stages. Generated-state counts are cumulative work, not simultaneous storage. Version snapshots use maximum, not addition. Each retry stage starts a fresh cold native model and reuses it across its selected knot types; no saved assignments imported.'
path.write_text(json.dumps(report,separators=(',',':'))+'\n')

u,m=report['cumulativeSummary'];checks=[s['independentVerification'] for s in stages]
rows=[]
for c in report['outcomesByCase']:
    n,j=c['knot'].split('_');a,b=c['lanes'];status=lambda r:f"identified ({r['moves']} moves)" if r['status']=='equivalent' else 'unknown'
    rows.append(f"<tr><td>\\({n}_{{{j}}}\\), seed {c['seedPair']}</td><td>{status(a)}</td><td>{status(b)}</td><td>{a['cumulativeMs']/1000:.2f} / {b['cumulativeMs']/1000:.2f}</td></tr>")
section=f'''<section id="immutable-results">
<h2>Nontrivial identifications through eight crossings</h2>
<p>The repeated transfer-validation bottleneck is removed. Each new local rule is checked against its complete incident-face alphabet, every resolved label and its stencil before activation; its nested evidence is then frozen in a private native catalog. Read-only views and sealed configuration prevent replacement. Normal transfer checks neither scan the catalog nor replay proofs. An explicit full-audit mode remains available. Once-only proof validation costs are included below.</p>
<p>The enlarged comparison uses 18 unchanged pairs from the earlier 105-pair matrix: the first prime reference at each crossing count from three through eight, with all three original seed pairs. Both endpoints still have five independently sampled lattice moves. No seed or endpoint is replaced. Every incident face throughout each knot is available, with no move-support patch. The fixed regular projection and single-Reidemeister endpoint grammar are unchanged.</p>
<p>Both lanes use exact query-local memoization of full signed-diagram endpoint maps and the same generic increasing-horizon schedule. They try horizons zero through ten, advancing only after complete finite exhaustion. Aggregate bounds are 5,000 expanded nodes and 60 seconds per initial query; the live-state limit is 200,000 per horizon. Remaining marked unknowns receive matched 120-second retries in both lanes. All failed first-attempt and repeated-horizon costs remain charged. No knot label, invariant, scramble history or construction route enters search.</p>
<table><thead><tr><th>Lane</th><th>Identified / unknown pairs</th><th>Total seconds, including retries</th><th>Expanded nodes</th><th>Peak MiB</th></tr></thead><tbody><tr><td>Brute force</td><td>{u['identified']} / {u['unknown']}</td><td>{u['totalMs']/1000:.2f}</td><td>{u['nodes']:,}</td><td>{u['maxRSSKiB']/1024:.1f}</td></tr><tr><td>Reused immutable GCTS</td><td>{m['identified']} / {m['unknown']}</td><td>{m['totalMs']/1000:.2f}</td><td>{m['nodes']:,}</td><td>{m['maxRSSKiB']/1024:.1f}</td></tr></tbody></table>
<p>Marked totals include {m['probeMs']/1000:.3f} seconds of learning probes, {m['activationValidationMs']/1000:.3f} seconds of once-only activation validation, {m['transferMs']:.3f} milliseconds of transfer checks and {m['certificateVerificationMs']/1000:.3f} seconds of JavaScript certificate verification. Marked graphs remove {m['candidateEliminations']:,} of {m['candidateCount']:,} legal candidates ({100*m['candidateEliminations']/m['candidateCount']:.2f}%). Different stages start fresh native models and transfer only within that stage; restarting and relearning are included in these costs.</p>
<p>These are positive pair identifications, including eight-crossing movies, with independent spatial endpoint replay. When brute force remains unknown, total-cost differences establish solved-versus-unknown behavior rather than an equal-success speedup factor. This enlarged experiment covers six representative types, not all 35 types at the larger budget; the complete earlier matrix remains below. Reference-bank selection, separate mirrors, composites, general isotopy completeness and twelve-crossing scaling remain open.</p>
<p>Independent replay verifies {sum(c['movies'] for c in checks)} lattice movies and {sum(c['resolvedLabels'] for c in checks):,} resolved local labels, in {sum(c['wallMs'] for c in checks)/1000:.2f} seconds after the timed runs. Inputs are reused, so no new scramble-generation cost is charged; the original common cost was 292.77 seconds. Query times include every repeated construction and cache warmup.</p>
<details><summary>Every representative knot and seed, with cumulative costs</summary><table><thead><tr><th>Pair</th><th>Brute force</th><th>GCTS</th><th>Seconds: brute / marked</th></tr></thead><tbody>{''.join(rows)}</tbody></table></details>
<p><a href="lattice-escalation-benchmark.json">All stages, bounds, proof catalogs and spatial certificates</a> · <a href="lattice-immutable-contract.json">Immutable-cache and algorithm contract</a> · <a href="../../scripts/benchmark-lattice-escalation.mjs">Reproduction harness</a> · <a href="../../scripts/verify-lattice-escalation.py">Independent verifier</a>.</p>
<pre>node scripts/benchmark-lattice-escalation.mjs
node scripts/benchmark-lattice-escalation.mjs --retry-report=research/knot-classifier/lattice-escalation-benchmark.json --max-ms=120000 --directory=/tmp/knot-escalation-retry --output=/tmp/knot-escalation-retry.json
node tests/test_knot_lattice_cached.mjs
python3 scripts/verify-lattice-escalation.py research/knot-classifier/lattice-escalation-benchmark.json</pre>
</section>
'''
html=root/'research/knot-classifier/lattice-classifier.html';text=html.read_text()
if '<section id="immutable-results">' in text:
    start=text.index('<section id="immutable-results">');end=text.index('</section>',start)+len('</section>');text=text[:start]+text[end:].lstrip('\n')
text=text.replace('<section id="through8-results">',section+'<section id="through8-results">',1)
text=text.replace('<h2>Prime knots through eight crossings: deeper independent scrambles</h2>', '<h2>Earlier six-second matrix: all prime types through eight crossings</h2>')
text=text.replace('Complete recognition, reference-bank selection, mirror/composite scoring and twelve-crossing scaling remain pending.', 'Representative five-move independent pairs through eight crossings are now identified with immutable proof reuse and larger budgets. Complete recognition, reference-bank selection, mirror/composite scoring and twelve-crossing scaling remain pending.')
html.write_text(text)
readme=root/'research/knot-classifier/README.md';old=readme.read_text()
if old.startswith('> **Immutable-cache update:**'):old=old.split('\n\n',1)[1]
readme.write_text(f"> **Immutable-cache update:** Local extension rules are validated once, recursively frozen and held in a private read-only native catalog. Repeated transfer proof replay is removed; full audit remains available. Both classifier lanes now support generic iterative horizons, with exact endpoint-map memoization and complete all-face domains. Larger-budget representative tests through eight crossings identify {m['identified']} / 18 pairs with markings; brute force identifies {u['identified']} / 18. Failed stages and retries are included in the [live cost report](lattice-classifier.html#immutable-results). This is six representative prime types, not a complete classifier score over all 35. Reproduce with `node scripts/benchmark-lattice-escalation.mjs`; verify with `python3 scripts/verify-lattice-escalation.py research/knot-classifier/lattice-escalation-benchmark.json`.\n\n"+old)
print(json.dumps({'summary':report['cumulativeSummary'],'verification':checks}))
