"""Metadata-only AST/hash/ZIP freeze; no scientific import or dispatch."""
import ast
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def pin(path, role=None):
    path = Path(path); raw = path.read_bytes()
    try: name = str(path.relative_to(ROOT))
    except ValueError: name = str(path)
    data = dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    if role is not None: data['role'] = role
    return data


def write_new(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def main():
    started = time.monotonic()
    predecessor = ROOT / '.gcts-active/family-proposal-rl-small-source-20261012'
    previous = json.loads((predecessor/'source-plan-v1.json').read_text())
    preserve = {}
    for record in previous['sources'] + previous['inputs'] + previous['preserved_sources_inputs']:
        actual = pin(ROOT / record['path'])
        expected = {k:record[k] for k in ('path','sha256','bytes')}
        if actual != expected: raise ValueError('predecessor immutable pin mismatch: '+record['path'])
        if record['path'] in preserve and preserve[record['path']] != actual:
            raise ValueError('conflicting predecessor source pin')
        preserve[record['path']] = actual
    for name in ('source-plan-v1.json','protocol-v1.json','donor-split-v1.json','integration-v1.json','readiness-v1.json'):
        actual = pin(predecessor/name); preserve[actual['path']] = actual
    source_names = ['overlay_successor_author_v2.py','family_learned_overlay_v2.py',
                    'real_overlay_fixture_worker_v1.py','owned_real_overlay_fixture_v1.py',
                    'freeze_real_overlay_fixture_v1.py']
    sources, asts = [], []
    for name in source_names:
        path = HERE/name
        ast.parse(path.read_text(), filename=str(path), feature_version=(3,9))
        sources.append(pin(path)); asts.append(dict(path=str(path.relative_to(ROOT)), parse='Python3.9_AST_only'))
    roles = {
        'unchanged_core': ROOT/'.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py',
        'unchanged_lifecycle': ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011/hilbert_cluster_lifecycle_v1.py',
        'frozen_features': predecessor/'family_graph_features_v1.py',
        'frozen_math': ROOT/'.gcts-active/family-proposal-learning-20261012/family_policy_math_v2.py',
        'overlay_successor': HERE/'family_learned_overlay_v2.py',
        'fixture_corpus': HERE/'real_overlay_fixture_corpus_v1.json',
        'protocol': HERE/'protocol-v1.json',
        'source_diff': HERE/'overlay-v1-to-v2.diff',
        'frozen_curriculum_split': predecessor/'donor-split-v1.json',
        'frozen_RL_protocol': predecessor/'protocol-v1.json',
        'owned_helpers': ROOT/'.gcts-active/family-proposal-learning-numeric-source-20261012/owned_numeric_gate_v1.py',
        'AGENTS': ROOT/'AGENTS.md',
        'master_contract': ROOT/'docs/basic-tiling-algorithm.md'
    }
    inputs = [pin(path,role) for role,path in roles.items()]
    for name in ('fixture_corpus','protocol'):
        json.loads(roles[name].read_text())
    corpus = json.loads(roles['fixture_corpus'].read_text())
    if len(corpus['scenario_order']) != 24 or len(set(corpus['scenario_order'])) != 24:
        raise ValueError('exact24 prospective scenarios required')
    runtime = previous['runtime']
    for name in ('binary','observer'):
        actual = pin(runtime[name]['path'])
        if actual != runtime[name]: raise ValueError('runtime changed')
    if Path(runtime['executable']).resolve() != Path(runtime['binary']['path']).resolve():
        raise ValueError('runtime executable alias changed')
    archive = HERE/'source-archive-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as bundle:
        for name in source_names+['real_overlay_fixture_corpus_v1.json','protocol-v1.json','overlay-v1-to-v2.diff']:
            item = zipfile.ZipInfo(name, date_time=(2026,10,12,0,0,0))
            item.external_attr = 0o100644 << 16
            bundle.writestr(item, (HERE/name).read_bytes())
    archive_pin = pin(archive)
    bundle_members = []
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            raw = bundle.read(name)
            if raw != (HERE/name).read_bytes(): raise ValueError('archive source mismatch')
            bundle_members.append(dict(name=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    plan = dict(schema='ROOT-real-Controller-overlay-fixture-plan-v1',
        status='SOURCE_ONLY_FROZEN_UNEXECUTED', sources=sources, inputs=inputs,
        preserved=list(preserve.values()), source_archive=archive_pin,
        runtime=runtime, worker_path=str((HERE/'real_overlay_fixture_worker_v1.py').relative_to(ROOT)),
        owner_path=str((HERE/'owned_real_overlay_fixture_v1.py').relative_to(ROOT)),
        activation_path=str((HERE/'root-fixture-activation-v1.json').relative_to(ROOT)),
        outputs=dict(directory=str((HERE/'owned-output-v1').relative_to(ROOT)),
            result=str((HERE/'owned-output-v1/fixture-result-v1.json').relative_to(ROOT)),
            lifetime=str((HERE/'owned-output-v1/fixture-lifetime-v1.json').relative_to(ROOT))),
        expected_scenario_ids=corpus['scenario_order'],
        limits=dict(child_seconds=25,supervisor_seconds=30,whole_ROOT_phase_seconds=60,
            memory_bytes=536870912,artifact_bytes=33554432,maximum_observers=1200,
            observer_seconds=1.0,observer_stream_bytes=4194304,worker_stream_bytes=4194304),
        activation_requirement='ROOT must fully review frozen V2/source diff/fixture/owner plus independent prospective review before exact one-shot activation. Actual result remains unaccepted until full independent raw replay and ROOT outer clock qualify it.',
        actual_scientific_calls_by_author=0, execution_authorized=False,
        claim_scope=corpus['scope'])
    write_new('fixture-plan-v1.json',plan)
    plan_pin = pin(HERE/'fixture-plan-v1.json')
    write_new('readiness-v1.json',dict(schema='real-overlay-fixture-source-readiness-v1',
        status='SOURCE_ONLY_READY_FOR_ROOT_AND_INDEPENDENT_REVIEW',plan=plan_pin,
        asts=asts, preserved_unique_pins=len(preserve), sources=len(sources),inputs=len(inputs),
        zip_members=bundle_members, archive=archive_pin,
        fixture_scenarios=24, whole_registration_mutants=5,
        V1_gap_scope='Prospective source finding only; V1 mutant was not executed',
        successor_scope='Canonical complete menu/draw requirement repair only; no outcome tuning',
        source_freeze_seconds_before_final_readiness_and_integration_write=time.monotonic()-started,
        scientific_imports_functions_fixtures_RNG_model_search_training_checker_native_calls=0,
        execution_authorized=False))
    files = [pin(HERE/name) for name in source_names+['real_overlay_fixture_corpus_v1.json',
        'protocol-v1.json','overlay-v1-to-v2.diff','source-archive-v1.zip','fixture-plan-v1.json','readiness-v1.json']]
    write_new('integration-v1.json',dict(schema='real-overlay-fixture-source-integration-v1',
        status='SOURCE_ONLY_COMPLETE_HANDOFF_NO_ACTIVATION', files=files,
        producer_scientific_runs=0, independent_scientific_runs=0,
        owner_command=[runtime['executable'],'-B',str((HERE/'owned_real_overlay_fixture_v1.py').relative_to(ROOT)),str((HERE/'fixture-plan-v1.json').relative_to(ROOT))],
        actual_imports_functions_fixtures_RNG_models_searches_training_replay_checks_native=0))
    print(json.dumps(dict(status='SOURCE_ONLY_READY',plan=plan_pin,preserved=len(preserve),
                         sources=len(sources),inputs=len(inputs),scenarios=24),indent=2))


if __name__ == '__main__': main()
