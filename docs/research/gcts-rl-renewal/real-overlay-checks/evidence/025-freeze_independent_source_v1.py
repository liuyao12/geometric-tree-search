"""Exclusive metadata-only independent source freeze. No scientific imports."""
import ast
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile


def main():
    began = time.monotonic(); here = Path(__file__).resolve().parent; root = here.parents[1]
    def pin(path):
        path = Path(path).resolve(); h = hashlib.sha256(); count = 0
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(65536), b''):
                h.update(block); count += len(block)
        return dict(path=str(path.relative_to(root)) if root in path.parents else str(path),
                    sha256=h.hexdigest(), bytes=count)
    def absolute(path):
        path = Path(path); return path if path.is_absolute() else root/path
    def save(name, value):
        with (here/name).open('x') as stream:
            json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
    frozen = root/'.gcts-active/family-proposal-real-overlay-source-20261012'
    fixture = json.loads((frozen/'fixture-plan-v1.json').read_text())
    preserved = {}
    for record in fixture['sources'] + fixture['inputs'] + fixture['preserved']:
        actual = pin(absolute(record['path']))
        if any(actual[k] != record[k] for k in ('sha256','bytes')):
            raise ValueError('exact inherited source/runtime/input changed: ' + record['path'])
        if actual['path'] in preserved and preserved[actual['path']] != actual:
            raise ValueError('conflicting source bytes')
        preserved[actual['path']] = actual
    for name in ('fixture-plan-v1.json','readiness-v1.json','integration-v1.json','source-archive-v1.zip'):
        record = pin(frozen/name); preserved[record['path']] = record
    names = ['independent_features_v1.py','independent_policy_v1.py','independent_fixture_points_v1.py',
        'independent_fixture_whole_v1.py','independent_fixture_replay_v1.py','independent_fixture_worker_v1.py',
        'owned_independent_fixture_replay_v1.py','finalize_actual_fixture_replay_plan_v1.py','freeze_independent_source_v1.py']
    sources, trees = [], []
    for name in names:
        source = pin(here/name); tree = ast.parse((here/name).read_text(), filename=name, feature_version=(3,9))
        sources.append(source)
        trees.append(dict(path=source['path'], AST_nodes=sum(1 for _ in ast.walk(tree)),
            imports=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}.union(
                {a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}))))
    original_features = ast.parse((root/'.gcts-active/family-proposal-rl-small-source-20261012/family_graph_features_v1.py').read_text())
    own_features = ast.parse((here/'independent_features_v1.py').read_text())
    def names_from(tree):
        return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and
            any(isinstance(t,ast.Name) and t.id=='FEATURE_NAMES' for t in n.targets))
    if names_from(original_features) != names_from(own_features) or len(names_from(own_features)) != 31:
        raise ValueError('independent exact31-feature schema differs from frozen predecessor')
    role_paths = {
        'fixture_plan':frozen/'fixture-plan-v1.json', 'fixture_corpus':frozen/'real_overlay_fixture_corpus_v1.json',
        'fixture_worker_source':frozen/'real_overlay_fixture_worker_v1.py',
        'fixture_owner_source':frozen/'owned_real_overlay_fixture_v1.py',
        'overlay_v2':frozen/'family_learned_overlay_v2.py', 'overlay_diff':frozen/'overlay-v1-to-v2.diff',
        'frozen_feature_source':root/'.gcts-active/family-proposal-rl-small-source-20261012/family_graph_features_v1.py',
        'frozen_update_source':root/'.gcts-active/family-proposal-rl-small-source-20261012/family_episode_learning_v1.py',
        'frozen_RL_protocol':root/'.gcts-active/family-proposal-rl-small-source-20261012/protocol-v1.json',
        'frozen_split':root/'.gcts-active/family-proposal-rl-small-source-20261012/donor-split-v1.json',
        'owned_helpers':root/'.gcts-active/family-proposal-learning-numeric-source-20261012/owned_numeric_gate_v1.py',
        'master_contract':root/'docs/basic-tiling-algorithm.md', 'AGENTS':root/'AGENTS.md',
        'independent_protocol':here/'protocol-v1.json', 'owner_diff':here/'owner-fixture-to-independent.diff'}
    inputs = [dict(role=role,**pin(path)) for role,path in role_paths.items()]
    runtime = fixture['runtime']
    for field in ('binary','observer'):
        actual = pin(runtime[field]['path'])
        if actual != runtime[field]: raise ValueError('actual runtime changed')
    if Path(runtime['executable']).resolve() != Path(runtime['binary']['path']).resolve():
        raise ValueError('runtime executable alias changed')
    corpus = json.loads(role_paths['fixture_corpus'].read_text())
    with zipfile.ZipFile(frozen/'source-archive-v1.zip') as bundle:
        fixture_members=[]
        for name in bundle.namelist():
            raw=bundle.read(name)
            if raw != (frozen/name).read_bytes(): raise ValueError('frozen fixture ZIP source differs')
            fixture_members.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    review = dict(schema='independent-family-RL-prospective-source-review-v1',
        status='V1_BLOCKER_RECORDED_V2_SOURCE_REPAIR_REVIEWED_RUNTIME_GATES_UNEXECUTED',
        reviewed_sources=[r for r in inputs if r['role'] in ('overlay_v2','overlay_diff','frozen_feature_source',
            'frozen_update_source','fixture_worker_source','fixture_owner_source','frozen_RL_protocol','frozen_split')],
        frozen_feature_count=31, fixture_scenarios=len(corpus['scenario_order']),
        predecessor_blocker=dict(id='prepared-menu-authenticity',
            source='.gcts-active/family-proposal-rl-small-source-20261012/family_learned_overlay_v1.py',
            finding='Graph semantic SHA alone does not bind mutable prepared menu/action IDs/draw flag; choose_prepared V1 accepts caller payload without rederiving it.',
            scope='Prospective source finding. V1 mutant was never executed by this reviewer.'),
        successor_disposition='Minimal V2 rederives exact menu and literal draw bool from same frozen/current graph, recipes, registry, hints and active state; comparison precedes any choice mutation. The complete source diff preserves feature schema/math/split/hyperparameters.',
        positive_source_evidence=['Complete original base stream remains a full permutation with NULL suppressing fixed advice',
            'Global graph decision is checked before advice; forced consumes no draw',
            'Whole Controller resync includes all pending members/full IDs/distant assigned marks; no partial proposal salvage',
            'Waiting persists; retired/consumed clears active ID; paired checkpoint restores graph/hints/overlay',
            'Dependency-complete selected strict-prior closure supplies potential; missing/zero/pending marks alone are not facts',
            '31 feature names use structural values, constructor heads and code equality only; no proof word/name/value lookup',
            'Fixed eight donor updates use old baseline advantage before clipping; fixed held-out split and evaluation do not update'],
        required_driver_obligations=['Bind each raw trajectory/result/resource receipt to exact complete independently rebuilt policy choices and gradients before qualified_update',
            'Enforce frozen donor order/seeds and final eighth checkpoint without selection',
            'Use chronological unique non-NULL commit IDs; restore active origin on rollback and count each commit retirement at most once',
            'Count Fmax over every actual primitive state including forced/failed branches, never accumulated rediscovery',
            'No update from resource UNKNOWN, partial tape, failure or unexecuted suffix',
            'Actual donor/held-out compiler/pool static gate and full scientific DFS/RNG/reward/update replay still required'],
        conformance_gaps=corpus['uncovered'],
        actual_scientific_imports_functions_fixtures_models_searches_RNG_training_replays_checkers_native=0,
        source_authoring_manual_review_seconds=None, execution_authorized=False)
    save('source-review-v1.json',review)
    plan = dict(schema='independent-family-RL-source-stage-v1',status='SOURCE_ONLY_FROZEN_NO_ACTUAL_REPLAY_PLAN',
        sources=sources,inputs=inputs,preserved=sorted(preserved.values(),key=lambda r:r['path']),runtime=runtime,
        source_review=pin(here/'source-review-v1.json'),
        actual_plan_finalizer='finalize_actual_fixture_replay_plan_v1.py',
        missing_actual_inputs=['Completed exact actual fixture result','Producer complete owned lifetime',
            'ROOT normalized complete terminal/source review','ROOT independent source review and separate activation'],
        actual_plan_exists=False, scope='All24 synthetic real-Controller fixture operations plus12 actual future saved-transcript mutations; donor/held-out DFS still a future gate',
        execution_authorized=False,ROOT_sole_actual_owner=True)
    save('source-plan-v1.json',plan)
    archive=here/'source-v1.zip'
    archived=names+['protocol-v1.json','owner-fixture-to-independent.diff','source-review-v1.json','source-plan-v1.json']
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in archived: bundle.write(here/name,name)
    with zipfile.ZipFile(archive) as bundle:
        members=[]
        for name in bundle.namelist():
            raw=bundle.read(name)
            if raw!=(here/name).read_bytes(): raise ValueError('independent archive source mismatch')
            members.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    readiness=dict(schema='independent-family-RL-source-readiness-v1',status='SOURCE_ONLY_COMPLETE_READY_FOR_ROOT_SOURCE_REVIEW',
        source_plan=pin(here/'source-plan-v1.json'),source_review=pin(here/'source-review-v1.json'),
        archive=pin(archive),sources=len(sources),input_roles=len(inputs),inherited_unique_pins=len(preserved),
        ASTs=trees,ZIP_members=members,verified_fixture_ZIP_members=fixture_members,
        metadata_seconds_before_final_readiness_and_integration_write=time.monotonic()-began,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        source_authoring_manual_inspection_cost_unmeasured=True,
        actual_scientific_imports_functions_fixtures_models_RNG_search_training_replay_checker_native=0,
        actual_plan_finalizer_unexecuted=True,execution_authorized=False)
    save('readiness-v1.json',readiness)
    files=[pin(here/name) for name in archived+['source-v1.zip','readiness-v1.json']]
    save('integration-v1.json',dict(schema='independent-family-RL-source-integration-v1',status='SOURCE_ONLY_UNEXECUTED_HANDOFF',
        files=files,scientific_calls=0,ROOT_sole_actual_owner=True))
    print(json.dumps(dict(source_plan=pin(here/'source-plan-v1.json'),integration=pin(here/'integration-v1.json'),
        sources=len(sources),inherited_pins=len(preserved),metadata_seconds=readiness['metadata_seconds_before_final_readiness_and_integration_write']),indent=2))


if __name__ == '__main__': main()
