"""STATIC ONLY: exact source/input freeze for a prospective geometry search.

Hashing, AST parsing and receipt JSON metadata are allowed here. This script
does not import an engine, parse a scientific model, execute a helper, authorize
dispatch or activate native/compiler authority. Root owns subsequent reviews.
"""
import ast
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LIFE = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'
AUDIT = ROOT / '.gcts-active/hilbert-cluster-full-independent-20261011'
BRIDGE = ROOT / '.gcts-active/shared-symbolic-native-bridge-20261011'
TERMINALS = ROOT / '.gcts-active/full-model-cluster-progress-20261011'
EPOCH = '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def verify(entry):
    result = pin(ROOT / entry['path'])
    if result != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('exact previous evidence changed: ' + entry['path'])
    return result


def save(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.perf_counter()
    planpath, receiptpath = HERE / 'search-plan-v1.json', HERE / 'source-freeze-v1.json'
    manifestpath = HERE / 'source-manifest-v1.json'
    outputs = ['base-complete-primitives-result-v1.json.gz', 'fixed-forward-novelty-result-v1.json.gz',
               'search-outcome-v1.json', 'search-launch-v1.json', 'search-supervision-v1.json',
               'search-lifetime-v1.json', 'search-stdout-v1.txt', 'search-stderr-v1.txt']
    for path in (planpath, receiptpath, manifestpath):
        if path.exists(): raise ValueError('immutable source freeze exists: ' + path.name)
    if (HERE / 'root-activation-v1.json').exists() or any((HERE / name).exists() for name in outputs):
        raise ValueError('source-only phase must have no dispatch or scientific artifacts')

    fullplan = read(LIFE / 'full-language-plan-v3.json')
    independentplan = read(AUDIT / 'audit-plan-v1.json')
    inspection = read(BRIDGE / 'static-source-inspection-v1.json')
    proposal = read(BRIDGE / 'prospective-search-gate-v1.json')
    bridgemanifest = read(BRIDGE / 'manifest-v1.json')
    for p in bridgemanifest['files']: verify(p)
    if proposal['model']['model_epoch'] != EPOCH or proposal['model']['boundary_changed'] is not False:
        raise ValueError('frozen original symbolic boundary/epoch required')
    if [proposal['model'][k] for k in ('formulas', 'recipes', 'rows', 'all_family_bodies_validated', 'active_cluster_descriptors')] != [217, 229, 24, 171, 0]:
        raise ValueError('cannot substitute a smaller language or authored proposal pool')

    # These accepted receipts are metadata, not new model/audit executions.
    fullresult = read(AUDIT / 'audit-result-v1.json')
    lifetime = read(AUDIT / 'audit-lifetime-v1.json')
    terminal = read(TERMINALS / 'root-full-independent-terminal-v1.json')
    scope = read(AUDIT / 'scope-clarification-v1.json')
    if fullresult['status'] != 'passed_independent_full_language_lifecycle_controlled_artifact_audit':
        raise ValueError('full actual lifecycle independent prerequisite missing')
    if (lifetime['status'] != 'passed_owned_independent_full_language_lifecycle_audit'
            or lifetime['child_exit_code'] != 0 or not lifetime['owned_child_terminal_and_reaped']
            or lifetime['full_owner_and_worker_seconds_before_receipt_write'] > 180
            or lifetime['conservative_combined_peak_bytes'] > 536870912):
        raise ValueError('accepted full actual independent lifetime incomplete')
    if (terminal['status'] != 'passed_root_terminal_receipt_check'
            or not terminal['all_owned_handles_terminal'] or terminal['exec_exit'] != 0
            or terminal['result'] != pin(AUDIT / 'audit-result-v1.json')
            or terminal['lifetime'] != pin(AUDIT / 'audit-lifetime-v1.json')
            or lifetime['result_pin'] != terminal['result']
            or lifetime['plan'] != pin(AUDIT / 'audit-plan-v1.json')
            or scope['terminal_result'] != terminal['result']
            or scope['root_terminal_reconciliation'] != pin(TERMINALS / 'root-full-independent-terminal-v1.json')):
        raise ValueError('full actual independent accepted source/receipt chain mismatch')
    if [terminal[k] for k in ('states', 'comparisons', 'source_bodies', 'corruptions')] != [11, 2979447, 171, 24]:
        raise ValueError('previous accepted census changed')

    sourcepaths = [HERE / name for name in (
        'shared_symbolic_geometry_search_v1.py', 'shared_symbolic_forward_order_v1.py',
        'shared_symbolic_bridge_decode_v1.py', 'shared_symbolic_search_run_v1.py',
        'shared_symbolic_search_outer_v1.py', 'shared_symbolic_search_freeze_v1.py')]
    sourcepaths += [LIFE / 'hilbert_cluster_lifecycle_v1.py',
                    ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py']
    for path in sourcepaths: ast.parse(path.read_text(), filename=str(path))
    sources = [pin(path) for path in sourcepaths]

    extras = [
        ('frozen_lifecycle_kernel', LIFE / 'hilbert_cluster_lifecycle_v1.py'),
        ('passed_full_lifecycle_producer_plan', LIFE / 'full-language-plan-v3.json'),
        ('passed_full_lifecycle_producer_outcome', LIFE / 'full-language-outcome-v3.json'),
        ('passed_full_lifecycle_producer_lifetime', LIFE / 'full-language-lifetime-v3.json'),
        ('passed_full_lifecycle_producer_supervision', LIFE / 'full-language-supervision-v3.json'),
        ('passed_full_lifecycle_root_producer_terminal', TERMINALS / 'root-full-producer-terminal-v3.json'),
        ('full_lifecycle_independent_plan', AUDIT / 'audit-plan-v1.json'),
        ('full_lifecycle_independent_result', AUDIT / 'audit-result-v1.json'),
        ('full_lifecycle_independent_lifetime', AUDIT / 'audit-lifetime-v1.json'),
        ('full_lifecycle_independent_activation', AUDIT / 'root-activation-v1.json'),
        ('full_lifecycle_root_terminal', TERMINALS / 'root-full-independent-terminal-v1.json'),
        ('full_lifecycle_independent_scope_clarification', AUDIT / 'scope-clarification-v1.json'),
        ('prior_bridge_five_file_manifest', BRIDGE / 'manifest-v1.json'),
        ('prior_bridge_source_inspection_freezer', BRIDGE / 'freeze_source_inspection_v1.py'),
        ('prior_bridge_static_source_inspection', BRIDGE / 'static-source-inspection-v1.json'),
        ('prior_bridge_design', BRIDGE / 'bridge-design-v1.json'),
        ('prior_bridge_prospective_search_gate', BRIDGE / 'prospective-search-gate-v1.json'),
    ]
    inputs = list(fullplan['inputs']) + [{'role': role, **pin(path)} for role, path in extras]
    # The mapping/decoder can be traced to exact shared machine sources without
    # importing, compiling or running them. Their hashes are also historical pins.
    inputs += [{'role': 'shared_machine_source_' + str(i).zfill(2), **verify(p)}
               for i, p in enumerate(inspection['sources'])]
    inputs += [{'role': 'shared_machine_artifact_' + str(i).zfill(2), **verify(p)}
               for i, p in enumerate(inspection['inputs'])]
    if len({p['role'] for p in inputs}) != len(inputs): raise ValueError('ambiguous input role')

    preserved = {}
    oldentries = []
    for parent in (fullplan, independentplan, inspection):
        for key in ('sources', 'libraries', 'inputs', 'preserved_files'):
            oldentries.extend(parent.get(key, []))
    # Capture task-owned stable raw lifetimes/failures and source successors only;
    # no current parent-report generator or publication checkout is included.
    for folder in (LIFE, AUDIT, BRIDGE):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts: oldentries.append(pin(path))
    oldentries += [p for p in inputs]
    for p in oldentries:
        q = verify(p)
        if q['path'] in preserved and preserved[q['path']] != q:
            raise ValueError('conflicting historical versions')
        preserved[q['path']] = q
    for p in sources + inputs:
        verify(p)
        if p['path'] in preserved and preserved[p['path']] != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('new input differs from previous frozen source')

    spec = proposal['fixed_forward_order_spec']
    plan = {
        'version': 'automatic-shared-symbolic-geometry-source-plan-v1',
        'status': 'frozen_source_only_root_and_independent_review_pending_no_dispatch',
        'saved_utc': datetime.now(timezone.utc).isoformat(),
        'sources': sources, 'inputs': inputs, 'preserved_files': [preserved[k] for k in sorted(preserved)],
        'prerequisites': {'full_actual_independent_result': pin(AUDIT / 'audit-result-v1.json'),
                         'full_actual_independent_lifetime': pin(AUDIT / 'audit-lifetime-v1.json'),
                         'root_terminal': pin(TERMINALS / 'root-full-independent-terminal-v1.json'),
                         'read_hint_scope_clarification': pin(AUDIT / 'scope-clarification-v1.json')},
        'model_epoch': EPOCH, 'model': proposal['model'],
        'observations': [
            {'id': 'base-complete-primitives', 'mode': 'base', 'attempts': 128, 'seconds': 20, 'event_ceiling': 2000},
            {'id': 'fixed-forward-novelty', 'mode': 'fixed-forward', 'attempts': 128, 'seconds': 20, 'event_ceiling': 2000}],
        'ordering_specification': spec,
        'source_boundaries': {
            'grammar': 'Same 229 recipes: 144 literal ordered two-port MP, 1 named guarded I.2 axiom, 3 exact recipient assumptions, 54 instantiation implications, 27 equality-substitution implications. No new rules or formulas.',
            'context': 'Original exact ordered three ground hypotheses and retained guarded I.2; local definition hypotheses never enter global seeds.',
            'boundary': '24 active positive obligations and exactly three seeded placements at generation zero; fixed original target and full negative-row formula exterior sentinel; translation only.',
            'source_body_registry': 'Validate all 171 registered finite bodies with complete source/native/dependency bindings; no active descriptors or body proposal keys.',
            'degree': 'Complete implicit domains from every recipe and every ordered strict-prior reference binding, all remote marking filters, explicit zero/absent distinctions and exact distinct identity multiplicity.',
            'scheduler': 'Unchanged primitive decision/step enforces global dead, global forced then earliest generation; full chosen domain enumerated before ordering.',
            'fallback': 'Base and fixed ordering are complete permutations; no shortlist or learned exclusion. Every proved exhausted child is excluded only in restored parent.',
            'rollback': 'Paired graph/hint checkpoints with exact whole initial semantic state restored for unknown or complete finite exhaustion.',
            'trace': 'Every node/decision/order/step/exclusion/rollback stores full semantic SHA and exact point/row/refcount/exclusion/hint projection; independent decoder reconstructs omitted factor tables from complete frozen language.',
            'trace_cutoff': '2,000-event cutoff may truncate the final operation trace; label unknown_trace_budget, restore exact paired root, never certify such a truncated subtree or add an unknown-child exclusion.',
            'decoder': 'Every 24 logical row command, ordered MP reference and full decorated identity remains present. Ground assumptions become exact fresh named axioms for the same Gamma-relative sequent; no discharge, universal closure, proof compression or rewritten theorem.',
            'authority': 'Host finite source relation only, native_accepted false. Symbolic checking is separately owned. Shared FOL-machine request bytes can be decoded but no native encoding/acceptance or universal palette activation occurs here.'},
        'limits': {'owner_seconds': 180, 'supervisor_seconds': 175, 'child_alarm_seconds': 170,
                   'host_bytes': 536870912, 'maximum_searches': 2, 'each_attempts': 128,
                   'each_search_seconds': 20, 'each_trace_event_ceiling': 2000,
                   'independent_audit_proposal_seconds': 180, 'independent_audit_proposal_bytes': 536870912},
        'resources': {
            'owner': 'Root alone dispatches one separately reviewed bounded phase through shared_symbolic_search_outer_v1.py. Root activation must bind exact plan bytes; this freeze creates no activation.',
            'enforcement': 'Task-owned fail-closed sampled own-child /bin/ps RSS/time watchdog, worker SIGALRM, supervisor SIGALRM/SIGTERM kill-and-reap cleanup, retrospective kernel peak gate. No OS soft limit claim.',
            'outer': 'Includes verification, worker/supervisor execution, serialization and reap; outer own final receipt write excluded explicitly. Cleanup overshoot retained as unknown and charged.',
            'peak': 'supervisor own + fresh child kernel peak; outer own + max(outer children kernel peak, supervisor conservative combined peak), avoiding inherited child double counting.',
            'failure': 'Metadata failure or missing sample kills/reaps child and returns unknown. No retry or revised budget without a preserved source/input successor and review.'},
        'independent_next_gate': {
            'not_authorized_by_this_freeze': True,
            'owner': 'external_prover_control authors separate source/plan; root alone dispatches after terminal producer',
            'domains': 'Reconstruct complete primitive legal keys/counts at every trace state, validate scheduler decisions, chosen full permutations, every t/m change, exact rollback/refcounts/exclusions and all used primitive inference commands.',
            'exhaustion': 'Every recorded excluded child must have full reconstructed finite failure/exhaustion, all alternatives covered, no resource-cutoff descendant. Unknown restores parent without excluding it.',
            'fixed_order': 'Recompute exact generic AST/readiness/novelty tiers and both key stream hashes; no target-specific proof oracle.',
            'certificate': 'Check original theory/hypotheses/target, strict-prior ordered references, full point identity/preimage/placement and every primitive inference; decode the exact flat request independently.',
            'adversaries': 'Changed omitted legal candidate/singleton/dead label, false exhausted-child exclusion, rollback/reference count, remote zero/absence, ordered port multiplicity, decorated identity, native authority label, altered formula/theory/target, changed or dropped command/reference, stale body/source binding.'},
        'outcome_labels': {
            'finite_exact_point_tiling': 'Complete finite point certificate only, pending independent symbolic proof and whole trace audit.',
            'exhausted_finite_marked_subtree': 'If root returns exhausted, only the unchanged complete 24-row marked finite language was exhausted; no mathematical unprovability claim.',
            'unknown_search_budget': 'Attempt/time limit and exact root restoration; no unknown-child exclusions.',
            'unknown_trace_budget': 'Exact root restoration; truncated trace cannot certify finite exhaustion.',
            'owner_resource_unknown': 'Preserve partial raw outputs/receipts; no whole acceptance or automatic retry.'},
        'costs': {
            'source_authoring': 'Unmeasured; no cross-process monotonic subtraction or CPU-effort estimate.',
            'new_static_freeze_seconds_before_plan_write': time.perf_counter() - started,
            'prior_preparation': 'All source native admissions (including original 546.8-second bill), all failed resource/serialization/loading attempts, finite transport and full primitive/lifecycle audits remain exact pinned dependencies, not free or newly native-admitted.',
            'cold_lane_setup': 'Each lane independently reloads exact model and validates all 171 families; separate setup, engine import and source verification timers are exported.',
            'search_subphases': 'Record fixed features/sort/permutation, complete domain ordering/hashing, graph/lifecycle counters, primitive step/resync, trace snapshots, exclusions and rollback timings. Overlapping subphase timers must not be summed as disjoint wall costs.',
            'total': 'Whole owner time includes cold preparation, all search work, decoder, serialization and supervisor costs. Separate independent audit and any later native query/replay are additional costs.',
            'inference_scope': 'One observation per order, no significance claim, new RL training or general speed comparison.'},
        'later_shared_native_gate': {**proposal['later_native_gate'], 'not_authorized_here': True,
            'label': 'No native gate implementation or request execution in this source phase; any later exact request/band/lifetime source plan requires fresh root review.'},
        'proposed_outputs': outputs,
        'root_command_after_two_source_reviews_and_exact_activation': 'python3 ' + str(HERE / 'shared_symbolic_search_outer_v1.py'),
        'scientific_executions_by_this_freeze': 0, 'model_constructions_by_this_freeze': 0,
        'native_queries': 0, 'compiler_activations': 0, 'training_episodes': 0,
        'active_cluster_descriptors': 0, 'authored_words_used_as_hints': 0,
        'read_scope': 'Compact family reader may physically decode example bytes before discarding them; no authored word is an ordering hint, proposal or mathematical acceptance authority.',
        'publication_owner': 'root', 'execution_authorized_by_this_freeze': False}
    save(planpath, plan)
    receipt = {'status': 'frozen_source_only_automatic_geometry_implementation_no_scientific_execution',
        'plan': pin(planpath), 'new_sources': 6, 'source_closure_count': len(sources), 'inputs': len(inputs),
        'preserved_files': len(preserved), 'unique_verified_paths': len({p['path'] for p in sources + inputs + list(preserved.values())}),
        'ast_parse_sources': len(sourcepaths), 'mismatches': 0,
        'freeze_seconds_before_receipt_write': time.perf_counter() - started,
        'source_authoring_seconds': None, 'actual_geometry_model_loads': 0, 'geometry_searches': 0,
        'native_queries': 0, 'compiler_activations': 0, 'training': False,
        'active_cluster_descriptors': 0, 'authored_words_used_as_hints': 0,
        'root_and_independent_source_reviews': 'pending', 'execution_authorized': False}
    save(receiptpath, receipt)
    files = [pin(path) for path in sourcepaths[:6]] + [pin(planpath), pin(receiptpath)]
    manifest = {'status': 'immutable_source_only_package_pending_two_source_reviews_and_root_dispatch',
        'files': files, 'total_files': len(files), 'total_bytes': sum(p['bytes'] for p in files),
        'plan': pin(planpath), 'scientific_executions': 0, 'native_queries': 0,
        'publication_owner': 'root', 'claim': 'Executable authored infrastructure and prospective bounded gate only; no proof discovery or model execution.'}
    save(manifestpath, manifest)
    print(json.dumps({'plan': pin(planpath), 'receipt': pin(receiptpath), 'manifest': pin(manifestpath),
                      'sources': len(sources), 'inputs': len(inputs), 'preserved': len(preserved)}, indent=2))


if __name__ == '__main__': main()
