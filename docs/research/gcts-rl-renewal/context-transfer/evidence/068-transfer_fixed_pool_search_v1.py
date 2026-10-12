"""Prospective fixed whole-pool adapter. SOURCE ONLY until ROOT dispatch.

No scientific imports or dispatch at module load. The caller passes exact pinned
unchanged lifecycle/core/search/proposal modules after owning all input gates.
This sibling preserves prior automatic DFS and event/UNKNOWN/child-exclusion
semantics while using Controller.ordered's all newly validated whole-union hints.
No target-word lookup, new proof tactic, atomic macro move or RL operation.
"""
import copy
import hashlib
import json
import math
import time


def pool_order_projection(control, decision, core):
    """Post-resync structural hint advice, never derived-hypothesis evidence."""
    ready=[]
    for descriptor, state in zip(control.descriptors,control.states):
        ready.append(dict(descriptor_id=descriptor.identifier,fixed_priority=descriptor.priority,
            status=state.status,reason=state.reason,eligible=[k.data() for k in state.eligible]))
    preferred=[];seen=set()
    if decision.kind=='branch':
        for state in control.states:
            if state.status=='ready':
                for key in state.eligible:
                    if key not in seen:seen.add(key);preferred.append(key.data())
    return dict(schema='fixed-whole-family-order-trace-v1',descriptor_order=ready,
        preferred_keys=preferred,preferred_keys_sha256=core.digest(preferred),
        advice_scope='Pending structural source-body obligations, not newly proved premises or a completed proof')


def fixed_pool_search(graph, authority, descriptors, life, prior_search, *, mode, attempts, seconds, event_ceiling):
    setup_started = time.perf_counter()
    core = life.core
    if mode not in ('base','fixed-forward','fixed-whole-family-pool'):
        raise ValueError('exact three frozen controls')
    if mode!='fixed-whole-family-pool' and descriptors:
        raise ValueError('primitive controls have no active descriptor')
    TraceLimit = prior_search.TraceLimit
    compact_state = prior_search.compact_state
    compact_state_from_saved = prior_search.compact_state_from_saved
    core.integer(attempts); core.integer(event_ceiling)
    if (attempts < 0 or event_ceiling < 1 or isinstance(seconds, bool)
            or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0):
        raise ValueError('finite nonnegative search bounds required')
    if not isinstance(descriptors, list):
        raise ValueError('literal entire freshly audited pool required')
    control = life.Controller(graph, authority, descriptors)
    if len(control.descriptors) != len(descriptors) or json.loads(control.root_rejected_text):
        raise ValueError('whole immutable proposal registration failed; no partial active pool')
    primitive = core.Executor(graph)
    ordering = prior_search.ForwardOrder(graph) if mode=='fixed-forward' else None
    setup_seconds = time.perf_counter() - setup_started
    graph_metrics_at_search_entry = dict(graph.metrics)
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
        keys = list(graph.candidates(decision.row))
        if len(keys) != decision.count or len(set(keys)) != len(keys):
            raise AssertionError('entire chosen point domain cardinality differs')
        ordered = list(control.ordered(decision))  # One whole resync, full base fallback.
        if ordering is not None and decision.kind=='branch':
            ordered=ordering.order(ordered)  # Literal unchanged generic forward comparator.
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
              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode,
              whole_pool_order_trace=pool_order_projection(control, decision, core))
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
            'graph_metrics_at_search_entry': graph_metrics_at_search_entry,
            'lifecycle_metrics': dict(control.metrics), 'ordering_metrics': metrics,
            'controller_and_ordering_setup_seconds': setup_seconds,
            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,
            'fixed_pool_descriptor_ids': [d.identifier for d in control.descriptors],
            'fixed_pool_priorities': [d.priority for d in control.descriptors],
            'search_clock_scope': 'Complete order, hint revalidation, step, trace and rollback work; finite operation boundary checks, possible overshoot',
            'checked_search_deadline_overshoot_seconds': max(0.0, time.perf_counter() - begin - seconds),
            'limits': {'attempts': attempts, 'seconds': seconds, 'events': event_ceiling},
            'active_cluster_descriptors': len(descriptors), 'authored_words_used_as_hints': 0, 'native_queries': 0,
            'new_RL_training': False, 'atomic_macro_moves': 0,
            'mathematical_acceptance': 'pending independent complete trace and symbolic certificate audit'}
