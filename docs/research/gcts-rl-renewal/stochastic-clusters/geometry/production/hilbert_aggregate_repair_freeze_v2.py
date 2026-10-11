"""Freeze streaming-only serialization repair; do not run the producer."""
import ast
import difflib
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write(path, text):
    if path.exists():
        raise ValueError('immutable repair file exists')
    path.write_text(text)


def replace_once(text, before, after):
    assert text.count(before) == 1, before[:70]
    return text.replace(before, after)


def main():
    started = time.perf_counter()
    original = json.loads((HERE / 'plan-v1.json').read_text())
    outer = json.loads((HERE / 'outer-lifetime-v1.json').read_text())
    stage = json.loads((HERE / 'stage-costs-v1.json').read_text())
    assert outer['status'] == stage['status'] == 'unknown_or_failed'
    assert stage['owned_child_wait_reaped'] and stage['exit_code'] == 0
    assert stage['reported_child_peak_bytes'] == 557432832
    prior_seconds = outer['full_outer_seconds_before_this_receipt_write']
    remaining = 180 - prior_seconds
    assert 0 < remaining < 180
    producer_v1 = (HERE / 'hilbert_aggregate_expand_v1.py').read_text()
    save_v1 = '''def save(path, value):
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\\n').encode()
    if path.exists():
        raise ValueError('immutable output already exists: ' + str(path))
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)
'''
    save_v2 = '''def save(path, value):
    if path.exists():
        raise ValueError('immutable output already exists: ' + str(path))
    encoder = json.JSONEncoder(indent=2, ensure_ascii=False)
    with path.open('xb') as raw:
        stream = gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) if path.suffix == '.gz' else raw
        try:
            pieces, size = [], 0
            for piece in encoder.iterencode(value):
                encoded = piece.encode('utf-8')
                pieces.append(encoded)
                size += len(encoded)
                if size >= 65536:
                    stream.write(b''.join(pieces))
                    pieces, size = [], 0
            pieces.append(b'\\n')
            stream.write(b''.join(pieces))
        finally:
            if stream is not raw:
                stream.close()


def raw_serialization_pin(path):
    hasher, size = hashlib.sha256(), 0
    with (gzip.open(path, 'rb') if path.suffix == '.gz' else path.open('rb')) as stream:
        while True:
            part = stream.read(1048576)
            if not part:
                break
            hasher.update(part)
            size += len(part)
    return {'sha256': hasher.hexdigest(), 'bytes': size}


def serialization_correspondence():
    started = time.perf_counter()
    records = []
    for old, new in (('expansions-v1.json.gz', 'expansions-v2.json.gz'),
                     ('model-v1.json.gz', 'model-v2.json.gz'),
                     ('example-correspondence-v1.json', 'example-correspondence-v2.json')):
        a, b = raw_serialization_pin(HERE / old), raw_serialization_pin(HERE / new)
        assert a == b, 'streaming serialization changed raw JSON bytes: ' + new
        records.append({'original_pin': file_pin(HERE / old), 'repair_pin': file_pin(HERE / new),
                        'raw_utf8_json_pin': a, 'byte_identical_after_decompression': True})
    result = {'status': 'streamed_serialization_exact_raw_byte_correspondence', 'records': records,
              'seconds_before_receipt_write': time.perf_counter() - started,
              'logical_audit_credit': False, 'native_queries': 0, 'target_searches': 0}
    save(HERE / 'serialization-correspondence-v2.json', result)
    return result
'''
    producer = replace_once(producer_v1, save_v1, save_v2)
    producer = replace_once(producer, 'signal.alarm(180)', f'signal.alarm({int(remaining)})')
    # Preserve the logical plan pin and every logical object; only output filenames change.
    producer = producer.replace("HERE / 'expansions-v1.json.gz'", "HERE / 'expansions-v2.json.gz'")
    producer = producer.replace("HERE / 'model-v1.json.gz'", "HERE / 'model-v2.json.gz'")
    producer = producer.replace("HERE / 'example-correspondence-v1.json'", "HERE / 'example-correspondence-v2.json'")
    producer = replace_once(producer, "    assert_bound(plan)\n    elapsed = time.perf_counter() - start", "    serialization = serialization_correspondence()\n    assert_bound(plan)\n    elapsed = time.perf_counter() - start")
    producer = replace_once(producer, "for p in ('expansions-v1.json.gz', 'model-v1.json.gz', 'example-correspondence-v1.json')", "for p in ('expansions-v2.json.gz', 'model-v2.json.gz', 'example-correspondence-v2.json')")
    producer = replace_once(producer, "save(HERE / 'production-v1.json', receipt)", "receipt['serialization_correspondence_pin'] = file_pin(HERE / 'serialization-correspondence-v2.json')\n    receipt['resource_amendment_pin'] = file_pin(HERE / 'plan-v2.json')\n    save(HERE / 'production-v2.json', receipt)")
    # The helper's correspondence list still references original v1 files literally.
    assert "('expansions-v1.json.gz', 'expansions-v2.json.gz')" in producer
    supervisor_v1 = (HERE / 'hilbert_aggregate_static_run_v1.py').read_text()
    supervisor = supervisor_v1.replace('hilbert_aggregate_expand_v1.py', 'hilbert_aggregate_expand_v2.py').replace('hilbert_aggregate_static_run_v1.py', 'hilbert_aggregate_static_run_v2.py')
    for old, new in [('plan-v1.json', 'plan-v2.json'), ('production-v1.json', 'production-v2.json'),
                     ('stage-costs-v1.json', 'stage-costs-v2.json'), ('production-launch-v1.json', 'production-launch-v2.json'),
                     ('production-stdout-v1.txt', 'production-stdout-v2.txt'), ('production-stderr-v1.txt', 'production-stderr-v2.txt')]:
        supervisor = supervisor.replace(old, new)
    supervisor = replace_once(supervisor, 'LIMIT_SECONDS = 180', 'LIMIT_SECONDS = ' + repr(remaining))
    outer_v1 = (HERE / 'hilbert_aggregate_outer_lifetime_v1.py').read_text()
    wrapper = outer_v1.replace('hilbert_aggregate_static_run_v1.py', 'hilbert_aggregate_static_run_v2.py').replace('outer-lifetime-v1.json', 'outer-lifetime-v2.json').replace('stage-costs-v1.json', 'stage-costs-v2.json').replace('plan-v1.json', 'plan-v2.json')
    wrapper = replace_once(wrapper, '    started = time.perf_counter()\n    result = subprocess.run', '''    started = time.perf_counter()
    amendment = json.loads((HERE / 'plan-v2.json').read_text())
    for p in amendment['sources'] + amendment['v1_evidence_pins'] + amendment['input_pins']:
        data = (HERE.parent.parent / p['path']).read_bytes()
        assert len(data) == p['bytes'] and hashlib.sha256(data).hexdigest() == p['sha256']
    result = subprocess.run''')
    wrapper = replace_once(wrapper, "combined_peak = own + children + (inner['conservative_sum_kernel_peak_bytes'] if inner else 0)", "combined_peak = own + max(children, inner['conservative_sum_kernel_peak_bytes'] if inner else 0)")
    wrapper = replace_once(wrapper, '# Conservative host charge intentionally double-counts some child peaks.', '# Max avoids adding an inherited descendant peak twice; outer own peak is added.')
    wrapper = replace_once(wrapper, 'total <= 180', f'total + {prior_seconds!r} <= 180')
    wrapper = replace_once(wrapper, "'wall_ceiling_seconds': 180, 'host_ceiling_bytes'", f"'wall_ceiling_seconds': {remaining!r}, 'prior_failed_v1_production_seconds': {prior_seconds!r}, 'cumulative_production_seconds': total + {prior_seconds!r}, 'host_ceiling_bytes'")
    changes = []
    for stem, before, after in [('hilbert_aggregate_expand', producer_v1, producer),
                                ('hilbert_aggregate_static_run', supervisor_v1, supervisor),
                                ('hilbert_aggregate_outer_lifetime', outer_v1, wrapper)]:
        ast.parse(after)
        write(HERE / (stem + '_v2.py'), after)
        changes.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                          fromfile=stem + '_v1.py', tofile=stem + '_v2.py'))
    write(HERE / 'repair-source-diff-v2.txt', ''.join(changes))
    old_names = ['plan-v1.json', 'outer-measurement-amendment-v1.json', 'production-v1.json', 'stage-costs-v1.json',
                 'outer-lifetime-v1.json', 'production-launch-v1.json', 'production-stdout-v1.txt', 'production-stderr-v1.txt',
                 'expansions-v1.json.gz', 'model-v1.json.gz', 'example-correspondence-v1.json', 'serialization-inspection-v1.json']
    source_names = ['hilbert_aggregate_expand_v2.py', 'hilbert_aggregate_static_run_v2.py',
                    'hilbert_aggregate_outer_lifetime_v2.py', 'hilbert_aggregate_repair_freeze_v2.py']
    amendment = {
        'version': 'hilbert-aggregate-serialization-only-repair-v2', 'status': 'frozen_before_one_repair_execution',
        'sources': [pin(HERE / n) for n in source_names], 'v1_evidence_pins': [pin(HERE / n) for n in old_names],
        'input_pins': [{k: p[k] for k in ('path', 'sha256', 'bytes')} for p in original['inputs']],
        'original_frozen_plan_pin': pin(HERE / 'plan-v1.json'), 'source_diff_pin': pin(HERE / 'repair-source-diff-v2.txt'),
        'logical_scope_change': False, 'exact_data_obligation': 'Decompressed UTF-8 JSON bytes, including indentation and final newline, identical for all three scientific outputs. New paths/receipts only.',
        'v1_status': 'UNKNOWN: actual child kernel peak exceeded 512 MiB', 'v1_child_kernel_peak_bytes': stage['reported_child_peak_bytes'],
        'v1_wrapper_double_counting': 'separate conservative accounting issue; does not explain away the actual child over-limit',
        'known_v1_failed_outer_lifetime_seconds': prior_seconds, 'remaining_production_wall_seconds': remaining,
        'original_cumulative_production_ceiling_seconds': 180, 'independent_audit_ceiling_seconds': 180,
        'host_ceiling_bytes': 512 * 1024 * 1024,
        'changes': ['stream JSONEncoder.iterencode with original formatting into gzip.GzipFile(filename empty, mtime zero)',
                    'bounded 64 KiB encoding buffer; no full serialized string/bytes allocation',
                    'versioned output filenames and byte-correspondence receipt',
                    'same fail-closed supervisor using remaining cumulative wall bill',
                    'outer peak = max(kernel descendant peak, supervisor conservative peak) + own peak'],
        'native_queries': 0, 'target_searches': 0, 'placement_graphs': 0, 'engine_or_authority_activation': False,
        'preparation_seconds_before_amendment_write': time.perf_counter() - started,
        'diagnostic_inspection_seconds': json.loads((HERE / 'serialization-inspection-v1.json').read_text())['inspection_seconds'],
        'prior_input_preparation_seconds': original['preparation_cost']['freeze_input_hashing_and_syntax_seconds_before_plan_write'],
    }
    write(HERE / 'plan-v2.json', json.dumps(amendment, indent=2) + '\n')
    print(json.dumps({'plan_pin': pin(HERE / 'plan-v2.json'), 'sources': amendment['sources'],
                      'remaining_seconds': remaining, 'execution_started': False}))


if __name__ == '__main__':
    main()
