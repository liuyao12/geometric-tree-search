"""METADATA ONLY prospective successor; no oracle/fixture/scientific imports.

Preserves the unexecuted V1 gate. Only runtime alias normalization and isolated
activation/output/owner namespace change; pure worker/oracles/corpus unchanged.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve(); data = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def save(name, value):
    with (BASE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def main():
    old = json.loads((BASE / 'fixture-plan-v1.json').read_text())
    previous = json.loads((BASE / 'fixture-integration-v1.json').read_text())
    for p in old['sources'] + old['inputs'] + old['preserved'] + previous['files']:
        if pin(p['path']) != p:
            raise ValueError('immutable V1 pin mismatch: ' + p['path'])
    ast.parse((BASE / 'family_fixture_owner_v2.py').read_text())
    plan = copy.deepcopy(old)
    plan['schema'] = 'root-owned-pure-family-fixture-plan-v2'
    plan['sources'] = [pin(BASE / 'family_fixture_owner_v2.py') if Path(p['path']).name == 'family_fixture_owner_v1.py' else p for p in old['sources']]
    plan['metadata_freezer'] = pin(__file__)
    preserved = old['preserved'] + previous['files'] + [pin(BASE / 'fixture-integration-v1.json')]
    plan['preserved'] = list({(p['path'], p['sha256']): p for p in preserved}.values())
    plan['owner_path'] = str(BASE / 'family_fixture_owner_v2.py')
    plan['activation_path'] = str(BASE / 'fixture-activation-v2.json')
    plan['required_activation'] = dict(schema='root-pure-family-fixture-activation-v2', authorized=True,
                                       plan_sha256='exact fixture-plan-v2.json hash')
    plan['outputs'] = {k: str(BASE / name) for k, name in dict(result='fixture-result-v2.json', lifetime='fixture-lifetime-v2.json', stdout='fixture-stdout-v2.txt', stderr='fixture-stderr-v2.txt').items()}
    plan['root_command'] = [plan['runtime']['executable'], str(BASE / 'family_fixture_owner_v2.py'), str(BASE / 'fixture-plan-v2.json')]
    plan['source_only_amendment'] = dict(original_plan=pin(BASE / 'fixture-plan-v1.json'), owner_diff=pin(BASE / 'family_fixture_owner_v2.diff'),
        cause='V1 freezer resolved binary path but V1 owner preserved executable alias; exact dict pin comparison would refuse launch.',
        correction='V2 compares pin(Path(sys.executable).resolve()) against the exact frozen runtime binary.',
        other_changes='Isolated V2 activation schema/basename, plan/owner and output filenames only.',
        unchanged_worker_oracles_corpus=True, prior_owner_or_fixture_execution=False, fixture_failure_count=0,
        source_authoring_seconds=None)
    save('fixture-plan-v2.json', plan)
    readiness = dict(status='source_ready_runtime_alias_successor_not_executed', plan=pin(BASE / 'fixture-plan-v2.json'),
        owner=pin(BASE / 'family_fixture_owner_v2.py'), diff=pin(BASE / 'family_fixture_owner_v2.diff'),
        previous_readiness=pin(BASE / 'fixture-readiness-v1.json'), unchanged_limit=plan['limits'],
        precise_activation_basename='fixture-activation-v2.json', precise_activation_schema='root-pure-family-fixture-activation-v2',
        runtime_path_rule='Runtime executable alias remains explicit; binary comparison resolves the alias before path+hash+length comparison.',
        fixture_results=0, fixture_failure_claim=False, owner_dispatches=0,
        syntax_scope='Owner AST and JSON/pins only; no module imports, functions, fixtures or science execution',
        all_V1_scope_limitations_preserved=True, root_dispatch_required=True)
    save('fixture-readiness-v2.json', readiness)
    files = [pin(BASE / name) for name in ('family_fixture_owner_v2.py', 'family_fixture_owner_v2.diff', 'family_fixture_freeze_v2.py', 'fixture-plan-v2.json', 'fixture-readiness-v2.json')]
    save('fixture-integration-v2.json', dict(status='immutable_unexecuted_pure_fixture_runtime_alias_successor', files=files,
         total_bytes=sum(p['bytes'] for p in files), preserved_V1_bundle=pin(BASE / 'fixture-integration-v1.json'),
         root_dispatch_required=True, activation_basename='fixture-activation-v2.json', fixture_execution=False))
    print(json.dumps(dict(plan=pin(BASE / 'fixture-plan-v2.json'), integration=pin(BASE / 'fixture-integration-v2.json'),
        sources=len(plan['sources']), inputs=len(plan['inputs']), preserved=len(plan['preserved']), execution=False)))


if __name__ == '__main__':
    main()
