"""Future ROOT-owned exact frozen-context/body/full-pool preparation.

SOURCE ONLY. No Controller, Executor, search, checker, training or RNG in this
phase. Every full group and every raw initial candidate remains in evidence.
"""
import copy
import hashlib
import json
import signal
import sys
import time
from curriculum_context_compiler_v1 import compile_context, construct_graph, construct_family_authority
from curriculum_selection_v1 import select_context
from curriculum_runtime_v1 import HERE, ROOT, plan_path, read, pin, verify, activation, load_life, save_json, save_gzip


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('50-second complete curriculum preparation child gate')))
    signal.alarm(50)
    path = plan_path(sys.argv[1]); plan = read(path); verify(plan); activation(plan, path)
    roles = {record['role']: ROOT / record['path'] for record in plan['inputs']}
    if len(roles) != len(plan['inputs']):
        raise ValueError('each exact input role must be present separately')
    reference = read(roles['curriculum_reference']); split = read(roles['frozen_donor_split'])
    protocol = read(roles['frozen_RL_protocol']); binding = read(roles['frozen_selection_binding'])
    selected = select_context(reference, split, protocol, binding, plan['selector'])
    old = read(roles['accepted_old_positive_disposition'])
    if old.get('trace_accepted') is not True or old.get('proof_accepted') is not True:
        raise ValueError('prior original exact primitive/source-body prerequisite unresolved')
    audit = read(roles['primitive_logical_audit']); source = read(roles['primitive_model'])
    if audit['status'] != 'passed_independent_finite_static_symbolic_and_aggregate_audit':
        raise ValueError('exact old finite primitive source audit required')
    if pin(roles['primitive_model']) not in [item['current_pin'] for item in audit['independent_serialization_correspondence']]:
        raise ValueError('original primitive audit does not bind these model bytes')
    bindings = {record['role']: {k: record[k] for k in ('path', 'sha256', 'bytes')} for record in plan['inputs']}
    bindings['fresh_context_compiler_plan'] = pin(path)
    source_pins = [pin(path)] + [{k: record[k] for k in ('path', 'sha256', 'bytes')}
                               for record in plan['sources'] + plan['inputs']]
    setup = time.perf_counter(); compiled = compile_context(source, selected, reference, bindings, source_pins)
    compilation_seconds = time.perf_counter() - setup
    imported = time.perf_counter(); search, life, proposals = load_life(roles)
    import_seconds = time.perf_counter() - imported; core = life.core
    constructed = time.perf_counter(); graph = construct_graph(compiled, core)
    graph_seconds = time.perf_counter() - constructed
    projection = read(roles['complete_family_projection']); projection.pop('example', None)
    body_plan = read(roles['old_complete_body_plan'])
    body_pins = [{k: record[k] for k in ('path', 'sha256', 'bytes')} for record in body_plan['inputs']]
    body_started = time.perf_counter(); original = construct_family_authority(graph, projection, life, body_pins + source_pins)
    body_seconds = time.perf_counter() - body_started
    grammar_started = time.perf_counter(); counters = {}
    authority, groups, anchors, interfaces = proposals.prepare(graph, original, projection, life, source_pins,
        min(started + 45, grammar_started + 30), counters)
    pool_seconds = time.perf_counter() - grammar_started
    if (counters['single_types_visited'] != 171 or counters['pair_types_visited'] != 29241
            or len(interfaces) != 171):
        raise ValueError('complete source/interface/single/ordered-pair census required')
    # Never trim a full pool to the prospective RL capacity. Preserve all
    # records; a >64 group count makes this RL version infeasible/unresolved.
    capacity_ok = len(groups) <= plan['RL_full_pool_capacity']
    domain_started = time.perf_counter(); rows = []; total = 0
    for row in range(24):
        if time.perf_counter() >= started + 45:
            raise TimeoutError('full initial domain census cutoff; partial census never accepted')
        digest = hashlib.sha256(); count = 0
        for key in graph.candidates(row):
            occupancy, markings = graph.point_data(key)
            digest.update((core.canonical({'key': key.data(), 't': occupancy, 'm': markings}) + '\n').encode('utf8'))
            count += 1
        if count != graph.domains[row].count:
            raise ValueError('every complete initial candidate iterator equals factor-domain count')
        rows.append({'row': row, 'count': count, 'key_t_m_stream_sha256': digest.hexdigest()}); total += count
    domain_seconds = time.perf_counter() - domain_started
    model_path = HERE / plan['outputs']['compiled_context']; save_gzip(model_path, compiled)
    evidence = {'schema': 'fresh-context-whole-family-pool-preparation-v1',
        'status': 'complete_fresh_context_preparation_pending_independent_static_audit',
        'plan': pin(path), 'sources': plan['sources'], 'inputs': plan['inputs'], 'compiled_context_pin': pin(model_path),
        'context': copy.deepcopy(graph.context), 'context_id': graph.context_id, 'formula_codes': graph.formulas,
        'formula_registry_sha256': graph.registry_sha, 'primitive_authority_epoch': graph.authority_epoch,
        'model_epoch': graph.model_epoch, 'graph_binding': life.graph_binding(graph),
        'initial_graph_semantic_state': graph.semantic_state(), 'complete_initial_domains': rows,
        'initial_complete_candidate_count': total, 'original_body_authority_epoch': original.epoch,
        'original_body_authority_graph_text': json.loads(original.graph_text),
        'original_body_authority_source_bindings': json.loads(original.source_text),
        'all_source_bodies': [{'name': name, 'body': json.loads(text)} for name, text in original.bodies],
        'declared_interfaces': list(interfaces), 'declared_interface_projection_sha256': core.digest(interfaces),
        'root_anchors': list(anchors), 'group_authority_epoch': authority.epoch,
        'group_epoch_payload': authority.epoch_payload(), 'groups': groups, 'preparation_counters': counters,
        'costs': {'context_compilation_seconds': compilation_seconds, 'scientific_import_seconds': import_seconds,
            'graph_construction_seconds': graph_seconds, 'all_body_registration_seconds': body_seconds,
            'complete_pool_preparation_seconds': pool_seconds, 'complete_initial_domain_census_seconds': domain_seconds},
        'curriculum_binding': copy.deepcopy(compiled['curriculum_binding']),
        'hypothesis_codes': list(compiled['hypothesis_codes']), 'target_code': compiled['target_code'],
        'RL_full_pool_capacity': plan['RL_full_pool_capacity'], 'RL_full_pool_capacity_satisfied': capacity_ok,
        'licenses': 229, 'non_assumption_witnesses': 226, 'source_body_count': 171, 'recipes': 229,
        'formulas': 217, 'height': 24, 'model_constructions': 1, 'recipient_seed_placements': 3,
        'Controller_calls': 0, 'Executor_calls': 0, 'target_searches': 0, 'logical_checker_calls': 0,
        'native_queries': 0, 'new_RL_training': False,
        'authority_scope': 'Fresh frozen-context finite point/body/pool preparation; old source receipts are provenance. Independent per-context static acceptance is mandatory before trajectories.'}
    evidence_path = HERE / plan['outputs']['preparation_evidence']; save_gzip(evidence_path, evidence)
    verify(plan)
    outcome = {'status': 'completed_fresh_context_preparation_pending_independent_gate', 'plan': pin(path),
        'selector': plan['selector'], 'partition': selected['split'],
        'compiled_context': pin(model_path), 'preparation_evidence': pin(evidence_path),
        'model_epoch': graph.model_epoch, 'group_authority_epoch': authority.epoch,
        'original_body_authority_epoch': original.epoch, 'complete_pool_group_count': len(groups),
        'single_types': counters['single_types_visited'], 'pair_types': counters['pair_types_visited'],
        'candidate_count': total, 'model_constructions': 1, 'target_searches': 0, 'native_queries': 0,
        'new_RL_training': False, 'RL_full_pool_capacity_satisfied': capacity_ok,
        'RL_feasibility_status': 'pending_independent_static_acceptance' if capacity_ok else 'UNRESOLVED_full_pool_exceeds_frozen_capacity_no_trimming',
        'curriculum_binding': copy.deepcopy(compiled['curriculum_binding']),
        'hypothesis_codes': list(compiled['hypothesis_codes']), 'target_code': compiled['target_code'],
        'worker_seconds_before_outcome_write': time.perf_counter() - started, 'costs': evidence['costs']}
    save_json(HERE / plan['phase']['outcome'], outcome)
    signal.alarm(0); print(json.dumps(outcome), flush=True)


if __name__ == '__main__':
    main()
