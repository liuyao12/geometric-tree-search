"""Freeze separate exact-acceleration correspondence, before measurements."""
import ast
import datetime
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'.gcts-active/commutativity13-20261011'
OLD=ROOT/'.gcts-active/commutativity-cluster-search-20261011'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def sources():
    found=set();pending=['commutativity13_freeze','commutativity13_preflight','commutativity13_audit','commutativity13_extract','commutativity13_search']
    while pending:
        n=pending.pop();p=HERE/(n+'.py')
        if n in found or not p.exists():continue
        found.add(n)
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Import):pending.extend(v.name.split('.')[0] for v in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
    return {str((HERE/(n+'.py')).relative_to(ROOT)):digest(HERE/(n+'.py')) for n in sorted(found)}


def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'preflight-plan.json').exists():raise ValueError('immutable freeze already exists')
    old=json.loads((OLD/'execution-freeze.json').read_text());source=sources();inputs=dict(old['input_sha256'])
    for n in ('fixed-r1-search.json.gz','fixed-r2-search.json.gz','search-audit-v5.json','search-audit-v5-plan.json'):
        p=OLD/n
        if p.exists():inputs[str(p.relative_to(ROOT))]=digest(p)
    with zipfile.ZipFile(OUT/'preflight-sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in source:z.write(ROOT/p,p)
    source[str((OUT/'preflight-sources.zip').relative_to(ROOT))]=digest(OUT/'preflight-sources.zip')
    spec=json.loads((OLD/'plan.json').read_text())['case']
    plan=dict(status='frozen_exact_acceleration_correspondence',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              case=spec,source_sha256=source,input_sha256=inputs,producer_seconds=300,audit_seconds=300,rss_bytes=536870912,
              projection_seconds_per_process=180,
              scope='All589previous actual fixed proposal events (294+295), complete13row model/static18480family bindings and four40attempt old/newbase/fixeddiagnostic fixture trees. Not target proof discovery or policy training.',
              exactness=['Identical candidate pools, canonical order, full work counters, all9features, fixed scores/distributions/tie selection; old48growth denominator retained.',
                         'All static bindings/incidence ordered exactly; full universe SHA rankings restricted to actual legal set,16-anchor boundedLRU.',
                         'Node-aware CJSON complete-value serialization; every actual diagnostic node/event/full census retained; every lateractual trace independently reconstructed.'],
              costs='All cold static-cache initialization,old/new event computation,projection decode,full node serialization and independent replay are charged. Correspondence warmcache is discarded before each actualfresh13rowobservation.',
              actual_search=dict(order=['base-r1','fixed-r1','fixed-r2','base-r2'],length=13,attempts=5000,seconds_per_observation=60,producer_seconds=300,audit_seconds=300,rss_bytes=536870912,launch_requires='Passed complete independent preflight plus separate exact executor source/input freeze and exchanged model hash.'),
              rl=dict(launched=False,reason='Four matched60smaximum observations allocate240s of300sproducer; no compatible policy exists and training plus a separate learned lane cannot be assured within remaining60s. Fixed weights stay authored and unchanged.'),
              prohibited_inputs='No ordinary commutativity word, closure ranks, witnesses, expanded/compact certificates or root post-search compaction artifacts are read. Target proof path/induction variable is not supplied.',
              native=dict(queries_authorized=0,heap_cells=262144,gate='Any found candidate is checkpointed and reported to parent with fixed-capacity preflight before any native query/resource change.'))
    (OUT/'preflight-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(plan_sha256=digest(OUT/'preflight-plan.json'),sources=len(source),inputs=len(inputs))))

if __name__=='__main__':main()
