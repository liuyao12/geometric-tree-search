"""Root read-only static package checks; no scientific loading or execution."""
from pathlib import Path
import ast
import hashlib
import json
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MEM = ROOT / '.gcts-active/stochastic-replay-memory-v5-20261011'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


started = time.perf_counter()
package_path = MEM / 'review-package-v5.json'
package = json.loads(package_path.read_text())
assert sha(package_path) == 'ff67751d41c6c136dbc8190c15e48ff899ea3806c5a9e4d9cbd2ece996b69c30'
for key in ['sources', 'inputs']:
    for path, expected in package[key].items():
        assert sha(ROOT / path) == expected, path
for entry in package['files']:
    p = ROOT / entry['path']
    assert sha(p) == entry['sha256'] and p.stat().st_size == entry['bytes'], entry['path']
for entry in package['prior_inclusive_phases_preserved']:
    assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
assert abs(sum(e['seconds'] for e in package['prior_inclusive_phases_preserved']) - 226.66065275) < 1e-8
archived = dict(package['sources'])
archived[package['consumer_argument']['path']] = package['consumer_argument']['sha256']
with zipfile.ZipFile(MEM / 'source-snapshot-v5.zip') as z:
    assert set(z.namelist()) == set(archived)
    for path, expected in archived.items():
        assert hashlib.sha256(z.read(path)).hexdigest() == expected, path
for path in package['sources']:
    if path.endswith('_v5.py'):
        ast.parse((ROOT / path).read_text())
helper = json.loads((MEM / 'helper-plan-v5.json').read_text())
evaluation = json.loads((MEM / 'evaluation-plan-v5.json').read_text())
assert helper['historical_failed_audit_seconds'] == evaluation['historical_failed_audit_seconds'] == 226.66065275
assert evaluation['seconds'] == 553.33934725 and helper['rss_bytes'] == evaluation['rss_bytes'] == 536870912
assert len(helper['jobs']) == 7 and len(evaluation['jobs']) == 6
for entry in evaluation['jobs']:
    assert entry['lifecycle_seconds'] == 120
    plan = json.loads((ROOT / entry['plan_path']).read_text())
    assert plan['seconds'] == 115 and plan['rss_bytes'] == 536870912
for entry in helper['jobs']:
    assert entry['lifecycle_seconds'] == 30
    plan = json.loads((ROOT / entry['plan_path']).read_text())
    assert plan['seconds'] == 25 and plan['rss_bytes'] == 536870912
receipt = {
    'status': 'passed_root_static_v5_source_pin_type_scope_and_budget_review',
    'package_sha256': sha(package_path),
    'helper_plan_sha256': sha(MEM / 'helper-plan-v5.json'),
    'evaluation_plan_sha256': sha(MEM / 'evaluation-plan-v5.json'),
    'source_pins': len(package['sources']),
    'input_pins': len(package['inputs']),
    'manifest_files': len(package['files']),
    'zip_sources_and_argument': len(archived),
    'scope': 'Complete byte/pin review, new loader/fixture/owner source inspection, worker two-line diff and pinned consumer-use argument; no scientific decode/replay. Independent source disposition and helper acceptance still required.',
    'alias_scope': 'Plain-list sharing only in read-only saved observations; other loads retain V2; mutating alias control deliberately distinguishes unsupported consumers.',
    'mathematical_checks': 'Unchanged full six original evaluations and complete graph/math/RNG/learning/hints/rollback checks.',
    'history_seconds': 226.66065275,
    'remaining_seconds_before_helpers': 553.33934725,
    'seconds_before_write': time.perf_counter() - started,
}
(HERE / 'arithmetic-source-review-v5.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
