"""Static metadata/output-only recovery freeze; no scientific import or run."""
import ast
import difflib
import hashlib
import json
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(65536),b''):h.update(b)
    return {'path':str(path.relative_to(ROOT)),'sha256':h.hexdigest(),'bytes':path.stat().st_size}


def main():
    start=time.perf_counter();dest=HERE/'plan-attempt-02.json'
    if dest.exists():raise ValueError('immutable attempt02 freeze exists')
    original=json.loads((HERE/'plan-v1.json').read_text())
    failure=json.loads((HERE/'fixtures-lifetime-v1.json').read_text())
    stage=json.loads((HERE/'fixtures-supervision-v1.json').read_text())
    assert failure['status']=='unknown_or_failed' and failure['supervisor_wait_reaped'] is True
    assert stage['owned_child_terminal_wait_reaped'] is True and stage['exit_code']==-9
    assert stage['resource_reason']=='watchdog_failure' and not stage['rss_samples']
    if (HERE/'fixtures-outcome-v1.json').exists():raise ValueError('first child outcome unexpectedly exists')
    preserved={}
    previous=original['sources']+original['inputs']+original['preserved_files']
    previous += [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and
                 (p.name in ('plan-v1.json','freeze-receipt-v1.json','authoring-cost-clarification-v1.json')
                  or p.name.startswith('fixtures-'))]
    for p in previous:
        actual=pin(ROOT/p['path'])
        if actual!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('frozen prior mismatch')
        if p['path'] in preserved and actual!=preserved[p['path']]:raise ValueError('ambiguous pin')
        preserved[p['path']]=actual
    pairs=[('hilbert_cluster_fixtures_v1.py','hilbert_cluster_fixtures_attempt02_v1.py'),
           ('hilbert_cluster_run_v1.py','hilbert_cluster_run_attempt02_v1.py'),
           ('hilbert_cluster_outer_v1.py','hilbert_cluster_outer_attempt02_v1.py')]
    diffs=[]
    for old,new in pairs:
        p=HERE/(new[:-3]+'-diff.txt')
        if p.exists():raise ValueError('immutable diff exists')
        p.write_text(''.join(difflib.unified_diff((HERE/old).read_text().splitlines(True),
                    (HERE/new).read_text().splitlines(True),fromfile=old,tofile=new)))
        diffs.append(pin(p))
    sources=[HERE/'hilbert_cluster_lifecycle_v1.py']+sorted(HERE.glob('hilbert_cluster*_attempt02_v1.py'))
    for p in sources:ast.parse(p.read_text(),filename=str(p))
    output=HERE/'attempt-02'
    output.mkdir(exist_ok=False)
    inputs=original['inputs']+[
        {'role':'frozen_lifecycle_parent_plan',**pin(HERE/'plan-v1.json')},
        {'role':'first_failed_lifecycle_supervision',**pin(HERE/'fixtures-supervision-v1.json')},
        {'role':'first_failed_lifecycle_full_lifetime',**pin(HERE/'fixtures-lifetime-v1.json')},
        {'role':'authoring_cost_correction',**pin(HERE/'authoring-cost-clarification-v1.json')}]
    amendment={'version':'hilbert-whole-cluster-tiny-attempt02-metadata-only',
        'status':'frozen_source_ready_root_review_and_one_escalated_owned_watchdog_dispatch_required',
        'sources':[pin(p) for p in sources],'inputs':inputs,
        'preserved_files':[preserved[k] for k in sorted(preserved)],'diffs':diffs,
        'original_plan_pin':pin(HERE/'plan-v1.json'),
        'logical_scope':'All kernels, fixture scientific assertions, full graph/whole lifecycle semantics and predicted11/64 counts unchanged. Only owned output path/argv/supervisor plan and runtime source-pin path identify isolated attempt02.',
        'output_directory':str(output.relative_to(ROOT)),
        'producer_limits':{'cumulative_outer_wall_seconds':60,'child_alarm_seconds':50,'supervisor_seconds':55,
                          'host_bytes':536870912,'execution_authorized_by_this_freeze':False},
        'prior_failure':{'status':'sandbox_metadata_permission_unknown_no_fixture_outcome',
                        'seconds':failure['full_supervisor_process_seconds_including_receipt_write'],
                        'conservative_host_peak_bytes':failure['conservative_host_peak_bytes'],
                        'child_exit_code':-9,'terminal_wait_reaped':True,'not_a_logical_failure':True},
        'enforcement':'Same fail-closed task-owned /bin/ps sampled watchdog, kill/wait/reap, childSIGALRM and final peak rejection; precise require_escalated own-child monitoring dispatch after root review. Never drop sampler.',
        'metrics_gap':'v1 worker tracks but does not export cumulative scan/order/rollback subphase metrics. Whole worker/supervisor/outer duration is charged; this evidence limitation is preserved, not silently repaired.',
        'authoring_cost':'Original cross-process elapsed field invalid. Bound authoring-cost clarification calendar interval619.829093s includes reads/review/idle, not CPU effort.',
        'freeze_seconds_before_plan_write':time.perf_counter()-start,
        'fixture_executions_at_freeze':0,'attempt02_fixture_executions_at_freeze':0,
        'prior_supervisory_attempts':1,'actual_model_executions':0,'native_queries':0,
        'actual_geometry_target_searches':0,'new_RL_training':False}
    dest.write_text(json.dumps(amendment,indent=2)+'\n')
    receipt={'status':'attempt02_sources_inputs_failure_bill_frozen_without_execution','plan':pin(dest),
        'sources':len(sources),'inputs':len(inputs),'preserved':len(preserved),
        'syntax':'ast.parse only, no engine imports','attempt02_executions':0,
        'freeze_seconds_before_receipt_write':time.perf_counter()-start}
    (HERE/'freeze-attempt-02.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
