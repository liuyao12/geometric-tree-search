"""Metadata-only source freezer: hashes/AST/JSON, no learning imports or calls.

Executing this utility does NOT activate or dispatch its prospective owner.
All outputs are exclusive; no original V1 file is replaced.
"""
import ast
import hashlib
import json
from pathlib import Path
import resource
import time

FOLDER = Path('.gcts-active/family-proposal-learning-numeric-source-20261012')
PRIOR = Path('.gcts-active/family-proposal-learning-20261012')


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def save(name, data):
    path = FOLDER / name
    with path.open('x', encoding='utf-8') as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write('\n')
    return path


def main():
    begin = time.perf_counter()
    for manifest in (FOLDER / 'integration-v1.json', PRIOR / 'integration.json', PRIOR / 'integration-v2.json'):
        for record in json.loads(manifest.read_text())['files']:
            if pin(Path(record['path'])) != record:
                raise ValueError('preserved source mismatch: ' + record['path'])
    alias = Path('/Library/Developer/CommandLineTools/usr/bin/python3')
    resolved = alias.resolve()
    expected_sha = 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    alias_pin = pin(alias); resolved_pin = pin(resolved)
    if any(record['sha256'] != expected_sha or record['bytes'] != 102352
           for record in (alias_pin, resolved_pin)):
        raise ValueError('ROOT-declared Python runtime mismatch')
    runtime = {'alias_pin': alias_pin, 'resolved_pin': resolved_pin,
               'observer_pin': pin(Path('/bin/ps')), 'expected_version': [3, 9],
               'platform': 'darwin', 'kernel_ru_maxrss_unit': 'bytes'}
    runner = FOLDER / 'numeric_gate_v2.py'
    owner = FOLDER / 'owned_numeric_gate_v1.py'
    freezer = FOLDER / 'freeze_numeric_owner_v1.py'
    for source in (runner, owner, freezer):
        ast.parse(source.read_text(), filename=str(source), feature_version=(3, 9))
    old_plan = json.loads((FOLDER / 'numeric-plan-v1.json').read_text())
    worker_plan = dict(old_plan)
    worker_plan['schema'] = 'family_learning_numeric_gate_plan_v2'
    worker_plan['preserved_V1_plan'] = pin(FOLDER / 'numeric-plan-v1.json')
    worker_plan['metadata_successor_diff'] = pin(FOLDER / 'numeric_gate_v2.diff')
    worker_plan['sources'] = [pin(runner)] + old_plan['sources'][1:]
    worker_plan['prospective_output'] = str(FOLDER / 'numeric-output-v2')
    worker_plan['required_outer_owner'] = str(owner) + ': separately ROOT-activated; one functional child plus bounded separately owned ps accounting commands.'
    worker_plan['execution_reporting'] = 'After actual worker invocation report numeric_fixture_worker_runs=1 and policy_numeric_functions_executed when invocation starts; production_engine/search/training runs remain zero. Before dispatch this plan is source-only.'
    worker_plan['prospective_command'] = [str(alias), '-B', str(runner), '--plan',
                                        str(FOLDER / 'numeric-plan-v2.json'), '--activation',
                                        str(FOLDER / 'owned-output-v1/worker-activation.json'),
                                        '--output', worker_plan['prospective_output']]
    worker_plan_path = save('numeric-plan-v2.json', worker_plan)
    expected_ids = [
        'python39_deferred_annotation_import',
        'mixture_case:epsilon0_temp05', 'mixture_case:epsilon01_temp1',
        'mixture_case:epsilon035_temp2', 'mixture_case:epsilon1_uniform',
        'mixture_case:zero_weights', 'mixture_case:duplicate_vectors',
        'plain_softmax_gradient_mutant_detected',
        'stable_extreme_logits:0.0', 'stable_extreme_logits:0.2',
        'synthetic_last_positive_roundoff_fallback',
        'malformed_probability_rejected:negative_normalized',
        'malformed_probability_rejected:nan', 'malformed_probability_rejected:plus_infinity',
        'malformed_probability_rejected:minus_infinity', 'malformed_probability_rejected:bool',
        'malformed_probability_rejected:string', 'malformed_probability_rejected:empty',
        'malformed_probability_rejected:nonsequence', 'malformed_probability_rejected:unnormalized',
        'advantage_before_direction_clip', 'old_baseline_before_update_then_EMA',
        'empty_executed_episode_changes_only_EMA', 'unexecuted_episode_cannot_update',
        'reward_counter_arithmetic_only', 'abstract_overlay_contract_not_engine_conformance',
    ]
    sources = worker_plan['sources'] + [pin(owner), pin(freezer)]
    input_paths = [worker_plan_path, FOLDER / 'numeric-plan-v1.json',
                   FOLDER / 'numeric-protocol-v1.json', FOLDER / 'integration-v1.json',
                   FOLDER / 'numeric_gate_v2.diff', PRIOR / 'protocol-v2.json',
                   PRIOR / 'integration.json', PRIOR / 'integration-v2.json']
    plan = {
        'schema': 'owned_family_learning_numeric_gate_plan_v1',
        'status': 'immutable_source_only_not_activated',
        'scope': 'One actual numeric fixture worker when separately ROOT activated; abstract selection-overlay contract only. No production graph/engine/search/training/native/replay/UI; no learned policy or Controller conformance claim.',
        'worker': str(runner), 'worker_plan': pin(worker_plan_path),
        'sources': sources, 'inputs': [pin(path) for path in input_paths],
        'runtime': runtime,
        'limits': {'functional_workers': 1, 'no_retry': True, 'internal_seconds': 10.0,
                   'owned_seconds': 15.0, 'whole_phase_seconds': 30.0,
                   'memory_bytes': 536870912, 'worker_stream_bytes': 65536,
                   'observer_seconds': 0.5, 'observer_stream_bytes': 262144,
                   'maximum_observer_commands': 256, 'artifact_bytes': 1048576},
        'numeric_output': worker_plan['prospective_output'],
        'owned_output': str(FOLDER / 'owned-output-v1'),
        'expected_control_ids': expected_ids,
        'required_activation': {
            'scope': 'root_authorized_owned_numeric_fixture_only',
            'plan': 'Exact owner-plan-v1.json path/SHA/bytes',
            'source_pins': 'Exact ordered owner plan.sources records',
            'runtime': 'Exact owner plan.runtime object'},
        'prospective_command': [str(alias), '-B', str(owner), '--plan',
                                str(FOLDER / 'owner-plan-v1.json'), '--activation',
                                str(FOLDER / 'owner-activation-v1.json')],
        'ownership': 'Only the one owned unreaped functional child session may be signaled. Every ps observer has its own PID wait4/reaping/streams. After functional leader reaping, orphan cleanup is limited to saved PID plus observed birth matches; no historical group/growth.',
        'resource_accounting': 'Full functional lifecycle includes import/hash/setup/final result serialization/cleanup/reaping. MacOS kernel owner+worker+maximum observer peaks conservatively summed; complete process-tree RSS samples include current observer. Unexpected worker descendants or observer failures force unknown. Final owner receipt writing excluded and disclosed.',
        'output_and_failure_scope': 'Exclusive functional and owned outputs; bounded stdout/stderr retained on nonzero/signal/timeout. Numeric partial/result files bounded before loading. Malformed/missing worker result, stream overflow, failed observation/cleanup/resource gate retain an unknown/failed owned receipt. Before-activation/pin errors launch no child and remain ROOT external terminal metadata; no restart.',
        'acceptance': 'Same owned PID terminal/reaped, exit0; exact ordered26 control IDs passed; actual numeric invocation reported; no engine/search/training; source/runtime pins exact; every owned/phase/memory/stream gate passes; independent source/numeric review. Abstract overlay remains not actual Controller conformance.',
        'preparation_scope': 'This freezer performs hashes, AST and JSON only. No policy function/import, numeric fixture, RNG, model, engine, training, search, replay or native execution.',
        'authoring_seconds': None, 'root_sole_dispatch_and_publication': True,
    }
    owner_plan = save('owner-plan-v1.json', plan)
    interval = time.perf_counter() - begin
    readiness = save('owner-readiness-v1.json', {
        'status': 'immutable_owned_numeric_entrypoint_source_ready_not_executed',
        'owner_plan': pin(owner_plan), 'worker_plan': pin(worker_plan_path),
        'owner_source': pin(owner), 'worker_source': pin(runner),
        'metadata_freezer': pin(freezer), 'runtime': runtime,
        'Python39_AST_parsed_sources': 3, 'policy_functions_imported_or_executed': 0,
        'numeric_fixture_runs': 0, 'RNG_calls': 0, 'engine_search_training_native_replay_runs': 0,
        'source_authoring_seconds': None, 'metadata_helper_interval_seconds': interval,
        'metadata_helper_interval_scope': 'Preserved pins/runtime hashes/three ASTs and exclusive worker/owner plan serialization; excludes interpreter startup and final readiness/manifest writes.',
        'metadata_helper_kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'runtime_adapter_implemented': False, 'actual_owner_started': False,
    })
    paths = [runner, FOLDER / 'numeric_gate_v2.diff', owner, freezer,
             worker_plan_path, owner_plan, readiness]
    integration = save('integration-owned-v1.json', {
        'status': 'immutable_source_only_owned_numeric_gate_successor',
        'files': [pin(path) for path in paths], 'total_files': len(paths),
        'total_bytes': sum(path.stat().st_size for path in paths),
        'preserved_V1_manifest': pin(FOLDER / 'integration-v1.json'),
        'numeric_fixture_runs': 0, 'root_sole_actual_owner_and_publisher': True,
        'no_old_source_report_PUB_changes': True,
    })
    print(json.dumps({'integration': pin(integration), 'plan': pin(owner_plan),
                      'readiness': pin(readiness), 'metadata_seconds': interval}, indent=2))


if __name__ == '__main__':
    main()
