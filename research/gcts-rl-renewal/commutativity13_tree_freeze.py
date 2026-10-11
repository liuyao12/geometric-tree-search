"""Fresh full tree audit freeze; same300s/512MiB and every node/event."""
import datetime
import hashlib
import json
import zipfile
from pathlib import Path
from commutativity13_phase_freeze import closure
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'.gcts-active/commutativity13-20261011'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    execution=json.loads((OUT/'execution-freeze.json').read_text())
    for p,v in {**execution['source_sha256'],**execution['input_sha256']}.items():
        if h(ROOT/p)!=v:raise ValueError('exact unchanged producer '+p)
    summary=json.loads((OUT/'search-summary.json').read_text())
    if summary['status']!='complete_four_matched13_search_observations_pending_independent_audit':raise ValueError('four producer outputs unresolved')
    before=(HERE/'commutativity13_tree_audit.py').read_text()
    after=(HERE/'commutativity13_tree_audit_stream.py').read_text()
    expected=before.replace("'tree-audit-plan.json'","'tree-audit-plan-stream.json'").replace("m=load(OUT/(observation['id']+'-model.json.gz'));raw=load(OUT/(observation['id']+'-search.json.gz'))", "raw=load(OUT/(observation['id']+'-search.json.gz'));m=load(OUT/(observation['id']+'-model.json.gz'))").replace("'tree-audit.json'","'tree-audit-stream.json'").replace('Every actual13row full graph/event independently replayed; no producer import.', 'Every actual13row full graph/event independently replayed; no producer import.\nTrace is decoded before loading its large model to bound live data lifetimes.')
    expected=expected.replace('from commutativity_cluster_audit import tree,families,need,packed,model_binding','from commutativity_cluster_audit import tree,families,need,packed,model_binding\nfrom commutativity13_structure import skeleton').replace("result['observations'].append(dict(id=observation['id'],**audited))", "structural=skeleton(raw['search']['tree'],OUT/(observation['id']+'-structure.jsonl'),OUT/'base-r1-structure.jsonl' if observation['id']!='base-r1' else None)\n        result['observations'].append(dict(id=observation['id'],**audited,**structural))")
    if after!=expected:raise ValueError('pure read-order lifetime delta plus read-only complete structural projection')
    path=OUT/'tree-audit-plan-stream.json'
    if path.exists():raise ValueError('immutable audit freeze already exists')
    inputs=dict(execution['input_sha256']);source={**execution['source_sha256'],**closure(['commutativity13_tree_audit_stream','commutativity13_tree_freeze'])}
    for n in ['execution-freeze.json','search-summary.json']:
        inputs[str((OUT/n).relative_to(ROOT))]=h(OUT/n)
    for v in execution['observations']:
        for end in ['model.json.gz','search.json.gz','checkpoint.json','summary.json']:
            p=OUT/(v['id']+'-'+end);inputs[str(p.relative_to(ROOT))]=h(p)
    zpath=OUT/'tree-audit-sources-stream.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in source:
            if p.endswith('.py'):z.write(ROOT/p,p)
    source[str(zpath.relative_to(ROOT))]=h(zpath)
    plan=dict(status='frozen_complete_four13row_graph_audit',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,input_sha256=inputs,
              audit_seconds=300,rss_bytes=536870912,observations=execution['observations'],native_target_queries_authorized=0,
              lifetime='Same frozen reversiblev3decoder. Decode entiretrace before loading large model; no source/trace/node/event/field truncation or budget extension. Independently replay all placement/domain/scheduler/proposal/hint/fallback/rollback values with old semantic audit.',
              budget='One300s512MiB complete graph audit, separate from cumulative preflightaudit. Any exhaustion is unknown, all prior costs and outputs preserved.')
    path.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan_sha256=h(path),sources=len(source),inputs=len(inputs))))
if __name__=='__main__':main()
