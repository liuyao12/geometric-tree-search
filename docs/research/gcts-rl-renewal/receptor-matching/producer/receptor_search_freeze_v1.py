"""Static source/input/preservation freeze only; never import scientific code."""
import ast
import copy
import difflib
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = ROOT / '.gcts-active/shared-symbolic-geometry-search-source-v2-20261011'
TRACE = ROOT / '.gcts-active/shared-symbolic-geometry-trace-independent-20261011'
TRACE_REVIEW = ROOT / '.gcts-active/automatic-geometry-actual-independent-review-20261011'
PROGRESS = ROOT / '.gcts-active/automatic-geometry-progress-20261011'
DIAGNOSIS = ROOT / '.gcts-active/automatic-geometry-search-diagnosis-20261011'
CROSS = ROOT / '.gcts-active/receptor-matching-cross-domain-source-20261011'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def verify(entry):
    actual = pin(ROOT / entry['path'])
    if actual != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('historical source/pin changed: ' + entry['path'])
    return actual


def save(name, value):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.perf_counter()
    if any((HERE / name).exists() for name in ('search-plan-v1.json', 'matcher-contract-v1.json',
            'source-freeze-v1.json', 'source-manifest-v1.json', 'root-activation-v1.json', 'search-outcome-v1.json')):
        raise ValueError('immutable search freeze/activation/output already exists')
    old = read(OLD / 'search-plan-v1.json')
    for entry in old['sources'] + old['inputs'] + old['preserved_files']:
        verify(entry)
    if len(old['inputs']) != 118:
        raise ValueError('preserve exact broader predecessor phase inputs')
    oldroles = {p['role']: ROOT / p['path'] for p in old['inputs']}
    bodyplan = read(oldroles['passed_full_lifecycle_producer_plan'])
    if (len(bodyplan['inputs']) != 56 or len({p['path'] for p in bodyplan['inputs']}) != 56
            or old['inputs'][:56] != bodyplan['inputs']):
        raise ValueError('exact accepted full 56-path body-source relation required')
    for entry in bodyplan['sources'] + bodyplan['inputs'] + bodyplan['preserved_files']:
        verify(entry)
    # Caller adapter uniqueness and complete projected registry remain source
    # metadata, not a substitute for importing/constructing a registry here.
    required_body_roles = ('complete_family_template_projection', 'primitive_logical_audit',
        'source_constant_transport_certificate', 'source_searched_native_receipt',
        'full_exact_source_expansions', 'prior_full_model_plan')
    for role in required_body_roles:
        entry = next(p for p in bodyplan['inputs'] if p['role'] == role)
        if entry != next(p for p in old['inputs'] if p['role'] == role):
            raise ValueError('body/source closure projection changed')
    terminal_review = read(TRACE_REVIEW / 'terminal-review-v1.json')
    if (terminal_review['status'] != 'passed_read_only_terminal_reconciliation_of_owned_independent_geometry_trace_audit'
            or not terminal_review['authority']['actual_audit_passed']
            or terminal_review['authority']['point_certificates'] != 0
            or terminal_review['terminal']['active_handles'] != 0):
        raise ValueError('actual old returned UNKNOWN trace audit prerequisite incomplete')
    for key in ('actual_result', 'actual_lifetime', 'plan', 'root_terminal', 'root_activation', 'source_manifest', 'source_freeze'):
        verify(terminal_review[key])
    pure_lifetime = read(HERE / 'pure-ast-lifetime-v1.json')
    pure = read(HERE / 'pure-ast-outcome-v1.json')
    if (pure_lifetime['status'] != 'passed_bounded_pure_AST_owner_gate'
            or pure['status'] != 'passed_bounded_pure_AST_matcher_controls'
            or pure['record_count'] != 64 or not pure_lifetime['child_wait_reaped']
            or any(pure[field] != 0 for field in ('actual_model_loads', 'engine_imports', 'ordering_graph_calls', 'searches', 'native_queries'))):
        raise ValueError('exact bounded pure-AST controls not passed')
    pureplan = read(HERE / 'pure-ast-plan-v1.json')
    for entry in pureplan['sources'] + pureplan['inputs']:
        verify(entry)
    same = ('shared_symbolic_forward_order_v1.py', 'shared_symbolic_bridge_decode_v1.py',
            'shared_symbolic_search_run_v1.py', 'shared_symbolic_search_outer_v1.py')
    for name in same:
        if (HERE / name).read_bytes() != (OLD / name).read_bytes():
            raise ValueError('unchanged fixed order/decoder/owner copy differs: ' + name)
    workername = 'shared_symbolic_geometry_search_v1.py'
    before = (OLD / workername).read_text()
    expected = before
    replacements = [
        ('from shared_symbolic_forward_order_v1 import ForwardOrder\n',
         'from shared_symbolic_forward_order_v1 import ForwardOrder\nfrom receptor_literal_match_v1 import ReceptorOrder\n'),
        ("    if mode not in ('base', 'fixed-forward'):\n", "    if mode not in ('fixed-forward', 'fixed-forward-receptor'):\n"),
        ("    ordering = ForwardOrder(graph) if mode == 'fixed-forward' else None\n",
         "    ordering = ForwardOrder(graph) if mode == 'fixed-forward' else ReceptorOrder(graph)\n"),
        ("              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode)\n",
         "              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode,\n              receptor_feature_trace=(copy.deepcopy(ordering.last_trace)\n                  if mode == 'fixed-forward-receptor' and decision.kind == 'branch' else None))\n"),
        ("            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,\n",
         "            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,\n            'receptor_pattern_registry': copy.deepcopy(ordering.pattern_records)\n                if mode == 'fixed-forward-receptor' else None,\n")]
    for needle, replacement in replacements:
        if expected.count(needle) != 1:
            raise ValueError('exact caller/order trace source boundary changed')
        expected = expected.replace(needle, replacement)
    after = (HERE / workername).read_text()
    if after != expected:
        raise ValueError('unlisted worker/scientific core diff')
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='frozen-search-v2/' + workername, tofile='receptor-v1/' + workername))
    if (HERE / 'worker-v2-to-receptor-v1.diff').read_text() != diff:
        raise ValueError('minimal source diff receipt mismatch')

    contract = {'status': 'frozen_literal_structural_receptor_order_contract_not_a_logic_rule',
        'API': {'pattern_from_guard': 'guard AST, ordered distinct prefix_binders, source label => literal-receptor-pattern-v1 record',
            'extract_pattern': 'witness plus declared ordered premise ASTs => pattern record',
            'literal_guard_match': 'pattern record plus closed quantifier-free recipient AST => status/bucket/successful bindings/reason',
            'evaluate_pattern': 'pattern record plus selected records {key,formula_code,formula} => per-key comparisons/matches and aggregate bucket',
            'ReceptorOrder': 'same graph interface as frozen ForwardOrder; complete chosen keys only; no native/logic oracle'},
        'extractors': {'instantiate': 'Require exact declared universal as outer implication antecedent. Inspect consequent; peel leading universal binders with distinct nonempty string names; immediate implication guard only.',
            'mp': 'Read exact first ordered premise as a rigid zero-slot guard; require second ordered premise literally equals implication(first, witness output). Do not inspect equality output as a guard and do not peel a quantified MP antecedent.',
            'other_rules': 'neutral, including equality-substitution and named axiom recipes'},
        'syntax': {'formula_constructors': ['pred', 'eq', 'not', 'and', 'imp', 'bot'],
            'literal_compound_term_constructors': 'Recursive fun(name,args) supported, including pattern slots inside constructors.',
            'slot_images': 'Only closed fun(name,[]) with nonempty string name; different slots may share the same image.',
            'rigid_constants': 'Already completed instantiation constants stay literal; cannot be rebound.',
            'prefix_slots': 'Exactly variables in the distinct peeled leading prefix; free/out-of-scope variables neutral.',
            'unsupported': 'Repeated/shadowed/empty prefix names; nested quantified guard or quantified/free recipient; unknown constructor or empty symbol; compound slot image. Literal or/exists are neutral in this first narrow subset.',
            'no_rewrites': 'No conjunction flattening, commutativity, equality symmetry, logical consequence, unification of selected proof commands or satisfiability test.'},
        'pair_precedence': 'Validate pattern/recipient shape first. Then compare literal tree in ordered traversal. Any definite constructor/polarity/symbol/arity/repeated-image mismatch dominates unsupported image elsewhere; otherwise an unsupported compound slot image is neutral. Successful bindings only; nonmatch/neutral bindings are empty.',
        'aggregation': 'Any exact supported selected match => match. Otherwise at least one supported nonmatch => nonmatch, even with other neutral recipients. Otherwise neutral. Nonmatch describes only the supported selected subset, never logical impossibility.',
        'score_order': {'match': 0, 'neutral': 1, 'nonmatch': 2},
        'complete_score': 'unchanged old readiness tier, then receptor bucket, then original AST size/canonical witness/recipe index/ordered references',
        'readiness': 'Exact original per-key tier conditions copied literally, substituting only the local name selected_outputs for historical proved. Physically selected output constraints may have pending ordered sources and are not established hypotheses/derivations.',
        'selected_only': 'Collect g.selected output codes/formula ASTs and exact keys. No formula from g.m or an empty row is consulted; same formula at distinct selected keys remains distinct.',
        'fallback': 'No candidate removal, merging, changed row scheduling, threshold, match-count bonus, degree update, marking, exclusion or descriptor. Every old legal alternative remains.',
        'trace_schema': {'registry': 'Full per-recipe pattern records once in each new-control result.',
            'per_branch': 'Selected exact key/formula-code records; per-recipe label/bucket/matches with bindings and distinct keys; count/label counts and SHA of every comparison; SHA of full sorted {key,score} stream.',
            'forced': 'receptor_feature_trace is null; forced singleton uses exact base key with no stale branch feature trace.',
            'timing': 'Aggregate separate selected-collection, pattern preparation, literal matching, score-feature, sort, permutation and payload/hash clocks; enclosing search/trace/order clocks overlap and must not be summed.'},
        'pure_controls': {'outcome': pin(HERE / 'pure-ast-outcome-v1.json'), 'lifetime': pin(HERE / 'pure-ast-lifetime-v1.json'),
            'records': 64, 'scope': 'Pure AST/selected-record only, no actual graph/order/model/search/native or mathematical proof acceptance.'},
        'scope_limit': 'Finite formula-color point model still differs from universal shared FOL-machine Wang palette. This authored fixed feature is not new RL training or a proof-search superiority claim.'}
    save('matcher-contract-v1.json', contract)
    sourcepaths = [HERE / name for name in (workername, *same, 'receptor_literal_match_v1.py',
        'pure_ast_fixtures_v1.py', 'pure_ast_owner_v1.py', Path(__file__).name)]
    sourcepaths += [ROOT / entry['path'] for entry in old['sources'][-2:]]
    for path in sourcepaths:
        ast.parse(path.read_text(), filename=str(path))
    sources = [pin(path) for path in sourcepaths]
    inputs = copy.deepcopy(old['inputs'])
    additions = {
        'previous_automatic_search_plan': OLD / 'search-plan-v1.json',
        'previous_automatic_producer_terminal': PROGRESS / 'root-producer-v2-terminal.json',
        'previous_automatic_independent_trace_result': ROOT / terminal_review['actual_result']['path'],
        'previous_automatic_independent_trace_lifetime': ROOT / terminal_review['actual_lifetime']['path'],
        'previous_automatic_independent_terminal_review': TRACE_REVIEW / 'terminal-review-v1.json',
        'previous_automatic_independent_root_terminal': ROOT / terminal_review['root_terminal']['path'],
        'metadata_only_diagnosis': DIAGNOSIS / 'diagnosis-v1.json',
        'prospective_receptor_design': DIAGNOSIS / 'next-gate-plan-v1.json',
        'literal_matcher_contract': HERE / 'matcher-contract-v1.json',
        'pure_AST_control_plan': HERE / 'pure-ast-plan-v1.json',
        'pure_AST_control_freeze': HERE / 'pure-ast-source-freeze-v1.json',
        'pure_AST_control_outcome': HERE / 'pure-ast-outcome-v1.json',
        'pure_AST_control_lifetime': HERE / 'pure-ast-lifetime-v1.json',
        'independent_cross_domain_corpus': CROSS / 'synthetic-corpus-v2.json',
        'independent_cross_domain_reference': CROSS / 'synthetic-reference-receipt-v2.json',
        'independent_cross_domain_reference_source': CROSS / 'synthetic_reference_controls_v2.py',
        'independent_cross_domain_reference_plan': CROSS / 'synthetic-plan-v2.json'}
    for role, path in additions.items():
        inputs.append({'role': role, **pin(path)})
    if inputs[:118] != old['inputs']:
        raise ValueError('old wider phase source-role prerequisite list was altered')
    preserved = {entry['path']: verify(entry) for entry in old['preserved_files']}
    prior = old['sources'] + old['inputs']
    for folder in (OLD, TRACE, TRACE_REVIEW, DIAGNOSIS, ROOT / '.gcts-active/shared-symbolic-geometry-search-v2-independent-20261011'):
        prior += [pin(path) for path in sorted(folder.rglob('*'))
                  if path.is_file() and '__pycache__' not in path.parts]
    prior += [pin(PROGRESS / 'root-producer-v2-terminal.json'), pin(PROGRESS / 'root-auditor-v1-terminal.json')]
    prior += [pin(HERE / name) for name in ('pure-ast-plan-v1.json', 'pure-ast-source-freeze-v1.json',
        'pure-ast-outcome-v1.json', 'pure-ast-lifetime-v1.json', 'pure-ast-stdout-v1.txt', 'pure-ast-stderr-v1.txt',
        'worker-v2-to-receptor-v1.diff', 'matcher-contract-v1.json')]
    for entry in prior + inputs:
        checked = verify(entry)
        if checked['path'] in preserved and checked != preserved[checked['path']]:
            raise ValueError('prior preservation collision')
        preserved[checked['path']] = checked
    plan = copy.deepcopy(old)
    plan.update({'version': 'literal-receptor-matching-geometry-search-source-plan-v1',
        'status': 'frozen_actual_search_source_only_pending_root_and_independent_review_no_activation',
        'saved_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources, 'inputs': inputs,
        'preserved_files': [preserved[k] for k in sorted(preserved)],
        'observations': [{'id': 'fixed-forward-reference', 'mode': 'fixed-forward', 'attempts': 128, 'seconds': 20, 'event_ceiling': 2000},
                         {'id': 'fixed-forward-receptor', 'mode': 'fixed-forward-receptor', 'attempts': 128, 'seconds': 20, 'event_ceiling': 2000}],
        'matcher_contract': pin(HERE / 'matcher-contract-v1.json'),
        'worker_minimal_diff': pin(HERE / 'worker-v2-to-receptor-v1.diff'),
        'root_command_after_two_source_reviews_and_exact_activation': 'python3 ' + str(HERE / 'shared_symbolic_search_outer_v1.py'),
        'proposed_outputs': ['fixed-forward-reference-result-v1.json.gz', 'fixed-forward-receptor-result-v1.json.gz',
            'search-outcome-v1.json', 'search-launch-v1.json', 'search-supervision-v1.json', 'search-lifetime-v1.json',
            'search-stdout-v1.txt', 'search-stderr-v1.txt'],
        'pure_AST_controls_executed': 1, 'actual_geometry_searches_by_this_phase': 0,
        'actual_geometry_model_constructions_by_this_phase': 0, 'actual_ranking_graph_calls_by_this_phase': 0,
        'pure_AST_control_scope': '64 syntax/selected-record controls accepted in a separately bounded child. Actual model, full permutations, scheduler, trace and symbolic theorem gate remain unexecuted.'})
    plan['prerequisites'].update({role: pin(path) for role, path in additions.items()})
    plan['ordering_specification']['proved_outputs'] = 'Historical tier variable only: exact physically selected output constraints, possibly with pending sources; not established proof/hypotheses.'
    plan['ordering_specification']['ties'] = 'Reference old score unchanged. New control inserts match0/neutral1/nonmatch2 after that same readiness tier, then exact old size/witness/recipe/reference ties. Every legal candidate remains.'
    plan['ordering_specification']['matcher'] = pin(HERE / 'matcher-contract-v1.json')
    plan['source_boundaries']['fallback'] = 'Both controls are full permutations; new matcher has no legality, dead/forced/count or pruning authority. Unknown child never excluded.'
    plan['source_boundaries']['feature'] = 'Generic literal selected-output constraint matching only; MP ordered antecedent or instantiated consequent guard, finite nullary images, repeated consistency, unsupported neutral. No target/theory/predicate/constant names or authored target words.'
    plan['independent_next_gate']['fixed_order'] = 'Recompute unchanged readiness and complete reference order. Independently rebuild all pattern records, selected constraint identities, per-recipe comparisons/matches/bindings and full comparison/score/base/order hashes, then compare all new complete permutations.'
    plan['costs'].update({'source_authoring': 'Unmeasured; no cross-process clock subtraction.',
        'new_static_freeze_seconds_before_plan_write': time.perf_counter() - started,
        'retained_previous_V1_failed_owner_seconds': 0.935204458,
        'retained_previous_V2_producer_owner_seconds': 8.109092125,
        'retained_previous_V2_independent_owner_seconds': 41.361476959,
        'separate_previous_owner_timer_sum_seconds': 50.405773542,
        'pure_AST_owner_seconds': pure_lifetime['full_child_and_owner_seconds_before_final_receipt_write'],
        'cumulative_owner_accounting': 'New actual gate remains separately bounded180/175/170s512MiB, not one cumulative gate for all research. Charge exact previous0.935204458+8.109092125+41.361476959 owner timers and fresh pure controls, source freezing, actual setup/search/feature/serialization and independent audit separately. Original546.8s native admissions and every historical UNKNOWN remain additional.',
        'matcher_subphases': 'Preparation, selected-output collection, literal per-recipe comparisons, score creation, sorting, permutation assertion, comparison/score payload hashing. Enclosing clocks overlap; no summing nested timers.'})
    plan['later_shared_native_gate']['eligibility'] = 'Only the first independently accepted new full symbolic certificate in fixed-reference then receptor-control order, under a separately reviewed exact-input/native capacity gate; none => zero requests. No native dispatch here.'
    plan['scientific_executions_by_this_freeze'] = 0
    plan['body_authority_adapter']['broader_prerequisite_verification'] = 'Exact prior118 role inputs unchanged, plus17 new phase/source/actual-trace/AST control bindings. Body factory still receives exact original accepted56-input plan, not this broader list.'
    plan['model']['boundary_changed'] = False
    save('search-plan-v1.json', plan)
    receipt = {'status': 'frozen_actual_search_sources_no_actual_model_or_search_execution',
        'plan': pin(HERE / 'search-plan-v1.json'), 'matcher_contract': pin(HERE / 'matcher-contract-v1.json'),
        'worker_diff': pin(HERE / 'worker-v2-to-receptor-v1.diff'), 'sources': len(sources),
        'inputs': len(inputs), 'old_inputs_unchanged': 118, 'body_source_inputs': 56,
        'preserved_files': len(preserved), 'unique_verified_paths': len({p['path'] for p in sources + inputs + list(preserved.values())}),
        'mismatches': 0, 'ast_parsed_sources': len(sources),
        'static_freeze_seconds_before_receipt_write': time.perf_counter() - started,
        'pure_AST_control_outcome': pin(HERE / 'pure-ast-outcome-v1.json'),
        'pure_AST_control_lifetime': pin(HERE / 'pure-ast-lifetime-v1.json'),
        'actual_model_loads': 0, 'actual_searches': 0, 'actual_ordering_graph_calls': 0,
        'native_queries': 0, 'compiler_activations': 0, 'new_training': 0,
        'active_cluster_descriptors': 0, 'authored_words_used_as_hints': 0,
        'root_and_independent_source_reviews': 'pending', 'execution_authorized': False}
    save('source-freeze-v1.json', receipt)
    files = [pin(path) for path in sourcepaths[:9]] + [pin(HERE / name) for name in (
        'worker-v2-to-receptor-v1.diff', 'matcher-contract-v1.json', 'search-plan-v1.json', 'source-freeze-v1.json',
        'pure-ast-plan-v1.json', 'pure-ast-source-freeze-v1.json', 'pure-ast-outcome-v1.json',
        'pure-ast-lifetime-v1.json', 'pure-ast-stdout-v1.txt', 'pure-ast-stderr-v1.txt')]
    save('source-manifest-v1.json', {'status': 'immutable_source_only_actual_geometry_receptor_ranking_package',
        'files': files, 'total_files': len(files), 'total_bytes': sum(p['bytes'] for p in files),
        'plan': pin(HERE / 'search-plan-v1.json'), 'scope': '64 pure AST controls passed; no actual geometry ranking/model/search/native/training or proof claim.',
        'publication_owner': 'root', 'execution_authorized': False})
    print(json.dumps({'plan': pin(HERE / 'search-plan-v1.json'), 'receipt': pin(HERE / 'source-freeze-v1.json'),
        'manifest': pin(HERE / 'source-manifest-v1.json'), 'sources': len(sources), 'inputs': len(inputs),
        'preserved': len(preserved), 'actual_searches': 0}, indent=2))


if __name__ == '__main__':
    main()
