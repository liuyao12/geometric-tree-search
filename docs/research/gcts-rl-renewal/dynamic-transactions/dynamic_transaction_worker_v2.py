"""One future owned qualification leaf; source authoring is not activation.

No children, randomness, training, target search or supplied proof word. All
imports, complete catalog loading, tiny products and production transactions
are charged to the reviewed 60-second/512-MiB enclosing owner. A success gives
incremental mechanism evidence only; whole clusters/features/order remain open.
"""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import resource
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'ROOT-compact-dynamic-transaction-worker-plan-v2'
LEXICAL_RUNTIME_PIN = {'path': '/Library/Developer/CommandLineTools/usr/bin/python3',
    'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 'bytes': 102352}
ROLES = {'point_core', 'compact_graph', 'compact_decoder',
         'dynamic_graph_adapter', 'dynamic_lifecycle_adapter', 'oracle', 'worker', 'master'}


def need(value, label):
    if not value:
        raise ValueError(label)


def pin(path):
    p = Path(path)
    h = hashlib.sha256(); size = 0
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return {'path': str(p), 'sha256': h.hexdigest(), 'bytes': size}


def verify(record):
    need(set(record) == {'path', 'sha256', 'bytes'}, 'exact closed pin')
    p = Path(record['path'])
    need(p.is_absolute() and (str(p.resolve()) == str(p) or record == LEXICAL_RUNTIME_PIN),
         'canonical science identity or exact declared lexical runtime pin')
    need(pin(p) == record, 'closed source/input bytes: ' + str(p))


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def load(name, record):
    verify(record)
    spec = importlib.util.spec_from_file_location(name, record['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def main():
    began = time.perf_counter()
    need(len(sys.argv) == 3 and sys.argv[1] == 'ROOT-qualify-only', 'literal owned entrypoint')
    plan_path = Path(sys.argv[2]).resolve()
    plan = json.loads(plan_path.read_bytes())
    need(set(plan) == {'schema', 'output_directory', 'sources', 'inputs', 'closure',
                      'source_review', 'limits', 'ROOT_owned_once_only'}, 'exact worker plan')
    need(plan['schema'] == SCHEMA and plan['ROOT_owned_once_only'] is True, 'one prospective leaf')
    need(plan['limits'] == {'whole_seconds': 60, 'peak_bytes': 536870912}, 'unchanged phase limits')
    need(set(plan['sources']) == ROLES, 'all exact source roles')
    need(set(plan['inputs']) == {'tiny_controls', 'catalog', 'audit_receipt',
                               'audit_ROOT_decision', 'preparation_ROOT_decision'}, 'complete inputs')
    out = Path(plan['output_directory'])
    need(out.is_absolute() and str(out.resolve()) == str(out) and out.parent == plan_path.parent
         and not out.exists(), 'fresh direct owned output namespace')
    records = [*plan['sources'].values(), *plan['inputs'].values(), plan['source_review']]
    closed = {r['path']: r for r in plan['closure']}
    need(len(closed) == len(plan['closure']) and all(closed.get(r['path']) == r for r in records),
         'every input/source in complete unique closed relation')
    for record in plan['closure']:
        verify(record)
    need(plan['sources']['worker']['path'] == str(Path(__file__).resolve()), 'executing exact worker')
    review = json.loads(Path(plan['source_review']['path']).read_bytes())
    need(review.get('source_ready') is True and review.get('source_only') is True
         and review.get('scientific_calls') == 0, 'prior independent source review')
    for name in ('audit_ROOT_decision', 'preparation_ROOT_decision'):
        decision = json.loads(Path(plan['inputs'][name]['path']).read_bytes())
        need(decision['ROOT_final_accepted'] is True and all(decision['predicates'].values()),
             'actual complete owned preparation and audit admission')
    audit = json.loads(Path(plan['inputs']['audit_receipt']['path']).read_bytes())
    need(audit['stage_completed'] is True and audit['logical_accepted'] is True
         and audit['initial_static_point_accepted'] is True, 'complete independent static catalog admission')
    header = json.loads(Path(plan['inputs']['catalog']['path']).read_bytes())
    for record in [*header['streams'].values(), *header['source_bindings']]:
        need(closed.get(record['path']) == record, 'whole catalog nested source/stream closure')
    need(header['dimensions']['primitive_license_count'] == 119633
         and header['dimensions']['formula_count'] == 113406, 'unchanged entire admitted catalog')
    out.mkdir()
    checks = []; events = []

    def tick(label):
        elapsed = time.perf_counter() - began
        need(elapsed < 55, 'cooperative phase reserve: ' + label)
        own_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
        need(own_peak < 500 * 1024 * 1024, 'cooperative leaf memory reserve')

    def check(name, value, **evidence):
        tick(name); need(value, name)
        checks.append({'name': name, 'passed': True, 'evidence': evidence})

    def event(name, **data):
        events.append({'name': name, 'worker_seconds': time.perf_counter() - began, **data})
        need(len(events) < 64, 'complete bounded event history')
        save(out / ('event-%02d.json' % (len(events) - 1)), events[-1])

    try:
        sources = plan['sources']
        core = load('qualification_point_core_v1', sources['point_core'])
        compact = load('qualification_compact_graph_v1', sources['compact_graph'])
        decoder = load('qualification_compact_decoder_v1', sources['compact_decoder'])
        dynamic = load('qualification_dynamic_graph_v1', sources['dynamic_graph_adapter'])
        lifecycle = load('qualification_dynamic_lifecycle_v1', sources['dynamic_lifecycle_adapter'])
        oracle = load('qualification_literal_oracle_v1', sources['oracle'])
        controls = json.loads(Path(plan['inputs']['tiny_controls']['path']).read_bytes())
        recipes = controls['recipes']
        tiny = SimpleNamespace(recipe_count=len(recipes), recipe_meta=lambda i: recipes[i])
        state_count = 0; factor_comparisons = 0; literal_key_count = 0
        stream_sha = hashlib.sha256()
        event('tiny_product_begin')
        for row in controls['rows']:
            for values in itertools.product(controls['formula_point_values'], repeat=row + 1):
                for offsets in itertools.product(controls['offset_values_by_row'][row], repeat=2):
                    marks = {(1, r): v for r, v in enumerate(values) if v is not None}
                    marks.update({(2 + port, row): value for port, value in enumerate(offsets) if value is not None})
                    for total in controls['total_values']:
                        expected_factors, expected_keys = oracle.literal_factors(recipes, row, total, marks)
                        factors = list(compact.FactorStream(core, tiny, row, total, marks))
                        actual_factors = [(f.recipe, f.left, f.right, f.different, f.count) for f in factors]
                        need(actual_factors == expected_factors, 'every tiny exact factor')
                        actual_keys = []
                        for f in factors:
                            if not recipes[f.recipe]['inputs']:
                                actual_keys.append((f.recipe, row, ()))
                            else:
                                for a in range(row):
                                    for b in range(row):
                                        if (f.left & (1 << a) and f.right & (1 << b)
                                                and (not f.different or a != b)):
                                            actual_keys.append((f.recipe, row, (a, b)))
                        need(actual_keys == expected_keys, 'every tiny literal key in original order')
                        # Per-state all exact keys, including identical-looking different recipe IDs.
                        stream_sha.update((oracle.canonical([row, total, values, offsets, expected_keys]) + '\n').encode())
                        state_count += 1; factor_comparisons += len(recipes); literal_key_count += len(expected_keys)
                        if state_count % 256 == 0:
                            tick('tiny_complete_products')
            event('tiny_row_closed', row=row, cumulative_states=state_count)
        check('all_predeclared_tiny_products_complete', state_count == controls['complete_product_state_count'],
              states=state_count, recipe_factor_comparisons=factor_comparisons,
              literal_key_occurrences=literal_key_count, complete_state_stream_sha256=stream_sha.hexdigest())
        runtime = [{'role': role, **sources[role]} for role in (
            'point_core', 'compact_graph', 'compact_decoder', 'dynamic_graph_adapter', 'dynamic_lifecycle_adapter')]
        Graph = dynamic.make_dynamic_graph_type(core, compact, decoder, runtime_sources=runtime)
        event('production_whole_catalog_load_begin')
        graph = Graph(header_pin=plan['inputs']['catalog'])
        event('production_whole_catalog_loaded', recipes=graph.catalog.recipe_count, formulas=graph.catalog.formula_count)
        raw = Path(header['streams']['recipes']['path']).read_bytes()
        all_recipes = oracle.raw_recipes(raw, 119633, 113406)
        check('whole_original_catalog_retained', len(graph.recipes) == len(all_recipes) == 119633)
        life = lifecycle.make_lifecycle(core, Graph)
        body_auth = life.BodyAuthority.build(graph, [sources['worker'], sources['oracle'], plan['inputs']['catalog']], [])
        control = life.Controller(graph, body_auth, [])
        production_states = []

        def audit_state(name):
            keys = [(k.recipe, k.row, k.refs) for k in graph.order]
            totals, marks, refs = oracle.reconstruct_union(all_recipes, 24, graph.initial_marks, keys)
            check(name + '_whole_point_union', totals == graph.totals and marks == graph.marks and refs == graph.mark_refs)
            exclusions = [[(k.recipe, k.row, k.refs) for k in row] for row in graph.excluded]
            counts = oracle.complete_counts(all_recipes, totals, marks, exclusions)
            check(name + '_all24_full_catalog_counts', counts == [(d.base_count, d.count) for d in graph.domains])
            expected = oracle.global_decision(counts, totals, graph.roots)
            d = graph.decision()
            check(name + '_global_decision', expected == (d.kind, d.row, d.count, d.generation))
            state = graph.semantic_state()
            production_states.append({'name': name, 'full_counts': [list(v) for v in counts],
                'decision': list(expected), 'state_sha256': oracle.digest(state),
                'selected_keys': [k.data() for k in graph.order]})
            event(name + '_state_closed')
            return state

        initial = audit_state('initial')
        header_copy = graph.catalog.header; header_copy['height'] = 5
        check('catalog_header_accessor_is_detached', graph.catalog.header['height'] == 24)
        try:
            graph.catalog.formula_count = 7
        except ValueError:
            sealed = True
        else:
            sealed = False
        check('ordinary_catalog_mutation_rejected', sealed and graph.catalog.formula_count == 113406)
        d = graph.decision()
        suspended = graph.candidates(d.row)
        first = next(suspended)  # Capture generator revision before the transaction.
        ordered = graph.ordered_domain(d)
        check('lazy_order_first_matches_base_traversal', ordered.first() == first and len(ordered) == d.count)
        checkpoint = control.checkpoint()
        original_control = control.semantic_state()
        core.Executor(graph).step(first)
        control.resync()
        audit_state('one_transaction')
        for name, operation in [('suspended_candidate_stream', lambda: next(suspended)),
                                ('ordered_domain', lambda: ordered.first())]:
            try:
                operation()
            except ValueError:
                rejected = True
            else:
                rejected = False
            check(name + '_stale_after_placement', rejected)
        control.rollback(checkpoint)
        restored = audit_state('restored')
        check('exact_paired_rollback', restored == initial and control.semantic_state() == original_control)
        unknown = life.Executor(control).solve(max_attempts=0, seconds=0)
        check('zero_budget_unknown_no_pruning', unknown['status'] == 'unknown_budget'
              and control.semantic_state() == original_control and all(not e for e in graph.excluded))
        saved = graph.context_id; graph.context_id = 'controlled-stale-context'
        try:
            graph.decision()
        except ValueError:
            stale = True
        else:
            stale = False
        finally:
            graph.context_id = saved
        check('untracked_context_change_rejected', stale)
        saved = graph.totals[4]; graph.totals[4] = 1
        try:
            graph.decision()
        except ValueError:
            stale = True
        else:
            stale = False
        finally:
            graph.totals[4] = saved
        check('untracked_point_change_rejected', stale and graph.semantic_state() == initial)
        for record in plan['closure']:
            verify(record)
        check('complete_source_input_closure_unchanged', True)
        evidence = {'schema': 'compact-dynamic-transaction-evidence-v1', 'checks': checks,
            'all_checks_passed': True, 'tiny_scope': controls['scope'], 'production_states': production_states,
            'production_scope': 'Entire admitted catalog, all24 counts, one scheduler-selected primitive transaction and exact rollback; no complete production candidate-stream enumeration.',
            'events': events, 'deferred': ['whole cluster pool and receptors', 'all31 feature values',
                'streamed proposal/overlay/DFS and trajectory replay', 'distant dead/forced fixtures',
                'nonzero generation, fractional residual and shared-positive-support scope controls'],
            'target_searches': 0, 'proof_certificates': 0, 'RNG_draws': 0, 'RL_updates': 0,
            'blanket_dynamic_qualification': False, 'general_tiling_conformance': False}
        save(out / 'qualification-evidence-v1.json', evidence)
        tick('final_evidence_closed')
        receipt = {'schema': 'compact-dynamic-transaction-worker-receipt-v1', 'stage': 'replay',
            'stage_completed': True, 'incremental_mechanism_checks_passed': True,
            'evidence': pin(out / 'qualification-evidence-v1.json'),
            'worker_elapsed_before_receipt_seconds': time.perf_counter() - began,
            'all_direct_children_terminal_and_reaped': True, 'direct_children_peak_sum_bytes': 0,
            'proof_certificates': 0, 'target_searches': 0, 'new_RL_training': False,
            'blanket_dynamic_qualification': False, 'resource_accepted': False}
        save(out / 'qualification-result-v1.json', receipt)
        print(json.dumps({'stage_completed': True, 'checks': len(checks), 'tiny_states': state_count}), flush=True)
    except BaseException as exc:
        save(out / 'qualification-result-v1.json', {'schema': 'compact-dynamic-transaction-worker-receipt-v1',
            'stage': 'replay', 'stage_completed': False, 'status': 'UNKNOWN_incremental_qualification',
            'error': {'type': type(exc).__name__, 'message': str(exc)}, 'checks_completed': checks,
            'all_direct_children_terminal_and_reaped': True, 'direct_children_peak_sum_bytes': 0,
            'proof_certificates': 0, 'target_searches': 0, 'new_RL_training': False,
            'blanket_dynamic_qualification': False, 'resource_accepted': False})
        raise


if __name__ == '__main__':
    main()
