"""Saved local calibration concordance only; no scientific evaluation or replay.
Four distinct original20 windows, no combined20/engine/target qualification.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(ref):
    p=Path(ref['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==ref;return p

EXPECTED_CONTRACT={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-calibration-cold-source-20261016/Source-contract-v1.json', 'sha256': 'd5a0467432caaf18cba837b1bd72c83eeefd80c2763b64641786af34b26fb773', 'bytes': 27670}
MODE_PURPOSE={'negative-protocol': 'unit-row-marked-aware-calibration-negative-protocol', 'singleton': 'unit-row-marked-aware-calibration-singleton', 'two': 'unit-row-marked-aware-calibration-two', 'zero': 'unit-row-marked-aware-calibration-zero'}
EXPECTED_CASES={'negative-protocol': ['MA-04-wrong-original-binding-provenance-rejected', 'MA-05-omitted-ordered-MP-fibre-rejected', 'MA-06-inconsistent-completion-flag-rejected'], 'singleton': ['MA-02-complete-marked-SINGLETON'], 'two': ['MA-03-two-marked-witnesses-lower-bound-only'], 'zero': ['MA-01-complete-marked-ZERO']}
LIMITS={'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

def native_refs(external):
    return {n:pin(external/n)for n in('ONCE.json','native-terminal.json','observation.json',
        'meter-stdout.txt','meter-stderr.txt','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt')}

def auth_plan(plan,pp,mode):
    assert plan['schema']=='ROOT-marked-aware-calibration-plan-v1' and plan['purpose']==MODE_PURPOSE[mode]
    assert plan['source_contract']==EXPECTED_CONTRACT and plan['limits']==LIMITS
    assert plan['resource_rule']=='single-owned-process-native-terminal-v1'
    contract=read(check(plan['source_contract']))
    assert contract['sources']==plan['sources'] and contract['inputs']==plan['inputs']
    assert len(plan['sources'])==13 and len(plan['inputs'])==8
    assert contract['source']==plan['sources']['intake'] and contract['source']['sha256']=='5780335b8f384dabe79062787771cc48a24d19464e8d51c10cc1e4579e1b1817'
    for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['runtime'],*contract['original_model_sources'].values(),*contract['original_model_inputs'].values()]:check(ref)
    assert len(contract['original_model_sources'])==17
    assert set(plan['reviews'])=={'ROOT','peer'}
    for role,ref in plan['reviews'].items():
        v=read(check(ref))
        assert v['scope']=='unit-row-marked-aware-calibration-cold-Source' and v['author_identity']=='/root/arithmetic_induction'
        assert v['source']==plan['sources']['intake'] and v['sources']==plan['sources'] and v['source_contract']==plan['source_contract']
        assert v['source_only']is v['source_review_passed']is True and type(v['scientific_calls'])is int and v['scientific_calls']==0 and v['scientific_acceptance']is False
        assert(v['reviewer_identity']=='/root'if role=='ROOT'else v['reviewer_identity']not in('/root','/root/arithmetic_induction'))
    grant=read(check(plan['ROOT_authorization']))
    assert grant['schema']=='ROOT-marked-aware-calibration-authorization-v1' and grant['author_identity']=='/root' and grant['actual_execution_authorized']is True
    assert type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
    for k in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):assert grant[k]==plan[k]
    return contract

def failure_only(mode):
    # Nonzero/no returned record is administrative closure, never a case result.
    plan_path=HERE/('ROOT-MA-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
    contract=auth_plan(plan,pp,mode);owned=HERE/('MA-'+mode+'-owned-v1');external=HERE/('MA-'+mode+'-external-v1')
    assert Path(plan['output_directory'])==owned
    bracket_path=HERE/('ROOT-MA-'+mode+'-tool-bracket-v1.json');bracket=read(bracket_path)
    assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
    assert type(bracket['tool_exit_code'])is int and 0<bracket['tool_exit_code']<256 and bracket['tool_session_id']is None
    date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
    assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
    native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
    for v in(observation,once):
        assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes'] and v['invocation_id']==plan['invocation_id'] and v['purpose']==plan['purpose']
    code=native['caller_returncode']
    assert type(code)is int and 0<code<256 and code==bracket['tool_exit_code']==observation['meter_returncode']
    assert observation['probe_returncode']==0 and native['wait4_status']==code*256 and native['all_reaped']is True
    assert native['caller_pid']==native['wait4_pid'] and native['error']is None and native['interrupted']is False and native['cancellation_forwarded']is False
    raw_probe=(external/'postterminal-probe-stdout.txt').read_bytes();probe=int(raw_probe)
    assert str(probe).encode()+b'\n'==raw_probe and probe==observation['postterminal_native_probe_ns']
    start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns']
    assert start<terminal<=probe and terminal-start==native['caller_kernel_elapsed_ns'] and probe-start<55000000000
    peak=native['wait4_usage'][2];assert type(peak)is int and peak==native['caller_kernel_peak_bytes'] and 0<peak<=536870912
    assert(external/'meter-stdout.txt').read_bytes()==b''
    stderr=(external/'meter-stderr.txt').read_bytes()
    assert(external/'postterminal-probe-stderr.txt').read_bytes()==b''
    deadline=(stderr==b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete marking data controls original20/500 reserve unfinished\n'
              and terminal-start>=20000000000)
    raw_outputs=[]
    if owned.exists():
        assert owned.is_dir() and all(p.is_file() and p.name in('engine-result.json','response.jsonl')for p in owned.iterdir())
        raw_outputs=[pin(p)for p in sorted(owned.iterdir())]
    # Do not decode even an extant partial owned file in this failure branch.
    prior=read(check(plan['inputs']['stageB_disposition']))
    assert prior['actual_closed']is prior['native_resources_qualified']is True
    for k in('ROOT_resource_accepted','ROOT_primary_accepted'):assert native[k]is observation[k]is False
    disposition=dict(schema='ROOT-marked-aware-calibration-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
        plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
        outputs=raw_outputs,native_evidence=native_refs(external),tool_bracket=pin(bracket_path),
        actual_closed=True,all_reaped=True,native_terminal_closed=True,native_resources_qualified=False,complete_wire_verified=False,
        original20_positive_native_gate_failed=True,native_deadline_confirmed=deadline,
        native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,
        aggregate_B_bytes=peak,terminal_T_bytes=peak,complete_Date_seconds=date,
        reported_case_count=None,passed_cases=None,skipped_cases=None,qualified_case_count=0,unqualified_case_count=len(EXPECTED_CASES[mode]),
        case_names=EXPECTED_CASES[mode],endpoint_controls_literal_concordance_accepted=False,
        complete_returned_record=False,owned_output_directory_exists=owned.exists(),whole_calibration_qualification_accepted=False,
        marking_id=prior['marking_id'],original_model_binding=contract['original_model_binding'],
        failure_kind='NATIVE20_DEADLINE_NO_RETURNED_CASE_RECORD'if deadline else'NONZERO_NO_RETURNED_CASE_RECORD',
        raw_stderr_pin=pin(external/'meter-stderr.txt'),
        diagnostic_limit='Opaque raw stderr/native administrative closure only; no inferred case progress, counts, degree, membership or semantic success.',
        reconciliation_scope='No output decode or scientific replay; nonzero administrative failure always0qualified/countsNone.',
        closure_helper=pin(Path(__file__).resolve()),resource_rule='single-owned-process-native-terminal-v1; B=T',
        target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
        complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
        scientific_replay=False,ROOT_resource_accepted=False)
    out=HERE/('ROOT-MA-'+mode+'-disposition-v1.json')
    with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':0,'reported_case_count':None,'positive_native_gate':False,'scientific_replay':False}))


def aggregate():
    refs={};records={};ids=[];plans=[];directories=[];qualified=[];unqualified=[]
    for mode,purpose in MODE_PURPOSE.items():
        p=HERE/('ROOT-MA-'+mode+'-disposition-v1.json');v=read(p);refs[mode]=pin(p);records[mode]=v
        assert v['schema']=='ROOT-marked-aware-calibration-endpoint-disposition-v1' and v['mode']==mode and v['purpose']==purpose
        assert v['actual_closed']is v['all_reaped']is v['native_terminal_closed']is True
        assert v['whole_calibration_qualification_accepted']is False and v['case_names']==EXPECTED_CASES[mode]
        assert v['closure_helper']==pin(Path(__file__).resolve())
        plan=read(check(v['plan']));auth_plan(plan,v['plan'],mode)
        assert v['sources']==plan['sources'] and v['inputs']==plan['inputs'] and v['source_contract']==plan['source_contract']
        assert v['invocation_id']==plan['invocation_id'];ids.append(v['invocation_id']);plans.append(v['plan']['sha256']);directories.append(plan['output_directory'])
        for ref in [*v['native_evidence'].values(),v['tool_bracket'],*v['outputs']]:check(ref)
        assert v['original_model_binding']==read(check(v['source_contract']))['original_model_binding']
        if v['endpoint_controls_literal_concordance_accepted']:
            assert v['native_resources_qualified']is v['complete_wire_verified']is v['complete_returned_record']is True
            assert v['qualified_case_count']==len(EXPECTED_CASES[mode]) and v['unqualified_case_count']==0
            assert v['reported_case_count']==v['passed_cases']==len(EXPECTED_CASES[mode]) and v['skipped_cases']==0
            check(v['lossless_transport_concordance']);check(v['raw_expanded']);qualified.extend(EXPECTED_CASES[mode])
        else:
            assert v['native_resources_qualified']is v['complete_wire_verified']is v['complete_returned_record']is False
            assert v['reported_case_count']is v['passed_cases']is v['skipped_cases']is None
            assert v['qualified_case_count']==0 and v['unqualified_case_count']==len(EXPECTED_CASES[mode]);unqualified.extend(EXPECTED_CASES[mode])
        for k in('target_search_performed','failure_marking_activated','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','scientific_replay','ROOT_resource_accepted'):assert v[k]is False
    assert len(set(ids))==len(set(plans))==len(set(directories))==4
    assert len({v['marking_id']for v in records.values()})==1
    complete=len(qualified)==6 and not unqualified
    result=dict(schema='ROOT-marked-aware-calibration-disposition-v1',endpoint_dispositions=refs,
        endpoint_summaries={m:{k:v[k]for k in('purpose','qualified_case_count','unqualified_case_count','native_resources_qualified','complete_wire_verified','native_launch_to_postprobe_ns','aggregate_B_bytes')}for m,v in records.items()},
        all_four_endpoints_closed=True,separate_endpoint_count=4,required_case_count=6,qualified_case_count=len(qualified),
        unqualified_case_count=len(unqualified),qualified_cases=qualified,unqualified_cases=unqualified,
        local_marked_aware_calibration_qualified=complete,combined20_suite_claimed=False,
        same_process_all_six_qualified=False,engine_integration_qualified=False,
        marking_id=next(iter(records.values()))['marking_id'],closure_helper=pin(Path(__file__).resolve()),
        scientific_replay=False,target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,
        exact_point_board_accepted=False,complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,
        RL_accepted=False,GCTS_advantage_claimed=False,ROOT_resource_accepted=False)
    out=HERE/'ROOT-MA-calibration-disposition-v1.json'
    with out.open('x')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':len(qualified),'local_calibration_qualified':complete,'scientific_replay':False}))


assert len(sys.argv)==2 and sys.argv[1]in(*MODE_PURPOSE,'aggregate')
if sys.argv[1]=='aggregate':aggregate();sys.exit(0)
mode=sys.argv[1]
if read(HERE/('MA-'+mode+'-external-v1')/'native-terminal.json')['caller_returncode']!=0:
    failure_only(mode);sys.exit(0)

plan_path=HERE/('ROOT-MA-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
owned=HERE/('MA-'+mode+'-owned-v1');external=HERE/('MA-'+mode+'-external-v1')
bracket=read(HERE/('ROOT-MA-'+mode+'-tool-bracket-v1.json'))
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
assert body['schema']=='ROOT-unit-row-marked-aware-calibration-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
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
transport=read(HERE/('ROOT-MA-'+mode+'-transport-concordance-v1.json'))
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
assert transport['encoded_cap_bytes']==4194304 and transport['expanded_cap_bytes']==16777216
assert transport['strict_canonical_JSON_LF'] is transport['strict_base64_reencoded'] is transport['single_complete_zlib_stream'] is True
assert transport['trailing_or_unconsumed_bytes'] is False and transport['scientific_replay'] is False
expanded_path=check(transport['expanded_file']);result=read(expanded_path)
assert expanded_path.read_bytes()==canonical(result)+b'\n'
data=result['marked_aware_calibration'];contract=read(check(plan['source_contract']))
assert plan['source_contract']==EXPECTED_CONTRACT and contract['schema']=='unit-row-marked-aware-calibration-cold-Source-contract-v1'
assert len(plan['sources'])==13 and len(plan['inputs'])==8 and plan['schema']=='ROOT-marked-aware-calibration-plan-v1'
assert plan['purpose']==MODE_PURPOSE[mode] and plan['limits']==LIMITS
assert result['sources']==contract['sources']==plan['sources'] and result['inputs']==contract['inputs']==plan['inputs']
assert result['purpose']==plan['purpose'] and plan['sources']['intake']==contract['source']
assert contract['source']['sha256']=='5780335b8f384dabe79062787771cc48a24d19464e8d51c10cc1e4579e1b1817'
assert body['version']=='unit-row-marked-aware-local-degree-calibration-cold-v1'
assert canonical(body)+b'\n'==lines[0] and canonical(completion)+b'\n'==lines[1]
binding=contract['original_model_binding']
assert result['language_binding']==body['language_binding']==body['original_model_binding']==binding
assert result['controls'] is result['search'] is result['found_validation'] is None
assert data['schema']=='ROOT-unit-row-marked-aware-calibration-payload-v1'
assert data['stage']=='LOCAL_NEW_MARKED_AWARE_NONIMP_DEGREE_ONLY'
assert data['endpoint_purpose']==plan['purpose'] and data['separate_endpoint_count']==4
assert data['whole_calibration_qualification_accepted']is data['same_process_all_six_qualified']is False
assert data['original_model_sources']==contract['original_model_sources'] and len(data['original_model_sources'])==17
assert data['original_model_binding']==binding
for ref in data['original_model_sources'].values():check(ref)
for ref in contract['original_model_inputs'].values():check(ref)
assert contract['original_model_inputs']=={k:plan['inputs'][k]for k in('declaration','profile')}
assert set(plan['reviews'])=={'ROOT','peer'}
for role,ref in plan['reviews'].items():
    review=read(check(ref))
    assert review['scope']=='unit-row-marked-aware-calibration-cold-Source' and review['author_identity']=='/root/arithmetic_induction'
    assert review['source']==plan['sources']['intake'] and review['sources']==plan['sources'] and review['source_contract']==plan['source_contract']
    assert review['source_only'] is review['source_review_passed'] is True and type(review['scientific_calls'])is int and review['scientific_calls']==0
    assert review['scientific_acceptance'] is False
    assert (review['reviewer_identity']=='/root' if role=='ROOT'else review['reviewer_identity']not in('/root','/root/arithmetic_induction'))
grant=read(check(plan['ROOT_authorization']))
assert grant['schema']=='ROOT-marked-aware-calibration-authorization-v1' and grant['author_identity']=='/root'
assert grant['actual_execution_authorized'] is True and type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
for k in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):assert grant[k]==plan[k]
assert Path(plan['output_directory'])==owned and plan['resource_rule']=='single-owned-process-native-terminal-v1'
expected=contract['API']['purpose_modes_and_ordered_cases'][plan['purpose']]
assert expected==EXPECTED_CASES[mode] and data['expected_cases']==expected
assert data['control_count']==len(data['controls'])==len(expected) and data['all_controls_completed'] is True
assert [c['case']for c in data['controls']]==expected and all(c['status']=='PASSED'for c in data['controls'])
assert data['prior_acceptance']=={k:v for k,v in plan['inputs'].items()if k.startswith('stageB_')}
prior=read(check(plan['inputs']['stageB_expanded']))['channel4_stageB']
prior_admission=read(check(plan['inputs']['stageB_disposition']))
assert prior_admission['actual_closed'] is prior_admission['all_reaped'] is prior_admission['native_resources_qualified'] is True
assert prior_admission['support_retention_archive_reference_controls_accepted'] is True
assert prior_admission['passed_cases']==9 and prior_admission['skipped_cases']==0
assert prior_admission['cached_degree_receipt_transfer_exercised'] is prior_admission['global_decision_or_scheduler_qualified'] is prior_admission['unknown_child_search_rollback_qualified'] is False
assert data['marking']==prior['marking'] and data['marking']['marking_id']==prior_admission['marking_id']
assert data['definition_check']['marking_checked'] is data['definition_check']['projection_literals_rechecked'] is True
assert data['definition_check']['marking']==data['marking']
assert data['definition_check']['marking_sha256']==hashlib.sha256(canonical(data['marking'])).hexdigest()
mid=data['marking']['marking_id']
decl=read(check(contract['original_model_inputs']['declaration']))

assert result['schema']=='ROOT-unit-row-marked-aware-calibration-result-v1' and stdout['schema']=='ROOT-unit-row-marked-aware-calibration-final-observation-v1'
def equal(left,right):
    assert canonical(left)==canonical(right)  # Full literal types, not a matcher.

def sha(value):return hashlib.sha256(canonical(value)).hexdigest()

def points(entries):
    assert type(entries)is list
    out={}
    for p,v in entries:
        assert type(p)is list and len(p)==2 and all(type(x)is int for x in p)
        assert tuple(p)not in out;out[tuple(p)]=v
    return out

def state(value):
    assert value['schema']=='unit-row-channel4-private-state-v1' and value['marking_id']==mid
    assert value['input_epoch']==binding['language_epoch'] and type(value['height'])is int and value['height']==24
    equal(value['generation'],[[[0,r],0]for r in range(24)])
    totals=points(value['t']);marks=points(value['m'])
    assert set(totals)=={(0,r)for r in range(24)} and all(type(v)is int and v in(0,1)for v in totals.values())
    assert type(marks[(4,0)])is int and marks[(4,0)]==0
    equal(marks[(1,23)],['formula',canonical(decl['target']).decode()])
    for k in range(-23,0):equal(marks[(1,k)],['outside',binding['language_epoch']])
    assert value['excluded']==[]  # All these fixtures have no justified failure exclusions.
    assert len({canonical(k)for k in value['selected']})==len(value['selected'])
    for k in value['selected']:
        assert type(k['generation'])is int and k['generation']==1
        assert k['type_preimage']['marking_id']==mid and k['type_preimage']['base_type_preimage']['input_epoch']==binding['language_epoch']
        assert k['translation'][0]==0 and 0<=k['translation'][1]<24
    assert sum(totals.values())==len(value['selected'])
    return value

def query_record(record):
    s=state(record['state']);row=record['query_row'];p=record['proposal'];r=record['receipt']
    assert type(row)is int and 0<=row<24 and points(s['t'])[(0,row)]==0
    assert p['schema']=='unit-row-marked-aware-nonimp-fibre-proposal-v1' and p['version']=='unit-row-marked-aware-nonimp-fibre-proposer-v1'
    assert r['schema']=='unit-row-marked-aware-nonimp-fibre-check-v1' and r['version']=='unit-row-independent-marked-aware-nonimp-fibre-checker-v1'
    for v in(p,r):
        equal(v['state'],s);assert v['state_sha256']==sha(s) and v['row']==row
        assert v['input_epoch']==binding['language_epoch'] and v['language_binding']==binding and v['marking_id']==mid
        assert v['original_state_sha256']==sha(v['original_state'])
        for k in('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert v[k]is False
    equal(p['original_state'],r['original_state'])
    equal(r['checked_candidates'],p['candidates']);equal(r['candidate_keys'],[c['placement_key']for c in p['candidates']])
    assert r['proposal_sha256']==sha(p) and r['marking_sha256']==sha(data['marking'])
    check=r['independent_marked_state_check'];assert check['marked_state_checked']is check['projection_literals_rechecked']is True
    assert check['original_binding']==binding and check['original_state_sha256']==p['original_state_sha256'] and check['marking_id']==mid
    equal(p['output_formula'],r['output_formula'])
    equal(points(s['m'])[(1,row)],['formula',canonical(p['output_formula']).decode()])
    assert p['untrusted']is True and r['accepted_local_evidence']is True
    assert len(record['seeds'])==len(s['selected'])
    for seed,selected in zip(record['seeds'],s['selected']):
        equal(seed['placement_key']['type_preimage'],selected['type_preimage']['base_type_preimage'])
        equal(seed['placement_key']['translation'],selected['translation'])
    actual=[]
    for c in p['candidates']:
        key=c['placement_key'];pre=key['type_preimage'];base=pre['base_type_preimage']
        assert key['translation']==[0,row] and pre['marking_id']==mid and base['input_epoch']==binding['language_epoch']
        assert base['primitive_witness']['rule']=='mp'
        actual.append([row+d for d in base['ordered_offsets']])
        equal(c['base_tile']['placement_key']['type_preimage'],base)
        equal(c['base_tile']['placement_key']['translation'],key['translation'])
    equal(actual,record['actual_candidate_reads'])
    assert len({canonical(k)for k in r['candidate_keys']})==len(r['candidate_keys'])
    return p,r

def complete_zero(record):
    p,r=query_record(record);f=p['fibre_cover']
    assert record['query_row']==1 and record['size1_carrier']is None
    assert p['kind']=='COMPLETE_NONIMP_FIBRE_COVER' and p['complete_cover_proposed']is True
    assert r['status']=='ZERO' and type(r['degree_exact'])is int and r['degree_exact']==0
    assert r['complete_cover_checked']is r['nonimp_fibre_cover_checked']is True
    assert r['candidate_keys']==p['candidates']==[] and r['sole_candidate']is None
    equal(f,r['checked_fibre_cover']);assert f['completed']is True and len(f['UG_fibres'])==len(f['ordered_MP_fibres'])==1
    assert f['UG_fibres'][0]['examined']==f['UG_fibres'][0]['rejections']==1
    assert f['ordered_MP_fibres'][0]['rows']==[0,0] and f['ordered_MP_fibres'][0]['case']=='FINITE_AST_OCCURS_CHECK_EMPTY'
    assert all(x['completed']is True for x in f['UG_fibres']+f['ordered_MP_fibres'])
    return p,r

if mode=='zero':
    assert set(data['families'])=={'ZERO'};complete_zero(data['families']['ZERO'])
elif mode=='singleton':
    assert set(data['families'])=={'SINGLETON'};record=data['families']['SINGLETON'];p,r=query_record(record);f=p['fibre_cover']
    assert record['query_row']==3 and record['size1_carrier']==[['bot']] and record['actual_candidate_reads']==[[2,0]]
    assert p['kind']=='COMPLETE_NONIMP_FIBRE_COVER' and p['complete_cover_proposed']is True
    assert r['status']=='SINGLETON' and type(r['degree_exact'])is int and r['degree_exact']==1 and len(p['candidates'])==1
    assert r['complete_cover_checked']is r['nonimp_fibre_cover_checked']is True
    equal(r['sole_candidate'],p['candidates'][0]);equal(f,r['checked_fibre_cover'])
    assert f['completed']is True and f['output_nodes']==42 and f['MP_antecedent_max_nodes']==1
    assert len(f['UG_fibres'])==3 and len(f['ordered_MP_fibres'])==9
    assert all(x['completed']is True for x in f['UG_fibres']+f['ordered_MP_fibres'])
elif mode=='two':
    assert set(data['families'])=={'TWO'};record=data['families']['TWO'];p,r=query_record(record)
    assert record['query_row']==3 and record['size1_carrier']==[['bot']] and record['actual_candidate_reads']==[[1,0],[1,2]]
    assert p['kind']=='TWO_LEGAL_WITNESSES' and p['complete_cover_proposed']is p['fibre_cover']['completed']is False
    assert r['status']=='TWO_OR_MORE' and r['complete_cover_checked']is r['nonimp_fibre_cover_checked']is False
    assert len(p['candidates'])==2 and r['degree_exact']is r['sole_candidate']is r['checked_fibre_cover']is None
else:
    assert set(data['families'])=={'NEGATIVE_PROTOCOL'};record=data['families']['NEGATIVE_PROTOCOL']
    p,r=complete_zero(record['valid_zero_fixture']);failures=record['failures'];assert len(failures)==3
    reasons=['whole original/marked current context','complete independent fibres/counts/hashes','literal completion flag']
    for i,failure in enumerate(failures):
        bad=json.loads(canonical(p))
        if i==0:bad['language_binding']['language_epoch']='0'*64
        elif i==1:
            omitted=bad['fibre_cover']['ordered_MP_fibres'].pop();equal(omitted,failure['omitted_original_fibre'])
        else:bad['complete_cover_proposed']=False
        equal(bad,failure['failing_proposal'])
        assert failure['expected_reason']==failure['actual_reason']=='marked-aware fibre evidence: '+reasons[i]
        assert failure['exception_type']=='ValueError' and failure['rejected']is True and failure['returned_receipt']is None

for k in('target_search_performed','engine_or_fallback_queried','old_degree_proposal_or_receipt_replayed','new_receipt_engine_compatibility_claimed','failure_marking_activated','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):assert data[k]is False
for k in('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert result[k]is False
for k in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):assert body[k]is False
for k in('logical_proof_accepted','ROOT_resource_accepted'):assert stdout[k]is False
for k in('ROOT_resource_accepted','ROOT_primary_accepted'):assert native[k]is observation[k]is False

disposition=dict(schema='ROOT-marked-aware-calibration-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
 plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
 outputs=outputs,native_evidence=native_refs(external),tool_bracket=pin(HERE/('ROOT-MA-'+mode+'-tool-bracket-v1.json')),
 lossless_transport_concordance=pin(HERE/('ROOT-MA-'+mode+'-transport-concordance-v1.json')),raw_expanded=pin(expanded_path),
 complete_wire_verified=True,native_terminal_closed=True,native_resources_qualified=True,complete_returned_record=True,
 native_deadline_confirmed=False,original20_positive_native_gate_failed=False,owned_output_directory_exists=True,
 native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,aggregate_B_bytes=peak,terminal_T_bytes=peak,
 complete_Date_seconds=date,resource_rule='single-owned-process-native-terminal-v1; B=T',actual_closed=True,all_reaped=True,
 reported_case_count=len(expected),qualified_case_count=len(expected),unqualified_case_count=0,passed_cases=len(expected),skipped_cases=0,
 case_names=expected,endpoint_controls_literal_concordance_accepted=True,whole_calibration_qualification_accepted=False,
 marking_id=mid,marking_sha256=sha(data['marking']),original_model_binding=binding,
 closure_helper=pin(Path(__file__).resolve()),reconciliation_scope='Saved native/wire/full literal state/proposal/new receipt/census/negative-data concordance only; no scientific function, membership, fibre enumeration or replay.',
 target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
 complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
 scientific_replay=False,ROOT_resource_accepted=False,
 remaining_gaps=['One endpoint only; all four distinct20 endpoints/six essential cases required for local calibration.','New local receipt not an engine11/c354 protocol; no graph/EOF/transfer/activation/search benefit/target proof qualification.'])
out=HERE/('ROOT-MA-'+mode+'-disposition-v1.json')
with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(out),'qualified_cases':len(expected),'native_ns':probe-start,'scientific_replay':False}))
