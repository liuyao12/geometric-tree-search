"""METADATA ONLY freezer: hashes and AST/JSON syntax, no fixture execution.

This file never imports the oracle, runner, producer, controller or any model.
Its execution only freezes the prospective ROOT-owned pure fixture package.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def pin(path):
    path = Path(path).resolve(); data = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def save(name, value):
    with (BASE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def main():
    names = ['family_binding_oracle_v1.py', 'family_embedding_oracle_v1.py', 'family_fixture_runner_v1.py', 'family_fixture_owner_v1.py']
    sources = [pin(BASE / name) for name in names]
    imports = {}
    for name in names:
        tree = ast.parse((BASE / name).read_text())
        imports[name] = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    corpus = BASE / 'family-fixture-corpus-v1.json'
    json.loads(corpus.read_text())
    previous = json.loads((BASE / 'integration-v1.json').read_text())
    preserved = [pin(ROOT / item['path']) for item in previous['files']] + [pin(BASE / 'integration-v1.json')]
    for item, actual in zip(previous['files'], preserved):
        if (item['sha256'], item['bytes']) != (actual['sha256'], actual['bytes']):
            raise ValueError('original independent design/oracle pin changed')
    plan = dict(schema='root-owned-pure-family-fixture-plan-v1', status='frozen_prospective_unexecuted',
        sources=sources, inputs=[pin(corpus), pin(ROOT / 'AGENTS.md'), pin(ROOT / 'docs/basic-tiling-algorithm.md')],
        preserved=preserved, metadata_freezer=pin(__file__),
        runtime=dict(executable=sys.executable, platform=sys.platform, version=sys.version, binary=pin(sys.executable)),
        worker_path=str(BASE / 'family_fixture_runner_v1.py'), owner_path=str(BASE / 'family_fixture_owner_v1.py'),
        corpus_path=str(corpus), activation_path=str(BASE / 'fixture-activation-v1.json'),
        required_activation=dict(schema='root-pure-family-fixture-activation-v1', authorized=True, plan_sha256='exact fixture-plan-v1.json hash'),
        limits=dict(whole_seconds=30, supervisor_seconds=28, child_seconds=25, peak_bytes=134217728),
        outputs={k: str(BASE / name) for k, name in dict(result='fixture-result-v1.json', lifetime='fixture-lifetime-v1.json', stdout='fixture-stdout-v1.txt', stderr='fixture-stderr-v1.txt').items()},
        root_command=[sys.executable, str(BASE / 'family_fixture_owner_v1.py'), str(BASE / 'fixture-plan-v1.json')],
        root_owned_process_metadata='/bin/ps -o rss= -p OWNED_PID only; require permitted process metadata; missing live metadata UNKNOWN with kill/wait-reap',
        method=['Hand-derived literal keys, ordered ports, signed offsets, point unions and occurrence counts in corpus.',
                'Independent synthetic identity preimages bind literal witnesses, refs, recipe, t/m, synthetic context/epoch/registry.',
                'Original V1 binding/aggregate oracle preserved; additive declaration/embedding adapter verifies exact declared member instead of last-member convention.',
                'Canonical single/pair enumeration visits full tiny type and filtered ordered-root Cartesian products; one increasing DAG embedding per binding.',
                'Embedding acceptance alone does not imply compatible joint aggregate; joint point union checked separately.',
                'Same-code receptor aliases preserve each ordered read port without adding premise t; distinct identities may not share occupancy.'],
        expected_scope=dict(pure_synthetic_only=True, actual_graph_or_model=False, scheduler=False,
            logical_inference_validity=False, actual_body_registry_certification=False, native_queries=0,
            training_or_search=False, fixture_results_unexecuted=True),
        accounting='Fixture source authoring unmeasured. Owned timers include runtime source verification, fixture calls, result preparation/serialization and process metadata; final lifetime receipt write follows its recorded timer. Pure fixture phase separate from future preparation/search/audit costs.',
        no_execution_by_freezer=True)
    save('fixture-plan-v1.json', plan)
    readiness = dict(status='source_ready_pure_fixture_plan_not_executed', plan=pin(BASE / 'fixture-plan-v1.json'),
        source_import_ast=imports, syntax_checks='AST/JSON parse only; no module imports, fixtures, model, scheduler, engine, logical checker or native calls',
        protocol_disposition='Fixed root single/pair pool can reuse paired controller only through a separately verified immutable union authority. This fixture gate does not implement or activate that authority.',
        limitations=['Synthetic equal-input binary primitive is deliberately not a logical inference.',
                     'Selected-root entries and already-selected keys are API prerequisites, not independently certified actual roots here.',
                     'Full projection digest/body fields require independently pinned actual source registry in a later production adapter.',
                     'Synthetic identity covers its declared fixture-only preimage; actual production full point preimages remain a separate audit.',
                     'Canonical DAG row adaptation regenerates offsets, not a rigid translation of an atomic macro.',
                     'Single/pair grammar and one embedding per binding do not exhaust arbitrary clusters, embeddings or proofs.',
                     'Synthetic roots sort full keys. Producer graph.order token indices must be reconstructed separately or normalized on both sides by full keys; this gate does not establish their ordering equality.',
                     'No actual rule/controller/epoch/pool/rollback/degree or inference validity tested.'])
    save('fixture-readiness-v1.json', readiness)
    new = [pin(BASE / n) for n in ('family_embedding_oracle_v1.py', 'family_fixture_runner_v1.py', 'family_fixture_owner_v1.py', 'family_fixture_freeze_v1.py', 'family-fixture-corpus-v1.json', 'fixture-plan-v1.json', 'fixture-readiness-v1.json')]
    save('fixture-integration-v1.json', dict(status='immutable_unexecuted_pure_fixture_package', files=new,
         total_bytes=sum(p['bytes'] for p in new), original_design_bundle=pin(BASE / 'integration-v1.json'),
         root_dispatch_required=True, activation_basename='fixture-activation-v1.json',
         scientific_or_fixture_execution=False))
    print(json.dumps(dict(plan=pin(BASE / 'fixture-plan-v1.json'), integration=pin(BASE / 'fixture-integration-v1.json'),
        sources=len(sources), inputs=3, preserved=len(preserved), new_files=len(new), execution=False)))


if __name__ == '__main__':
    main()
