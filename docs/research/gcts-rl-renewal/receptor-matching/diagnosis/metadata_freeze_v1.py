"""Static pin freeze before reading either fresh compressed trace payload."""
import ast
import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CURRENT = ROOT / '.gcts-active/receptor-matching-geometry-source-20261011'
OLD = ROOT / '.gcts-active/automatic-geometry-search-diagnosis-20261011'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def verify(entry):
    actual = pin(ROOT / entry['path'])
    if actual != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('historical source pin changed: ' + entry['path'])
    return actual


def save(name, value):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.perf_counter()
    if any((HERE / name).exists() for name in ('metadata-plan-v1.json', 'metadata-source-freeze-v1.json',
                                              'metadata-diagnosis-v1.json', 'metadata-lifetime-v1.json')):
        raise ValueError('immutable metadata freeze/output already exists')
    # Read only the historical source plan, not any result/actual/model payload.
    previous_plan = json.loads((CURRENT / 'search-plan-v1.json').read_text())
    preserved = {entry['path']: verify(entry) for entry in previous_plan['sources'] + previous_plan['inputs']
                 + previous_plan['preserved_files']}
    roles = {entry['role']: ROOT / entry['path'] for entry in previous_plan['inputs']}
    input_paths = {
        'fresh_reference_trace': CURRENT / 'fixed-forward-reference-result-v1.json.gz',
        'fresh_receptor_trace': CURRENT / 'fixed-forward-receptor-result-v1.json.gz',
        'fresh_source_plan': CURRENT / 'search-plan-v1.json',
        'fresh_matcher_contract': CURRENT / 'matcher-contract-v1.json',
        'fresh_outcome': CURRENT / 'search-outcome-v1.json',
        'fresh_lifetime': CURRENT / 'search-lifetime-v1.json',
        'fresh_supervision': CURRENT / 'search-supervision-v1.json',
        'fresh_root_activation': CURRENT / 'root-activation-v1.json',
        'fresh_root_terminal': ROOT / '.gcts-active/receptor-matching-progress-20261011/root-producer-terminal-v1.json',
        'literal_primitive_schema': roles['primitive_model'],
        'previous_published_metadata_diagnosis': OLD / 'diagnosis-v1.json',
        'previous_published_metadata_next_plan': OLD / 'next-gate-plan-v1.json',
        'previous_published_metadata_manifest': OLD / 'manifest-v1.json',
        'previous_accepted_trace_terminal_review': ROOT / '.gcts-active/automatic-geometry-actual-independent-review-20261011/terminal-review-v1.json',
        'fresh_root_source_review': ROOT / '.gcts-active/receptor-matching-progress-20261011/root-source-review-v1.json',
        'fresh_independent_source_review': ROOT / '.gcts-active/receptor-matching-geometry-independent-20261011/producer-source-review-v1.json',
        'fresh_third_source_review': ROOT / '.gcts-active/receptor-matching-source-third-review-20261011/source-review-v1.json'}
    inputs = [{'role': role, **pin(path)} for role, path in input_paths.items()]
    for folder in (CURRENT, OLD):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                entry = pin(path)
                if entry['path'] in preserved and preserved[entry['path']] != entry:
                    raise ValueError('preservation conflict')
                preserved[entry['path']] = entry
    for entry in inputs:
        preserved[entry['path']] = {k: entry[k] for k in ('path', 'sha256', 'bytes')}
    sources = [pin(HERE / name) for name in ('recorded_trace_metadata_v1.py', 'metadata_owner_v1.py', Path(__file__).name)]
    for entry in sources:
        ast.parse((ROOT / entry['path']).read_text(), filename=entry['path'])
    plan = {'status': 'frozen_metadata_only_plan_before_fresh_result_payload_decode',
        'saved_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources, 'inputs': inputs,
        'preserved_files': [preserved[path] for path in sorted(preserved)],
        'limits': {'owner_seconds': 60, 'child_SIGALRM_seconds': 55, 'host_bytes': 536870912},
        'method': 'Load exact encoded result bytes and literal source-schema JSON after hash verification; count recorded events, selected keys/outputs, saved pattern/feature comparisons, occupied/frontier rows and key-prefix differences. Never invoke matcher/engine/checker or rebuild any point state.',
        'root_authorization': 'Root directly requested this bounded read-only saved-artifact diagnosis. No mathematical execution, retry, budget increase or scientific source mutation authorized.',
        'source_payloads_before_this_freeze': {'fresh_trace_payloads_decoded': 0, 'model_schema_decoded': 0,
                                             'actual_result_metadata_decoded': 0},
        'prospective_questions': ['Did the new recorded prefix still instantiate both first point variables to the same constant?',
            'What saved receptor labels/bindings accompanied its first divergence?',
            'At which occupied/frontier rows and source-rule choices were the later attempts spent?',
            'Did guarded literal matching address only the prefix or produce any complete certificate?',
            'Does recorded structure motivate prefix/conjunction compatibility or generic source-family advice, with full fallback?'],
        'no_authority': 'Metadata diagnosis is not independent trace/order/logical acceptance. Pending separately owned actual audit must qualify all scientific claims. No new proof word is supplied to an algorithm.',
        'proposed_outputs': ['metadata-diagnosis-v1.json', 'metadata-lifetime-v1.json', 'metadata-stdout-v1.txt', 'metadata-stderr-v1.txt'],
        'command': 'python3 ' + str(HERE / 'metadata_owner_v1.py'),
        'source_authoring_seconds': None,
        'static_freeze_seconds_before_plan_write': time.perf_counter() - started,
        'costs': 'Retain all previous source/native/UNKNOWN/preparation and search/audit timers. Fresh producer9.340212875s/128057344B is distinct from metadata-only time; old owner sum50.405773542s remains additional and excludes old546.8s native admission bill and other setup.'}
    save('metadata-plan-v1.json', plan)
    receipt = {'status': 'metadata_source_inputs_frozen_before_any_fresh_trace_payload_decode',
        'plan': pin(HERE / 'metadata-plan-v1.json'), 'sources': len(sources), 'inputs': len(inputs),
        'preserved_files': len(preserved), 'mismatches': 0,
        'unique_verified_paths': len({p['path'] for p in sources + inputs + list(preserved.values())}),
        'AST_parse_only': len(sources), 'fresh_trace_payloads_decoded': 0, 'engine_imports': 0,
        'model_constructions': 0, 'checker_imports': 0, 'searches': 0, 'native_queries': 0,
        'static_freeze_seconds_before_receipt_write': time.perf_counter() - started}
    save('metadata-source-freeze-v1.json', receipt)
    print(json.dumps({'plan': pin(HERE / 'metadata-plan-v1.json'), 'receipt': pin(HERE / 'metadata-source-freeze-v1.json'),
                      'sources': len(sources), 'inputs': len(inputs), 'preserved': len(preserved)}, indent=2))


if __name__ == '__main__':
    main()
