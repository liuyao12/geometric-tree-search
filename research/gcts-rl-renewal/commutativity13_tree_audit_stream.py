"""Every actual13row full graph/event independently replayed; no producer import.
Trace is decoded before loading its large model to bound live data lifetimes."""
import gc
import gzip
import hashlib
import json
import resource
import time
from pathlib import Path
from commutativity_cluster_intern_v3 import load
from commutativity_cluster_audit import tree,families,need,packed,model_binding
from commutativity13_structure import skeleton

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.gcts-active/commutativity13-20261011'
PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011'


def main():
    began=time.perf_counter();plan=json.loads((OUT/'tree-audit-plan-stream.json').read_text())
    for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'full13tree exactfreeze '+p)
    execution=json.loads((OUT/'execution-freeze.json').read_text());catalog=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz');declared=families(catalog)
    result=dict(status='checking_every_actual13row_graph_tree',observations=[],native_target_queries=0)
    def within():
        result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if result['seconds']<=300 and result['peak_rss_bytes']<=536870912:return True
        result.update(status='unknown_complete13tree_audit_resource_budget',wall_overshoot_seconds=max(0.,result['seconds']-300),memory_overshoot_bytes=max(0,result['peak_rss_bytes']-536870912))
        (OUT/'tree-audit-stream.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return False
    bound=None
    for observation in execution['observations']:
        if not within():return
        raw=load(OUT/(observation['id']+'-search.json.gz'));m=load(OUT/(observation['id']+'-model.json.gz'))
        need(m['case']==raw['case'] and raw['observation']==observation,'exact actual balanced observation')
        model_binding(raw['case'],catalog,m['model'])
        current=hashlib.sha256(packed((m['model']['placements'],m['model']['roots'],m['model']['initial_marks'],m['row_domains']))).hexdigest()
        if bound is None:bound=current
        else:need(bound==current,'identical complete candidate language/boundary across all four lanes')
        if not within():return
        audited=tree(raw['case'],m['model'],raw['search'],declared)
        structural=skeleton(raw['search']['tree'],OUT/(observation['id']+'-structure.jsonl'),OUT/'base-r1-structure.jsonl' if observation['id']!='base-r1' else None)
        result['observations'].append(dict(id=observation['id'],**audited,**structural))
        (OUT/'tree-audit-stream.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE13TREE '+json.dumps(result['observations'][-1]),flush=True)
        del m,raw;gc.collect()
        if not within():return
    result.update(status='passed_complete_four13row_graph_and_proposal_traces',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  scope='All actual nodes/global full-universe legal domains/dead-forced-generation decisions/events/exact old proposal pools/counters/features/scores/ties/hint scheduling/full basefallback/failed-child retirement/rollback/decoded word. No native target acceptance or RLclaim.')
    (OUT/'tree-audit-stream.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
