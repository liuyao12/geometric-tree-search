"""Static-only V2 caller adapter freeze, preserving actual failed V1 evidence.

No engine import, fixture, model construction, search, native run or training.
The original 118 phase inputs remain exact; body authority receives the accepted
original full-lifecycle 56-input plan rather than aliased phase metadata.
"""
import ast
import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
V1 = ROOT / '.gcts-active/shared-symbolic-geometry-search-source-20261011'
ROOT_REVIEW = ROOT / '.gcts-active/shared-symbolic-geometry-search-root-review-20261011'
INDEPENDENT = ROOT / '.gcts-active/shared-symbolic-geometry-search-independent-20261011'
TERMINAL = ROOT / '.gcts-active/automatic-geometry-progress-20261011/root-producer-v1-terminal.json'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def verify(entry):
    actual = pin(ROOT / entry['path'])
    if actual != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('frozen original evidence mismatch: ' + entry['path'])
    return actual


def save(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.perf_counter()
    outputs = ('search-plan-v1.json', 'source-freeze-v2.json', 'source-manifest-v2.json', 'failure-causal-amendment-v2.json')
    if any((HERE / name).exists() for name in outputs): raise ValueError('immutable V2 freeze already exists')
    original = read(V1 / 'search-plan-v1.json')
    for p in original['sources'] + original['inputs'] + original['preserved_files']: verify(p)
    inputs = copy.deepcopy(original['inputs'])
    if len(inputs) != 118: raise ValueError('original broad phase prerequisite list must remain unchanged')
    unique = len({p['path'] for p in inputs})
    if unique != 104: raise ValueError('preserve the actual 14 repeated-path role aliases as phase metadata')
    roles = {p['role']: ROOT / p['path'] for p in inputs}
    bodypath = roles['passed_full_lifecycle_producer_plan']
    bodyplan = read(bodypath)
    for p in bodyplan['sources'] + bodyplan['inputs'] + bodyplan['preserved_files']: verify(p)
    if (len(bodyplan['inputs']) != 56 or len({p['path'] for p in bodyplan['inputs']}) != 56
            or inputs[:56] != bodyplan['inputs']):
        raise ValueError('body authority must use the exact accepted original 56-input full plan')
    bound = next(p for p in inputs if p['role'] == 'passed_full_lifecycle_producer_plan')
    if pin(bodypath) != {k: bound[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('accepted original source-body plan byte binding changed')
    bodyroles = {p['role']: p for p in bodyplan['inputs']}
    phaseroles = {p['role']: p for p in inputs}
    required = ('primitive_model', 'primitive_logical_audit', 'complete_family_template_projection',
        'source_constant_transport_certificate', 'source_constant_transport_audit', 'exact_three_source_schemas',
        'source_searched_native_receipt', 'source_searched_native_independent_audit',
        'source_general_transport_argument', 'source_general_transport_ledger', 'source_general_transport_review',
        'full_exact_source_expansions', 'prior_full_model_plan')
    for role in required:
        if bodyroles[role] != phaseroles[role]: raise ValueError('original source/dependency closure changed: ' + role)
    if original['model_epoch'] != '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c':
        raise ValueError('original point-plan epoch changed')

    # Read only exact actual terminal receipts and causal text, never invoke a
    # mathematical helper or infer theorem validity from a launch-status field.
    lifetime = read(V1 / 'search-lifetime-v1.json')
    supervision = read(V1 / 'search-supervision-v1.json')
    terminal = read(TERMINAL)
    failed_seconds = Decimal(str(lifetime['full_supervisor_process_seconds_including_receipt_write']))
    if (failed_seconds != Decimal('0.935204458') or lifetime['process_return_code'] != 1
            or not lifetime['supervisor_wait_reaped'] or not lifetime['worker_terminal_reaped_confirmed']
            or supervision['exit_code'] != 1 or not supervision['owned_child_terminal_wait_reaped']
            or lifetime['supervision'] != pin(V1 / 'search-supervision-v1.json')):
        raise ValueError('actual V1 failed lifetime/reaping evidence incomplete')
    if (terminal['status'] != 'root_reconciled_failed_adapter_before_target_search'
            or not terminal['all_owned_handles_terminal'] or terminal['owner_tool_exit_code'] != 1
            or terminal['full_failed_owned_seconds'] != float(failed_seconds)
            or terminal['target_searches_started'] != 0 or terminal['target_searches_completed'] != 0
            or terminal['new_proofs'] != 0 or terminal['native_queries'] != 0):
        raise ValueError('V1 root terminal scope/cost not bound')
    for p in terminal['inputs']: verify(p)
    if 'ValueError: duplicate source pin' not in (V1 / 'search-stderr-v1.txt').read_text():
        raise ValueError('actual caller failure cause missing')
    if (V1 / 'search-outcome-v1.json').exists(): raise ValueError('V1 missing-outcome scope changed')
    for spec in original['observations']:
        if (V1 / (spec['id'] + '-result-v1.json.gz')).exists():
            raise ValueError('V1 target-search result unexpectedly exists')
    if (HERE / 'root-activation-v1.json').exists() or any((HERE / name).exists() for name in original['proposed_outputs']):
        raise ValueError('V2 must remain source-only, without activation or scientific output')

    same = ('shared_symbolic_forward_order_v1.py', 'shared_symbolic_bridge_decode_v1.py',
            'shared_symbolic_search_run_v1.py', 'shared_symbolic_search_outer_v1.py')
    for name in same:
        if (HERE / name).read_bytes() != (V1 / name).read_bytes():
            raise ValueError('ordering/decoder/supervisor/outer must remain byte-identical: ' + name)
    workername = 'shared_symbolic_geometry_search_v1.py'
    oldworker = (V1 / workername).read_text()
    needle = '        family = life.frozen_family_authority(g, plan)\n'
    replacement = "        body_plan = json.loads(roles['passed_full_lifecycle_producer_plan'].read_text())\n        family = life.frozen_family_authority(g, body_plan)\n"
    if oldworker.count(needle) != 1 or (HERE / workername).read_text() != oldworker.replace(needle, replacement):
        raise ValueError('only exact source-bound body-authority caller replacement is permitted')
    sourcepaths = [HERE / name for name in (workername, *same, Path(__file__).name)]
    sourcepaths += [ROOT / p['path'] for p in original['sources'][-2:]]
    for path in sourcepaths: ast.parse(path.read_text(), filename=str(path))
    sources = [pin(path) for path in sourcepaths]

    preserved = {p['path']: verify(p) for p in original['preserved_files']}
    oldentries = original['sources'] + original['inputs']
    for folder in (V1, ROOT_REVIEW, INDEPENDENT):
        oldentries += [pin(path) for path in sorted(folder.rglob('*'))
                       if path.is_file() and '__pycache__' not in path.parts]
    oldentries += [pin(TERMINAL)]
    for p in oldentries:
        q = verify(p)
        if q['path'] in preserved and preserved[q['path']] != q: raise ValueError('historical pin conflict')
        preserved[q['path']] = q

    causal = {'status': 'frozen_source_only_minimal_body_authority_caller_amendment',
        'failed_v1_root_terminal': pin(TERMINAL), 'failed_v1_lifetime': pin(V1 / 'search-lifetime-v1.json'),
        'failed_v1_supervision': pin(V1 / 'search-supervision-v1.json'),
        'failed_v1_stderr': pin(V1 / 'search-stderr-v1.txt'), 'failed_v1_activation': pin(V1 / 'root-activation-v1.json'),
        'failed_v1_root_source_review': pin(ROOT_REVIEW / 'source-review-v1.json'),
        'failed_v1_independent_source_review': pin(INDEPENDENT / 'source-review-v1.json'),
        'failed_v1_independent_causal_review': pin(INDEPENDENT / 'failed-terminal-causal-review-v1.json'),
        'worker_diff': pin(HERE / 'worker-adapter-v1-to-v2.diff'),
        'cause': 'The authored V1 caller gave the full 118-role phase metadata to a source-body authority factory requiring unique file paths; 14 repeated-path aliases were rejected after model construction, before automatic_search.',
        'review_gap': 'The author and both prior source reviews missed this caller-interface uniqueness precondition. The actual failure is preserved; it was neither proof rejection nor a completed target-search result.',
        'repair': 'Use exact accepted original full-language-plan-v3.json and its 56 unique input pins for frozen_family_authority. Keep all 118 broader phase prerequisites and complete preservation verification unchanged.',
        'not_a_proof_deduplication': 'No proof row, ordered premise, receptor port, primitive recipe, mapped source body, dependency or fallback candidate is removed or merged.',
        'all_other_scientific_code': 'Byte-identical forward order/decoder and unchanged DFS except this one caller hunk; unchanged primitive core/lifecycle kernel, model context/epoch, boundary, budgets and empty descriptors.',
        'naming': 'Sibling V2 folder retains source/output basenames used by byte-identical owners. Exact paths and plan bytes differ; old V1 files are never overwritten.',
        'prior_failed_owner_seconds': float(failed_seconds), 'prior_failed_peak_bytes': lifetime['conservative_host_peak_bytes'],
        'prior_target_searches_started': 0, 'prior_proofs': 0, 'prior_native_queries': 0,
        'v2_scientific_executions': 0, 'v2_native_queries': 0, 'v2_training': False}
    causalpath = HERE / 'failure-causal-amendment-v2.json'; save(causalpath, causal)
    preserved[causalpath.relative_to(ROOT).as_posix()] = pin(causalpath)
    preserved[(HERE / 'worker-adapter-v1-to-v2.diff').relative_to(ROOT).as_posix()] = pin(HERE / 'worker-adapter-v1-to-v2.diff')

    plan = copy.deepcopy(original)
    plan.update({'version': 'automatic-shared-symbolic-geometry-source-plan-v2-body-authority-caller',
        'status': 'frozen_source_only_v2_caller_repair_root_and_independent_review_pending_no_dispatch',
        'saved_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources, 'inputs': inputs,
        'preserved_files': [preserved[k] for k in sorted(preserved)],
        'body_authority_adapter': {'exact_accepted_original_full_plan': pin(bodypath),
            'original_source_relation_inputs': 56, 'unique_source_relation_paths': 56,
            'broad_phase_role_inputs': 118, 'broad_phase_unique_paths': 104, 'phase_role_aliases': 14,
            'source_projection': {k: bodyroles['complete_family_template_projection'][k] for k in ('path', 'sha256', 'bytes')},
            'source_logical_audit': {k: bodyroles['primitive_logical_audit'][k] for k in ('path', 'sha256', 'bytes')},
            'all_source_bodies': 171, 'body_authority_relation': 'original accepted full 56-input source relation; no alias deduplication and no primitive-only source plan',
            'broader_prerequisite_verification': 'unchanged original 118 role inputs plus preserved entire V1 failure/review/activation closure'},
        'v1_failed_prerequisite': {'root_terminal': pin(TERMINAL), 'lifetime': pin(V1 / 'search-lifetime-v1.json'),
            'amendment': pin(causalpath), 'prior_failed_owner_seconds': float(failed_seconds),
            'owner_and_children_terminal_reaped': True, 'target_searches_started': 0, 'proofs': 0, 'native_queries': 0},
        'root_command_after_two_source_reviews_and_exact_activation': 'python3 ' + str(HERE / 'shared_symbolic_search_outer_v1.py')})
    plan['prerequisites']['actual_failed_v1_root_terminal'] = pin(TERMINAL)
    plan['prerequisites']['actual_failed_v1_lifetime'] = pin(V1 / 'search-lifetime-v1.json')
    plan['costs']['new_static_freeze_seconds_before_plan_write'] = time.perf_counter() - started
    plan['costs']['retained_v1_failed_owner_seconds'] = float(failed_seconds)
    plan['costs']['cumulative_owner_accounting'] = 'The separately bounded fresh V2 phase keeps the original 180/175/170-second and 512 MiB gates. Add actual V2 lifetime to retained V1 failure 0.935204458 seconds; do not claim the combined prior and fresh phases passed a single cumulative 180-second gate.'
    plan['source_boundaries']['source_body_registry'] = 'Validate all 171 bodies using the exact accepted original 56-unique-input full-lifecycle plan; broader 118-input source/receipt checks stay intact. Empty active descriptors; no target word as hint.'
    planpath = HERE / 'search-plan-v1.json'; save(planpath, plan)
    receipt = {'status': 'frozen_source_only_v2_body_authority_caller_repair_no_scientific_execution',
        'plan': pin(planpath), 'causal_amendment': pin(causalpath), 'sources': len(sources), 'new_sources': 6,
        'inputs': len(inputs), 'body_source_unique_paths': 56, 'preserved_files': len(preserved),
        'unique_verified_paths': len({p['path'] for p in sources + inputs + list(preserved.values())}),
        'mismatches': 0, 'ast_parsed_sources': len(sourcepaths),
        'freeze_seconds_before_receipt_write': time.perf_counter() - started,
        'retained_failed_v1_owner_seconds': float(failed_seconds), 'source_authoring_seconds': None,
        'actual_geometry_model_loads_by_this_freeze': 0, 'geometry_searches_by_this_freeze': 0,
        'native_queries': 0, 'compiler_activations': 0, 'training': False, 'active_cluster_descriptors': 0,
        'root_and_independent_source_reviews': 'pending', 'execution_authorized': False}
    receiptpath = HERE / 'source-freeze-v2.json'; save(receiptpath, receipt)
    files = [pin(path) for path in sourcepaths[:6]] + [pin(HERE / 'worker-adapter-v1-to-v2.diff'), pin(causalpath), pin(planpath), pin(receiptpath)]
    manifest = {'status': 'immutable_source_only_v2_caller_repair_pending_two_reviews_and_root_dispatch',
        'files': files, 'total_files': len(files), 'total_bytes': sum(p['bytes'] for p in files), 'plan': pin(planpath),
        'retained_v1_failed_owner_seconds': float(failed_seconds), 'scientific_executions': 0,
        'native_queries': 0, 'publication_owner': 'root', 'claim': 'Minimal source-body plan adapter repair only, no proof discovery or fresh model execution.'}
    manifestpath = HERE / 'source-manifest-v2.json'; save(manifestpath, manifest)
    print(json.dumps({'plan': pin(planpath), 'receipt': pin(receiptpath), 'manifest': pin(manifestpath),
                     'sources': len(sources), 'inputs': len(inputs), 'preserved': len(preserved)}, indent=2))


if __name__ == '__main__': main()
