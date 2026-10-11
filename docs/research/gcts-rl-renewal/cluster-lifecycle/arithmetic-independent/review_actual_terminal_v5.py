"""Read terminal artifacts only: no loader, graph checker or replay execution."""
import hashlib
import json
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / '.gcts-active/stochastic-replay-memory-v5-20261011'
OUT = Path(__file__).resolve().parent


def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(65536), b''): h.update(b)
    return dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=h.hexdigest())


def main():
    start = time.perf_counter()
    pp = D/'evaluation-plan-v5-attempt-02.json'; plan = json.loads(pp.read_bytes())
    fp = D/'evaluation-v5/phase-receipt-attempt-02.json'; phase = json.loads(fp.read_bytes())
    ap = ROOT/plan['root_activation_path']; activation = json.loads(ap.read_bytes())
    assert activation['plan_sha256'] == phase['plan_sha256'] == pin(pp)['sha256']
    assert activation['status'] == 'authorized_by_root_after_independent_review'
    for p,h in activation['prerequisite_sha256'].items(): assert pin(ROOT/p)['sha256'] == h
    verified = {}
    for section in ('source_sha256', 'input_sha256'):
        for p,h in plan[section].items():
            verified[p] = pin(ROOT/p)
            assert verified[p]['sha256'] == h, p
    assert phase['status'] == 'unknown_loading_phase_resource_budget'
    assert phase['attempted'] == ['base-r1', 'untrained-r1']
    assert phase['failed'] == ['untrained-r1']
    assert phase['unexecuted'] == ['trained-r1', 'trained-r2', 'untrained-r2', 'base-r2']
    assert len(phase['observations']) == 2
    findings = []
    artifact_pins = []
    expected = [('base-r1',124903546,'35325a229b8282ba22e0cceea66128641a037f166de2335af890d53eafbb005d',0,0,0,441925632),
        ('untrained-r1',130293777,'cf9c119d426e0b3bac2cd1e286dcac9431053da4304c1b8e1ede86ec7c0cf29f',411,357,221,626147328)]
    for observed, exp, job in zip(phase['observations'], expected, plan['jobs']):
        name,n,h,events,hints,changes,peak = exp
        assert job['job'] == name
        rp = ROOT/job['output_path']; lp = rp.parent/(name+'-lifetime.json')
        r=json.loads(rp.read_bytes()); l=json.loads(lp.read_bytes())
        assert r == observed['receipt'] and l == observed['lifetime']
        assert pin(rp)['sha256'] == l['receipt_sha256']
        assert r['job'] == l['job'] == name and r['plan_sha256'] == job['plan_sha256']
        assert l['exit_code'] == 0 and l['terminal_and_reaped'] is True and l['failure'] is None
        assert l['conservative_owner_plus_worker_peak_bytes'] == peak == l['kernel_fresh_worker_peak_bytes']+l['kernel_owner_peak_bytes']
        assert l['full_worker_seconds'] <= 120 and r['seconds_before_receipt_write'] <= 115
        gate=r['complete_original_trace_byte_correspondence']
        assert gate['status']=='passed_complete_original_compact_json_byte_correspondence'
        assert gate['bytes']==n and gate['original_uncompressed_sha256']==gate['emitted_sha256']==h
        tree=r['tree']; metrics=tree['metrics']
        assert tree['status']=='unknown_search_budget' and tree['nodes']==metrics['nodes']==5001
        assert tree['policy_events']==events and tree['hints']==hints and tree['executed_changed_first_branches']==changes
        assert metrics['attempts']==5000 and metrics['max_satisfied_points']==45
        assert metrics['forced']==3249 and metrics['branch']==620 and metrics['dead']==1132
        assert r['searches']==r['training_episodes']==r['native_queries']==0
        if name=='base-r1':
            assert r['status']=='passed_complete_actual_graph_rng_and_policy_replay'
            assert l['status']=='passed_owned_loading_worker_lifetime' and peak<=536870912
        else:
            assert r['status']=='unknown_independent_replay_resource_budget'
            assert l['status']=='unknown_or_failed_owned_loading_worker_lifetime' and peak>536870912
            assert l['memory_overshoot_bytes']==peak-536870912==89276416
        artifact_pins.extend((pin(rp),pin(lp)))
        findings.append(dict(job=name, worker_status=r['status'], lifetime_status=l['status'],
            full_original_bytes=n, original_sha256=h, nodes=5001, recorded_policy_events=events,
            recorded_hints=hints, recorded_changed_first_branches=changes,
            owned_seconds=l['full_worker_seconds'], conservative_peak_bytes=peak,
            resource_qualification=(name=='base-r1')))
    failed=D/'evaluation-v5/phase-receipt.json'; old=json.loads(failed.read_bytes())
    assert pin(failed)['sha256']=='407362a7bc3811e953ed4a1da940f060be8fd2ef4934737bb83b45eaaa906f99'
    assert old['attempted']==[] and old['unexecuted']==[j['job'] for j in plan['jobs']]
    assert abs(old['seconds_before_phase_receipt_write']-.078432542)<1e-9
    helper=11.494624209; previous=226.739085292; elapsed=115.89094675; cumulative=354.124656251
    assert phase['helper_phase_seconds_already_charged']==helper
    assert phase['historical_failed_audit_seconds']==previous
    assert phase['seconds_before_phase_receipt_write']==elapsed
    assert abs(previous+helper+elapsed-cumulative)<1e-8
    assert phase['cumulative_audit_seconds_before_phase_receipt_write']==cumulative
    assert phase['conservative_owner_plus_worker_peak_bytes']==626147328
    assert phase['original_cumulative_audit_seconds']==780
    assert phase['searches']==phase['training_episodes']==phase['native_queries']==0
    receipt=dict(status='passed_independent_v5_terminal_reconciliation_partial_resource_unknown',
        phase=pin(fp),plan=pin(pp),activation=pin(ap),exact_receipt_pins=artifact_pins,
        prior_activation_failure=pin(failed),source_pins_verified=len(plan['source_sha256']),
        input_pins_verified=len(plan['input_sha256']),observations=findings,
        phase_seconds=elapsed, cumulative_audit_seconds=cumulative, remaining_original_seconds=780-cumulative,
        whole_phase_resource_status='unknown; second worker exceeds unchanged 512 MiB, remaining four unexecuted',
        conclusions=[
            'Base-r1 all 5001 nodes and complete original-byte/semantic checks are qualified by its passed 441925632-byte owned gate.',
            'Untrained-r1 full byte and semantic records remain inspectable but resource qualification fails at 626147328 bytes; its 221 recorded changed branches are not a passed whole evaluation audit.',
            'Both original searches remain unknown after 5000 attempts; this phase performs replay only, not search/training/native proof discovery.',
            'Four actual audits remain unexecuted, although all six original search producers completed previously.',
            'Missing-activation launch remains separate immutable infrastructure evidence and its 0.078432542 seconds remains charged.',
            'Resource memory gate is retrospective after wait4; no hard OS cap, RSS sampling, descendants or full mathematical proof-gain claim.',
            'Source preparation/manual review and final receipt writes are excluded from measured owner clocks and not represented as total research cost.',
        ],metadata_review_seconds_before_receipt_write=time.perf_counter()-start,
        engine_imports=0, loads_or_replays_executed=0, searches=0, native_queries=0)
    out=OUT/'actual-terminal-review-v5.json'
    with out.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps({'receipt':pin(out),'status':receipt['status'],'remaining':780-cumulative}))


if __name__=='__main__':main()
