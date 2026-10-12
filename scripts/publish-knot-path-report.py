"""Write the reviewed path-search formulation and measured scheduler comparison."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
report=json.loads((root/'research/knot-classifier/lattice-path-schedules-benchmark.json').read_text())
lanes={l['id']:l for l in report['lanes']}
assert all([len(r['certificate']['steps']) for r in lanes[name]['runs']]==[8,10] for name in ['balanced-gcts','adaptive-gcts'])
assert all(not r['certificate'] for name in ['balanced-brute','adaptive-brute'] for r in lanes[name]['runs'])
assert [a['stats']['nodes']-b['stats']['nodes'] for a,b in zip(lanes['balanced-gcts']['runs'],lanes['adaptive-gcts']['runs'])]==[5,0]
rows=[]
names={'balanced-gcts':'Balanced + GCTS','adaptive-gcts':'Adaptive + GCTS','balanced-brute':'Balanced brute force','adaptive-brute':'Adaptive brute force'}
for row in report['summary']:
    rows.append(f"<tr><td>{names[row['lane']]}</td><td>{row['identified']} / {row['unknown']}</td><td>{row['totalMs']/1000:.2f}</td><td>{row['nodes']:,}</td><td>{row['maxRSSKiB']/1024:.1f}</td></tr>")
checks=report['independentVerification']
section=f'''<section id="path-search-results">
<h2>The selected formulation: lattice move paths with GCTS markings</h2>
<p>The classifier searches the graph of exact lattice embeddings. A node is a whole knot; an edge is a checked reversible lattice move. A bidirectional search grows from both endpoints and joins two parent paths. This directly matches the equivalence question and does not require filling a space-time volume. A verified path can still be rendered as a knot movie.</p>
<p>The engine sees opaque keys, complete candidate domains and point values. At each state there is one choice point, with unit \\(t\\) for every move. Seam \\(m\\)-values encode opaque endpoint agreement. Online local extension failures produce proved failed-budget \\(m\\)-values; boundary disagreement removes candidates through the point/candidate graph. Unknown probes add no exclusions. These are real candidate markings in a declared graph-path adaptation. Space-time exact tiling and the reference neighboring-tile/corona learner remain separate formulations.</p>
<p>No knot name, invariant, crossing label, ancestor, scramble history or preferred move type enters search. The author adapter and independent verifier define legal lattice moves. Every incident face throughout the knot remains available under the existing fixed-projection grammar and finite edge bounds. Learned profiles are validated once and kept immutable, preserving the earlier transfer-cost improvement.</p>
<h3>Testing a different tree scheduler</h3>
<p>Balanced scheduling expands the shallower breadth-first wave. Adaptive scheduling expands the smaller pending frontier, with depth breaking ties. Each wave retains complete layer enumeration and shortest-prefix bookkeeping. As the two radii grow, any allowed path within their sum crosses both retained balls, so changing which side expands preserves bounded path existence. This is a specialized graph scheduler; the reference tiling generation rule is not claimed.</p>
<p>The four-lane pilot uses two unchanged existing pairs: \\(3_1\\), seed 0, and the harder \\(8_1\\), seed 1. Both endpoints have five independently sampled lattice moves. Each lane starts fresh; marked lanes reuse only their own newly learned catalog across the two types. All four lanes share horizons zero through ten, a 120-second aggregate query budget, 5,000 expanded nodes, 200,000 live states, 240 unit edges, complete move inventories and the same neutral seed. No cases are replaced. Times include repeated horizons, probes, validation, memoization warmup and JavaScript certificate verification.</p>
<table><thead><tr><th>Scheduler and markings</th><th>Identified / unknown</th><th>Total seconds</th><th>Expanded states</th><th>Peak MiB</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Both marked schedulers identify both pairs, with eight- and ten-move certificates. Adaptive scheduling saves five expansions on the trefoil and saves none on the harder eight-crossing pair; their total times are essentially equal. This pilot establishes no marked identification advantage, so balanced bidirectional search remains the classifier default. Adaptive brute force spends less total time before reaching its limits, while both pairs remain unknown. GCTS is the effective pruning mechanism on these cases. Brute-force unknowns provide no equal-success timing comparison.</p>
<p>The generic scheduler tests cover 1,536 exhaustive graph/budget/marking combinations against an independent reachability oracle. An asymmetric control uses 54 expansions with balanced scheduling and four with adaptive scheduling; that demonstrates a possible benefit, rather than a knot-specific performance claim. Independent Python replay checks {checks['movies']} spatial movies and {checks['resolvedLabels']:,} resolved local proof labels in {checks['wallMs']/1000:.2f} seconds after the timed runs.</p>
<p>The larger earlier result remains 18 identified independent pairs through eight crossings. This two-case scheduler pilot does not expand recognition coverage. Full-bank classification, mirrors, composites, larger scrambles and twelve-crossing scaling remain acceptance gates. RL, if added, should propose validated move clusters with complete base-move fallback.</p>
<p><a href="lattice-path-schedules-benchmark.json">Four-lane evidence and certificates</a> · <a href="lattice-path-contract.json">Path-search formulation, proof scope and gaps</a> · <a href="../../tests/test_knot_path_schedules.mjs">Generic scheduler tests</a> · <a href="../../scripts/benchmark-knot-path-schedules.mjs">Reproduction harness</a>.</p>
</section>
'''
page=root/'research/knot-classifier/lattice-classifier.html';text=page.read_text()
if '<section id="path-search-results">' in text:
    start=text.index('<section id="path-search-results">');end=text.index('</section>',start)+len('</section>');text=text[:start]+text[end:].lstrip('\n')
text=text.replace('<section id="immutable-results">',section+'<section id="immutable-results">',1)
text=text.replace('The search assembles lattice realizations of Reidemeister tiles in space-time. Projection and the knot movie present the resulting certificate; they do not replace the lattice state or determine search bounds.', 'The current classifier searches for paths of checked lattice moves between exact embeddings. Learned point markings prune that graph search. Projection and the knot movie present the resulting certificate; they do not replace the lattice state or determine search bounds.')
text=text.replace('Exact whole-lattice-state seam reduction implemented. Local spatial occupancy/collar point functions remain pending.', 'Whole-lattice move-path point domains and capacity/extension markings are implemented. A global space-time tiling is an optional research formulation.')
page.write_text(text)
readme=root/'research/knot-classifier/README.md';old=readme.read_text()
if old.startswith('> **Path-search formulation:**'):old=old.split('\n\n',1)[1]
readme.write_text('> **Path-search formulation:** The classifier uses generic bidirectional search over exact lattice embeddings, with online proved point markings. A global space-time tiling is optional. A four-lane matched scheduler pilot found essentially equal marked performance for balanced and smaller-frontier scheduling; balanced remains the default. Both schedules preserve complete move domains and finite path existence. See the [live formulation and comparison](lattice-classifier.html#path-search-results) and [contract](lattice-path-contract.json).\n\n'+old)
print(json.dumps({'summary':report['summary'],'verification':checks}))
