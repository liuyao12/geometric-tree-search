"""New bounded pure loader fixtures; no actual trace or engine is opened."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def check(value, label):
    if not value:
        raise AssertionError(label)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def fixtures():
    def valid(name, value):
        return {'name': name, 'raw': json.dumps(value, ensure_ascii=False).encode('utf-8'), 'expected': 'equal_json_value'}
    cases = [
        valid('nested_ordered_repeated_quads', {'a': [[1, 2, 3, 4], {'b': [[1, 2, 3, 4], [4, 3, 2, 1]]}], 'key': [1, 2, 3, 4]}),
        valid('signs_big_integers_and_nonquad_arrays', {'a': [-1, 0, 2**130, -2**130], 'b': [1, 2, 3], 'c': [1, 2, 3, 4, 5], 'd': [[1, 2, 3, 4]]}),
        valid('bool_float_null_scalars_not_integer_keys', {'a': [True, 2, 3, 4], 'b': [1., 2., 3., 4.], 'c': [None, False, 0, 'x'], 'd': -0.0}),
        valid('quoted_numeric_text_escaped_quotes_backslashes_unicode', {'a': '[1,2,3,4]', 'b': '\\"[5,6,7,8]\\', 'c': 'λ漢字', 'd': [1, 2, 3, 4]}),
        {'name': 'integer_negative_zero_same_json_value', 'raw': b'{"a":[-0,2,3,4]}', 'expected': 'equal_json_value'},
    ]
    # Sweep array starts and escaped quotes across the exact 65536-byte chunk.
    for width in (65499, 65509, 65519, 65529, 65535, 65536, 65537, 65545):
        cases.append(valid('chunk_boundary_' + str(width), {'padding': 'x' * width + '\\"[1,2,3,4]', 'actual': [8, 7, 6, 5], 'nested': [[8, 7, 6, 5]]}))
    for name, raw in [
        ('reserved_value_literal', b'{"a":"#0"}'),
        ('reserved_value_escaped', b'{"a":"\\u00230"}'),
        ('reserved_key_literal', b'{"#0":[1,2,3,4]}'),
        ('reserved_key_escaped', b'{"\\u00230":[1,2,3,4]}'),
        ('malformed_missing_comma', b'{"a":[1 2,3,4]}'),
        ('malformed_unterminated_string', b'{"a":"[1,2,3,4]'),
    ]:
        cases.append({'name': name, 'raw': raw, 'expected': 'reject'})
    # Deliberately retained implementation limitations, not support claims.
    cases.extend([
        {'name': 'top_level_quad_not_restored', 'raw': b'[1,2,3,4]', 'expected': 'known_top_level_mismatch'},
        {'name': 'top_level_array_not_fully_restored', 'raw': b'[[1,2,3,4],{"b":[5,6,7,8]}]', 'expected': 'known_top_level_mismatch'},
        {'name': 'invalid_leading_zero_rewrite_is_not_strict_json', 'raw': b'{"a":[01,2,3,4]}', 'expected': 'known_invalid_json_accepted'},
        {'name': 'valid_large_unmatched_prefix_fails_closed', 'raw': b' ' * (2097152 + 65536) + b'{"a":1}', 'expected': 'resource_unknown'},
    ])
    return cases

def worker():
    started = time.perf_counter()
    plan = json.loads((HERE / 'fixture-plan-v1.json').read_bytes())
    for pin in plan['sources']:
        check(digest(ROOT / pin['path']) == pin['sha256'], 'frozen source')
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('pure fixture budget')))
    signal.setitimer(signal.ITIMER_REAL, plan['worker_seconds'])
    spec = importlib.util.spec_from_file_location('pinned_loader_only', ROOT / plan['loader'])
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    cases = fixtures()
    check(len(cases) == plan['fixture_count'], 'complete declared fixture count')
    check(sum(len(case['raw']) for case in cases) == plan['total_fixture_bytes'], 'declared fixture bytes')
    reports = []
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        for index, case in enumerate(cases):
            path = Path(tmp) / (str(index) + '.json.gz')
            path.write_bytes(gzip.compress(case['raw'], mtime=0))
            before = digest(path)
            expected = case['expected']
            try:
                value = loader.load(path)
            except (ValueError, json.JSONDecodeError) as exc:
                check(expected in ('reject', 'resource_unknown'), 'unexpected rejection: ' + case['name'])
                if expected == 'resource_unknown':
                    check(str(exc) == 'unknown_decoder_long_token_resource_budget', 'known resource outcome')
                report = {'name': case['name'], 'observed': 'resource_unknown' if expected == 'resource_unknown' else 'rejected', 'reason': str(exc)}
            else:
                if expected == 'equal_json_value':
                    literal = json.loads(case['raw'])
                    check(canonical(value) == canonical(literal), 'every JSON field/value preserved: ' + case['name'])
                    report = {'name': case['name'], 'observed': 'exact_json_value', 'canonical_sha256': hashlib.sha256(canonical(value)).hexdigest()}
                elif expected == 'known_top_level_mismatch':
                    literal = json.loads(case['raw'])
                    check(canonical(value) != canonical(literal), 'documented unsupported top-level shape')
                    report = {'name': case['name'], 'observed': 'documented_top_level_mismatch', 'value': value}
                elif expected == 'known_invalid_json_accepted':
                    try:
                        json.loads(case['raw'])
                    except json.JSONDecodeError:
                        pass
                    else:
                        raise AssertionError('fixture must be invalid strict JSON')
                    check(canonical(value) == b'{"a":[1,2,3,4]}', 'documented leading-zero rewrite')
                    report = {'name': case['name'], 'observed': 'documented_invalid_json_admission', 'value': value}
                else:
                    raise AssertionError('required rejection was not observed: ' + case['name'])
            check(before == digest(path), 'original fixture gzip bytes unchanged')
            report['raw_sha256'] = hashlib.sha256(case['raw']).hexdigest()
            report['raw_bytes'] = len(case['raw'])
            reports.append(report)
    signal.setitimer(signal.ITIMER_REAL, 0)
    result = {'status': 'passed_bounded_loader_scope_and_equivalence_fixtures', 'plan_sha256': digest(HERE / 'fixture-plan-v1.json'), 'fixtures': reports, 'fixture_count': len(reports), 'seconds_before_receipt_write': time.perf_counter() - started, 'kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'new_searches': 0, 'new_native_queries': 0, 'actual_trace_loads': 0, 'scope': 'Normalized JSON-array value equivalence on declared valid top-level objects; explicit unsupported top-level and strict-JSON cases remain limitations, not successes of a general parser.'}
    check(result['seconds_before_receipt_write'] <= plan['worker_seconds'], 'worker time gate')
    output = HERE / 'fixture-worker-v1.json'
    check(not output.exists(), 'new output')
    output.write_text(json.dumps(result, indent=2) + '\n')

def owner():
    started = time.perf_counter()
    plan = json.loads((HERE / 'fixture-plan-v1.json').read_bytes())
    check(not (HERE / 'fixture-lifetime-v1.json').exists(), 'single execution')
    child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = child.communicate(timeout=plan['lifetime_seconds'])
        failure = None
    except subprocess.TimeoutExpired:
        child.kill()
        stdout, stderr = child.communicate()
        failure = 'lifetime timeout'
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    result = {'status': 'passed_bounded_fixture_lifetime' if child.returncode == 0 and failure is None and elapsed <= plan['lifetime_seconds'] and peak <= plan['rss_bytes'] else 'unknown_or_failed_fixture_lifetime', 'plan_sha256': digest(HERE / 'fixture-plan-v1.json'), 'pid': child.pid, 'exit_code': child.returncode, 'terminal_and_reaped': True, 'seconds_before_final_receipt_write': elapsed, 'conservative_owner_plus_child_kernel_peak_bytes': peak, 'failure': failure, 'stderr': stderr.decode('utf-8'), 'memory_scope': 'Post-exit conservative kernel peak gate; no hard OS memory cap or external RSS sampling claim.', 'new_searches': 0, 'new_native_queries': 0, 'actual_trace_loads': 0}
    (HERE / 'fixture-lifetime-v1.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    worker() if '--worker' in sys.argv else owner()
