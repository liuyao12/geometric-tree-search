"""ROOT metadata gate and exact activation; no policy import or execution."""
import ast
import hashlib
import json
from pathlib import Path
import resource
import time

FOLDER = Path('.gcts-active/family-proposal-learning-numeric-source-20261012')
PROGRESS = Path('.gcts-active/family-numeric-actual-progress-20261012')

def pin(path):
    data = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def save(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')

def main():
    begin = time.monotonic()
    expected = 'a9c41c98a38a9e03b658f27a9390fe14f66a261d94ceb5fc4e1ef033aa2fb5af'
    plan_path = FOLDER / 'owner-plan-v1.json'
    plan_pin = pin(plan_path)
    assert plan_pin['sha256'] == expected and plan_pin['bytes'] == 8405
    plan = json.loads(plan_path.read_text())
    review_path = Path('.gcts-active/family-numeric-source-review-20261012/source-review-v1.json')
    review_pin = pin(review_path)
    assert review_pin['sha256'] == '659b267fdf4e2e8dea1e8751fc119358ffa64a07895c0ae4c8868d832e688cee'
    review = json.loads(review_path.read_text())
    assert review['status'] == 'PASS_source_only_prospective_numeric_review'
    assert review['blocking_defects'] == []
    records = plan['sources'] + plan['inputs'] + list(plan['runtime'][k] for k in ('alias_pin', 'resolved_pin', 'observer_pin'))
    for record in records:
        assert pin(record['path']) == record, record['path']
    parsed = []
    for record in plan['sources']:
        if record['path'].endswith('.py'):
            ast.parse(Path(record['path']).read_text(), filename=record['path'], feature_version=(3, 9))
            parsed.append(record['path'])
    absent = [FOLDER / 'owner-activation-v1.json', Path(plan['numeric_output']), Path(plan['owned_output'])]
    assert all(not path.exists() for path in absent)
    activation = {'scope': 'root_authorized_owned_numeric_fixture_only', 'plan': plan_pin,
                  'source_pins': plan['sources'], 'runtime': plan['runtime'],
                  'independent_source_review': review_pin,
                  'authorization': 'User-authorized research program; ROOT owns one numeric fixture, no engine or training.'}
    save(PROGRESS / 'source-review-v1.json', {
        'status': 'passed_fresh_ROOT_metadata_and_full_source_review', 'plan': plan_pin,
        'independent_review': review_pin, 'source_pins': records,
        'Python39_AST_sources': parsed, 'prospective_paths_confirmed_absent': [str(p) for p in absent],
        'numeric_or_policy_or_search_calls': 0,
        'metadata_seconds_before_final_write': time.monotonic() - begin,
        'kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'ROOT_source_coverage': 'Complete owner, worker, policy math, bridge, owner-plan, numeric-plan and metadata freezer read.'})
    save(absent[0], activation)
    print(json.dumps({'activation': pin(absent[0]), 'metadata_review': pin(PROGRESS / 'source-review-v1.json')}))

if __name__ == '__main__':
    main()
