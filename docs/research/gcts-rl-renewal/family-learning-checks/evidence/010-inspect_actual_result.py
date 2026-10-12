"""Independent ROOT inspection of saved numeric evidence, no policy imports."""
import hashlib
import json
import math
from pathlib import Path
import time

SOURCE = Path('.gcts-active/family-proposal-learning-numeric-source-20261012')
OUT = Path('.gcts-active/family-numeric-actual-progress-20261012')

def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def close(a, b):
    assert math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-12), (a, b)

def main():
    started = time.monotonic()
    plan = json.loads((SOURCE/'owner-plan-v1.json').read_text())
    result_path = SOURCE/'numeric-output-v2/result.json'
    owner_path = SOURCE/'owned-output-v1/owned-lifetime.json'
    outer_path = OUT/'outer-terminal-v1.json'
    result = json.loads(result_path.read_text())
    owner = json.loads(owner_path.read_text())
    outer = json.loads(outer_path.read_text())
    assert owner['worker_result'] == pin(result_path)
    assert outer['owner_receipt'] == pin(owner_path)
    assert [c['id'] for c in result['controls']] == plan['expected_control_ids']
    assert len(result['controls']) == 26 and all(c['status']=='passed' for c in result['controls'])
    assert result['numeric_fixture_worker_runs'] == 1 and result['policy_numeric_functions_executed'] is True
    assert all(result[k] == 0 for k in ('production_engine_runs','search_runs','training_runs','random_draws_generated'))
    assert result['runtime_adapter_implemented'] is False
    assert outer['status']=='passed_complete_numeric_fixture_lifecycle'
    assert outer['same_PID_terminal_and_reaped'] and outer['exit_code']==0 and not outer['forced_kill']
    assert outer['full_seconds_including_owner_final_serialization_and_reaping'] <= 30
    assert outer['conservative_combined_peak_bytes'] <= 536870912
    assert owner['resource_gate_passed'] and owner['numeric_and_abstract_contract_gate_passed']
    assert owner['worker_terminal_and_reaped_same_PID'] and owner['worker_exit_code']==0
    assert owner['remaining_owned_pids']==[] and owner['cleaned_verified_orphan_pids']==[]
    controls = {c['id']: c['detail'] for c in result['controls']}
    cases = []
    for key, detail in controls.items():
        if not key.startswith('mixture_case:'):
            continue
        d=detail['distribution']; f=d['features']; w=d['weights']; names=d['feature_names']
        assert d['action_ids']==['A','B','NULL']
        logits=[sum(w.get(n,0)*x.get(n,0) for n in names)/d['temperature'] for x in f]
        raw=[math.exp(x-max(logits)) for x in logits]; q=[x/sum(raw) for x in raw]
        p=[(1-d['epsilon'])*x+d['epsilon']/len(raw) for x in q]
        for a,b in zip(d['softmax'],q): close(a,b)
        for a,b in zip(d['probabilities'],p): close(a,b)
        for i, gradient in enumerate(detail['gradients']):
            for n in names:
                expectation=sum(q[j]*f[j].get(n,0) for j in range(len(f)))
                expected=(1-d['epsilon'])*q[i]/p[i]/d['temperature']*(f[i].get(n,0)-expectation)
                close(gradient[n],expected)
        assert detail['finite_derivatives']==6 and detail['draws_per_case']==4
        cases.append(key)
    assert len(cases)==6
    assert controls['plain_softmax_gradient_mutant_detected']['detected'] is True
    clipped=controls['advantage_before_direction_clip']
    for key,expected in [('advantage',2),('advantage_direction_L2_before_clip',10),('clip_scale',.1),('baseline',.4)]: close(clipped[key],expected)
    close(clipped['weights']['a'],.03);close(clipped['weights']['b'],.04)
    overlay=controls['abstract_overlay_contract_not_engine_conformance']
    assert all(overlay[k] is True for k in ('NULL_suppresses_fixed_priority','complete_fallback_preserved','paired_active_and_view_restored','original_catalog_unchanged','two_contract_mutants_distinguished'))
    disposition={'status':'passed_ROOT_independent_saved_numeric_result_inspection',
                 'inputs':[pin(p) for p in (result_path,owner_path,outer_path,SOURCE/'owner-plan-v1.json')],
                 'ordered_controls':26,'independently_recomputed_mixtures':6,'independently_recomputed_gradient_components':36,
                 'worker_reported_finite_differences':36,'worker_reported_deterministic_draws':24,
                 'scope':'Saved scalar outputs and ownership inspected; no policy reimport, new fixture run, engine, actual Controller, training or search.',
                 'inspection_seconds_before_serialization':time.monotonic()-started,
                 'actual_numeric_fixture_accepted':True,'actual_RL_training_runs':0}
    with (OUT/'actual-numeric-disposition-v1.json').open('x') as stream:
        json.dump(disposition,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(disposition))

if __name__=='__main__': main()
