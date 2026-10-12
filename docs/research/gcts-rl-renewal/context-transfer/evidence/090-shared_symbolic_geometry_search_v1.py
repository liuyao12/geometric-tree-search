"""Root-gated automatic full primitive search; immutable source-only until dispatch.

Complete graph is the frozen kernel. All 171 family bodies are validated but the
proposal registry is empty. No authored target word, native calls or training.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
import math
import signal
import sys
import time
from pathlib import Path
from shared_symbolic_forward_order_v1 import ForwardOrder
from shared_symbolic_bridge_decode_v1 import decode

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    h = hashlib.sha256(); path = Path(path)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def verify_plan(plan):
    started = time.perf_counter()
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / p['path']) != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen search prerequisite/source changed: ' + p['path'])
    return time.perf_counter() - started


def load_lifecycle(path):
    spec = importlib.util.spec_from_file_location('frozen_lifecycle_automatic_geometry', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TraceLimit(Exception):
    pass


def compact_state(controller, core):
    # Exact full snapshot hash plus reconstructible graph/hint projection. Huge
    # complete factor tables need not be copied into every event: counts and all
    # point values/exclusions reconstruct them under the frozen 229 recipe inputs.
    full = controller.semantic_state()
    projection = copy.deepcopy({k: v for k, v in full.items() if k != 'graph'})
    graph = full['graph']
    projection['graph'] = {k: v for k, v in graph.items() if k != 'domains'}
    projection['graph']['domains'] = [{'base_count': d['base_count'], 'count': d['count'],
                                      'excluded_legal': d['excluded_legal']} for d in graph['domains']]
    return {'full_semantic_sha256': core.digest(full), 'projection': projection}


def automatic_search(graph, authority, mode, life, *, attempts, seconds, event_ceiling):
    setup_started = time.perf_counter()
    core = life.core
    core.integer(attempts); core.integer(event_ceiling)
    if (attempts < 0 or event_ceiling < 1 or isinstance(seconds, bool)
            or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0):
        raise ValueError('finite nonnegative search bounds required')
    if mode not in ('base', 'fixed-forward'):
        raise ValueError('only two declared fixed order controls')
    control = life.Controller(graph, authority, [])
    if control.descriptors or control.states:
        raise ValueError('no target word or cluster proposals allowed')
    primitive = core.Executor(graph)
    ordering = ForwardOrder(graph) if mode == 'fixed-forward' else None
    setup_seconds = time.perf_counter() - setup_started
    begin = time.perf_counter(); deadline = begin + seconds
    start_attempts = graph.metrics['attempts']
    initial = control.checkpoint(); initial_state = control.semantic_state()
    events = []; node_count = 0
    metrics = {'complete_order_calls': 0, 'complete_order_keys': 0, 'order_seconds': 0.0,
               'order_stream_hash_seconds': 0.0, 'trace_seconds': 0.0,
               'primitive_step_seconds': 0.0, 'rollback_seconds': 0.0, 'exclusion_seconds': 0.0}

    def event(kind, node, **fields):
        started = time.perf_counter()
        if len(events) >= event_ceiling:
            raise TraceLimit('complete trace budget; never finite exhaustion')
        events.append({'kind': kind, 'node': node, **fields, 'state': compact_state(control, core)})
        metrics['trace_seconds'] += time.perf_counter() - started

    def rollback(checkpoint, node, reason):
        started = time.perf_counter()
        control.rollback(checkpoint)
        metrics['rollback_seconds'] += time.perf_counter() - started
        event('paired_rollback', node, checkpoint=list(checkpoint), reason=reason)

    def order(decision, node):
        started = time.perf_counter()
        if decision != graph.decision():
            raise ValueError('stale global decision cannot select an order')
        control.resync(decision)
        keys = list(graph.candidates(decision.row))
        if len(keys) != decision.count or len(set(keys)) != len(keys):
            raise AssertionError('entire chosen point domain cardinality differs')
        ordered = ordering.order(keys) if ordering is not None and decision.kind == 'branch' else keys
        if len(ordered) != len(keys) or set(ordered) != set(keys):
            raise AssertionError('complete base fallback permutation required')
        if decision.kind == 'forced' and ordered != keys:
            raise AssertionError('ordering may not bypass forced singleton')
        stream = lambda values: hashlib.sha256(('\n'.join(core.canonical(k.data()) for k in values) + '\n').encode()).hexdigest()
        metrics['complete_order_calls'] += 1
        metrics['complete_order_keys'] += len(keys)
        metrics['order_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        base_hash, ordered_hash = stream(keys), stream(ordered)
        metrics['order_stream_hash_seconds'] += time.perf_counter() - started
        event('complete_chosen_domain_order', node, decision=[decision.kind, decision.row, decision.count, decision.generation],
              base_keys_sha256=base_hash, ordered_keys_sha256=ordered_hash,
              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode)
        return ordered[0]

    def step(key, node):
        started = time.perf_counter()
        primitive.step(key)  # Old unchanged global dead/forced/earliest executor.
        control.resync()
        metrics['primitive_step_seconds'] += time.perf_counter() - started
        event('primitive_step', node, key=key.data())

    def walk(parent_node=None):
        nonlocal node_count
        node = node_count; node_count += 1
        checkpoint = control.checkpoint()
        event('node_enter', node, parent_node=parent_node, checkpoint=list(checkpoint))
        while True:
            decision = graph.decision()
            event('global_decision', node, decision=[decision.kind, decision.row, decision.count, decision.generation])
            if decision.kind == 'dead':
                event('proved_global_dead', node)
                rollback(checkpoint, node, 'dead_subtree')
                event('node_return', node, status='exhausted_finite_marked_subtree')
                return 'exhausted_finite_marked_subtree', node
            if decision.kind == 'complete':
                control.resync(decision)
                event('node_return', node, status='finite_exact_point_tiling')
                return 'finite_exact_point_tiling', node
            if graph.metrics['attempts'] - start_attempts >= attempts or time.perf_counter() >= deadline:
                event('budget_unknown_no_exclusion', node)
                rollback(checkpoint, node, 'budget_unknown')
                event('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            key = order(decision, node)
            # Complete ordering and trace work are included in the search clock.
            if time.perf_counter() >= deadline:
                event('budget_unknown_after_order_no_exclusion', node)
                rollback(checkpoint, node, 'budget_unknown_after_order')
                event('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            if decision.kind == 'forced':
                step(key, node)
                continue
            parent = control.checkpoint()
            event('branch_begin', node, key=key.data(), parent_checkpoint=list(parent))
            step(key, node)
            status, child_node = walk(node)
            if status == 'finite_exact_point_tiling':
                event('node_return', node, status=status, child_node=child_node)
                return status, node
            rollback(parent, node, 'restored_branch_parent')
            if status.startswith('unknown_'):
                rollback(checkpoint, node, 'unknown_child_without_exclusion')
                event('node_return', node, status=status, child_node=child_node)
                return status, node
            if status != 'exhausted_finite_marked_subtree':
                raise AssertionError('only fully exhausted child can be excluded')
            event('before_exhausted_child_exclusion', node, key=key.data(), child_node=child_node, child_status=status)
            started = time.perf_counter()
            graph.exclude_failed_child(key)
            graph.metrics['backtracks'] += 1
            control.resync()
            metrics['exclusion_seconds'] += time.perf_counter() - started
            event('parent_local_exhausted_child_exclusion', node, key=key.data(), child_node=child_node, child_status=status)

    try:
        event('solve_begin', None, mode=mode, max_attempts=attempts, seconds=seconds, event_ceiling=event_ceiling)
        status, root_node = walk()
    except TraceLimit as exc:
        status, root_node = 'unknown_trace_budget', 0
        termination = {'kind': 'trace_limit', 'message': str(exc), 'events_retained': len(events)}
    else:
        termination = {'kind': 'returned', 'root_node': root_node}
    if status != 'finite_exact_point_tiling':
        started = time.perf_counter()
        control.rollback(initial)  # May restore after trace limit without another trace event.
        metrics['rollback_seconds'] += time.perf_counter() - started
        if control.semantic_state() != initial_state:
            raise AssertionError('unknown/exhausted whole paired root rollback differs')
    point_certificate = graph.point_certificate() if status == 'finite_exact_point_tiling' else None
    return {'status': status, 'mode': mode, 'events': events, 'termination': termination,
            'node_count': node_count, 'attempts': graph.metrics['attempts'] - start_attempts,
            'initial_state': compact_state_from_saved(initial_state, core),
            'terminal_state': compact_state(control, core),
            'root_restored': status != 'finite_exact_point_tiling', 'point_certificate': point_certificate,
            'seconds': time.perf_counter() - begin, 'graph_metrics': dict(graph.metrics),
            'lifecycle_metrics': dict(control.metrics), 'ordering_metrics': metrics,
            'controller_and_ordering_setup_seconds': setup_seconds,
            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,
            'limits': {'attempts': attempts, 'seconds': seconds, 'events': event_ceiling},
            'active_cluster_descriptors': 0, 'authored_words_used_as_hints': 0, 'native_queries': 0,
            'mathematical_acceptance': 'pending independent complete trace and symbolic certificate audit'}


def compact_state_from_saved(full, core):
    saved = copy.deepcopy(full)
    for d in saved['graph']['domains']:
        del d['factors']
    return {'full_semantic_sha256': core.digest(full), 'projection': saved}


def save_gzip(path, value):
    if path.exists(): raise ValueError('immutable output exists')
    encoder = json.JSONEncoder(indent=2, ensure_ascii=True, allow_nan=False)
    with path.open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as out:
            for block in encoder.iterencode(value): out.write(block.encode('utf-8'))
            out.write(b'\n')


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('owned automatic geometry phase alarm')))
    signal.alarm(170)
    planpath = HERE / 'search-plan-v1.json'; plan = json.loads(planpath.read_text())
    first_pin_seconds = verify_plan(plan)
    activation = json.loads((HERE / 'root-activation-v1.json').read_text())
    if activation['status'] != 'root_authorized_bounded_automatic_primitive_geometry_search' or activation['plan'] != pin(planpath):
        raise ValueError('explicit reviewed root dispatch binding required')
    roles = {p['role']: ROOT / p['path'] for p in plan['inputs']}
    actual_audit = json.loads(roles['full_lifecycle_independent_result'].read_text())
    if actual_audit['status'] != 'passed_independent_full_language_lifecycle_controlled_artifact_audit':
        raise ValueError('full actual language lifecycle prerequisite not accepted')
    import_started = time.perf_counter()
    life = load_lifecycle(roles['frozen_lifecycle_kernel'])
    engine_import_seconds = time.perf_counter() - import_started
    core = life.core
    old_plan = json.loads(roles['prior_full_model_plan'].read_text())
    observations = []
    for spec in plan['observations']:
        checkpoint_started = time.perf_counter()
        g = core.frozen_model(ROOT, old_plan)
        if g.model_epoch != plan['model_epoch'] or (len(g.recipes), len(g.formulas), g.height) != (229, 217, 24):
            raise ValueError('full declared primitive inventory/boundary must stay identical')
        model_seconds = time.perf_counter() - checkpoint_started
        family_started = time.perf_counter()
        body_plan = json.loads(roles['passed_full_lifecycle_producer_plan'].read_text())
        family = life.frozen_family_authority(g, body_plan)
        if len(family.bodies) != 171:
            raise ValueError('all source families required even though proposals are empty')
        family_seconds = time.perf_counter() - family_started
        result = automatic_search(g, family, spec['mode'], life,
                                  attempts=spec['attempts'], seconds=spec['seconds'], event_ceiling=spec['event_ceiling'])
        result['preparation_costs'] = {'cold_model_seconds': model_seconds, 'full_family_registry_seconds': family_seconds}
        if result['point_certificate'] is not None:
            result['decoded_certificate'] = decode(g, result['point_certificate'], core)
        else:
            result['decoded_certificate'] = None
        result['observation_id'] = spec['id']
        result['body_authority_epoch'] = family.epoch
        result['validated_source_body_count'] = len(family.bodies)
        path = HERE / (spec['id'] + '-result-v1.json.gz')
        serialization_started = time.perf_counter()
        save_gzip(path, result)
        serialization_seconds = time.perf_counter() - serialization_started
        observations.append({'id': spec['id'], 'mode': spec['mode'], 'status': result['status'],
            'result': pin(path), 'attempts': result['attempts'], 'seconds': result['seconds'],
            'events': len(result['events']), 'serialization_seconds': serialization_seconds,
            'preparation_costs': result['preparation_costs'], 'decoded_certificate': result['decoded_certificate'] is not None})
        print(json.dumps(observations[-1]), flush=True)
        del result, g, family
    final_pin_seconds = verify_plan(plan)
    outcome = {'status': 'completed_bounded_automatic_primitive_geometry_observations_pending_independent_audit',
               'observations': observations, 'plan': pin(planpath), 'root_activation': pin(HERE / 'root-activation-v1.json'),
               'worker_seconds_before_final_receipt_write': time.perf_counter() - started,
               'initial_pin_verification_seconds': first_pin_seconds,
               'final_pin_verification_seconds': final_pin_seconds,
               'frozen_engine_import_seconds': engine_import_seconds,
               'target_search_observations': len(observations), 'native_queries': 0,
               'native_authority_activated': False, 'new_RL_training': False, 'authored_words_used_as_hints': 0,
               'claim': 'Search observations only; exact theorem acceptance requires the separately owned symbolic/trace audit.'}
    path = HERE / 'search-outcome-v1.json'
    with path.open('x') as stream: stream.write(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(outcome), flush=True)


if __name__ == '__main__':
    main()
