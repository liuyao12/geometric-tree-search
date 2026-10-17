"""Saved-byte interpretation only; no project imports, calls, clocks or replay."""
import base64
import collections
import hashlib
import json
import re
import zlib
from pathlib import Path

O = Path('/private/tmp/gcts-head-gated-data-review-20261017')

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

def canonical(v, ascii_only=False):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=ascii_only, allow_nan=False)

def digest(v, ascii_only=False):
    return hashlib.sha256(canonical(v, ascii_only).encode()).hexdigest()

def equal(a, b):
    return canonical(a) == canonical(b)

def save(n, v):
    p = O / n
    with p.open('xb') as f:
        f.write((json.dumps(v, sort_keys=True, indent=2) + '\n').encode())
    return pin(p)

stages = ['BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS',
          'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE',
          'BEFORE_MARKING_CHECK', 'BEFORE_POOL_READ', 'BEFORE_ENGINE', 'BEFORE_PROVIDER',
          'AFTER_PROVIDER', 'AFTER_ENGINE', 'BEFORE_OUTPUT']
common, arms = {}, {}
for mode, code, interval, peak in [('visible', 2, 20203157000, 94683136), ('literal', 0, 8448856000, 82657280)]:
    H = Path('/private/tmp/gcts-head-gated-inference-' + mode + '-ROOT-20261017')
    pref = pin(H / 'ROOT-plan-v1.json');plan = json.loads(check(pref))
    dref = pin(H / 'ROOT-disposition-v1.json');disp = json.loads(check(dref))
    auth = json.loads(check(plan['ROOT_authorization']))
    contract = json.loads(check(plan['source_contract']))
    assert disp['plan'] == pref and disp['source_contract'] == plan['source_contract']
    assert len(plan['sources']) == 22 and len(plan['inputs']) == 10
    assert auth['author_identity'] == '/root' and auth['actual_execution_authorized'] is True
    assert auth['maximum_actual_invocations'] == 1 and auth['unchanged_actual_may_be_restarted'] is False
    for k in ('sources', 'inputs', 'limits', 'runtime', 'source_contract', 'purpose', 'invocation_id', 'output_directory'):
        assert equal(auth[k], plan[k])
    native = {k: check(v) for k, v in disp['native_files'].items()}
    once, obs, terminal = (json.loads(native[k]) for k in ('ONCE.json', 'observation.json', 'native-terminal.json'))
    bracket = json.loads(check(disp['tool_bracket']))
    for v in (once, obs, bracket):
        assert v['plan_sha256'] == pref['sha256'] and v['plan_bytes'] == pref['bytes']
    assert once['invocation_id'] == obs['invocation_id'] == plan['invocation_id']
    assert once['purpose'] == obs['purpose'] == plan['purpose']
    assert type(bracket['tool_session_id']) is int and bracket['tool_session_id'] > 0
    assert type(bracket['observed_session_id']) is int and bracket['observed_session_id'] == bracket['tool_session_id']
    assert type(bracket['tool_exit_code']) is int and bracket['tool_exit_code'] == code
    assert bracket['unchanged_actual_restarted'] is False
    assert bracket['complete_Date_seconds'] == (bracket['ended_Date_ms'] - bracket['began_Date_ms']) / 1000
    assert 0 < bracket['complete_Date_seconds'] < 91
    assert type(terminal['caller_returncode']) is int and terminal['caller_returncode'] == code
    assert type(obs['meter_returncode']) is int and obs['meter_returncode'] == code
    assert terminal['wait4_pid'] == terminal['caller_pid'] and terminal['wait4_status'] == code << 8
    assert terminal['all_reaped'] is disp['all_reaped'] is disp['actual_closed'] is True
    assert terminal['error'] is None and terminal['interrupted'] is False and terminal['cancellation_forwarded'] is False
    assert native['postterminal-probe-stderr.txt'] == b'' and obs['probe_returncode'] == 0
    assert int(native['postterminal-probe-stdout.txt']) == obs['postterminal_native_probe_ns']
    elapsed = obs['postterminal_native_probe_ns'] - terminal['caller_launch_began_ns']
    assert elapsed == disp['native_launch_to_postprobe_ns'] == interval
    assert terminal['caller_kernel_peak_bytes'] == terminal['wait4_usage'][2] == disp['aggregate_B_bytes'] == peak
    assert peak < 536870912
    lines = native['meter-stderr.txt'].decode().splitlines(keepends=True)
    phases, tail = [], ''
    for index, line in enumerate(lines):
        m = re.fullmatch(r'COMPONENT_INVENTORY_PHASE ([A-Z_]+) ([0-9]{1,19})\n', line)
        if m:
            assert not tail
            phases.append({'stage': m[1], 'native_ns': int(m[2])})
        else:
            tail += line
    assert phases == disp['phase_observations']
    assert [x['stage'] for x in phases] == (stages if code == 0 else stages[:11])
    ns = [x['native_ns'] for x in phases]
    assert ns == sorted(ns) and terminal['caller_launch_began_ns'] < ns[0] < ns[-1] < terminal['caller_terminal_observed_ns']
    assert disp['stderr_tail_sha256'] == {'bytes': len(tail.encode()), 'sha256': hashlib.sha256(tail.encode()).hexdigest()}
    assert disp['logical_proof_accepted'] is disp['whole_engine_qualified'] is disp['GCTS_advantage_claimed'] is disp['RL_accepted'] is False
    assert disp['complete_GCTS_model_accepted'] is False and disp['scientific_replay'] is False
    arm = {'disposition': dref, 'plan': pref, 'authorization': plan['ROOT_authorization'],
           'source_contract': plan['source_contract'], 'tool_bracket': disp['tool_bracket'],
           'native_exit': code, 'tool_session_id': bracket['tool_session_id'], 'all_reaped': True,
           'native_launch_to_postprobe_ns': elapsed, 'native_seconds': elapsed / 1000000000,
           'aggregate_B_bytes': peak, 'aggregate_MiB': peak / 1048576,
           'complete_tool_Date_seconds': bracket['complete_Date_seconds'],
           'native_resources_qualified': disp['native_resources_qualified'],
           'complete_wire_verified': disp['complete_wire_verified'],
           'receiver_probe_record_complete': disp['receiver_probe_record_complete'],
           'phase_records': phases, 'stderr_tail_bytes': len(tail.encode())}
    if code == 2:
        f = disp['failure_diagnostic']
        draw = check(f['diagnostic']);diagnostic = json.loads(draw)
        completion = json.loads(check(f['completion']))
        assert completion['sha256'] == f['diagnostic']['sha256'] and completion['bytes'] == len(draw)
        assert completion['file'] == 'unknown-diagnostic.json'
        assert completion['diagnostic_only'] is True and completion['positive_joint_gate_accepted'] is False
        assert completion['terminal_exit2_and_external_failure_closure_required'] is True
        assert f['complete_pair'] is True and equal(f['context'], diagnostic['context'])
        context = diagnostic['context'];detail = diagnostic['diagnostic']
        assert set(diagnostic['last_observations']) == {'proposer','fallback','completion','validator'}
        assert all(x is None for x in diagnostic['last_observations'].values())
        assert equal(f['last_observations'], diagnostic['last_observations'])
        assert context['sources'] == plan['sources'] and context['inputs'] == plan['inputs']
        assert context['source_contract'] == plan['source_contract']
        assert context['plan'] == {k: pref[k] for k in ('bytes','sha256')}
        assert context['invocation_id'] == plan['invocation_id'] and context['purpose'] == plan['purpose']
        assert context['joint_deadline_ns'] - context['joint_began_ns'] == 20000000000
        assert context['diagnostic_only'] is True and context['positive_joint_gate_accepted'] is False
        assert context['reported_case_count'] is f['reported_case_count'] is None
        assert context['qualified_case_count'] == f['qualified_case_count'] == 0
        assert f['failure_cause_established'] is f['last_observation_is_active_failure_frame'] is False
        assert detail['diagnostic_only'] is True and detail['returned_control_record'] is False
        assert detail['last_observation_is_active_failure_frame'] is False
        assert set(p.name for p in (H/'RI-owned-v1').iterdir()) == {'unknown-diagnostic.json','diagnostic-completion.json'}
        assert not (H/'ROOT-expanded-result-v1.json').exists()
        assert disp['status'] == 'UNKNOWN' and disp['receiver_probe_record_complete'] is False
        assert disp['native_resources_qualified'] is disp['complete_wire_verified'] is False
        assert native['meter-stdout.txt'] == b''
        assert tail == 'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete marking data controls original20/500 reserve unfinished\n'
        arm.update(status='UNKNOWN', failure_pair={'diagnostic':f['diagnostic'],'completion':f['completion']},
            diagnostic_pair_complete=True, returned_control_record=False,
            administrative_qualified_case_count=0, reported_case_count=None,
            last_observations=diagnostic['last_observations'], provider_counts=None, offers=None,
            whole_physical_plans=None, actual_branch=None, state=None, census=None,
            consumer_receipt=None, engine_trace=None, exact_root_rollback=None,
            failure_cause_established=False, active_failure_frame_established=False,
            phase_meaning='Reached fixed writes through AFTER_PROVIDER only. No AFTER_ENGINE or BEFORE_OUTPUT write. This does not recover report contents, status, counters, current state/branch, an active fault frame or exclusive failure cause. All unreturned scientific observations remain UNKNOWN.')
        common[mode] = {'plan':plan,'context':context}
    else:
        assert elapsed < 20000000000 and not tail and disp['native_resources_qualified'] is True
        assert disp['status'] == 'RECEIVER_PROBE_RECORDED' and disp['failure_diagnostic'] is None
        envelope = json.loads(check(disp['outputs'][0]))
        response_raw = check(disp['outputs'][1]);response_lines=response_raw.splitlines(keepends=True)
        assert len(response_lines) == 2
        body, completion = map(json.loads, response_lines)
        assert completion['body_bytes'] == len(response_lines[0])
        assert completion['body_sha256'] == hashlib.sha256(response_lines[0]).hexdigest()
        assert completion['exit_zero_and_coordinator_deadline_required'] is True
        assert body['plan'] == {k: pref[k] for k in ('bytes','sha256')}
        for k in ('sources','inputs','limits','invocation_id'):
            assert equal(body[k], plan[k])
        assert body['outputs'] == disp['outputs'][:1]
        stdout = json.loads(native['meter-stdout.txt'])
        assert stdout['outputs'] == disp['outputs'] and stdout['response'] == disp['outputs'][1]
        compressed=base64.b64decode(envelope['payload_base64'],validate=True)
        assert len(compressed)==envelope['compressed_bytes'] and hashlib.sha256(compressed).hexdigest()==envelope['compressed_sha256']
        expanded_raw=check(disp['expanded'])
        assert zlib.decompress(compressed)==expanded_raw
        assert envelope['expanded_bytes']==len(expanded_raw) and envelope['expanded_sha256']==disp['expanded']['sha256']
        payload=json.loads(expanded_raw);probe=payload['receiver_probe'];q=probe['receiver'];engine=q['engine_result'];events=engine['events']
        assert payload['sources']==plan['sources'] and payload['inputs']==plan['inputs'] and payload['purpose']==plan['purpose']
        assert len(probe['original_model_sources'])==17 and len(probe['original_model_inputs'])==2
        assert equal(payload['language_binding'],probe['original_model_binding'])
        assert q['matching_mode']=='LITERAL_GROUND' and q['inventory_reused'] is True and q['inventory_construction_charged_in_this_window'] is False
        preference=next(x for x in events if x['kind']=='FAMILY_PREFERENCE');wrapper=preference['receipts'][0]
        report=wrapper['provider_report'];consumer=wrapper['consumer_receipt'];observations=q['observations']
        assert len(observations['provider_calls'])==len(observations['consumer_calls'])==1
        po,co=observations['provider_calls'][0],observations['consumer_calls'][0]
        assert po['report_sha256']==digest(report) and co['receipt_sha256']==digest(consumer)
        assert co['request_sha256']==consumer['request_sha256']==digest({'schema':'receptor-family-primitive-preference-request-v1','mode':'BATCH','payload':report['batch']})
        assert report['schema']=='receptor-family-observed-receptor-transfer-provider-v2'
        assert report['version']=='receptor-family-observed-receptor-transfer-provider-v8-head-gated'
        assert report['matching_mode']=='LITERAL_GROUND' and report['batch']['instances']==[] and report['offers']==[]
        assert report['work']['steps']==150611 and report['work']['row_trials']==64
        assert q['provider_limits']==report['work']['limits']=={'depth':128,'input_bytes':4194304,'instances':1,'records':2,'row_trials':64,'work':1000000}
        assert equal(po['state'],q['initial_state']) and equal(report['checked_state'],q['initial_state'])
        assert equal(report['request']['state'],q['initial_state']) and equal(consumer['entry']['state'],q['initial_state'])
        for x in (po,report,report['request'],report['batch'],wrapper,consumer,co):assert x['decision']=={'kind':'BRANCH','row':23}
        for x in (report,report['batch'],wrapper,consumer,co):assert x['state_sha256']==digest(q['initial_state'])
        assert q['frozen_open_pool_sha256']==digest(report['request']['mined'])
        plans=report['physical_assignment_plan']['plans'];checks=report['physical_assignment_plan']['head_gate']['checks']
        assert len(plans)==len(checks)==30 and report['accounting']['attempted_assignments']==30
        assert report['physical_assignment_plan']['record_allocations']==[{'bounded_reason':'OWN_PER_RECORD_PHYSICAL_ROW_TRIAL_PREFIX','planned_assignments':15,'record_index':i,'row_trial_quota':32,'row_trials':32,'status':'BOUNDED_STRUCTURAL_PREFIX'} for i in range(2)]
        gate_summaries=[];skipped=[];absent_passes=[]
        receipts=[]
        for index,(p,g) in enumerate(zip(plans,checks)):
            assert p['plan_index']==g['plan_index']==index and p['record_index']==g['record_index']
            record=report['records'][g['record_index']]
            expansion=record['source_ground_check']['expansion']
            shape={'nodes':[{k:n[k] for k in ('id','rule','ordered_inputs','origin')}for n in expansion['primitive_nodes']],
                   'inputs':[x['port_id']for x in expansion['input_ports']],
                   'outputs':[{'port_id':x['port_id'],'source':x['source']}for x in expansion['outputs']]}
            assignment={tuple(k):v for k,v in p['assignment']}
            rows={'schema':'receptor-family-six-rule-row-assignment-v1',
                'node_rows':[[n['id'],assignment[('node',n['id'])]]for n in shape['nodes']],
                'input_rows':[[pid,assignment[('input',pid)]]for pid in shape['inputs']]}
            expected={'descriptor':record['record']['descriptor'],'layout_shape':shape,'row_assignment':rows,
                      'limits':{'depth':128,'input_bytes':1048576,'requirements':4096,'work':100000}}
            receipt=g['receipt'];assert equal(g['request'],expected) and equal(receipt['request'],expected)
            assert receipt['request_sha256']==digest(expected,True)
            assert receipt['schema']=='receptor-family-coarse-head-plan-check-v1' and receipt['version']=='receptor-family-coarse-formula-head-plan-marks-v1'
            assert receipt['planning_channel']==5 and receipt['scope']=='THIS_PHYSICAL_CLUSTER_PLAN_ONLY'
            assert receipt['gate_completed'] is True and receipt['reason'] is None
            assert receipt['status']in('HEAD_CONFLICT','NO_KNOWN_HEAD_CONFLICT')
            conflict=receipt['status']=='HEAD_CONFLICT'
            assert receipt['advisory_plan_rejected'] is conflict and bool(receipt['conflicts']) is conflict
            assert g['outcome']==('SKIP_THIS_PHYSICAL_PLAN'if conflict else'PASS_TO_OBSERVED_MATCHING')
            assert receipt['work']['limits']==expected['limits']
            assert receipt['flags']['advisory_cluster_plan_only'] is receipt['flags']['native_validation_required'] is True
            assert all(x is False for k,x in receipt['flags'].items()if k not in('advisory_cluster_plan_only','native_validation_required'))
            if conflict:skipped.append(index)
            if not conflict and receipt['unknown_requirement_indices']:absent_passes.append(index)
            for ri in receipt['unknown_requirement_indices']:
                assert receipt['requirements'][ri]['head'] is None and receipt['requirements'][ri]['mark'] is None
            gate_summaries.append({'plan_index':index,'record_index':g['record_index'],'outcome':g['outcome'],
                'status':receipt['status'],'request_ascii_sha256':receipt['request_sha256'],
                'literal_receipt_sha256':digest(receipt),'absent_requirement_count':len(receipt['unknown_requirement_indices']),
                'conflict_points':[x['point']for x in receipt['conflicts']]})
            receipts.append(receipt)
        assert skipped==[0,15] and absent_passes==list(range(16,30))
        accounting=report['accounting']
        expected_counts={'head_gate_calls':30,'head_gate_receipts_returned':30,'head_gate_conflicting_plans':2,
            'head_gate_no_known_conflict':28,'head_gate_unknown':0,'head_gate_absent_head_passes':14,
            'head_gate_downstream_assignments':28,'binding_attempts':28,'ground_environment_proposals':0,
            'checked_expansions':0,'preflight_checks':0,'native_member_exclusions':0,'native_adaptations':0,
            'checked_instances':0,'offered_instances':0}
        assert all(accounting[k]==v for k,v in expected_counts.items())
        assert [(x['record_index'],len(x['matches']))for x in report['records']]==[(0,14),(1,14)]
        assert consumer['status']==wrapper['status']=='UNKNOWN' and consumer['selection'] is None and consumer['checks']==[]
        assert len(report['prototype_census'])==0 and len(wrapper['prototype_census'])==28
        names={}
        for name,pre in wrapper['prototype_census']:
            assert canonical(json.loads(pre))==pre and(name not in names or names[name]==pre);names[name]=pre
        assert len(names)==28 and sum(name.startswith('bounded-point-tile-')for name in names)==14
        assert [x['kind']for x in events]==['DECISION','FALLBACK','TRY','FAMILY_PREFERENCE','INVALIDATE','PLACE','DECISION','RESTORE','INVALIDATE','EXCLUDE']
        assert [x['decision']for x in events if x['kind']=='DECISION']==[{'kind':'BRANCH','row':23},{'kind':'DEAD','row':0}]
        assert events[3]['mode']=='CANONICAL_FALLBACK' and events[7]['child_status']=='EXHAUSTED' and events[9]['reason']=='CHILD_EXHAUSTED'
        assert all(equal(events[i]['key'],events[2]['key'])for i in(3,5,7,9))
        assert engine['status']=='UNKNOWN' and engine['reason']=='node ceiling; no exhausted conclusion'
        assert engine['root_restored'] is engine['stack_restored'] is q['root_restored'] is True
        assert engine['root_snapshot_sha256']==engine['final_snapshot_sha256']
        assert all(p[0]!=5 for p,v in q['initial_state']['m'])
        assert all(p[0]!=5 for p,v in engine['last_observed_state']['m'])
        assert engine['counts']['family_choices']==0 and engine['counts']['family_canonical_choices']==1
        assert q['useful_transfer_accepted'] is q['whole_engine_qualified'] is q['logical_proof_accepted'] is q['RL_accepted'] is False
        assert probe['new_theorem_discovered'] is False
        arm.update(status=disp['status'],expanded=disp['expanded'],provider_reason=report['reason'],
            provider_work=report['work'],provider_accounting=accounting,
            provider_report_sha256=po['report_sha256'],consumer_receipt_sha256=co['receipt_sha256'],
            consumer_request_sha256=co['request_sha256'],engine_wrapper_sha256=digest(wrapper),
            provider_census_entries=0,engine_wrapper_census_entries=28,engine_wrapper_original_types=14,engine_wrapper_decorated_types=14,
            engine_wrapper_census_sha256=digest(wrapper['prototype_census']),
            physical_structural_plans_sha256=digest(plans),full_gate_prefix_sha256=digest(report['physical_assignment_plan']['head_gate']),
            gate_receipt_summaries=gate_summaries,gate_conflict_plans=[{'plan':plans[i],'receipt_conflicts':receipts[i]['conflicts'],
                'absent_requirements':receipts[i]['unknown_requirement_indices']}for i in skipped],
            gate_work_steps_sum=sum(x['work']['steps']for x in receipts),
            actual_branch={'kind':'BRANCH','row':23},same_frozen_pool_sha256=q['frozen_open_pool_sha256'],
            actual_initial_state_sha256=digest(q['initial_state']),engine_status=engine['status'],engine_reason=engine['reason'],
            engine_counts=engine['counts'],event_kinds=[x['kind']for x in events],
            canonical_fallback_key=events[2]['key'],recorded_root_restored=True,
            root_snapshot_sha256=engine['root_snapshot_sha256'],final_snapshot_sha256=engine['final_snapshot_sha256'],
            native_channel5_in_state=False)
        common[mode]={'plan':plan,'payload':payload,'probe':probe,'receiver':q}
    arms[mode]=arm

for k in ('sources','inputs','limits','runtime','source_contract'):
    assert equal(common['visible']['plan'][k],common['literal']['plan'][k])
assert equal(common['visible']['context']['original_model_binding'],common['literal']['probe']['original_model_binding'])
result={'schema':'ROOT-head-gated-receiver-saved-data-review-v1','reviewer_identity':'/root/hilbert_advice_controls',
    'root_interpretation_author':'/root','saved_data_review_passed':True,'discrepancies':[],
    'authorship_disclosure':'Reviewer authored provider8 and earlier host/consumer/engine ancestry; this is independent saved-data interpretation/concordance of Root records, not a second mathematical implementation or scientific replay.',
    'arms':arms,'configured_pair_joins':{'same_executable_sources22':True,'same_inputs10':True,
        'same_native_limits_and_runtime':True,'same_source_contract':common['literal']['plan']['source_contract'],
        'same_frozen_inventory_input':common['literal']['plan']['inputs']['frozen_inventory'],
        'original_semantic_sources17_inputs2_epoch_unchanged_in_returned_literal_payload_and_failure_context':True,
        'same_actual_whole30plans_across_arms':None,'same_actual_initial_state_across_arms':None,
        'same_actual_branch_across_arms':None,'reason':'Visible full provider/engine result was not returned. Shared configuration is observed; scientific path equality is UNKNOWN.'},
    'interpretation':['Literal completed30 gate receipts with full request/preimage data and original ASCII request SHA joins:2 completed plan conflicts,28 no-known conflicts,14 of those pass with absent meta heads,0 gateUNKNOWN.',
        'The two skipped advisory layouts are plans0/15, both with imp and all requirements at planning point(5,0). These are no native candidate/degree/EOF exclusions and channel5 is absent from returned native state.',
        'Literal performed28 explicit-origin binding attempts after gate; no complete environment, current independent expansion, native preflight, adaptation or offer. Same canonical primitive then recorded DEAD0/child restoration/exclusion and node-capUNKNOWN.',
        'Visible exited2 after20.203157 native seconds and returned only the completed diagnostic pair. Eleven reached writes end withAFTER_PROVIDER; all4 last-entry slots are null. Counts/offers/state/branch/census/rollback are unreturned UNKNOWN, never zero or inferred equal to literal.',
        'Literal native8.448856seconds/82657280bytes qualifies its native resource window under original bounds. Its complete toolDate50.59seconds is separately recorded, not replaced by native interval.',
        'These data do not establish a timing bottleneck, gate speedup, useful transfer, theorem, learned marking, full-engine/GCTS/RL qualification or current-source correctness from timing. No third actual or scientific replay occurred.'],
    'scientific_replay':False,'scientific_calls':0,'project_module_evaluated':False,'new_actuals':0,
    'scientific_acceptance':False,'proof_accepted':False,'useful_transfer_accepted':False,
    'whole_engine_qualified':False,'GCTS_advantage_claimed':False,'RL_accepted':False}
ref=save('saved-head-gated-findings-v1.json',result)
href=save('handoff-v1.json',{'schema':'ROOT-head-gated-saved-data-review-handoff-v1','findings':ref,
    'saved_data_review_passed':True,'discrepancies':[],'scientific_replay':False,'scientific_calls':0,'scientific_acceptance':False})
print(json.dumps({'findings':ref,'handoff':href},sort_keys=True))
