"""Static one-line fixture-baseline repair and isolated attempt03 freeze."""
import ast
import difflib
import hashlib
import json
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(path):
    path=Path(path);sha=hashlib.sha256()
    with path.open('rb') as stream:
        for x in iter(lambda:stream.read(65536),b''):sha.update(x)
    return {'path':str(path.relative_to(ROOT)),'sha256':sha.hexdigest(),'bytes':path.stat().st_size}


def main():
    start=time.perf_counter();dest=HERE/'plan-attempt-03.json'
    if dest.exists():raise ValueError('immutable attempt03 freeze exists')
    previous=json.loads((HERE/'plan-attempt-02.json').read_text())
    lifetimes=[json.loads((base/'fixtures-lifetime-v1.json').read_text()) for base in (HERE,HERE/'attempt-02')]
    for lifetime in lifetimes:
        assert lifetime['status']=='unknown_or_failed' and lifetime['supervisor_wait_reaped'] is True
    stage=json.loads((HERE/'attempt-02/fixtures-supervision-v1.json').read_text())
    assert stage['owned_child_terminal_wait_reaped'] is True and stage['exit_code']==1
    assert stage['rss_samples'] and (HERE/'attempt-02/fixtures-outcome-v1.json').exists() is False
    stderr=(HERE/'attempt-02/fixtures-stderr-v1.txt').read_text()
    assert 'line 280' in stderr and 'AssertionError' in stderr
    preserved={}
    candidates=previous['sources']+previous['inputs']+previous['preserved_files']
    candidates += [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and
                   ('attempt02' in p.name or p.name in ('plan-attempt-02.json','freeze-attempt-02.json','full-language-design-v1.json')
                    or p.name.startswith('hilbert_cluster_full'))]
    candidates += [pin(p) for p in sorted((HERE/'attempt-02').iterdir()) if p.is_file()]
    for p in candidates:
        actual=pin(ROOT/p['path'])
        if actual!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('old evidence mismatch')
        if p['path'] in preserved and preserved[p['path']]!=actual:raise ValueError('ambiguous old pin')
        preserved[p['path']]=actual
    causal={'status':'source_only_causal_diagnosis_of_attempt02_combined_assertion',
        'bindings':[pin(HERE/'hilbert_cluster_fixtures_attempt02_v1.py'),pin(HERE/'hilbert_cluster_lifecycle_v1.py'),
                    pin(HERE/'attempt-02/fixtures-stderr-v1.txt')],
        'observed':'Combined status/restoration assertion at fixture line280 failed; no actual unknown result or partial fixture outcome was serialized.',
        'source_chain':['initial snapshot saved at line275; zero-budget result comparison passes before line277',
                        'snapshot(line277) calls compare(control)',
                        'compare exhausts control.ordered(decision)',
                        'ordered calls control.resync and increments trailed hint revision',
                        'the next solve checkpoints that new call-entry state, yet old assertion compared to earlier initial revision'],
        'repair':'Refresh initial after the inspection snapshot; separately assert unknown status and exact actual call-entry restoration. Save before/after/result/events on either failure.',
        'kernel_semantics_changed':False,'runtime_diagnostic_executed':False,
        'remaining_test':'Fresh bounded run and separate independent audit must determine actual status/restoration; source diagnosis is not a successful fixture receipt.'}
    causepath=HERE/'attempt02-causal-diagnosis-v1.json'
    if causepath.exists():raise ValueError('immutable causal note exists')
    causepath.write_text(json.dumps(causal,indent=2)+'\n')
    diffs=[]
    for kind in ('fixtures','run','outer'):
        old=HERE/('hilbert_cluster_'+kind+'_attempt02_v1.py')
        new=HERE/('hilbert_cluster_'+kind+'_attempt03_v1.py')
        out=HERE/(new.stem+'-diff.txt')
        if out.exists():raise ValueError('immutable repair diff exists')
        out.write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),
                                                 fromfile=old.name,tofile=new.name)))
        diffs.append(pin(out))
    sources=[HERE/'hilbert_cluster_lifecycle_v1.py']+sorted(HERE.glob('hilbert_cluster*_attempt03_v1.py'))
    for p in sources:ast.parse(p.read_text(),filename=str(p))
    output=HERE/'attempt-03';output.mkdir(exist_ok=False)
    inputs=previous['inputs']+[
        {'role':'frozen_attempt02_plan',**pin(HERE/'plan-attempt-02.json')},
        {'role':'second_failed_supervision',**pin(HERE/'attempt-02/fixtures-supervision-v1.json')},
        {'role':'second_failed_full_lifetime',**pin(HERE/'attempt-02/fixtures-lifetime-v1.json')},
        {'role':'fixture_failure_causal_diagnosis',**pin(causepath)}]
    plan={'version':'hilbert-whole-cluster-tiny-attempt03-fixture-baseline-repair',
        'status':'frozen_source_ready_root_and_independent_review_before_one_escalated_owned_dispatch',
        'sources':[pin(p) for p in sources],'inputs':inputs,
        'preserved_files':[preserved[k] for k in sorted(preserved)],'diffs':diffs,
        'parent_plan':pin(HERE/'plan-attempt-02.json'),'causal_note':pin(causepath),
        'repair':'Refresh expected parent immediately after snapshot-driven hint resync; split unknown status/restoration assertions and preserve actual diagnostics. Kernel/body/point/lifecycle/scheduler/fallback semantics unchanged.',
        'producer_limits':{'cumulative_outer_wall_seconds':60,'child_alarm_seconds':50,'supervisor_seconds':55,
                          'host_bytes':536870912,'execution_authorized_by_this_freeze':False},
        'output_directory':str(output.relative_to(ROOT)),
        'preserved_unknown_work':{'first_seconds':lifetimes[0]['full_supervisor_process_seconds_including_receipt_write'],
            'second_seconds':lifetimes[1]['full_supervisor_process_seconds_including_receipt_write'],
            'cumulative_prior_seconds':sum(x['full_supervisor_process_seconds_including_receipt_write'] for x in lifetimes),
            'first_reason':'sandbox metadata PermissionError, owned child killed/reaped -9, no outcome',
            'second_reason':'combined fixture assertion, owned child exit1/reaped, no outcome; not theorem invalidity',
            'first_peak_bytes':lifetimes[0]['conservative_host_peak_bytes'],
            'second_peak_bytes':lifetimes[1]['conservative_host_peak_bytes']},
        'cost_scope':'Within-process supervisor/outer durations charged, old authoring clarification retained. Unexported scan/order/rollback counter caveat remains.',
        'scientific_counts':'11 fixture groups and64 formula states remain predictions until complete outcome and independent audit.',
        'native_queries':0,'actual_model_executions':0,'actual_geometry_target_searches':0,'new_RL_training':False,
        'attempt03_executions':0,'source_syntax':'ast.parse only, no scientific import/run',
        'freeze_seconds_before_plan_write':time.perf_counter()-start}
    dest.write_text(json.dumps(plan,indent=2)+'\n')
    receipt={'status':'attempt03_baseline_repair_frozen_without_execution','plan':pin(dest),
             'sources':len(sources),'inputs':len(inputs),'preserved':len(preserved),
             'freeze_seconds_before_receipt_write':time.perf_counter()-start,'attempt03_executions':0}
    (HERE/'freeze-attempt-03.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
