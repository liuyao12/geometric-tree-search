"""SOURCE ONLY metadata finalizer; ROOT may call after actual producer completion.

No model/result decoding, imports of scientific modules, fixture or replay. A
future actual plan binds exact producer bytes and ROOT normalized source/terminal
evidence. Absent inputs produce no plan; no placeholder hashes or output pins.
"""
import hashlib
import json
from pathlib import Path
import sys


def pin(path, root):
    path = Path(path).resolve(); raw = path.read_bytes()
    return dict(path=str(path.relative_to(root)) if root in path.parents else str(path),
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def absolute(path, root):
    path = Path(path)
    return path if path.is_absolute() else root / path


def main():
    root = Path(__file__).resolve().parents[2]; here = Path(__file__).resolve().parent
    if len(sys.argv) != 3:
        raise ValueError('pass actual ROOT normalized producer terminal and source-review file paths')
    source = json.loads((here / 'source-plan-v1.json').read_text())
    expected = {}
    for record in source['sources'] + source['inputs'] + source['preserved']:
        actual = pin(absolute(record['path'], root), root)
        if any(actual[k] != record[k] for k in ('sha256', 'bytes')):
            raise ValueError('source freeze changed: ' + record['path'])
        if actual['path'] in expected and expected[actual['path']] != actual:
            raise ValueError('conflicting exact byte identity')
        expected[actual['path']] = actual
    fixture_plan_path = root / '.gcts-active/family-proposal-real-overlay-source-20261012/fixture-plan-v1.json'
    fixture_plan = json.loads(fixture_plan_path.read_text()); fixture_plan_pin = pin(fixture_plan_path, root)
    terminal_path, review_path = [absolute(arg, root) for arg in sys.argv[1:]]
    terminal, review = [json.loads(path.read_text()) for path in (terminal_path, review_path)]
    if (terminal['schema'] != 'ROOT-actual-real-Controller-overlay-fixture-terminal-v1'
            or terminal['source_plan_pin'] != fixture_plan_pin
            or terminal['full_resource_accepted'] is not True
            or terminal['owner_exit_code'] != 0 or terminal['owner_terminal_reaped'] is not True
            or terminal['worker_terminal_reaped'] is not True):
        raise ValueError('actual terminal/reaped ROOT-qualified producer evidence required')
    if (review['schema'] != 'ROOT-real-Controller-overlay-fixture-source-review-v1'
            or review['fixture_plan'] != fixture_plan_pin or review['source_review_passed'] is not True
            or review['full_sources_reviewed'] is not True):
        raise ValueError('exact ROOT full fixture/overlay/wrapper/owner source review required')
    result_path = root / fixture_plan['outputs']['result']
    lifetime_path = root / fixture_plan['outputs']['lifetime']
    result_pin, lifetime_pin = pin(result_path, root), pin(lifetime_path, root)
    if terminal['result_pin'] != result_pin or terminal['owned_lifetime_pin'] != lifetime_pin:
        raise ValueError('ROOT terminal does not bind these actual immutable output bytes')
    lifetime = json.loads(lifetime_path.read_text())
    if (lifetime['plan'] != fixture_plan_pin or lifetime['result'] != result_pin
            or lifetime['resource_gate_before_final_receipt'] is not True
            or lifetime['worker_terminal_reaped'] is not True or lifetime['worker_exit_code'] != 0):
        raise ValueError('producer actual complete owner receipt required')
    roles = {r['role']: r for r in source['inputs'] if 'role' in r}
    new_inputs = [dict(role=role, **record) for role, record in (
        ('actual_fixture_plan', fixture_plan_pin), ('actual_fixture_result', result_pin),
        ('actual_fixture_owned_lifetime', lifetime_pin), ('actual_fixture_ROOT_terminal', pin(terminal_path, root)),
        ('ROOT_fixture_source_review', pin(review_path, root)))]
    new_inputs += [dict(role=role, **{k: roles[role][k] for k in ('path', 'sha256', 'bytes')})
                   for role in ('fixture_corpus', 'owned_helpers', 'master_contract', 'AGENTS')]
    output = here / 'actual-replay-plan-v1.json'
    plan = dict(schema='ROOT-independent-real-Controller-overlay-replay-plan-v1',
        status='actual_producer_bytes_bound_requires_separate_ROOT_activation',
        sources=source['sources'], inputs=new_inputs,
        preserved=sorted(expected.values(), key=lambda r:r['path']), runtime=source['runtime'],
        activation_path=str((here/'root-actual-replay-activation-v1.json').relative_to(root)),
        worker_path=str((here/'independent_fixture_worker_v1.py').relative_to(root)),
        owner_path=str((here/'owned_independent_fixture_replay_v1.py').relative_to(root)),
        limits=dict(child_seconds=25, supervisor_seconds=30, whole_ROOT_phase_seconds=60,
            memory_bytes=536870912, artifact_bytes=33554432, maximum_observers=1200,
            observer_seconds=1.0, observer_stream_bytes=4194304, worker_stream_bytes=4194304),
        outputs=dict(directory=str((here/'owned-output-v1').relative_to(root)),
            result=str((here/'owned-output-v1'/'independent-result-v1.json').relative_to(root)),
            lifetime=str((here/'owned-output-v1'/'independent-lifetime-v1.json').relative_to(root))),
        expected_scenario_ids=fixture_plan['expected_scenario_ids'],
        actual_producer_resource_claim='ROOT outer terminal plus exact producer owned receipt, rechecked by worker',
        scope='Synthetic fixture state/domain/overlay/feature/math replay only; no donor DFS, RL training or mathematical proof',
        execution_authorized=False, ROOT_sole_actual_owner=True)
    for r in new_inputs:
        if any(pin(absolute(r['path'], root), root)[k] != r[k] for k in ('sha256','bytes')):
            raise ValueError('actual input changed during metadata finalization')
    with output.open('x') as stream:
        json.dump(plan, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(actual_replay_plan=pin(output,root), scientific_calls=0), indent=2))


if __name__ == '__main__': main()
