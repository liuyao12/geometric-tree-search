"""Exclusive metadata/source-only freeze; never imports or calls policy modules.

Source-plan/manifests/AST and incremental raw byte hashing only. Scientific
models, trajectories and numeric results are pinned but never decoded here.
The freezer cannot authorize a driver, fixture, RNG, training or search.
"""
import ast
import hashlib
import json
import resource
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block); size += len(block)
    return dict(path=str(path.relative_to(ROOT)) if ROOT in path.parents else str(path),
                sha256=digest.hexdigest(), bytes=size)


def absolute(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def save(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    began = time.perf_counter()
    if any((HERE / name).exists() for name in ('source-plan-v1.json', 'readiness-v1.json', 'integration-v1.json')):
        raise ValueError('new immutable package already frozen')
    sources = [pin(HERE / name) for name in ('family_graph_features_v1.py', 'family_learned_overlay_v1.py',
        'family_episode_learning_v1.py', 'family_curriculum_resolver_v1.py', 'freeze_source_v1.py')]
    protocol = pin(HERE / 'protocol-v1.json'); split = pin(HERE / 'donor-split-v1.json')
    # Source protocol/split are metadata, not generated AST/model/results.
    description = json.loads(absolute(protocol['path']).read_text())
    curriculum = json.loads(absolute(split['path']).read_text())
    if description['execution_authorized'] is not False or curriculum['execution_authorized'] is not False:
        raise ValueError('source author cannot authorize any scientific phase')
    reviews = json.loads((ROOT / '.gcts-active/family-numeric-source-review-20261012/source-review-v1.json').read_text())
    previous = json.loads((ROOT / '.gcts-active/fixed-family-pool-search-source-20261012/search-plan-v1.json').read_text())
    expected = {}
    for record in reviews['verified_pins'] + previous['sources'] + previous['inputs'] + previous['preserved_files']:
        actual = pin(absolute(record['path']))
        if actual['sha256'] != record['sha256'] or actual['bytes'] != record['bytes']:
            raise ValueError('inherited exact byte changed: ' + record['path'])
        prior = expected.setdefault(actual['path'], actual)
        if prior != actual:
            raise ValueError('conflicting inherited byte identity')
    relevant = {
        'master_contract': 'docs/basic-tiling-algorithm.md',
        'agent_instructions': 'AGENTS.md',
        'math_v2': '.gcts-active/family-proposal-learning-20261012/family_policy_math_v2.py',
        'bridge_v2': '.gcts-active/family-proposal-learning-20261012/family_pool_bridge_v2.py',
        'numeric_source_review': '.gcts-active/family-numeric-source-review-20261012/source-review-v1.json',
        'numeric_actual_ROOT_terminal': '.gcts-active/family-numeric-actual-progress-20261012/outer-terminal-v1.json',
        'numeric_actual_result_RAW_ONLY': '.gcts-active/family-proposal-learning-numeric-source-20261012/numeric-output-v2/result.json',
        'numeric_actual_owned_lifetime_RAW_ONLY': '.gcts-active/family-proposal-learning-numeric-source-20261012/owned-output-v1/owned-lifetime.json',
        'heldout_prospective_boundary': '.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json',
        'primitive_core': '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py',
        'root_fixed_Controller': '.gcts-active/hilbert-cluster-lifecycle-20261011/hilbert_cluster_lifecycle_v1.py',
        'family_composer': '.gcts-active/family-proposal-source-20261012/family_proposal_v2.py',
        'original_fixed_adapter': '.gcts-active/fixed-family-pool-search-source-20261012/fixed_family_pool_adapter_v1.py',
        'original_fixed_registrar': '.gcts-active/fixed-family-pool-search-source-20261012/fixed_family_pool_registration_v1.py',
        'independent_point_transaction': '.gcts-active/shared-symbolic-geometry-trace-independent-20261011/geometry_trace_point_v1.py',
        'independent_whole_hint_transaction': '.gcts-active/fixed-family-pool-search-source-20261012/fixed_family_pool_trace_oracle_v1.py',
        'independent_positive_certificate': '.gcts-active/receptor-matching-geometry-independent-20261011/positive_certificate_oracle_v1.py',
    }
    inputs = [dict(role=role, **pin(ROOT / path)) for role, path in relevant.items()]
    parsed = []
    for record in sources:
        tree = ast.parse(absolute(record['path']).read_text(), filename=record['path'], feature_version=(3, 9))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom): imports.append(node.module)
        parsed.append(dict(source=record, AST_nodes=sum(1 for _ in ast.walk(tree)), imports=sorted(set(imports))))
    runtime_alias = Path('/Library/Developer/CommandLineTools/usr/bin/python3')
    runtime = dict(executable=str(runtime_alias), binary=pin(runtime_alias.resolve()), observer=pin('/bin/ps'),
                   platform=sys.platform)
    plan = dict(schema='small_whole_family_RL_source_freeze_v1',
        status='immutable_SOURCE_ONLY_requires_ROOT_and_independent_review_before_any_fixture_or_scientific_dispatch',
        sources=sources, protocol=protocol, donor_split=split, inputs=inputs,
        preserved_sources_inputs=sorted(expected.values(), key=lambda r: r['path']), runtime=runtime,
        source_plan_path=str((HERE / 'source-plan-v1.json').relative_to(ROOT)),
        source_authoring_seconds=None,
        available_implementation='Pure feature/paired selection overlay/qualified update/curriculum resolution libraries; no owned scientific driver or independent new-policy replay implementation.',
        existing_numeric_scope='ROOT-reported math/abstract test-double result only; raw pins preserved without result decoding by this freezer.',
        heldout_scope='Pinned mixed context excluded from all donors and tuning; formulas/theorem families already present in library.',
        actual_policy_library_imports_functions_fixtures_RNG_models_training_searches_replays_checkers_native=0,
        root_only_execution=True, execution_authorized=False)
    save('source-plan-v1.json', plan)
    archive = HERE / 'source-v1.zip'
    archived_files = sources + [protocol, split, pin(HERE / 'source-plan-v1.json')]
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as stream:
        for record in archived_files: stream.write(absolute(record['path']), Path(record['path']).name)
    readiness = dict(status='source_only_implementation_ready_for_review_NOT_EXECUTION',
        source_plan=pin(HERE / 'source-plan-v1.json'), protocol=protocol, split=split, archive=pin(archive),
        new_sources=len(sources), inherited_unique_paths=len(expected), relevant_inputs=len(inputs), ASTs=parsed,
        metadata_seconds_before_readiness_write=time.perf_counter() - began,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
            (1 if sys.platform == 'darwin' else 1024),
        scope='Metadata/helper work only; source authoring/manual inspection unmeasured and additional. No policy import or function invocation, AST construction from source functions, fixture, RNG, scientific payload decode, model/checker/training/search/replay/native/owner launch.',
        missing_gates=['Complete donor and heldout compiler/pool static source+actual independent gate',
            'New real-Controller overlay/features controls', 'Owned driver and complete independent new-policy actual replay freeze',
            'ROOT exact phase activation'], execution_authorized=False)
    save('readiness-v1.json', readiness)
    files = sources + [protocol, split, pin(HERE / 'source-plan-v1.json'), pin(HERE / 'readiness-v1.json'), pin(archive)]
    save('integration-v1.json', dict(status='immutable_small_whole_family_RL_SOURCE_ONLY_package',
        files=files, actual_scientific_execution=False, ROOT_sole_actual_owner_and_publisher=True))
    print(json.dumps(dict(source_plan=pin(HERE / 'source-plan-v1.json'), integration=pin(HERE / 'integration-v1.json'),
        new_sources=len(sources), inherited_unique_paths=len(expected), helper_seconds=readiness['metadata_seconds_before_readiness_write']), indent=2))


if __name__ == '__main__': main()
