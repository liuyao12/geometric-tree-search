"""Prospective separately ROOT-activated independent actual fixture replay.

No scientific imports at module load. The actual source plan is finalized only
after the producer has terminal/reaped ROOT evidence. No fixture/model/search,
policy import, arithmetic or replay has been executed by this source author.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time


def pin(path, root):
    path = Path(path).resolve(); raw = path.read_bytes()
    return dict(path=str(path.relative_to(root)) if root in path.parents else str(path),
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def verify(record, root):
    path = Path(record['path']); path = path if path.is_absolute() else root / path
    observed = pin(path, root)
    if any(observed[k] != record[k] for k in ('sha256', 'bytes')):
        raise ValueError('immutable source/input/runtime changed: ' + record['path'])
    return path


def load(record, root, name):
    spec = importlib.util.spec_from_file_location(name, verify(record, root))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def actual_resource_inputs(roles, root, plan):
    lifetime = json.loads(verify(roles['actual_fixture_owned_lifetime'], root).read_text())
    outer = json.loads(verify(roles['actual_fixture_ROOT_terminal'], root).read_text())
    expected_plan = {k: roles['actual_fixture_plan'][k] for k in ('path', 'sha256', 'bytes')}
    expected_result = {k: roles['actual_fixture_result'][k] for k in ('path', 'sha256', 'bytes')}
    expected_lifetime = {k: roles['actual_fixture_owned_lifetime'][k] for k in ('path', 'sha256', 'bytes')}
    if (lifetime['schema'] != 'owned-real-Controller-overlay-fixture-lifetime-v1'
            or lifetime['plan'] != expected_plan or lifetime['result'] != expected_result
            or lifetime['resource_gate_before_final_receipt'] is not True
            or lifetime['worker_terminal_reaped'] is not True or lifetime['worker_exit_code'] != 0
            or lifetime['forced_kill'] is not False or lifetime['streams_open_after_reap'] is not False
            or lifetime['remaining_owned_pids'] != [] or lifetime['failure'] is not None
            or lifetime['child_lifetime_including_imports_serialization_and_reaping_seconds'] > 25
            or lifetime['supervisor_seconds_before_final_receipt'] > 30
            or lifetime['conservative_combined_peak_bytes'] > 536870912):
        raise ValueError('complete producer owned lifetime did not qualify')
    if (outer['schema'] != 'ROOT-actual-real-Controller-overlay-fixture-terminal-v1'
            or outer['source_plan_pin'] != expected_plan or outer['result_pin'] != expected_result
            or outer['owned_lifetime_pin'] != expected_lifetime or outer['full_resource_accepted'] is not True
            or outer['owner_exit_code'] != 0 or outer['owner_terminal_reaped'] is not True
            or outer['worker_terminal_reaped'] is not True or outer['full_owner_lifetime_seconds'] > 60
            or outer['conservative_combined_peak_bytes'] > 536870912):
        raise ValueError('ROOT producer full lifetime including final serialization/reap did not qualify')
    return dict(owned_lifetime=expected_lifetime, ROOT_terminal={k: roles['actual_fixture_ROOT_terminal'][k]
        for k in ('path', 'sha256', 'bytes')}, complete_producer_resource_accepted=True,
        own_replay_full_ROOT_resource_acceptance_still_required=True)


def mutation_controls(replay, result, corpus, bindings):
    """Actually call the independent auditor on changed saved transcripts later.

    These controls are unexecuted source today; no expected-rejection booleans
    are used as evidence without a future activated function invocation.
    """
    edits = [
        ('missing-scenario', lambda d: d['scenarios'].pop()),
        ('missing-terminal-operation', lambda d: d['scenarios'][0]['events'].pop()),
        ('wrong-whole-aggregate', lambda d: d['scenarios'][0]['descriptors'][0]['aggregate_m'].append([1, 5, 0])),
        ('lost-complete-domain-key', lambda d: d['scenarios'][0]['events'][0]['after']['complete_domains'][1].pop()),
        ('changed-controller-hint', lambda d: d['scenarios'][0]['events'][0]['after']['overlay']['controller']['hint_states'][0].update(status='consumed')),
        ('changed-menu-vector', lambda d: d['scenarios'][0]['events'][1]['result']['menu']['feature_vectors'][0].update(bias=0.25)),
        ('disabled-draw-flag', lambda d: d['scenarios'][0]['events'][2]['payload']['prepared'].update(needs_one_draw=False)),
        ('wrong-policy-probability', lambda d: d['scenarios'][0]['events'][2]['result'][1]['policy']['distribution']['probabilities'].__setitem__(0, 0.0)),
        ('wrong-mixture-gradient', lambda d: d['scenarios'][0]['events'][2]['result'][1]['policy']['score_gradient']['gradient'].update(null=0.0)),
        ('pending-output-as-fact', lambda d: next(s for s in d['scenarios'] if s['id']=='pending-source-not-fact')['events'][4]['result'].update(fact_potential=1)),
        ('broken-paired-overlay-rollback', lambda d: next(s for s in d['scenarios'] if s['id']=='paired-rollback')['terminal']['overlay'].update(overlay_revision=999)),
        ('unknown-creates-exclusion', lambda d: next(s for s in d['scenarios'] if s['id']=='unknown-no-exclusion')['terminal']['overlay']['controller']['graph']['excluded'][1].append([0, 1, []])),
    ]
    receipts = []
    for name, mutate in edits:
        changed = copy.deepcopy(result); mutate(changed)
        try:
            replay.audit(changed, corpus, bindings)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            receipts.append(dict(id=name, actual_independent_rejection=True,
                                 reason=type(exc).__name__ + ': ' + str(exc)))
        else:
            raise ValueError('independent gate accepted an actual malformed saved transcript: ' + name)
    return receipts


def main():
    root = Path(__file__).resolve().parents[2]
    plan_path = Path(sys.argv[1]).resolve(); plan = json.loads(plan_path.read_text())
    activation = json.loads((root / plan['activation_path']).read_text())
    if (activation.get('schema') != 'ROOT-independent-real-Controller-overlay-replay-activation-v1'
            or activation.get('authorized') is not True or activation.get('plan') != pin(plan_path, root)):
        raise ValueError('separate exact ROOT replay activation required')
    for record in plan['sources'] + plan['inputs'] + plan['preserved']:
        verify(record, root)
    verify(plan['runtime']['binary'], root); verify(plan['runtime']['observer'], root)
    if Path(sys.executable).resolve() != Path(plan['runtime']['binary']['path']).resolve():
        raise ValueError('pinned Python runtime required')
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('independent fixture deadline')))
    signal.alarm(plan['limits']['child_seconds']); began = time.monotonic()
    roles = {record['role']: record for record in plan['inputs'] if 'role' in record}
    resources = actual_resource_inputs(roles, root, plan)
    for name in ('independent_fixture_points_v1', 'independent_fixture_whole_v1',
                 'independent_features_v1', 'independent_policy_v1'):
        load(next(r for r in plan['sources'] if Path(r['path']).stem == name), root, name)
    replay = load(next(r for r in plan['sources'] if Path(r['path']).stem == 'independent_fixture_replay_v1'), root,
                  'independent_fixture_replay_v1')
    corpus = json.loads(verify(roles['fixture_corpus'], root).read_text())
    raw = json.loads(verify(roles['actual_fixture_result'], root).read_text())
    fixture_plan = json.loads(verify(roles['actual_fixture_plan'], root).read_text())
    bindings = [{k: r[k] for k in ('path', 'sha256', 'bytes')} for r in fixture_plan['inputs']]
    result = replay.audit(raw, corpus, bindings)
    result.update(actual_mutation_controls=mutation_controls(replay, raw, corpus, bindings),
        actual_result_pin={k: roles['actual_fixture_result'][k] for k in ('path','sha256','bytes')},
        actual_resource_inputs=resources, owned_resource_accepted=False,
        full_ROOT_outer_clock_qualified=False, worker_pid=os.getpid(),
        worker_compute_before_final_serialization_seconds=time.monotonic()-began,
        plan_pin=pin(plan_path, root), execution_owner='ROOT')
    with (root / plan['outputs']['result']).open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    signal.alarm(0)


if __name__ == '__main__': main()
