"""Static-only full-language lifecycle input/receipt freeze; no engine import.

The v3 filename matches the three already frozen, unexecuted owner sources.
This script verifies historical bytes and accepted tiny prerequisite receipts.
It neither loads a scientific model nor authorizes/dispatches its execution.
"""
import ast
import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INDEPENDENT = ROOT / '.gcts-active/hilbert-cluster-independent-20261011'
TINY_ACCEPTED = 'passed_independent_tiny_whole_lifecycle_point_body_and_finite_dfs_audit'


def pin(path):
    path = Path(path)
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            sha.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha.hexdigest(),
            'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def verify(expected):
    actual = pin(ROOT / expected['path'])
    if actual != {k: expected[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('historical byte mismatch: ' + expected['path'])
    return actual


def immutable_save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def main():
    started = time.perf_counter()
    planpath = HERE / 'full-language-plan-v3.json'
    receiptpath = HERE / 'full-language-freeze-v3.json'
    for path in (planpath, receiptpath):
        if path.exists():
            raise ValueError('immutable freeze already exists: ' + path.name)
    proposed_outputs = ['full-language-outcome-v3.json', 'full-language-launch-v3.json',
                        'full-language-supervision-v3.json', 'full-language-lifetime-v3.json',
                        'full-language-stdout-v3.txt', 'full-language-stderr-v3.txt']
    if any((HERE / name).exists() for name in proposed_outputs):
        raise ValueError('full actual gate has already produced an artifact')

    tiny_plan = read(HERE / 'plan-attempt-03.json')
    independent_plan = read(INDEPENDENT / 'actual-audit-plan-v2.json')
    readiness = read(HERE / 'full-language-source-ready-v3.json')
    # Exact pre-reviewed scientific source and old model provenance are unchanged.
    for expected in readiness['sources'] + readiness['diffs']:
        verify(expected)
    for field in ('frozen_kernel', 'prior_point_plan', 'prior_point_outcome',
                  'preserved_v2_checkpoint', 'source_causal_review'):
        verify(readiness[field])

    tiny_outcome_path = HERE / 'attempt-03/fixtures-outcome-v1.json'
    tiny_lifetime_path = HERE / 'attempt-03/fixtures-lifetime-v1.json'
    tiny_supervision_path = HERE / 'attempt-03/fixtures-supervision-v1.json'
    tiny_outcome, tiny_lifetime, tiny_supervision = map(read,
        (tiny_outcome_path, tiny_lifetime_path, tiny_supervision_path))
    if tiny_lifetime['status'] != 'passed_authored_tiny_lifecycle_full_lifetime':
        raise ValueError('producer tiny lifetime prerequisite not accepted')
    if (tiny_lifetime['process_return_code'] != 0 or not tiny_lifetime['supervisor_wait_reaped']
            or tiny_lifetime['cumulative_tiny_seconds'] > 60
            or tiny_lifetime['conservative_host_peak_bytes'] > 536870912):
        raise ValueError('producer tiny gate/reaping prerequisite incomplete')
    if (tiny_supervision['exit_code'] != 0 or not tiny_supervision['owned_child_terminal_wait_reaped']
            or tiny_lifetime['supervision_sha256'] != pin(tiny_supervision_path)['sha256']
            or tiny_lifetime['plan_sha256'] != pin(HERE / 'plan-attempt-03.json')['sha256']):
        raise ValueError('producer tiny exact receipt chain incomplete')

    independent_result_path = INDEPENDENT / 'actual-audit-result-v2.json'
    independent_lifetime_path = INDEPENDENT / 'actual-audit-lifetime-v2.json'
    independent_terminal_path = INDEPENDENT / 'actual-terminal-review-v2.json'
    independent_result, independent_lifetime, independent_terminal = map(read,
        (independent_result_path, independent_lifetime_path, independent_terminal_path))
    if independent_result['status'] != TINY_ACCEPTED:
        raise ValueError('independent tiny result prerequisite not accepted')
    if (independent_lifetime['status'] != 'passed_owned_independent_tiny_lifecycle_audit'
            or independent_lifetime['child_exit_code'] != 0
            or not independent_lifetime['owned_child_terminal_and_reaped']
            or independent_lifetime['full_owner_and_worker_seconds_before_receipt_write'] > 60
            or independent_lifetime['conservative_combined_peak_bytes'] > 536870912):
        raise ValueError('independent tiny lifetime gate/reaping prerequisite incomplete')
    if independent_terminal['status'] != 'passed_read_only_terminal_independent_tiny_gate_reconciliation':
        raise ValueError('independent tiny terminal review incomplete')
    for field, path in [('plan', INDEPENDENT / 'actual-audit-plan-v2.json'),
                        ('result', independent_result_path),
                        ('lifetime', independent_lifetime_path),
                        ('activation', INDEPENDENT / 'root-activation-v2.json')]:
        if independent_terminal[field] != pin(path):
            raise ValueError('independent terminal binding mismatch: ' + field)
    if (independent_result['outcome_pin'] != pin(tiny_outcome_path)
            or independent_result['plan_sha256'] != pin(INDEPENDENT / 'actual-audit-plan-v2.json')['sha256']
            or independent_lifetime['result_pin'] != pin(independent_result_path)
            or independent_lifetime['plan'] != pin(INDEPENDENT / 'actual-audit-plan-v2.json')):
        raise ValueError('independent tiny exact result/lifetime chain mismatch')
    census = independent_terminal['census']
    if ([census[k] for k in ('controlled_states', 'candidate_comparisons', 'authority_registries',
                            'transactions', 'recorded_dfs_events', 'independently_exhausted_children',
                            'unknown_controls', 'actual_corruptions_rejected', 'separate_positive_controls')]
            != [81, 694, 73, 15, 31, 1, 2, 24, 4]):
        raise ValueError('independent tiny accepted census mismatch')

    first = read(HERE / 'fixtures-lifetime-v1.json')
    second = read(HERE / 'attempt-02/fixtures-lifetime-v1.json')
    cumulative = sum(Decimal(str(x['full_supervisor_process_seconds_including_receipt_write']))
                     for x in (first, second, tiny_lifetime))
    if cumulative != Decimal(str(tiny_lifetime['cumulative_tiny_seconds'])):
        raise ValueError('tiny cumulative failure/success cost mismatch')

    sources = [ROOT / p['path'] for p in readiness['sources']]
    sources += [HERE / 'hilbert_cluster_lifecycle_v1.py',
                ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py',
                Path(__file__)]
    for path in sources:
        ast.parse(path.read_text(), filename=str(path))
    source_pins = [pin(path) for path in sources]
    extras = [
        ('repository_contract', ROOT / 'AGENTS.md'),
        ('full_language_v3_source_ready', HERE / 'full-language-source-ready-v3.json'),
        ('full_language_source_causal_review', HERE / 'full-v2-source-causal-review-v1.json'),
        ('tiny_lifecycle_complete_plan', HERE / 'plan-attempt-03.json'),
        ('new_tiny_lifecycle_outcome', tiny_outcome_path),
        ('new_tiny_lifecycle_lifetime', tiny_lifetime_path),
        ('new_tiny_lifecycle_supervision', tiny_supervision_path),
        ('tiny_lifecycle_producer_conformance_note', HERE / 'producer-conformance-note-v1.json'),
        ('new_tiny_lifecycle_independent_plan', INDEPENDENT / 'actual-audit-plan-v2.json'),
        ('new_tiny_lifecycle_independent_result', independent_result_path),
        ('new_tiny_lifecycle_independent_lifetime', independent_lifetime_path),
        ('new_tiny_lifecycle_independent_terminal_review', independent_terminal_path),
        ('new_tiny_lifecycle_independent_activation', INDEPENDENT / 'root-activation-v2.json'),
    ]
    inputs = list(tiny_plan['inputs']) + [{'role': role, **pin(path)} for role, path in extras]
    if len({p['role'] for p in inputs}) != len(inputs):
        raise ValueError('ambiguous input role')
    for expected in inputs:
        verify(expected)

    # Only already frozen task-owned folders are newly inventoried. No current
    # parent report, publication checkout or independent full-audit draft is used.
    old_entries = []
    for parent in (tiny_plan, independent_plan):
        old_entries += parent['sources'] + parent['inputs'] + parent['preserved_files']
    for folder in (HERE, INDEPENDENT):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path != Path(__file__):
                old_entries.append(pin(path))
    preserved = {}
    for expected in old_entries:
        actual = verify(expected)
        if actual['path'] in preserved and preserved[actual['path']] != actual:
            raise ValueError('conflicting historical source pin')
        preserved[actual['path']] = actual
    for p in source_pins + inputs:
        if p['path'] in preserved and preserved[p['path']] != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('source/input differs from preserved bytes')

    old_outcome = read(ROOT / readiness['prior_point_outcome']['path'])
    epoch = old_outcome['model_epoch']
    if epoch != '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c':
        raise ValueError('frozen old point-model epoch changed')
    observations = [
        'full_initial_registry_and_graph', 'shared_exact_member_after_branch_action',
        'whole_uniqueness_family_retired_with_legal_siblings', 'full_parent_graph_and_hints_revived',
        'remote_marks_global_forced_before_hint_action', 'after_global_forced_shared_member',
        'after_second_global_forced_family_member', 'remote_forced_parent_revived',
        'whole_distant_cluster_retired_legal_axiom_sibling', 'distant_hint_revived_exact_shared_state',
        'post_rejection_unchanged_complete_graph',
    ]
    plan = {
        'version': 'full-actual-language-whole-cluster-lifecycle-plan-v3',
        'status': 'frozen_full_actual_source_inputs_prerequisites_root_and_independent_review_pending_dispatch',
        'saved_utc': datetime.now(timezone.utc).isoformat(),
        'filename_reason': 'Exact unoccupied full-language-plan-v3.json is required by all three frozen scientific v3 scripts. Old readiness prose naming v2 remains immutable historical evidence.',
        'sources': source_pins, 'inputs': inputs,
        'preserved_files': [preserved[k] for k in sorted(preserved)],
        'tiny_independent_accepted_status': TINY_ACCEPTED,
        'source_ready_checkpoint': pin(HERE / 'full-language-source-ready-v3.json'),
        'producer_limits': {'outer_wall_seconds': 180, 'supervisor_seconds': 175,
                            'child_alarm_seconds': 170, 'host_bytes': 536870912,
                            'scope': 'One separately authorized full actual controlled phase, not a retry or extension of the tiny phase.',
                            'execution_authorized_by_this_freeze': False},
        'resource_enforcement': {'owned_child': 'Fail-closed external /bin/ps sampled RSS/time watchdog; failure kills and waits/reaps the owned child.',
            'alarm': 'Worker SIGALRM at 170 seconds.',
            'post_reap': 'Supervisor own+child kernel peak rejection and outer own+max(children kernel peak, supervisor conservative peak).',
            'OS_soft_limit_claim': 'none',
            'clock_scope': 'Outer includes pin checks, entire child, reaping and worker/supervisor receipts; final outer own receipt write excluded and explicitly disclosed.',
            'permitted_metadata': 'Read-only RSS of this task-owned bounded child only; root dispatch should request sandbox escalation if necessary, never omit the sampler.'},
        'exact_model': {'prior_point_plan': readiness['prior_point_plan'],
            'prior_point_outcome': readiness['prior_point_outcome'], 'model_epoch': epoch,
            'primitive_recipes': 229, 'formula_values': 217, 'required_rows': 24,
            'translation_only_orientation': 'identity', 'root_generation': 0,
            'global_seed_placements': 3, 'global_seed_generation': 0,
            'zero_absent_semantics': 'Formula code zero is an assigned m-value; absent points remain unconstrained.',
            'new_provenance': 'BodyAuthority adds current frozen input/native/source/audit receipts only; primitive model is loaded from its exact prior point plan.',
            'local_assumptions': 'Canonical per-definition receptor aliases add no global recipient seeds or occupancy.'},
        'prospective_counts': {'all_source_family_bodies': 171, 'fixed_primitive_proposal_bodies': 4,
            'complete_body_registry': 175, 'fixed_descriptors': 5, 'controlled_states': 11,
            'complete_state_ceiling': 12, 'actual_counts_not_measured_by_this_freeze': True},
        'planned_controlled_state_labels': observations,
        'full_candidate_obligations': [
            'Stream the full raw recipe/ordered strict-prior offset language at every row in every declared state and compare every key, t and m against complete implicit domains.',
            'Record all 229 per-recipe counts and exact complete stream digests; certify zero/singleton from full language, never proposal lists.',
            'Reconstruct global dead/forced/earliest-generation decision; hints cannot change point degree or later-point priority.',
            'At selected decision row, fixed preferred order plus complete base fallback is a full permutation; forced row uses the exact base singleton.',
            'Register every 171 source body and four authored fixed primitive proposal bodies; validate exact primitive member/receptor transport and full authority/body/identity bindings.',
            'Check waiting/ready/consumed/whole branch-absorbing retirement, exact shared member identity, forced-first resynchronization, and paired rollback before observational resynchronization.',
            'Reject point-consistent changed family body with freshly recomputed identity/cache/self-hash, plus changed model/context/authority/formula epochs.',
            'Low-level remote-mark and same-output/different-reference catalog transactions are explicitly controls, not scheduler-valid search actions.',
        ],
        'exhaustion_scope': 'No full-model failed-child pruning is manufactured or tested by this controlled gate. The accepted tiny independent DFS establishes its one exhausted-child exclusion and two unknown restorations; full actual DFS discovery remains outside scope.',
        'no_authored_target_seed': 'Old authored24 witness is bound as historical evidence only; worker never reads its proof word. Compact family projection discards its example field and loads all 171 bodies. Fixed controls are not a target derivation or training data.',
        'outputs': {name: str((HERE / name).relative_to(ROOT)) for name in proposed_outputs},
        'expected_outcome_schema': ['comparisons', 'states', 'controlled_operations', 'authority_registry',
            'descriptors', 'rejected_corruptions', 'identities', 'full_source_bodies',
            'complete_primitive_recipes', 'formula_values', 'required_rows', 'exact_prior_point_model_epoch',
            'lifecycle_source_relation_epoch', 'controlled_states', 'all_state_candidate_key_t_m_comparisons',
            'graph_metrics', 'lifecycle_metrics', 'preparation_costs', 'worker_seconds_before_receipt_write'],
        'expected_child_status_if_all_authored_checks_pass': 'passed_authored_full_language_lifecycle_controls_pending_independent_audit',
        'independent_actual_gate': 'External independently owned reconstruction is separately frozen and root-reviewed before its own dispatch; source freeze and producer acceptance cannot replace it.',
        'cost_accounting': {
            'tiny_first_failed_seconds': first['full_supervisor_process_seconds_including_receipt_write'],
            'tiny_second_failed_seconds': second['full_supervisor_process_seconds_including_receipt_write'],
            'tiny_third_accepted_seconds': tiny_lifetime['full_supervisor_process_seconds_including_receipt_write'],
            'tiny_cumulative_seconds_including_failures': float(cumulative),
            'independent_tiny_owned_seconds': independent_lifetime['full_owner_and_worker_seconds_before_receipt_write'],
            'independent_tiny_terminal_metadata_seconds': independent_terminal['metadata_reconciliation_seconds_before_receipt_write'],
            'tiny_child_peak_bytes': tiny_lifetime['conservative_host_peak_bytes'],
            'independent_tiny_peak_bytes': independent_lifetime['conservative_combined_peak_bytes'],
            'budget_separation': 'Prior tiny and audit work stays charged separately; it is not silently reset or subtracted from this new 180-second full phase.',
            'earlier_work': 'All prior geometry native admission/repair/resource-unknown/static expansion/primitive full-model bills remain bound by preserved evidence. Cached family source authority is not free or freshly native-admitted.',
            'full_source_authoring': 'Unmeasured; no cross-process monotonic subtraction or CPU effort claim.',
            'new_static_freeze_seconds_before_plan_write': time.perf_counter() - started,
            'future_full_exports': 'Within-process family preparation, descriptor/controller preparation, and cumulative graph/hint scan/order/rollback counters. The old tiny omission of exported subphase counters remains.'},
        'authority_scope': 'Finite checked symbolic source relation and host point/hint conformance only. Native/compiler preservation, formal aggregate execution correspondence, arbitrary graph-metadata mutation protocol and searched higher geometry theorem remain separate obligations.',
        'owner_command_after_root_review_only': 'python3 .gcts-active/hilbert-cluster-lifecycle-20261011/hilbert_cluster_full_outer_v3.py',
        'actual_model_executions_by_this_freeze': 0, 'target_DFS_searches': 0, 'native_queries': 0,
        'compiler_changes': 0, 'new_RL_training': False, 'native_authority_activation': False,
        'static_validation': 'stdlib hashing/read-only JSON receipt reconciliation and ast.parse only; no kernel import, model load or scientific execution.'}
    immutable_save(planpath, plan)
    receipt = {'status': 'full_actual_language_v3_source_and_input_freeze_no_scientific_execution',
        'plan': pin(planpath), 'sources': len(source_pins), 'inputs': len(inputs),
        'preserved_files': len(preserved),
        'unique_verified_paths': len({p['path'] for p in source_pins + inputs + list(preserved.values())}),
        'all_historical_source_and_input_bytes_match': True,
        'freeze_seconds_before_receipt_write': time.perf_counter() - started,
        'output_file_absence_checked': proposed_outputs,
        'tiny_prerequisite_result': pin(independent_result_path),
        'future_actual_dispatch': 'root-owned only, pending source/plan review',
        'actual_model_loads': 0, 'target_searches': 0, 'native_queries': 0, 'authority_activations': 0}
    immutable_save(receiptpath, receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
