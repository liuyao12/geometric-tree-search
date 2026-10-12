"""ROOT metadata-only integration; no scientific imports, calls or launch."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / '.gcts-active/cluster-transfer-compact-progress-20261012'
ENGINE = ROOT / '.gcts-active/cluster-transfer-compact-telemetry-engine-source-20261012'
COMPILER = ROOT / '.gcts-active/cluster-transfer-compact-telemetry-compiler-source-20261012'


def read(path):
    raw = Path(path).read_bytes()
    assert len(raw) <= 1048576
    return json.loads(raw)


def pin(path, absolute=False):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    name = str(p.resolve()) if absolute else str(p.relative_to(ROOT))
    return dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def save(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    assert len(sys.argv) == 2
    review_path = Path(sys.argv[1]).resolve()
    review = read(review_path)
    engine = read(ENGINE / 'handoff-v1.json')
    compiler = read(COMPILER / 'handoff-v1.json')
    assert engine['source_only'] is True and engine['scientific_acceptance'] is False
    assert compiler['source_only'] is True and compiler['scientific_acceptance'] is False
    sources = {role: pin(record['path'], absolute=True)
               for role, record in engine['source_roles'].items()}
    inputs = {role: pin(record['path'], absolute=True)
              for role, record in engine['inputs'].items()}
    for record in [*engine['source_roles'].values(), *engine['inputs'].values()]:
        assert pin(record['path']) == record
    assert sources['compiler']['sha256'] == compiler['active_compiler']['sha256']
    assert review['source_only'] is True and review['source_ready'] is True
    assert review['scientific_acceptance'] is False
    assert review['all_checks_passed'] is True and review['check_count'] == 23
    assert len(review['checks']) == 23 and all(item['pass'] is True for item in review['checks'])
    assert review['review_execution']['scientific_calls'] == 0
    assert review['sources'] == sources and review['inputs'] == inputs
    assert not (HERE / 'preparation-plan-v1.json').exists()
    assert not (HERE / 'preparation-owner-v1').exists()
    output = HERE / 'train-pa-right-zero-preparation-v1'
    assert not output.exists()
    helpers = ['run_owned_bridge_v2.py', 'freeze_compact_phase_v1.py',
               'close_stage_decision_v1.py']
    for name in helpers:
        raw = (OLD / name).read_bytes()
        ast.parse(raw)
        with (HERE / name).open('xb') as stream:
            stream.write(raw)
    assert pin(HERE / helpers[0])['sha256'] == '2df179c4d500ba17ee832dd7dafb7a43e3fa2f2c171d5b745bfe448275fc1656'
    limits = dict(whole_seconds=60, peak_bytes=536870912, caller_seconds=90)
    worker_plan = dict(schema='ROOT-fresh-ground-compact-telemetry-preparation-plan-v2',
        selector='train-pa-right-zero', output_directory=str(output), inputs=inputs,
        sources=sources, source_review=pin(review_path, absolute=True),
        limits={key: limits[key] for key in ('whole_seconds', 'peak_bytes')},
        ROOT_owned_once_only=True)
    save('ROOT-worker-preparation-plan-v2.json', worker_plan)
    root_review = dict(schema='ROOT-compact-telemetry-source-review-v1',
        source_review_passed=True, scientific_calls=0, source_only=True,
        scientific_acceptance=False, reviewed_source_readiness=pin(review_path),
        owner=pin(HERE / helpers[0]), owner_relocation='Exact frozen owner V2 bytes, same HERE depth; relative closure pins and preparation-result-v2 receipt path.',
        sources=sources, inputs=inputs, resource_limits=limits,
        historical_UNKNOWN_preserved=True, dynamic_search_conformance=False,
        old_audit_worker_v1_compatible=False,
        scope='Full nine-statement declaration retained, one first-PA preparation only; scalar diagnostics charged, no candidate/inventory reduction or dependent activation.')
    save('ROOT-source-review-v1.json', root_review)
    paths = [Path(record['path']) for record in [*sources.values(), *inputs.values()]]
    paths += [review_path, Path(__file__), HERE / 'ROOT-worker-preparation-plan-v2.json']
    for directory in (ENGINE, COMPILER):
        paths += [directory / name for name in ['handoff-v1.json', 'source-protocol-v1.json', 'source-metadata-review-v1.json']]
    paths += [COMPILER / 'instrumentation-diff-v2.patch', ENGINE / 'instrumentation-diff-v1.patch']
    paths += [OLD / 'ROOT-final-progress-decision-v1.json', OLD / 'preparation-ROOT-final-decision-v1.json']
    paths += [Path(item['pin']['path']) for item in review['declared_pin_observations']]
    paths += [Path(item['path']) for item in review['review_inputs'].values()]
    paths += [Path(review['protocol']['path']), review_path.parent / 'handoff-v1.json']
    closure = {record['path']: record for record in (pin(path) for path in paths)}
    worker_relative = str(Path(sources['worker']['path']).relative_to(ROOT))
    spec = dict(schema='ROOT-fresh-cluster-static-prospective-spec-v1', stage='preparation',
        scope='One distinct telemetry-only source epoch: entire unchanged first-PA declaration grammar, complete24 initial point-domain factors and charged diagnostic/evidence/receipt postlude. No search, proof acceptance, independent audit, mining, RL or native query. Same60s/512MiB/90caller limits.',
        scientific_calls_by_spec_author=0, instance_count=1, declared_fixture_case_count=9,
        closure=list(closure.values()), worker=worker_relative,
        worker_arguments=['ROOT-prepare-only', str(HERE / 'ROOT-worker-preparation-plan-v2.json')],
        worker_receipt=str((output / 'preparation-result-v2.json').relative_to(ROOT)), limits=limits)
    save('preparation-prospective-spec-v1.json', spec)
    print(json.dumps(dict(spec=pin(HERE / 'preparation-prospective-spec-v1.json'),
        worker_plan=pin(HERE / 'ROOT-worker-preparation-plan-v2.json'),
        source_review=pin(HERE / 'ROOT-source-review-v1.json'), scientific_calls=0)))


if __name__ == '__main__':
    main()
