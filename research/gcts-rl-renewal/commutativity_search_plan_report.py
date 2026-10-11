"""Read-only export of the frozen practical experiment specification.

No model construction, target search, proof extraction, training or native run.
"""
import hashlib
import json
from pathlib import Path
from induction_receptors_export import math, esc

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/commutativity-cluster-search-20261011'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def main():
    frozen = OUT / 'plan.json'
    plan = json.loads(frozen.read_text())
    assert not plan['execution_enabled'] and plan['searches_executed'] == 0
    for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    plan_sha = hashlib.sha256(frozen.read_bytes()).hexdigest()
    exported = DOC / 'commutativity_search_plan.json'
    exported.write_bytes(frozen.read_bytes())
    html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Commutativity: bounded search plan</title><link rel="stylesheet" href="report.css">
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>main{max-width:1050px;margin:auto;padding:24px}section{margin:32px 0}.status{background:#fff3dc;border-left:4px solid #c28b2a;padding:16px}.pin{overflow-wrap:anywhere}nav{display:flex;gap:14px;flex-wrap:wrap}</style></head><body><main>
<p><a href="index.html#goals">Research program</a> · <a href="commutativity_admissions.html#result">Complete native inventory</a></p>
<h1>Commutativity: the next bounded search comparison</h1>
<nav><a href="#status">Status</a><a href="#comparison">Matched algorithms</a><a href="#clusters">Clusters</a><a href="#gates">Certification gates</a><a href="#limits">Limits</a></nav>
<section id="status"><p class="status">Frozen experiment specification only. The complete 94-interface native registry has passed independent reconciliation, but no commutativity target search, ordinary extraction or whole-target native check has run. The experiment still requires a compatible executor/source freeze and parent review before measurement.</p>'''
    html += '<p>The query is ' + math(plan['case']['target']) + '. It uses the unchanged recursive addition equations and natural-number induction, the complete five-node contextual term grammar, and the two actual discovered arithmetic certificates.</p>'
    html += '<p>The predicate ' + math(plan['grammar']['induction_predicate']) + ' is instantiated for both possible induction variables, with the other parameter universally closed. All declared rewrite directions, occurrences, substitutions and source receptors remain available. This is a finite contextual proof language; arbitrary first-order induction predicates are outside its present grammar.</p></section>'
    html += '''<section id="comparison"><h2>The algorithms share exactly the same proof language</h2><p>The initial comparison fixes 12 rows, 48 required points and 17,158 translated placements, representing 153 retained inference templates and all 94 admitted definitions. Every required point starts active with generation zero. The base lane uses the reference global dead/forced/earliest-generation scheduler and deterministic incident-candidate order. The fixed-cluster lane uses exactly the same graph, legality and fallback, with validated cluster continuation preferences.</p><p>Each lane has two fresh deterministic observations, at most 5,000 placement attempts and 60 seconds each. Repetitions check reconstruction and shared-host cost variation; they are not independent statistical trials of learned performance.</p><p>A separate ordinary control scans every retained hyperedge to the full fixed point using deterministic first-ready witnesses. It reconstructs the target DAG only after closure, and runs after all GCTS traces freeze. Its actual word length will be compared with the same 12-row boundary. Its witness never seeds GCTS. An ordinary forward proof is credited to ordinary forward search.</p></section>
<section id="clusters"><h2>Proof-backed families, with open cluster proposals</h2><p>All 42 promoted-lemma-root/rewrite families remain available, with 16,170 raw parameter choices and 13,860 internally compatible bindings at this boundary. Each complete family expands to eight existing base placements. Its other premise stays an explicit external receptor. Proposals can also contain arbitrary bounded one-to-three-placement shapes from the complete legal base inventory.</p><p>A bounded proposal pool of 24 and 2,048 validation checks per branch affects ordering only. It never supplies dead-end or forced-move counts. Every aggregate must pass exact occupancy and marking checks; after every scheduled constituent the engine returns to global propagation. All alternative base candidates remain available and rollback restores hint/state/graph/generation metadata.</p><p>The fixed score is authored. Only the two actually discovered proof certificates receive the promoted-lemma feature; the generic authored local interfaces are not called learned. No compatible trained cluster policy exists, and no RL training is included in this first comparison. A later source-only training option requires its own tasks, reward, action/feature bindings, budgets and independent replay.</p></section>
<section id="gates"><h2>Independent checks before any proved-target claim</h2><p>The new executor must bind the exact registry and reconstruct the entire point universe. An independent audit will compare every placement and all family/source bindings, then replay every recorded GCTS node for complete incidence, global decision ordering, fallback and rollback. The initial candidate language and boundary must be identical across both lanes.</p><p>The older semantic guidance assumes all blocks have a nonzero block mode and primitive commands have no source mode. That assumption fails for the zero-input theorem blocks and unary native generalization in this inventory. A fresh generic adapter must use each inference template's actual premise arity; no frozen historical source will be edited.</p><p>Every found model, complete search tree, placements, decoded word, proposals and cost checkpoint will be saved before whole native checking. The first candidate in each algorithm lane may be expanded and compacted only by audited generic definition slicing and formula-DAG sharing. Its original theory and exact target remain fixed. A separately audited capacity/encoding preflight precedes fresh whole native acceptance and complete independent replay.</p></section>
<section id="limits"><h2>Explicit ceilings and unresolved costs</h2><p>The four searches together have a 240-second search cap; ordinary extraction has 60 seconds. Complete graph preflight has 180 seconds, graph/tree audit 300 seconds, and host processes have 512 MiB. No automatic row-boundary increase is included.</p><p>At most three fresh whole target requests are checked at 20 billion native microsteps each, with 600 seconds cumulative production and a separate 600 seconds replay. The parser, checker and universal palette remain unchanged, with the previously audited 262,144-cell external heap boundary. Each whole-request preflight has 180 seconds and 20 million tree instructions; local-interface capacities do not guarantee whole-proof feasibility. Every exceeded boundary or budget remains unknown.</p><p>All previous grammar/admission costs, exact reuse credits and memory/search/checker unknowns remain in their immutable reports. Target word length, whole certificate size and any GCTS speed contribution remain unmeasured. Manual infrastructure development is unmeasured.</p>'''
    html += '<p><a href="commutativity_search_plan.json">Complete exact frozen specification and source/input hashes</a></p><p class="pin">Specification SHA-256: ' + plan_sha + '</p></section></main></body></html>'
    reader = DOC / 'commutativity_search_plan.html'
    reader.write_text(html)
    files = [reader, exported, Path(__file__)]
    result = dict(status='prepared-specification-only-awaiting-parent-review', published=False,
                  reader='commutativity_search_plan.html?v=20261011-csp1#status',
                  plan_sha256=plan_sha, searches_executed=0, native_target_queries_executed=0,
                  files=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size,
                              sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    (OUT / 'integration.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(reader=result['reader'], files=len(files),
                         manifest_sha256=hashlib.sha256((OUT / 'integration.json').read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
