"""Whole saved evidence/resource concordance only. No degree or logical replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(ref):
    p=Path(ref['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==ref;return p
mode='marking'
plan_path=HERE/'ROOT-marking-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'marking-owned-v1';external=HERE/'marking-external-v1'
bracket=read(HERE/'ROOT-marking-tool-bracket-v1.json')
assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
assert bracket['tool_exit_code']==0 and bracket['tool_session_id'] is None
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
assert sorted(p.name for p in owned.iterdir())==['engine-result.json','response.jsonl']
outputs=[pin(owned/n) for n in ('engine-result.json','response.jsonl')]
lines=(owned/'response.jsonl').read_bytes().splitlines(keepends=True)
assert len(lines)==2 and all(x.endswith(b'\n') for x in lines)
body,completion=map(json.loads,lines)
assert completion['body_sha256']==hashlib.sha256(lines[0]).hexdigest() and completion['body_bytes']==len(lines[0])
assert completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True
assert body['schema']=='ROOT-unit-row-global-engine-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
assert body['plan']=={k:pp[k] for k in ('sha256','bytes')} and body['sources']==plan['sources'] and body['inputs']==plan['inputs']
assert body['invocation_id']==plan['invocation_id'] and body['limits']==plan['limits'] and body['outputs']==outputs[:1]
for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(ref)
stdout_raw=(external/'meter-stdout.txt').read_bytes();assert stdout_raw.endswith(b'\n') and len(stdout_raw.splitlines())==1
stdout=json.loads(stdout_raw);assert stdout['outputs']==outputs and stdout['response']==outputs[-1] and stdout['pending_external'] is True
assert not (external/'meter-stderr.txt').read_bytes() and not (external/'postterminal-probe-stderr.txt').read_bytes()
native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
for v in (observation,once):assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes'] and v['invocation_id']==plan['invocation_id']
assert observation['meter_returncode']==observation['probe_returncode']==0
probe=int((external/'postterminal-probe-stdout.txt').read_bytes());assert probe==observation['postterminal_native_probe_ns']
assert native['caller_returncode']==native['wait4_status']==0 and native['all_reaped'] is True
assert native['caller_pid']==native['wait4_pid'] and native['error'] is None and native['interrupted'] is False and native['cancellation_forwarded'] is False
start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns'];g=body['joint_began_ns']
assert start<=g<terminal<=probe and body['joint_deadline_ns']==g+20000000000
assert terminal-start==native['caller_kernel_elapsed_ns'] and 0<probe-start<20000000000
peak=native['wait4_usage'][2];assert type(peak) is int and peak==native['caller_kernel_peak_bytes'] and 0<peak<=536870912
transport=read(HERE/'ROOT-marking-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));data=result['marking_data']
contract=read(check(plan['source_contract']))
assert len(plan['sources'])==9 and len(plan['inputs'])==8
assert plan['purpose']=='unit-row-certified-row0-marking-data-controls'
assert contract['sources']==plan['sources'] and contract['inputs']==plan['inputs']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['purpose']==plan['purpose']
binding=contract['original_model_binding']
assert result['language_binding']==body['language_binding']==body['original_model_binding']==binding
assert result['controls'] is result['search'] is result['found_validation'] is None
assert data['schema']=='ROOT-certified-row0-marking-data-payload-v1'
assert data['original_model_binding']==binding and data['original_model_sources']==contract['original_model_sources']
for ref in data['original_model_sources'].values():check(ref)
assert data['control_count']==16 and len(data['controls'])==16
assert data['all_controls_completed'] is data['constructed_marking_data'] is data['independent_marking_data_checked'] is True
assert [c['case']for c in data['controls']]==contract['controls'] and all(c['status']=='PASSED'for c in data['controls'])
assert data['prior_acceptance']=={k:v for k,v in plan['inputs'].items()if k.startswith('certification_')}
prior=read(check(plan['inputs']['certification_expanded']))['certification']
marking=data['marking'];definition=data['definition_check'];root=data['marked_root'];rootcheck=data['root_check']
assert marking['schema']=='unit-row-certified-row0-marking-v1'
assert marking['definition']['original_binding']==binding
assert definition['marking_checked'] is definition['projection_literals_rechecked'] is True
assert definition['marking']==marking and definition['marking_id']==marking['marking_id']
assert definition['marking_sha256']==hashlib.sha256(canonical(marking)).hexdigest()
assert root['base_state']==data['base_root'] and root['decorated_selected']==[] and root['added_m_values']==[[[4,0],0]]
assert rootcheck['marked_state_checked'] is True and rootcheck['selected_count']==0
assert rootcheck['marked_state_sha256']==hashlib.sha256(canonical(root)).hexdigest()
assert rootcheck['original_state_sha256']==hashlib.sha256(canonical(data['base_root'])).hexdigest()
fixtures=data['fixtures'];assert len(fixtures)==4
assert [f['arm']for f in fixtures]==['canonical','advised','AX0','UG23-read1']
summary=[]
for index,f in enumerate(fixtures):
    packet=f['decorated_tile'];base=packet['base_tile'];comp=f['point_comparison']
    assert comp['schema']=='measured-pure-point-mark-comparison-v1'
    assert comp['original_base_tile']==base and comp['full_decorated_tile']==packet
    assert comp['base_root_state']==data['base_root'] and comp['marked_root_state']==root
    assert comp['original_base_legal'] is True and comp['original_base_legality_reason'] is None
    assert packet['local_t_values']==base['local_t_values'] and packet['global_t_values']==base['global_t_values']
    assert packet['local_m_values']==base['local_m_values']+packet['added_local_m_values']
    assert packet['global_m_values']==base['global_m_values']+packet['added_global_m_values']
    assert base['placement_key']['type_preimage']['input_epoch']==binding['language_epoch'] and packet['marking_id']==marking['marking_id']
    if index<2:
        sample=prior['samples'][index]
        assert f['base_state']==sample['state'] and base['placement_key']==sample['selection']['selected_key']
        assert comp['compatible'] is False
        assert comp['conflict_points']==[{'point':[4,0],'state_value':0,'tile_value':1}]
        assert comp['shared_added_channel_points']==[{'point':[4,0],'state_value':0,'tile_value':1}]
        assert f['builder_rejection']=='certified point marking: channel4 point-mark conflict'
        assert f['independent_state_rejection']=='channel4 verifier: channel4 point agreement'
        assert f['conflicting_state_attempt']['decorated_selected']==[packet]
    else:
        assert comp['compatible'] is True and comp['conflict_points']==[]
        state=f['state'];receipt=f['independent_state_receipt']
        assert state['base_state']==f['base_state'] and state['decorated_selected']==[packet]
        assert receipt['marked_state_checked'] is receipt['projection_literals_rechecked'] is True
        assert receipt['selected_count']==1 and receipt['original_binding']==binding
        assert receipt['marked_state_sha256']==hashlib.sha256(canonical(state)).hexdigest()
        assert receipt['original_state_sha256']==hashlib.sha256(canonical(f['base_state'])).hexdigest()
    summary.append(dict(arm=f['arm'],original_base_legal=True,marked_point_compatible=comp['compatible'],
        added_local_m_values=packet['added_local_m_values'],added_global_m_values=packet['added_global_m_values'],
        conflict_points=comp['conflict_points']))
assert fixtures[2]['decorated_tile']['added_local_m_values']==[]
assert fixtures[3]['decorated_tile']['added_global_m_values']==[[[4,1],1]]
assert fixtures[3]['decorated_tile']['base_tile']['placement_key']['type_preimage']['ordered_offsets']==[-22]
for k in ('engine_activated','failure_marking_activated','target_search_performed','logical_proof_accepted',
          'exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
          'RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):assert data[k]is False
for k in ('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert result[k]is False
for k in ('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
          'failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):assert body[k]is False
disposition=dict(schema='ROOT-certified-row0-marking-disposition-v1',previous_goal_turn='progress',current_goal_turn='progress',
    plan=pp,outputs=outputs,lossless_transport_concordance=pin(HERE/'ROOT-marking-transport-concordance-v1.json'),
    complete_wire_verified=True,native_resources_qualified=True,native_launch_to_postprobe_ns=probe-start,
    native_worker_lifetime_ns=terminal-start,aggregate_B_bytes=peak,terminal_T_bytes=peak,complete_Date_seconds=date,
    resource_rule='single-owned-process-native-terminal-v1; B=T',actual_closed=True,all_reaped=True,passed_cases=16,skipped_cases=0,
    constructed_marking_data_accepted=True,independent_marking_data_check_accepted=True,point_comparison_fixtures=summary,
    marking_id=marking['marking_id'],marking_sha256=hashlib.sha256(canonical(marking)).hexdigest(),original_model_binding=binding,
    reconciliation_scope='Whole saved literal bytes/response/native/identity/receipt joins only; no scientific model, point matcher or checker replay.',
    verifier_scope='Separately authored verifier reconstructs original17 model and six-rule row0 certificates plus all added points; not a second mathematical kernel.',
    engine_activated=False,target_search_performed=False,logical_proof_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
    complete_GCTS_model_accepted=False,broad_goal_complete=False,
    remaining_gaps=['No current marked graph/degree/fallback/dependency/rollback qualification or target search.',
      'Only two externally certified literal formulas and first-row boundary; no arbitrary-row generalization.',
      'Current unit-row specialization lacks full reference conformance and universal finite Wang palette.',
      'Turtle/Penrose/PA/Hilbert/RL/infinite-plane/substitution goals remain open.'])
p=HERE/'ROOT-marking-disposition-v1.json'
with p.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(dict(disposition=pin(p),passed_cases=16,fixtures=4,native_ns=probe-start,aggregate_B_bytes=peak,scientific_replay=False)))
