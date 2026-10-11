"""Source/pin review only. No lifecycle producer/engine import or execution."""
import ast
import difflib
import hashlib
import json
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011'
OUT=Path(__file__).resolve().parent


def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)


def main():
    start=time.perf_counter(); pp=D/'plan-attempt-03.json'; plan=json.loads(pp.read_bytes())
    assert pin(pp)['sha256']=='2636005736ad4a90290db3994aa35a341a9ce7ca0c12eab82ba18d5675782707'
    verified={}
    for section in ('sources','inputs','preserved_files','diffs'):
        for entry in plan[section]:
            p=ROOT/entry['path']; actual=verified.setdefault(entry['path'],pin(p))
            assert actual=={k:entry[k] for k in ('path','sha256','bytes')}
            if section=='sources':ast.parse(p.read_bytes())
    assert pin(D/'plan-attempt-02.json')==plan['parent_plan']
    assert pin(D/'attempt02-causal-diagnosis-v1.json')==plan['causal_note']
    assert pin(D/'hilbert_cluster_lifecycle_v1.py')['sha256']=='e836501e29605df6c226342a0a2b63d7fa9ff2f91dc3c1b43e830f49f188744f'
    for kind in ('fixtures','run','outer'):
        a=f'hilbert_cluster_{kind}_attempt02_v1.py'; b=f'hilbert_cluster_{kind}_attempt03_v1.py'
        diff=''.join(difflib.unified_diff((D/a).read_text().splitlines(True),(D/b).read_text().splitlines(True),fromfile=a,tofile=b))
        assert diff==(D/f'hilbert_cluster_{kind}_attempt03_v1-diff.txt').read_text()
    source=(D/'hilbert_cluster_fixtures_attempt03_v1.py').read_text()
    normalized=source.replace("'attempt-03'","'attempt-02'").replace('only isolated attempt-03 output allowed','only isolated attempt-02 output allowed')
    normalized=normalized.replace('    # Inspection above resynchronizes the hint revision: save its ACTUAL next-call baseline.\n    initial = c.semantic_state()\n','')
    new="""    status_ok = unknown['status'] == 'unknown_budget'
    restoration_ok = c.semantic_state() == initial
    if not status_ok or not restoration_ok:
        diagnostic={'status':'failed_unknown_fixture_diagnostic', 'result':unknown,
                    'expected_parent':initial, 'actual_parent':c.semantic_state(),
                    'status_ok':status_ok,'restoration_ok':restoration_ok,'events':e.events}
        (output/'fixture-failure-diagnostic-v1.json').write_text(json.dumps(diagnostic,indent=2)+'\\n')
    assert status_ok, 'one-child cutoff was not unknown'
    assert restoration_ok, 'one-child cutoff failed actual call-entry paired restoration'
"""
    assert new in normalized
    normalized=normalized.replace(new,"    assert unknown['status'] == 'unknown_budget' and c.semantic_state() == initial\n")
    assert normalized==(D/'hilbert_cluster_fixtures_attempt02_v1.py').read_text()
    for kind in ('run','outer'):
        s=(D/f'hilbert_cluster_{kind}_attempt03_v1.py').read_text().replace('attempt-03','attempt-02').replace('attempt03','attempt02')
        if kind=='outer':s=s.replace('PRIOR_FAILED_SECONDS=0.5955343319999999','PRIOR_FAILED_SECONDS=0.272813916')
        assert s==(D/f'hilbert_cluster_{kind}_attempt02_v1.py').read_text()
    assert plan['producer_limits']==dict(cumulative_outer_wall_seconds=60,child_alarm_seconds=50,
        supervisor_seconds=55,host_bytes=536870912,execution_authorized_by_this_freeze=False)
    lives=[json.loads((D/f).read_bytes()) for f in ['fixtures-lifetime-v1.json','attempt-02/fixtures-lifetime-v1.json']]
    old=plan['preserved_unknown_work']
    assert old['first_seconds']==lives[0]['full_supervisor_process_seconds_including_receipt_write']
    assert old['second_seconds']==lives[1]['full_supervisor_process_seconds_including_receipt_write']
    assert abs(old['first_seconds']+old['second_seconds']-old['cumulative_prior_seconds'])<1e-12
    assert old['first_peak_bytes']==28327936 and old['second_peak_bytes']==47972352
    assert plan['native_queries']==plan['actual_model_executions']==plan['actual_geometry_target_searches']==plan['attempt03_executions']==0
    assert plan['new_RL_training'] is False
    receipt=dict(status='passed_independent_fixture_baseline_successor_source_readiness',plan=pin(pp),
        source_entries=len(plan['sources']),input_entries=len(plan['inputs']),preserved_entries=len(plan['preserved_files']),
        verified_unique_paths=len(verified),sources=plan['sources'],diffs=plan['diffs'],
        previous_diagnosis=pin(OUT/'tiny-attempt02-failure-diagnosis-v1.json'),
        conclusions=[
            'Only expected fixture baseline moves past the inspecting snapshot, whose ordered-domain call resynchronizes hint revision. Exact restoration assertion retained; status and restoration now checked separately with failure payload.',
            'Every remaining scientific fixture assertion text-identical to attempt-02. Logical kernel byte-identical. Output/argv/supervisor plan/source identities versioned to isolated attempt-03.',
            'Same 50-second child alarm, 55-second owned watchdog, cumulative 60-second outer and 512 MiB limits; both failed prior lifetimes charged 0.595534332 seconds.',
            'No failed outcome relabeled; actual whole producer and independently frozen future adapter remain separate gates.',
        ],scope='Source readiness for root-owned tiny retry only. No scientific import, fixture execution, actual model, target search, native or compiler activation.',
        cost_caveats=['Authoring calendar interval is not CPU effort; old invalid cross-process timer preserved.',
                      'Unexported controller metrics cannot support separate scan/order/rollback cost claims.',
                      'Final outer receipt writes excluded from timer; actual resource success remains unestablished.'],
        metadata_review_seconds_before_receipt_write=time.perf_counter()-start,manual_source_review_time='unmeasured')
    out=OUT/'tiny-attempt03-source-review-v1.json'
    with out.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps({'status':receipt['status'],'receipt':pin(out)}))


if __name__=='__main__':main()
