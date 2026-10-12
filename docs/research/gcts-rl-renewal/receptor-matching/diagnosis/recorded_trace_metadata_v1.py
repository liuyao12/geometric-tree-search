"""Read frozen trace/schema metadata, never reconstruct a point graph or proof.

No scientific imports, pattern matcher calls, candidate enumeration, state
replay, inference checking, search, native encoding or target-proof hint.
"""
import collections
import gzip
import hashlib
import json
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    with (gzip.open(path, 'rt') if Path(path).suffix == '.gz' else Path(path).open()) as stream:
        return json.load(stream)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def self_inequalities(ast):
    """Count literal not(eq(x,x)) subtrees; no logical simplification."""
    if not isinstance(ast, list):
        return 0
    count = int(len(ast) == 2 and ast[0] == 'not' and isinstance(ast[1], list)
                and len(ast[1]) == 3 and ast[1][0] == 'eq' and ast[1][1] == ast[1][2])
    return count + sum(self_inequalities(item) for item in ast[1:])


def summarize(result, recipes, codes):
    events = result['events']; steps = []; orders = []; last_order = None
    exclusions = []; decisions = []; row_attempts = collections.Counter(); rule_attempts = collections.Counter()
    recipe_attempts = collections.Counter(); branch_buckets = collections.Counter(); branch_patterns = collections.Counter()
    matching_keys = collections.Counter(); prefix = []; max_occupied = -1; deepest = None
    pattern_registry = result.get('receptor_pattern_registry')
    for index, event in enumerate(events):
        graph = event['state']['projection']['graph']
        occupied = sum(graph['totals'])
        if occupied > max_occupied:
            max_occupied = occupied
            deepest = {'event_index': index, 'node': event['node'], 'kind': event['kind'],
                'occupied_rows': [i for i, amount in enumerate(graph['totals']) if amount],
                'frontier_rows': [i for i, amount in enumerate(graph['totals']) if amount == 0],
                'selected_order': graph['order'],
                'assigned_formula_points': [entry for entry in graph['marks'] if entry[0] == 1]
                    if isinstance(graph.get('marks'), list) else None}
        if event['kind'] == 'global_decision':
            decisions.append({'event_index': index, 'node': event['node'], 'decision': event['decision']})
        elif event['kind'] == 'parent_local_exhausted_child_exclusion':
            exclusions.append({'event_index': index, 'node': event['node'], 'key': event['key'],
                               'child_node': event['child_node'], 'recorded_status': event['child_status']})
        elif event['kind'] == 'complete_chosen_domain_order':
            feature_trace = event.get('receptor_feature_trace')
            key = event['selected_key']; recipe = recipes[key[0]]; witness = recipe['primitive_witness']
            feature = None
            if feature_trace is not None:
                feature = next((entry for entry in feature_trace['recipe_features'] if entry['recipe'] == key[0]), None)
                if feature is None:
                    raise ValueError('saved chosen recipe lacks recorded feature metadata')
                branch_buckets[feature['status']] += 1
                branch_patterns[feature['pattern_status']] += 1
                for match in feature['matches']:
                    matching_keys[canonical(match['key'])] += 1
            order = {'event_index': index, 'node': event['node'], 'decision': event['decision'], 'key': key,
                'rule': witness['rule'], 'output_code': codes[canonical(witness['formula'])],
                'recorded_complete_count': event['complete_count'],
                'base_keys_sha256': event['base_keys_sha256'], 'ordered_keys_sha256': event['ordered_keys_sha256'],
                'recorded_chosen_feature': feature,
                'recorded_pattern': pattern_registry[key[0]] if pattern_registry is not None else None,
                'selected_constraint_keys': feature_trace['selected_output_constraints'] if feature_trace is not None else None,
                'full_comparison_or_order_hashes_verified_here': False}
            orders.append(order); last_order = order
        elif event['kind'] == 'primitive_step':
            key = event['key']; witness = recipes[key[0]]['primitive_witness']
            feature = last_order['recorded_chosen_feature'] if last_order is not None and last_order['key'] == key else None
            pattern = last_order['recorded_pattern'] if last_order is not None and last_order['key'] == key else None
            step = {'step_index': len(steps), 'event_index': index, 'node': event['node'], 'key': key,
                'rule': witness['rule'], 'output_code': codes[canonical(witness['formula'])],
                'universal_binder': witness['universal'][1] if witness['rule'] == 'instantiate' else None,
                'closed_term': witness.get('term'),
                'ordered_premise_codes': [codes[canonical(ast)] for ast in recipe['ordered_premise_formulas']],
                'recorded_bucket': feature['status'] if feature is not None else None,
                'recorded_matches': feature['matches'] if feature is not None else None,
                'recorded_pattern_prefix': pattern['prefix_binders'] if pattern is not None else None,
                'recorded_literal_guard': pattern['guard'] if pattern is not None else None,
                'literal_guard_self_inequality_count': self_inequalities(pattern['guard']) if pattern is not None else None,
                'occupied_rows_after_step': [i for i, amount in enumerate(graph['totals']) if amount],
                'frontier_rows_after_step': [i for i, amount in enumerate(graph['totals']) if amount == 0]}
            steps.append(step)
            if len(prefix) < 20:
                prefix.append(step)
            row_attempts[str(key[1])] += 1; rule_attempts[witness['rule']] += 1; recipe_attempts[str(key[0])] += 1
    deepest['selected_outputs'] = [{'key': key, 'rule': recipes[key[0]]['primitive_witness']['rule'],
        'output_code': codes[canonical(recipes[key[0]]['primitive_witness']['formula'])],
        'formula': recipes[key[0]]['primitive_witness']['formula']} for key in deepest['selected_order']]
    tail = steps[15:]
    return {'id': result['observation_id'], 'mode': result['mode'], 'recorded_status': result['status'],
        'recorded_attempts': result['attempts'], 'recorded_nodes': result['node_count'], 'events': len(events),
        'recorded_seconds': result['seconds'], 'event_kind_counts': dict(collections.Counter(e['kind'] for e in events)),
        'all_recorded_step_keys': [entry['key'] for entry in steps], 'first_twenty_recorded_steps': prefix,
        'row_attempt_counts': dict(row_attempts), 'rule_attempt_counts': dict(rule_attempts),
        'recipe_attempt_counts': dict(recipe_attempts),
        'first_fifteen_attempt_rows': [entry['key'][1] for entry in steps[:15]],
        'after_first_fifteen': {'attempts': len(tail), 'rows': sorted({entry['key'][1] for entry in tail}),
            'row_attempt_counts': dict(collections.Counter(str(entry['key'][1]) for entry in tail)),
            'rule_attempt_counts': dict(collections.Counter(entry['rule'] for entry in tail))},
        'excluded_parent_rows': dict(collections.Counter(str(entry['key'][1]) for entry in exclusions)),
        'minimum_recorded_excluded_parent_row': min((entry['key'][1] for entry in exclusions), default=None),
        'first_deepest_state': deepest, 'recorded_max_occupied_rows': max_occupied,
        'decision_kind_counts': dict(collections.Counter(entry['decision'][0] for entry in decisions)),
        'decision_row_counts': dict(collections.Counter(str(entry['decision'][1]) for entry in decisions)),
        'recorded_branch_chosen_bucket_counts': dict(branch_buckets),
        'recorded_branch_chosen_pattern_status_counts': dict(branch_patterns),
        'recorded_matched_selected_key_frequencies': dict(matching_keys),
        'pattern_registry_status_counts': dict(collections.Counter(entry['status'] for entry in pattern_registry))
            if pattern_registry is not None else None,
        'pattern_registry_source_counts': dict(collections.Counter(entry['source'] for entry in pattern_registry))
            if pattern_registry is not None else None,
        'all_recorded_orders': orders,
        'recorded_root_restored_flag': result['root_restored'],
        'saved_initial_terminal_snapshots_equal': result['initial_state'] == result['terminal_state'],
        'recorded_limits': result['limits'], 'point_certificate_present': result['point_certificate'] is not None,
        'decoded_certificate_present': result['decoded_certificate'] is not None,
        'recorded_graph_metrics': result['graph_metrics'], 'recorded_order_metrics': result['ordering_metrics'],
        'recorded_feature_metrics': result['fixed_forward_metrics'],
        'recorded_preparation_costs': result['preparation_costs'],
        'scope': 'Saved structural metadata only; no regenerated candidate, comparison/order hash verification, logical proof or trace acceptance.'}


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('55-second metadata-only child')))
    signal.alarm(55)
    plan = read(HERE / 'metadata-plan-v1.json')
    for entry in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / entry['path']) != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('metadata input/preservation changed')
    verification_seconds = time.perf_counter() - started
    roles = {entry['role']: ROOT / entry['path'] for entry in plan['inputs']}
    decoding_started = time.perf_counter()
    schema = read(roles['literal_primitive_schema'])
    recipes = schema['recipes']; codes = {canonical(ast): i for i, ast in enumerate(schema['formula_codes'])}
    previous = read(roles['previous_published_metadata_diagnosis'])
    observations = []
    decode_seconds = time.perf_counter() - decoding_started
    summary_seconds = 0.0
    for role in ('fresh_reference_trace', 'fresh_receptor_trace'):
        clock = time.perf_counter(); result = read(roles[role]); decode_seconds += time.perf_counter() - clock
        clock = time.perf_counter(); observation = summarize(result, recipes, codes)
        summary_seconds += time.perf_counter() - clock
        observation['trace'] = pin(roles[role]); observations.append(observation)
        del result
    reference, receptor = observations
    divergence = next((i for i, (a, b) in enumerate(zip(reference['all_recorded_step_keys'], receptor['all_recorded_step_keys']))
                       if a != b), None)
    previous_fixed = next(entry for entry in previous['observations'] if entry['id'] == 'fixed-forward-novelty')
    old_prefix = [entry['key'] for entry in previous_fixed['first_fifteen_recorded_steps']]
    output = {'status': 'source_bound_saved_receptor_trace_metadata_pending_independent_actual_audit',
        'plan': pin(HERE / 'metadata-plan-v1.json'), 'source': pin(Path(__file__)),
        'observations': observations,
        'comparison': {'first_recorded_step_divergence_index': divergence,
            'reference_key_at_divergence': reference['all_recorded_step_keys'][divergence] if divergence is not None else None,
            'receptor_key_at_divergence': receptor['all_recorded_step_keys'][divergence] if divergence is not None else None,
            'fresh_reference_first_fifteen_equal_previous_frozen_metadata': reference['all_recorded_step_keys'][:15] == old_prefix,
            'previous_fixed_first_fifteen': old_prefix,
            'same_limits': reference['recorded_limits'] == receptor['recorded_limits'],
            'proofs_returned': int(reference['point_certificate_present']) + int(receptor['point_certificate_present']),
            'scope': 'Recorded keys/labels only; no counterfactual orders, scheduler/domain reconstruction or search gain inferred.'},
        'costs': {'source_authoring_seconds': None, 'pin_verification_seconds': verification_seconds,
            'payload_decode_seconds': decode_seconds, 'record_summary_seconds': summary_seconds,
            'metadata_seconds_before_output_write': time.perf_counter() - started,
            'current_root_reported_producer_seconds': 9.340212875,
            'current_root_reported_producer_peak_bytes': 128057344,
            'retained_prior_recorded_owner_timer_sum_seconds': 50.405773542,
            'prior_native_preparation': 'Original546.8s admissions, all historical UNKNOWN/repairs/transport/model/lifecycle and earlier search/audit costs stay pinned additional dependencies.',
            'timer_scope': 'Root reported producer timer and this metadata timer are distinct. Decoding/summary/pin timers are child subphases, not additional disjoint owner time.'},
        'no_scientific_work': {'engine_imports': 0, 'matcher_calls': 0, 'checker_imports': 0,
            'model_constructions': 0, 'candidate_regenerations': 0, 'state_replays': 0,
            'logical_checks': 0, 'searches': 0, 'native_queries': 0, 'training': 0,
            'authored_words_used_as_hints': 0},
        'authority': 'Metadata counts and literal labels only; separate independent actual audit owns trace/domain/order/logic acceptance.',
        'publication_owner': 'root'}
    with (HERE / 'metadata-diagnosis-v1.json').open('x') as stream:
        stream.write(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': output['status'], 'output': pin(HERE / 'metadata-diagnosis-v1.json'),
        'observations': [{k: entry[k] for k in ('id', 'recorded_status', 'recorded_attempts', 'recorded_nodes', 'events', 'recorded_max_occupied_rows')}
                         for entry in observations], 'comparison': output['comparison'],
        'metadata_seconds_before_output_write': output['costs']['metadata_seconds_before_output_write']}))


if __name__ == '__main__':
    main()
