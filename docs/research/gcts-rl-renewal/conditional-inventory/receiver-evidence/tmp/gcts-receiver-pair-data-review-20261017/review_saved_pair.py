"""Read-only saved-data concordance audit. No project imports or replay."""
import base64
import collections
import hashlib
import json
import re
import zlib
from pathlib import Path

O = Path('/private/tmp/gcts-receiver-pair-data-review-20261017')

def raw(p):
    p = Path(p)
    assert not getattr(p.stat(), 'st_flags', 0) & 0x40000000
    return p.read_bytes()

def pin(p):
    b = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def check(ref):
    assert pin(ref['path']) == ref
    return raw(ref['path'])

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()

def equal(a, b):
    return canonical(a) == canonical(b)

def save(name, value):
    p = O / name
    with p.open('xb') as f:
        f.write((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())
    return pin(p)

stages = ['BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS',
          'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE',
          'BEFORE_MARKING_CHECK', 'BEFORE_POOL_READ', 'BEFORE_ENGINE', 'BEFORE_PROVIDER',
          'AFTER_PROVIDER', 'AFTER_ENGINE', 'BEFORE_OUTPUT']
data, arms = {}, {}
for mode in ('visible', 'literal'):
    H = Path('/private/tmp/gcts-receiver-inference-' + mode + '-ROOT-20261017')
    plan_ref = pin(H / 'ROOT-plan-v1.json')
    plan = json.loads(check(plan_ref))
    disposition_ref = pin(H / 'ROOT-disposition-v1.json')
    disp = json.loads(check(disposition_ref))
    expanded_ref = pin(H / 'ROOT-expanded-result-v1.json')
    expanded_raw = check(expanded_ref)
    payload = json.loads(expanded_raw)
    auth = json.loads(check(plan['ROOT_authorization']))
    contract = json.loads(check(plan['source_contract']))
    assert disp['plan'] == plan_ref and disp['expanded'] == expanded_ref
    assert disp['source_contract'] == plan['source_contract']
    assert auth['author_identity'] == '/root' and auth['actual_execution_authorized'] is True
    assert type(auth['maximum_actual_invocations']) is int and auth['maximum_actual_invocations'] == 1
    assert auth['unchanged_actual_may_be_restarted'] is False and auth['scientific_acceptance'] is False
    for key in ('sources', 'inputs', 'limits', 'runtime', 'source_contract', 'purpose', 'invocation_id', 'output_directory'):
        assert equal(auth[key], plan[key])
    assert equal(payload['sources'], plan['sources']) and equal(payload['inputs'], plan['inputs'])
    assert len(plan['sources']) == 21 and len(plan['inputs']) == 10
    native = {name: check(ref) for name, ref in disp['native_files'].items()}
    obs = json.loads(native['observation.json'])
    terminal = json.loads(native['native-terminal.json'])
    once = json.loads(native['ONCE.json'])
    bracket = json.loads(check(disp['tool_bracket']))
    for v in (obs, once, bracket):
        assert v['plan_sha256'] == plan_ref['sha256'] and v['plan_bytes'] == plan_ref['bytes']
    for v in (obs, once):
        assert v['invocation_id'] == plan['invocation_id'] and v['purpose'] == plan['purpose']
    assert bracket['unchanged_actual_restarted'] is False
    assert type(bracket['tool_exit_code']) is int and bracket['tool_exit_code'] == 0
    assert ((bracket['tool_session_id'] is None and bracket['observed_session_id'] is None)
            or (type(bracket['tool_session_id']) is int and bracket['tool_session_id'] > 0
                and type(bracket['observed_session_id']) is int
                and bracket['observed_session_id'] == bracket['tool_session_id']))
    assert bracket['complete_Date_seconds'] == (bracket['ended_Date_ms'] - bracket['began_Date_ms']) / 1000
    assert 0 <= bracket['complete_Date_seconds'] < 91
    assert terminal['all_reaped'] is True and terminal['error'] is None
    assert terminal['interrupted'] is False and terminal['cancellation_forwarded'] is False
    assert type(terminal['caller_returncode']) is int and terminal['caller_returncode'] == 0
    assert type(obs['meter_returncode']) is int and obs['meter_returncode'] == 0
    assert type(obs['probe_returncode']) is int and obs['probe_returncode'] == 0
    assert native['postterminal-probe-stderr.txt'] == b''
    assert int(native['postterminal-probe-stdout.txt']) == obs['postterminal_native_probe_ns']
    elapsed = obs['postterminal_native_probe_ns'] - terminal['caller_launch_began_ns']
    assert elapsed == disp['native_launch_to_postprobe_ns'] and 0 < elapsed < 20000000000
    assert terminal['wait4_pid'] == terminal['caller_pid'] and terminal['wait4_status'] == 0
    assert terminal['caller_kernel_peak_bytes'] == terminal['wait4_usage'][2] == disp['aggregate_B_bytes']
    assert 0 < disp['aggregate_B_bytes'] < 536870912
    assert disp['all_reaped'] is True and disp['actual_closed'] is True
    assert disp['native_resources_qualified'] is True and disp['complete_wire_verified'] is True
    assert disp['reported_theorem_count'] == 0 and disp['receiver_probe_record_complete'] is True
    assert disp['failure_diagnostic'] is None and disp['scientific_replay'] is False
    outputs = [json.loads(check(ref)) if ref['path'].endswith('.json') else check(ref) for ref in disp['outputs']]
    envelope, response_raw = outputs
    lines = response_raw.splitlines(keepends=True)
    assert len(lines) == 2 and all(x.endswith(b'\n') for x in lines)
    body, completion = map(json.loads, lines)
    assert completion['body_bytes'] == len(lines[0])
    assert completion['body_sha256'] == hashlib.sha256(lines[0]).hexdigest()
    assert completion['exit_zero_and_coordinator_deadline_required'] is True
    assert body['plan'] == {k: plan_ref[k] for k in ('bytes', 'sha256')}
    for key in ('sources', 'inputs', 'limits', 'invocation_id'):
        assert equal(body[key], plan[key])
    assert payload['purpose'] == plan['purpose']
    assert body['outputs'] == disp['outputs'][:1]
    final_observation = json.loads(native['meter-stdout.txt'])
    assert final_observation['outputs'] == disp['outputs'] and final_observation['response'] == disp['outputs'][1]
    assert envelope['schema'] == 'ROOT-unit-row-lossless-result-envelope-v1' and envelope['encoding'] == 'zlib+base64'
    compressed = base64.b64decode(envelope['payload_base64'], validate=True)
    assert len(compressed) == envelope['compressed_bytes']
    assert hashlib.sha256(compressed).hexdigest() == envelope['compressed_sha256']
    decoded = zlib.decompress(compressed)
    assert decoded == expanded_raw and len(decoded) == envelope['expanded_bytes'] == expanded_ref['bytes']
    assert envelope['expanded_sha256'] == expanded_ref['sha256']
    parsed_phases = []
    for line in native['meter-stderr.txt'].decode().splitlines():
        m = re.fullmatch(r'COMPONENT_INVENTORY_PHASE ([A-Z_]+) ([0-9]{1,19})', line)
        assert m
        parsed_phases.append({'stage': m[1], 'native_ns': int(m[2])})
    assert [x['stage'] for x in parsed_phases] == stages
    assert parsed_phases == disp['phase_observations']
    phase_ns = [x['native_ns'] for x in parsed_phases]
    assert phase_ns == sorted(phase_ns)
    assert body['joint_deadline_ns'] - body['joint_began_ns'] == 20000000000
    assert terminal['caller_launch_began_ns'] <= body['joint_began_ns'] <= phase_ns[0]
    assert phase_ns[-1] <= terminal['caller_terminal_observed_ns'] < obs['postterminal_native_probe_ns'] < body['joint_deadline_ns']
    probe = payload['receiver_probe']
    q = probe['receiver']
    engine = q['engine_result']
    events = engine['events']
    preference = [e for e in events if e['kind'] == 'FAMILY_PREFERENCE']
    assert len(preference) == 1 and preference[0]['mode'] == 'CANONICAL_FALLBACK'
    assert len(preference[0]['receipts']) == 1
    wrapper = preference[0]['receipts'][0]
    report, consumer = wrapper['provider_report'], wrapper['consumer_receipt']
    assert wrapper['schema'] == 'receptor-family-engine-full-census-check-v1'
    assert wrapper['census_is_collision_evidence_only'] is True
    assert wrapper['status'] == consumer['status'] == 'UNKNOWN'
    assert consumer['checks'] == [] and consumer['selection'] is None
    assert q['matching_mode'] == ('VISIBLE_RECEPTOR' if mode == 'visible' else 'LITERAL_GROUND')
    assert report['matching_mode'] == q['matching_mode']
    assert report['version'] == 'receptor-family-observed-receptor-transfer-provider-v7'
    assert report['schema'] == 'receptor-family-observed-receptor-transfer-provider-v2'
    assert report['batch']['status'] == 'UNKNOWN' and report['batch']['instances'] == []
    assert report['offers'] == [] and q['provider_limits'] == report['work']['limits']
    assert len(report['physical_assignment_plan']['plans']) == report['accounting']['planned_assignments'] == 30
    assert report['physical_assignment_plan']['record_allocations'] == [
        {'bounded_reason': 'OWN_PER_RECORD_PHYSICAL_ROW_TRIAL_PREFIX', 'planned_assignments': 15,
         'record_index': i, 'row_trial_quota': 32, 'row_trials': 32, 'status': 'BOUNDED_STRUCTURAL_PREFIX'} for i in range(2)]
    assert report['work']['row_trials'] == 64 and report['physical_assignment_plan']['complete_within_declared_limits'] is False
    assert report['physical_assignment_plan']['row_trials_per_record'] == 32
    assert report['physical_assignment_plan']['unallocated_remainder'] == 0
    initial = q['initial_state']
    initial_sha = digest(initial)
    observations = q['observations']
    assert len(observations['provider_calls']) == len(observations['consumer_calls']) == 1
    provider_obs, consumer_obs = observations['provider_calls'][0], observations['consumer_calls'][0]
    assert provider_obs['report_sha256'] == digest(report)
    assert consumer_obs['receipt_sha256'] == digest(consumer)
    assert consumer_obs['request_sha256'] == consumer['request_sha256'] == digest({
        'schema': 'receptor-family-primitive-preference-request-v1', 'mode': 'BATCH', 'payload': report['batch']})
    for v in (provider_obs, report, report['request'], report['batch'], consumer_obs, consumer, wrapper):
        assert v['decision'] == {'kind': 'BRANCH', 'row': 23}
    assert equal(provider_obs['state'], initial) and equal(report['request']['state'], initial)
    assert equal(report['checked_state'], initial) and equal(consumer['entry']['state'], initial)
    for v in (report, report['batch'], consumer_obs, consumer, wrapper):
        assert v['state_sha256'] == initial_sha
    assert q['frozen_open_pool_sha256'] == digest(report['request']['mined'])
    assert probe['frozen_inventory_input'] == plan['inputs']['frozen_inventory']
    assert probe['inventory_acceptance_input'] == plan['inputs']['inventory_acceptance']
    assert probe['inventory_reused'] is True and probe['construction_in_this_window'] is False
    assert q['inventory_reused'] is True and q['inventory_construction_charged_in_this_window'] is False
    assert len(probe['original_model_sources']) == 17 and len(probe['original_model_inputs']) == 2
    assert equal(probe['original_model_binding'], payload['language_binding'])
    assert equal(body['original_model_binding'], payload['language_binding'])
    assert q['branch_tie'] == engine['scheduler_policy']['branch_tie'] == 'ASSIGNED-OUTPUT-THEN-ROW'
    assert q['maximum_nodes'] == 2 and q['maximum_events'] == 256
    assert [(e['kind'], e.get('decision')) for e in events if e['kind'] == 'DECISION'] == [
        ('DECISION', {'kind': 'BRANCH', 'row': 23}), ('DECISION', {'kind': 'DEAD', 'row': 0})]
    assert [e['kind'] for e in events] == ['DECISION', 'FALLBACK', 'TRY', 'FAMILY_PREFERENCE',
        'INVALIDATE', 'PLACE', 'DECISION', 'RESTORE', 'INVALIDATE', 'EXCLUDE']
    assert events[0]['statuses'] == [[i, 'TWO_OR_MORE'] for i in range(24)]
    assert events[6]['statuses'] == [[0, 'ZERO']]
    keys = [events[i]['key'] for i in (2, 3, 5, 7, 9)]
    assert all(equal(k, keys[0]) for k in keys)
    assert events[2]['depth'] == events[7]['depth'] == 0
    assert events[7]['child_status'] == 'EXHAUSTED' and events[9]['reason'] == 'CHILD_EXHAUSTED'
    assert events[0]['state_sha256'] == events[2]['state_sha256'] == events[7]['state_sha256'] == initial_sha
    assert events[4]['state_sha256'] == events[5]['state_sha256'] == events[6]['state_sha256']
    assert events[8]['state_sha256'] == events[9]['state_sha256']
    assert engine['status'] == 'UNKNOWN' and engine['reason'] == 'node ceiling; no exhausted conclusion'
    assert engine['found'] is None and engine['trace_complete'] is False
    assert engine['root_restored'] is engine['stack_restored'] is q['root_restored'] is True
    assert engine['root_snapshot_sha256'] == engine['final_snapshot_sha256']
    counts = engine['counts']
    for k, v in {'nodes': 2, 'global_scans': 2, 'branches': 1, 'forced': 0, 'placements': 1,
                 'backtracks': 1, 'restores': 1, 'fallback_advances': 1, 'family_batches': 1,
                 'family_checks': 1, 'family_choices': 0, 'family_unknown': 1, 'family_canonical_choices': 1}.items():
        assert counts[k] == v
    combined_names = {}
    for census in (report['prototype_census'], wrapper['prototype_census']):
        assert census == sorted(census) and len({e[0] for e in census}) == len(census)
        for name, encoded in census:
            pre = json.loads(encoded)
            assert canonical(pre) == encoded
            assert name not in combined_names or combined_names[name] == encoded
            combined_names[name] = encoded
    assert len(wrapper['prototype_census']) == 28
    assert len([e for e in wrapper['prototype_census'] if e[0].startswith('bounded-point-tile-')]) == 14
    grounds = [g for record in report['records'] for match in record['matches'] for g in match['groundings']]
    for ground in grounds:
        if ground['preflight'] is not None:
            for tile in ground['preflight']['tiles']:
                for key in (tile['base_tile']['placement_key'], tile['placement_key']):
                    assert dict(report['prototype_census'])[key['tile_type_id']] == canonical(key['type_preimage'])
    assert len(grounds) == report['accounting']['ground_environment_proposals']
    assert len([g for g in grounds if g['check'] is not None]) == report['accounting']['checked_expansions']
    assert len([g for g in grounds if g['preflight'] is not None]) == report['accounting']['preflight_checks']
    assert len([g for g in grounds if g['status'] == 'COMPLETED_NATIVE_MEMBER_EXCLUSION']) == report['accounting']['native_member_exclusions']
    for v in (payload, probe, q, engine, wrapper, consumer, disp):
        for k in ('logical_proof_accepted', 'RL_accepted'):
            if k in v:
                assert v[k] is False
    assert q['useful_transfer_accepted'] is False and q['whole_engine_qualified'] is False
    assert probe['new_theorem_discovered'] is False and probe['family_library_activated'] is False
    assert probe['engine_activated'] is False and probe['scheduler_or_rollback_accepted'] is False
    assert disp['whole_engine_qualified'] is False and disp['GCTS_advantage_claimed'] is False
    arms[mode] = {'saved_disposition': disposition_ref, 'expanded_result': expanded_ref,
        'plan': plan_ref, 'authorization': plan['ROOT_authorization'], 'source_contract': plan['source_contract'],
        'matching_mode': q['matching_mode'], 'native_launch_to_postprobe_ns': elapsed,
        'native_seconds': elapsed / 1000000000, 'aggregate_B_bytes': disp['aggregate_B_bytes'],
        'aggregate_MiB': disp['aggregate_B_bytes'] / 1048576,
        'tool_Date_seconds': bracket['complete_Date_seconds'], 'tool_session_id': bracket['tool_session_id'],
        'native_exit': terminal['caller_returncode'], 'all_reaped': True,
        'phases_joined': len(parsed_phases), 'phase_records_sha256': digest(parsed_phases),
        'provider_reason': report['reason'], 'provider_work': report['work'],
        'provider_accounting': report['accounting'],
        'provider_census_entries': len(report['prototype_census']),
        'engine_wrapper_census_entries': 28, 'engine_wrapper_original_types': 14, 'engine_wrapper_decorated_types': 14,
        'provider_callback_report_sha256': provider_obs['report_sha256'],
        'consumer_callback_receipt_sha256': consumer_obs['receipt_sha256'],
        'consumer_request_sha256': consumer_obs['request_sha256'], 'engine_wrapper_sha256': digest(wrapper),
        'engine_counts': counts, 'engine_status': engine['status'], 'engine_reason': engine['reason'],
        'root_snapshot_sha256': engine['root_snapshot_sha256'], 'final_snapshot_sha256': engine['final_snapshot_sha256'],
        'saved_grounding_status_counts': dict(collections.Counter(g['status'] for g in grounds)),
        'saved_preflight_status_counts': dict(collections.Counter(g['preflight']['status'] if g['preflight'] else 'NOT_RETURNED' for g in grounds))}
    data[mode] = {'plan': plan, 'payload': payload, 'probe': probe, 'receiver': q, 'report': report,
                  'wrapper': wrapper, 'consumer': consumer, 'engine': engine, 'key': keys[0]}

v, l = data['visible'], data['literal']
for path in ('sources', 'inputs', 'limits', 'runtime', 'source_contract'):
    assert equal(v['plan'][path], l['plan'][path])
for path in ('initial_state', 'provider_limits', 'source_pool_component_id', 'source_pool_families',
             'frozen_open_pool_sha256', 'maximum_nodes', 'maximum_events', 'branch_tie'):
    assert equal(v['receiver'][path], l['receiver'][path])
assert equal(v['report']['request']['mined'], l['report']['request']['mined'])
assert equal(v['report']['physical_assignment_plan'], l['report']['physical_assignment_plan'])
assert equal(v['key'], l['key']) and equal(v['consumer'], l['consumer'])
assert equal(v['wrapper']['prototype_census'], l['wrapper']['prototype_census'])
assert equal(v['engine']['counts'], l['engine']['counts'])
assert equal(v['engine']['last_observed_state'], l['engine']['last_observed_state'])
assert v['engine']['root_snapshot_sha256'] == l['engine']['root_snapshot_sha256']
assert len(v['probe']['original_model_sources']) == len(l['probe']['original_model_sources']) == 17
assert equal(v['probe']['original_model_sources'], l['probe']['original_model_sources'])
assert equal(v['probe']['original_model_binding'], l['probe']['original_model_binding'])
assert arms['visible']['provider_work']['steps'] == 1000000
assert arms['literal']['provider_work']['steps'] == 129586
assert arms['visible']['provider_accounting']['binding_attempts'] == 60
assert arms['literal']['provider_accounting']['binding_attempts'] == 30
record = v['report']['records'][1]
first_abstract_plan = v['report']['physical_assignment_plan']['plans'][15]
assert first_abstract_plan['assignment'] == [[['input','i0'],0],[['node','n0'],0],[['node','n1'],23]]
g = record['matches'][0]['groundings'][5]
preflight = g['preflight']
assert preflight['status'] == 'INCOMPATIBLE_ASSIGNMENT'
assert preflight['reason'] == 'literal_repeated_or_remote_formula_mark_conflict'
assert preflight['node_id'] == 'n1' and preflight['row'] == 23
assert [x['membership']['status'] for x in preflight['membership']] == ['MEMBER', 'MEMBER']
input_port = g['port_bindings']['inputs'][0]
assert input_port['occupied'] is False and input_port['fact_accepted'] is False
assert input_port['source']['row'] == 0 and input_port['source']['original_full_key'] is None
axiom_formula = preflight['membership'][0]['witness']['formula']
assert preflight['tiles'][0]['global_m_values'] == [[[1,0],['formula',canonical(axiom_formula)]]]
assert input_port['formula'] == ['imp', axiom_formula, g['environment']['substitution']['F0']['body']]
assert not equal(axiom_formula, input_port['formula'])
origin_env = record['record']['substitution']
current_env = g['environment']['substitution']
assert origin_env['F0'] == {'body': ['bot'], 'formal_names': []}
assert current_env['F0']['formal_names'] == [] and current_env['F0']['body'][0] == 'all'
assert equal(current_env['F0']['body'], v['report']['branch_output_receptor'])
assert {k:x for k,x in origin_env.items() if k != 'F0'} == {k:x for k,x in current_env.items() if k != 'F0'}
findings = {
    'schema': 'ROOT-receiver-pair-saved-data-interpretation-review-v1',
    'reviewer_identity': '/root/hilbert_advice_controls', 'root_interpretation_author': '/root',
    'authorship_disclosure': 'Reviewer authored provider7 and earlier host/consumer/engine ancestry; this is a distinct saved-data concordance/interpretation audit of Root records, NOT a second independent mathematical implementation or semantic replay.',
    'saved_data_review_passed': True, 'discrepancies': [],
    'authorization': 'Root explicitly authorized current saved JSON/raw transport/native record reads only; earlier Source-only result-read ban lifted for these two runs.',
    'arms': arms,
    'common': {'current_executable_sources': 21, 'current_inputs': 10,
        'original_semantic_sources': 17, 'original_semantic_inputs': 2,
        'original_model_binding': v['probe']['original_model_binding'],
        'frozen_inventory_input': v['plan']['inputs']['frozen_inventory'],
        'inventory_acceptance_input': v['plan']['inputs']['inventory_acceptance'],
        'inventory_reused': True, 'inventory_construction_charged_in_receiver_windows': False,
        'same_whole_mined_pool_sha256': v['receiver']['frozen_open_pool_sha256'],
        'same_initial_state_sha256': digest(v['receiver']['initial_state']),
        'same_actual_decision': {'kind': 'BRANCH', 'row': 23},
        'same_branch_tie': 'ASSIGNED-OUTPUT-THEN-ROW', 'same_provider_caps': v['receiver']['provider_limits'],
        'same_all30_physical_plans_sha256': digest(v['report']['physical_assignment_plan']),
        'planning_counts': {'records': 2, 'row_trials_each': 32, 'total_row_trials': 64,
                            'plans_each': 15, 'total_plans': 30, 'unallocated_remainder': 0},
        'same_full_canonical_fallback_key': v['key'],
        'same_literal_consumer_receipt_sha256': digest(v['consumer']),
        'same_engine_owned_full_census_sha256': digest(v['wrapper']['prototype_census']),
        'same_closed_wrapper_census_count': 28, 'same_wrapper_original_count': 14, 'same_wrapper_decorated_count': 14,
        'trace': ['actual global BRANCH23', 'family/provider UNKNOWN and zero offers',
                  'same actual canonical primitive PLACE23', 'actual checked DEAD0',
                  'child EXHAUSTED and owned RESTORE', 'same full-key CHILD_EXHAUSTED EXCLUDE',
                  'maximum_nodes2 UNKNOWN', 'recorded exact root snapshot digest restoration'],
        'both_event_count': 10, 'engine_counts_literal_equal': True},
    'first_abstract_plan_point_conflict': {
        'plan_index': 15, 'record_index': 1, 'family_id': record['record']['family_id'],
        'assignment': first_abstract_plan['assignment'], 'grounding_index': 5,
        'preceding_trials': 'The first five groundings in this same plan are completed native exclusions; this is the first whole-point-conflict observation, not the first grounding.',
        'independent_expansion_status': g['check']['status'],
        'native_members': [{'node_id': x['node_id'], 'rule': x['witness']['rule'], 'status': x['membership']['status']} for x in preflight['membership']],
        'status': preflight['status'], 'reason': preflight['reason'],
        'point': [1,0], 'native_member_output_formula': axiom_formula,
        'unoccupied_external_input_formula_obligation': input_port['formula'],
        'external_occupied': False, 'fact_accepted': False,
        'interpretation': 'Same assigned row for the proposed AX output and external implication obligation gives unequal complete formula values. The saved preflight rejects this physical assignment; neither input occupancy nor syntax matching qualifies a transfer.'},
    'substituted_parameter_difference': {
        'parameter': 'F0', 'kind': 'FORMULA', 'formal_names': [],
        'source_body': origin_env['F0']['body'], 'current_inferred_body': current_env['F0']['body'],
        'difference': 'Complete FORMULA body changed from literal bot to actual assigned all-formula at the receiver; the four VARIABLE bindings in this particular trial remain source-literal x/y.',
        'qualified_transfer': False},
    'denominator_cautions': [
        'Thirty identical materialized physical plans is not thirty completed inference plans: visible attempts16, literal attempts30.',
        'Inference44 ground environments includes43 returned independent checks/preflights plus one unfinished grounding at own1m;42 completed native exclusions plus one point conflict, zero native adaptations/instances/offers.',
        'Literal30 explicit-origin bindings produce no environment at this receiver; this is a bounded-prefix no-offer observation, not an impossibility or completeness result.',
        'Provider census2 versus0 and engine wrapper census28 versus28 are literal FULL-preimage data, not candidate/degree/proof counts.',
        'Native resource success and reached ordered phases do not imply semantic usefulness, source-level correctness from timing, exclusive costs, speedup or whole-engine qualification.',
        'Recorded root/final snapshot digest equality and root_restored flags are joined saved evidence; no independent engine rollback or mathematical recheck was performed.'
    ],
    'flags': {'scientific_replay': False, 'project_module_evaluated': False, 'scientific_calls': 0,
              'new_actuals': 0, 'new_theorems': 0, 'logical_proof_accepted': False,
              'useful_transfer_accepted': False, 'whole_engine_qualified': False,
              'complete_GCTS_model_accepted': False, 'GCTS_advantage_claimed': False,
              'RL_accepted': False, 'scientific_acceptance': False}
}
ref = save('saved-pair-findings-v1.json', findings)
handoff = save('handoff-v1.json', {'schema': 'ROOT-receiver-pair-saved-data-review-handoff-v1',
    'findings': ref, 'saved_data_review_passed': True, 'discrepancies': [],
    'scientific_replay': False, 'scientific_calls': 0, 'scientific_acceptance': False})
print(json.dumps({'findings': ref, 'handoff': handoff}, sort_keys=True))
