"""Metadata-only pin/AST review. Does not import or execute reviewed programs."""
import ast
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return {'path': label, 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def records(value):
    if isinstance(value, dict):
        if set(('path', 'sha256', 'bytes')) <= set(value):
            yield {key: value[key] for key in ('path', 'sha256', 'bytes')}
        for nested in value.values():
            yield from records(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from records(nested)


def main():
    started = time.perf_counter()
    planpath = HERE / 'review-plan-v1.json'
    plan = json.loads(planpath.read_text())
    checked = {}
    occurrence_count = 0
    queue = list(plan['inputs'])
    # Only declared manifest projections are followed, never scientific inputs.
    for manifest in plan['follow_manifests']:
        queue.extend(records(json.loads((ROOT / manifest).read_text())))
    for expected in queue:
        occurrence_count += 1
        location = Path(expected['path'])
        if not location.is_absolute():
            location = ROOT / location
        actual = pin(location)
        if actual != expected:
            raise ValueError('raw-byte pin mismatch: ' + expected['path'])
        old = checked.setdefault(expected['path'], expected)
        if old != expected:
            raise ValueError('inconsistent byte version: ' + expected['path'])
    asts = []
    for label in plan['AST_sources']:
        source = (ROOT / label).read_text()
        tree = ast.parse(source, filename=label)
        asts.append({'source': pin(ROOT / label), 'nodes': sum(1 for _ in ast.walk(tree)),
                     'executed_or_imported': False})
    absent = {label: not (ROOT / label).exists() for label in plan['must_be_absent']}
    if not all(absent.values()):
        raise ValueError('prospective output or activation already exists')
    result = {
        'status': 'PASS_source_only_prospective_numeric_review',
        'review_plan': pin(planpath), 'review_source': pin(Path(__file__)),
        'pin_occurrences': occurrence_count, 'unique_pins': len(checked),
        'verified_pins': sorted(checked.values(), key=lambda row: row['path']),
        'AST_sources': asts, 'prospective_activation_and_output_absent': absent,
        'manual_full_source_coverage': plan['manual_full_source_coverage'],
        'findings': plan['findings'], 'blocking_defects': [],
        'scope': plan['scope'], 'numeric_actual_acceptance': False,
        'review_metadata_seconds_before_receipt_write': time.perf_counter() - started,
        'review_kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                   * (1 if sys.platform == 'darwin' else 1024),
        'source_authoring_seconds': None,
        'scientific_program_imports': 0, 'numeric_function_invocations': 0,
        'fixture_runs': 0, 'RNG_calls': 0, 'model_engine_search_replay_native_training_runs': 0,
        'ROOT_sole_actual_owner_and_publisher': True,
    }
    with (HERE / 'source-review-v1.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in (
        'status', 'pin_occurrences', 'unique_pins', 'review_metadata_seconds_before_receipt_write',
        'review_kernel_peak_bytes')}))


if __name__ == '__main__':
    main()
