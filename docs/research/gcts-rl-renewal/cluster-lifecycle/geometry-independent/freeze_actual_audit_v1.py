"""Static prospective audit freeze only. No scientific execution/import."""
import ast
import hashlib
import json
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
D=ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011'


def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)


def main():
    began=time.perf_counter();sources=[]
    for name in ['lifecycle_oracle_v2.py','independent_lifecycle_records_v1.py','independent_lifecycle_replay_v2.py',
                 'lifecycle_actual_audit_v1.py','lifecycle_actual_owner_v1.py','freeze_actual_audit_v1.py']:
        p=HERE/name;ast.parse(p.read_bytes());sources.append(pin(p))
    inputs=[pin(ROOT/'AGENTS.md'),pin(ROOT/'docs/basic-tiling-algorithm.md')]
    for name in ['plan-v1.json','plan-attempt-02.json','plan-attempt-03.json','authoring-cost-clarification-v1.json',
        'attempt02-causal-diagnosis-v1.json','hilbert_cluster_lifecycle_v1.py','hilbert_cluster_fixtures_attempt03_v1.py',
        'fixtures-lifetime-v1.json','fixtures-supervision-v1.json','attempt-02/fixtures-lifetime-v1.json',
        'attempt-02/fixtures-supervision-v1.json','attempt-02/fixtures-stderr-v1.txt',
        'attempt-03/fixtures-outcome-v1.json','attempt-03/fixtures-lifetime-v1.json',
        'attempt-03/fixtures-supervision-v1.json','attempt-03/fixtures-stderr-v1.txt','attempt-03/fixtures-stdout-v1.txt']:
        inputs.append(pin(D/name))
    for name in ['design-v1.json','design-v2.json','tiny-source-review-v1.json','tiny-attempt02-source-review-v1.json',
                 'tiny-attempt02-failure-diagnosis-v1.json','tiny-attempt03-source-review-v1.json']:
        inputs.append(pin(HERE/name))
    producer=json.loads((D/'plan-attempt-03.json').read_bytes())
    preserved={}
    for entry in producer['sources']+producer['inputs']+producer['preserved_files']:
        actual=pin(ROOT/entry['path']);assert actual=={k:entry[k] for k in ('path','sha256','bytes')}
        preserved[entry['path']]=actual
    plan=dict(status='frozen_source_ready_root_review_and_one_independent_tiny_dispatch_required',
        version='independent-whole-cluster-tiny-v1',sources=sources,inputs=inputs,
        preserved_files=list(preserved.values()),whole_seconds=60,worker_alarm_seconds=50,peak_bytes=536870912,
        root_activation_path=str((HERE/'root-activation-v1.json').relative_to(ROOT)),
        worker_path=str((HERE/'lifecycle_actual_audit_v1.py').relative_to(ROOT)),
        owner_path=str((HERE/'lifecycle_actual_owner_v1.py').relative_to(ROOT)),
        result_path=str((HERE/'actual-audit-result-v1.json').relative_to(ROOT)),
        lifetime_path=str((HERE/'actual-audit-lifetime-v1.json').relative_to(ROOT)),
        stdout_path=str((HERE/'actual-audit-stdout-v1.txt').relative_to(ROOT)),
        stderr_path=str((HERE/'actual-audit-stderr-v1.txt').relative_to(ROOT)),
        expected_counts={'states':81,'complete_raw_candidate_comparisons':694,'registries':73,
            'controlled_transactions':15,'dfs_events_including_begins':31,'bounded_dfs_series':3,'actual_corruptions':24},
        counts_are_predictions_until_audit_terminal=True,
        method=['Direct complete tiny primitive universe from exact source-bound witness/ordered ports and point triples; no producer or graph imports.',
            'Exact registered body reconstruction from authored source plus explicit row transport, complete decorated identities, source/context/boundary/epoch checks.',
            'Independent full snapshot graph/hint state implementation, branch-absorbing whole retirement and exact preferred plus fallback permutation.',
            'All saved controlled before/after transactions and independent complete tiny DFS event/state replay; every excluded child independently exhausted, unknown never prunes.',
            '24 independently generated concrete corruptions, separate positive noninjective-port/retirement/rollback/unknown controls.'],
        limits_scope='60-second whole owner lifetime / 50-second worker alarm / 512 MiB retrospective conservative kernel peak; sole direct child, no native/search/production model.',
        gaps=['Toy source registries are authored infrastructure; synthetic zero and opaque-pair rules are not mathematical proofs.',
              'Unsaved producer negative calls (nonfinite budgets and untracked public metadata) receive source review only, not independent replay from status records.',
              'No actual 24-row Hilbert lifecycle/search/compiler/native correspondence or learned-policy activation.',
              'Separate producer cumulative 1.019903957 seconds retains both failures; source authoring and final own receipt write are unmeasured/excluded.'],
        freeze_metadata_seconds_before_plan_write=time.perf_counter()-began,
        actual_audits_executed=0,engine_imports=0,target_searches=0,native_queries=0)
    out=HERE/'actual-audit-plan-v1.json'
    with out.open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
    print(json.dumps({'plan':pin(out),'sources':len(sources),'inputs':len(inputs),'preserved':len(preserved)}))


if __name__=='__main__':main()
