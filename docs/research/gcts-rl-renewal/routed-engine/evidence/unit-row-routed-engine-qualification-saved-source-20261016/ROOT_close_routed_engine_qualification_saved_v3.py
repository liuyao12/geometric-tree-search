"""Saved routed engine control concordance only; no scientific evaluation or replay.
Six distinct original20 windows; no combined20/oldStageC/target promotion.
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

EXPECTED_CONTRACT={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-routed-engine-qualification-cold-source-20261016/Source-contract-v1.json', 'sha256': 'dbe07d4eff585af988f052d7ed08ff164c3dc65ed8cdda2bac16be981db54941', 'bytes': 38188}
MODE_PURPOSE={'router-protocol': 'unit-row-marked-aware-router-protocol-controls', 'global-forced-dead': 'unit-row-marked-aware-global-forced-dead-controls', 'singleton-transfer': 'unit-row-marked-aware-singleton-transfer-controls', 'two-transfer': 'unit-row-marked-aware-two-transfer-controls', 'short-EOF': 'unit-row-marked-aware-short-EOF-controls', 'child-UNKNOWN': 'unit-row-marked-aware-child-UNKNOWN-controls'}
EXPECTED_CASES={'router-protocol': ['MR-01-new-and-legacy-route-consumption', 'MR-02-wrong-route-and-context-rejected'], 'global-forced-dead': ['MR-03-global-forced-requery-dead-exhaustion', 'MR-04-owned-full-root-restoration'], 'singleton-transfer': ['MR-05-native-singleton-full-origin-transfer', 'MR-06-current-sole-consumption-and-owned-rollback'], 'two-transfer': ['MR-07-native-TWO-full-origin-transfer', 'MR-08-refreshed-witnesses-global-branch-and-owned-rollback'], 'short-EOF': ['MR-09-real-short-stream-and-fresh-complete-keySET', 'MR-10-legacy-implication-EOF-remains-unaccepted'], 'child-UNKNOWN': ['MR-11-actual-child-native-first-declared-UNKNOWN', 'MR-12-UNKNOWN-no-exclusion-full-owned-rollback']}
LIMITS={'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

def native_refs(external):
    return {n:pin(external/n)for n in('ONCE.json','native-terminal.json','observation.json',
        'meter-stdout.txt','meter-stderr.txt','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt')}

def auth_plan(plan,pp,mode):
    assert plan['schema']=='ROOT-routed-engine-qualification-plan-v1' and plan['purpose']==MODE_PURPOSE[mode]
    assert plan['source_contract']==EXPECTED_CONTRACT and plan['limits']==LIMITS
    assert plan['resource_rule']=='single-owned-process-native-terminal-v1'
    contract=read(check(plan['source_contract']))
    assert contract['sources']==plan['sources'] and contract['inputs']==plan['inputs']
    assert len(plan['sources'])==14 and len(plan['inputs'])==8
    assert contract['source']==plan['sources']['intake'] and contract['source']['sha256']=='38f8f86f5af3474a0eed6fac7ff89c5d9c2b327d1413a2164be24ca8d7ea6e60'
    for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['runtime'],*contract['original_model_sources'].values(),*contract['original_model_inputs'].values()]:check(ref)
    assert len(contract['original_model_sources'])==17
    assert set(plan['reviews'])=={'ROOT','peer'}
    for role,ref in plan['reviews'].items():
        v=read(check(ref))
        assert v['scope']=='unit-row-routed-engine-qualification-cold-Source' and v['author_identity']=='/root/hilbert_advice_controls'
        assert v['source']==plan['sources']['intake'] and v['sources']==plan['sources'] and v['source_contract']==plan['source_contract']
        assert v['source_only']is v['source_review_passed']is True and type(v['scientific_calls'])is int and v['scientific_calls']==0 and v['scientific_acceptance']is False
        assert(v['reviewer_identity']=='/root'if role=='ROOT'else v['reviewer_identity']not in('/root','/root/hilbert_advice_controls'))
    grant=read(check(plan['ROOT_authorization']))
    assert grant['schema']=='ROOT-routed-engine-qualification-authorization-v1' and grant['author_identity']=='/root' and grant['actual_execution_authorized']is True
    assert type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
    for k in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):assert grant[k]==plan[k]
    return contract

def failure_only(mode):
    # Nonzero/no returned record is administrative closure, never a case result.
    plan_path=HERE/('ROOT-MR-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
    contract=auth_plan(plan,pp,mode);owned=HERE/('MR-'+mode+'-owned-v1');external=HERE/('MR-'+mode+'-external-v1')
    assert Path(plan['output_directory'])==owned
    bracket_path=HERE/('ROOT-MR-'+mode+'-tool-bracket-v1.json');bracket=read(bracket_path)
    assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
    assert type(bracket['tool_exit_code'])is int and 0<bracket['tool_exit_code']<256 and ((bracket['tool_session_id'] is None and bracket['observed_session_id'] is None)
        or (type(bracket['tool_session_id']) is int and bracket['tool_session_id'] > 0
            and type(bracket['observed_session_id']) is int
            and bracket['observed_session_id'] == bracket['tool_session_id']))
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
    disposition=dict(schema='ROOT-routed-engine-qualification-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
        plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
        outputs=raw_outputs,native_evidence=native_refs(external),tool_bracket=pin(bracket_path),
        actual_closed=True,all_reaped=True,native_terminal_closed=True,native_resources_qualified=False,complete_wire_verified=False,
        original20_positive_native_gate_failed=True,native_deadline_confirmed=deadline,
        native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,
        aggregate_B_bytes=peak,terminal_T_bytes=peak,complete_Date_seconds=date,
        reported_case_count=None,passed_cases=None,skipped_cases=None,qualified_case_count=0,unqualified_case_count=len(EXPECTED_CASES[mode]),
        case_names=EXPECTED_CASES[mode],endpoint_controls_literal_concordance_accepted=False,
        complete_returned_record=False,owned_output_directory_exists=owned.exists(),whole_engine_qualification_accepted=False,
        prior_StageC_suite_qualified=False,
        marking_id=prior['marking_id'],original_model_binding=contract['original_model_binding'],
        failure_kind='NATIVE20_DEADLINE_NO_RETURNED_CASE_RECORD'if deadline else'NONZERO_NO_RETURNED_CASE_RECORD',
        raw_stderr_pin=pin(external/'meter-stderr.txt'),
        diagnostic_limit='Opaque raw stderr/native administrative closure only; no inferred case progress, counts, degree, membership or semantic success.',
        reconciliation_scope='No output decode or scientific replay; nonzero administrative failure always0qualified/countsNone.',
        closure_helper=pin(Path(__file__).resolve()),resource_rule='single-owned-process-native-terminal-v1; B=T',
        target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
        complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
        scientific_replay=False,ROOT_resource_accepted=False)
    out=HERE/('ROOT-MR-'+mode+'-disposition-v1.json')
    with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':0,'reported_case_count':None,'positive_native_gate':False,'scientific_replay':False}))


def aggregate():
    refs={};records={};ids=[];plans=[];directories=[];qualified=[];unqualified=[]
    for mode,purpose in MODE_PURPOSE.items():
        p=HERE/('ROOT-MR-'+mode+'-disposition-v1.json');v=read(p);refs[mode]=pin(p);records[mode]=v
        assert v['schema']=='ROOT-routed-engine-qualification-endpoint-disposition-v1' and v['mode']==mode and v['purpose']==purpose
        assert v['actual_closed']is v['all_reaped']is v['native_terminal_closed']is True
        assert v['whole_engine_qualification_accepted']is False and v['case_names']==EXPECTED_CASES[mode]
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
    assert len(set(ids))==len(set(plans))==len(set(directories))==6
    assert len({v['marking_id']for v in records.values()})==1
    complete=len(qualified)==12 and not unqualified
    result=dict(schema='ROOT-routed-engine-qualification-disposition-v1',endpoint_dispositions=refs,
        endpoint_summaries={m:{k:v[k]for k in('purpose','qualified_case_count','unqualified_case_count','native_resources_qualified','complete_wire_verified','native_launch_to_postprobe_ns','aggregate_B_bytes')}for m,v in records.items()},
        all_six_endpoints_closed=True,separate_endpoint_count=6,required_case_count=12,qualified_case_count=len(qualified),
        unqualified_case_count=len(unqualified),qualified_cases=qualified,unqualified_cases=unqualified,
        routed_engine_qualification_accepted=complete,combined20_suite_claimed=False,
        same_process_all_twelve_qualified=False,bounded_routed_engine_controls_qualified=complete,prior_StageC_suite_qualified=False,
        marking_id=next(iter(records.values()))['marking_id'],closure_helper=pin(Path(__file__).resolve()),
        scientific_replay=False,target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,
        exact_point_board_accepted=False,complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,
        RL_accepted=False,GCTS_advantage_claimed=False,ROOT_resource_accepted=False)
    out=HERE/'ROOT-MR-qualification-disposition-v1.json'
    with out.open('x')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':len(qualified),'bounded_routed_engine_controls_qualified':complete,'scientific_replay':False}))


assert len(sys.argv)==2 and sys.argv[1]in(*MODE_PURPOSE,'aggregate')
if sys.argv[1]=='aggregate':aggregate();sys.exit(0)
mode=sys.argv[1]
if read(HERE/('MR-'+mode+'-external-v1')/'native-terminal.json')['caller_returncode']!=0:
    failure_only(mode);sys.exit(0)

plan_path=HERE/('ROOT-MR-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
owned=HERE/('MR-'+mode+'-owned-v1');external=HERE/('MR-'+mode+'-external-v1')
bracket=read(HERE/('ROOT-MR-'+mode+'-tool-bracket-v1.json'))
assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
assert bracket['tool_exit_code']==0 and ((bracket['tool_session_id'] is None and bracket['observed_session_id'] is None)
    or (type(bracket['tool_session_id']) is int and bracket['tool_session_id'] > 0
        and type(bracket['observed_session_id']) is int
        and bracket['observed_session_id'] == bracket['tool_session_id']))
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
assert sorted(p.name for p in owned.iterdir())==['engine-result.json','response.jsonl']
outputs=[pin(owned/n) for n in ('engine-result.json','response.jsonl')]
lines=(owned/'response.jsonl').read_bytes().splitlines(keepends=True)
assert len(lines)==2 and all(x.endswith(b'\n') for x in lines)
body,completion=map(json.loads,lines)
assert completion['body_sha256']==hashlib.sha256(lines[0]).hexdigest() and completion['body_bytes']==len(lines[0])
assert completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True
assert body['schema']=='ROOT-unit-row-routed-engine-qualification-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
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
transport=read(HERE/('ROOT-MR-'+mode+'-transport-concordance-v1.json'))
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
assert transport['encoded_cap_bytes']==4194304 and transport['expanded_cap_bytes']==16777216
assert transport['strict_canonical_JSON_LF'] is transport['strict_base64_reencoded'] is transport['single_complete_zlib_stream'] is True
assert transport['trailing_or_unconsumed_bytes'] is False and transport['scientific_replay'] is False
expanded_path=check(transport['expanded_file']);result=read(expanded_path)
assert expanded_path.read_bytes()==canonical(result)+b'\n'
data=result['routed_engine_qualification'];contract=read(check(plan['source_contract']))
assert plan['source_contract']==EXPECTED_CONTRACT and contract['schema']=='unit-row-routed-engine-qualification-cold-Source-contract-v1'
assert len(plan['sources'])==14 and len(plan['inputs'])==8 and plan['schema']=='ROOT-routed-engine-qualification-plan-v1'
assert plan['purpose']==MODE_PURPOSE[mode] and plan['limits']==LIMITS
assert result['sources']==contract['sources']==plan['sources'] and result['inputs']==contract['inputs']==plan['inputs']
assert result['purpose']==plan['purpose'] and plan['sources']['intake']==contract['source']
assert contract['source']['sha256']=='38f8f86f5af3474a0eed6fac7ff89c5d9c2b327d1413a2164be24ca8d7ea6e60'
assert body['version']=='unit-row-routed-engine-qualification-cold-v1'
assert canonical(body)+b'\n'==lines[0] and canonical(completion)+b'\n'==lines[1]
binding=contract['original_model_binding']
assert result['language_binding']==body['language_binding']==body['original_model_binding']==binding
assert result['controls'] is result['search'] is result['found_validation'] is None
assert data['schema']=='ROOT-unit-row-routed-engine-qualification-payload-v1'
assert data['stage']=='ROUTED_ENGINE_CONSUMER_QUALIFICATION_ONLY'
assert data['endpoint_purpose']==plan['purpose'] and data['separate_endpoint_count']==6 and data['required_case_count']==12
assert data['whole_engine_qualification_accepted']is data['same_process_all_twelve_qualified']is False
assert data['original_model_sources']==contract['original_model_sources'] and len(data['original_model_sources'])==17
assert data['original_model_binding']==binding
for ref in data['original_model_sources'].values():check(ref)
for ref in contract['original_model_inputs'].values():check(ref)
assert contract['original_model_inputs']=={k:plan['inputs'][k]for k in('declaration','profile')}
assert set(plan['reviews'])=={'ROOT','peer'}
for role,ref in plan['reviews'].items():
    review=read(check(ref))
    assert review['scope']=='unit-row-routed-engine-qualification-cold-Source' and review['author_identity']=='/root/hilbert_advice_controls'
    assert review['source']==plan['sources']['intake'] and review['sources']==plan['sources'] and review['source_contract']==plan['source_contract']
    assert review['source_only'] is review['source_review_passed'] is True and type(review['scientific_calls'])is int and review['scientific_calls']==0
    assert review['scientific_acceptance'] is False
    assert (review['reviewer_identity']=='/root' if role=='ROOT'else review['reviewer_identity']not in('/root','/root/hilbert_advice_controls'))
grant=read(check(plan['ROOT_authorization']))
assert grant['schema']=='ROOT-routed-engine-qualification-authorization-v1' and grant['author_identity']=='/root'
assert grant['actual_execution_authorized'] is True and type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
for k in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):assert grant[k]==plan[k]
assert Path(plan['output_directory'])==owned and plan['resource_rule']=='single-owned-process-native-terminal-v1'
expected_cases=tuple(contract['API']['purpose_modes_and_ordered_cases'][plan['purpose']])
assert list(expected_cases)==EXPECTED_CASES[mode] and data['expected_cases']==list(expected_cases)
assert data['control_count']==len(data['controls'])==len(expected_cases) and data['all_controls_completed'] is True
assert [c['case']for c in data['controls']]==list(expected_cases) and all(c['status']=='PASSED'for c in data['controls'])
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

assert result['schema']=='ROOT-unit-row-routed-engine-qualification-result-v1' and stdout['schema']=='ROOT-unit-row-routed-engine-qualification-final-observation-v1'
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

ENGINE_VERSION='lazy-unit-row-global-engine-v12-routed-marked-aware-degree'
NEW_SCHEMA='unit-row-marked-aware-nonimp-fibre-check-v1'
NEW_VERSION='unit-row-independent-marked-aware-nonimp-fibre-checker-v1'
RULES=['axiom','assumption','instantiate','eq_subst','mp','generalize']
FALSE_FLAGS=('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted')

def packet(value,current):
    key=value['placement_key'];row=key['translation'][1];pre=key['type_preimage'];base=pre['base_type_preimage']
    assert key['translation']==[0,row] and type(row)is int and 0<=row<24
    assert pre['schema']=='unit-row-row0-decorated-type-v1' and pre['marking_id']==mid and base['input_epoch']==binding['language_epoch']
    equal(value['base_tile']['placement_key']['type_preimage'],base)
    equal(value['base_tile']['placement_key']['translation'],key['translation'])
    equal(value['global_t_values'],[[[0,row],1]])
    equal(value['selection_record'],dict(key,generation=1))
    offsets=base['ordered_offsets'];premises=base['ordered_premise_formulas'];obs=value['read_obligations']
    assert len(offsets)==len(premises)==len(obs) and all(type(d)is int and -23<=d<0 and 0<=row+d<row for d in offsets)
    totals=points(current['t'])
    for d,formula,o in zip(offsets,premises,obs):
        equal(o,{'row':row+d,'formula':formula,'occupied':totals[(0,row+d)]==1,'fact_accepted':False})
    return value

def native_receipt(value,current,row,proposal=None):
    state(current)
    assert value['input_epoch']==binding['language_epoch'] and value['marking_id']==mid
    assert value['state_sha256']==sha(current) and type(value['row'])is int and value['row']==row
    assert all(value[k]is False for k in FALSE_FLAGS)
    keys=value['candidate_keys'];assert type(keys)is list and len({canonical(k)for k in keys})==len(keys)
    covered=value['complete_cover_checked'];assert type(covered)is bool
    if covered:
        n=value['degree_exact'];assert type(n)is int and n==len(keys)
        assert value['status']==('ZERO'if n==0 else'SINGLETON'if n==1 else'MANY')
        if n==1:packet(value['sole_candidate'],current);equal(value['sole_candidate']['placement_key'],keys[0])
        else:assert value['sole_candidate']is None
    else:
        assert value['degree_exact']is value['sole_candidate']is None
        assert(value['status']=='TWO_OR_MORE'and len(keys)>=2)or(value['status']=='UNKNOWN'and len(keys)<=1)
    assert value['accepted_local_evidence']is(value['status']!='UNKNOWN')
    if value['schema']==NEW_SCHEMA:
        assert value['version']==NEW_VERSION and value['nonimp_fibre_cover_checked']is covered
        equal(value['state'],current);assert value['original_state_sha256']==sha(value['original_state'])
        assert value['language_binding']==binding and value['marking_sha256']==sha(data['marking'])
        equal(points(current['m'])[(1,row)],['formula',canonical(value['output_formula']).decode()])
        assert value['output_formula'][0]!='imp' and 'original_base_receipt'not in value
        equal(value['candidate_keys'],[c['placement_key']for c in value['checked_candidates']])
        for c in value['checked_candidates']:packet(c,current)
        chk=value['independent_marked_state_check']
        assert chk['marked_state_checked']is chk['projection_literals_rechecked']is True
        assert chk['original_binding']==binding and chk['marking_id']==mid and chk['original_state_sha256']==value['original_state_sha256']
        if covered:assert type(value['checked_fibre_cover'])is dict and value['checked_fibre_cover']['completed']is True
        else:assert value['checked_fibre_cover']is None
        if proposal is not None:
            assert proposal['schema']=='unit-row-marked-aware-nonimp-fibre-proposal-v1'
            assert proposal['version']=='unit-row-marked-aware-nonimp-fibre-proposer-v1'
            assert value['proposal_sha256']==sha(proposal)
            equal(proposal['state'],current);equal(proposal['original_state'],value['original_state'])
            assert proposal['state_sha256']==sha(current) and proposal['original_state_sha256']==value['original_state_sha256']
            assert proposal['language_binding']==binding and proposal['marking_id']==mid and proposal['row']==row
            equal(proposal['candidates'],value['checked_candidates'])
            equal(proposal['root_rejections'],value['checked_root_rejections'])
            assert proposal['complete_cover_proposed']is covered and proposal['untrusted']is True
            if covered:equal(proposal['fibre_cover'],value['checked_fibre_cover'])
            else:assert proposal['fibre_cover']['completed']is False
    else:
        assert value['schema']=='unit-row-channel4-degree-evidence-check-v1'
        assert value['version']=='unit-row-channel4-filtered-degree-semantics-v1'
        assert type(value['original_base_receipt'])is dict and type(value['missing_mark_cover_checked'])is bool
        if proposal is not None:
            assert proposal['schema']=='unit-row-channel4-degree-evidence-proposal-v1' and proposal['version']=='unit-row-channel4-point-adapter-v1'
            equal(proposal['state'],current);assert proposal['state_sha256']==sha(current)
            assert proposal['language_binding']==binding and proposal['marking_id']==mid and proposal['row']==row
            equal(proposal['marked_rejections'],value['marked_rejections'])
            equal([c['placement_key']for c in proposal['candidates']],keys)
            for c in proposal['candidates']:packet(c,current)
            b=proposal['original_proposal'];r=value['original_base_receipt']
            assert r['state_sha256']==sha(b['state'])==b['state_sha256'] and r['row']==b['row']==row
            assert r['input_epoch']==b['input_epoch']==binding['language_epoch']
    if proposal is not None:assert all(proposal[k]is False for k in FALSE_FLAGS)
    return value

def query_record(q):
    assert q['state_sha256']==sha(q['state'])
    return native_receipt(q['receipt'],q['state'],q['row'],q['proposal'])

def logged_receipt(log,value,current,row):
    matches=[q for q in log['queries']if q['row']==row and q['state_sha256']==sha(current)
        and sha(q['proposal'])==value['proposal_sha256']]
    assert matches
    for q in matches:
        equal(q['state'],current);native_receipt(value,current,row,q['proposal'])

def snapshot(v):
    state(v['state']);assert v['schema']=='unit-row-channel4-routed-engine-snapshot-v1' and v['version']==ENGINE_VERSION
    assert v['marking_id']==mid and v['scheduler_policy']['branch_tie']=='ROW' and v['pending_preferences']is None
    assert len({r for r,c in v['certificates']})==len(v['certificates'])
    assert len({r for r,c in v['cursors']})==len(v['cursors'])
    return v

def certificate(v,row):return dict(v['certificates'])[row]
def core(v):return {k:x for k,x in v.items()if k!='read_obligations'}

def selected_append(before,after,tile):
    packet(tile,before)
    equal(after['selected'],before['selected']+[tile['selection_record']])
    row=tile['placement_key']['translation'][1];old,new=points(before['t']),points(after['t'])
    assert old[(0,row)]==0 and new[(0,row)]==1
    equal({str(k):v for k,v in old.items()if k!=(0,row)},{str(k):v for k,v in new.items()if k!=(0,row)})
    state(after)

def search_result(f,status):
    before=snapshot(f['before']);after=snapshot(f['after']);equal(after,before);equal(f['outer_after'],before)
    equal(before['state'],f['initial_state']);r=f['search_result']
    assert r['schema']=='unit-row-channel4-routed-lazy-global-search-result-v1' and r['version']==ENGINE_VERSION
    assert r['status']==status and r['root_restored']is r['stack_restored']is True and r['found']is None
    assert r['root_snapshot_sha256']==sha(before)==r['final_snapshot_sha256']
    assert r['marking_id']==mid and r['input_epoch']==binding['language_epoch'] and r['branch_advice_enabled']is False
    equal(r['scheduler_policy'],before['scheduler_policy'])
    ev=r['events'];assert [x['event']for x in ev]==list(range(len(ev))) and 0<len(ev)<=2000
    assert not any(x['kind']=='EXCLUDE'for x in ev)
    for k in('logical_proof_accepted','exact_point_board_accepted','complete_candidate_graph_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted'):assert r[k]is False
    return r,ev

def seed_join(seeds,current):
    assert len(seeds)==len(current['selected'])
    for seed,chosen in zip(seeds,current['selected']):
        equal(seed['placement_key']['type_preimage'],chosen['type_preimage']['base_type_preimage'])
        equal(seed['placement_key']['translation'],chosen['translation'])

def transfer_join(f,single):
    before=snapshot(f['before']);checked=snapshot(f['checked_snapshot']);placed=snapshot(f['after_placement'])
    equal(before['state'],f['initial_state']);equal(checked['state'],before['state']);seed_join(f['seeds'],before['state'])
    row=f['queried_row'];assert row==(1 if single else 3)
    origin=f['original_receipt'];equal(origin,certificate(checked,row));logged_receipt(f['actual_log'],origin,checked['state'],row)
    assert origin['status']==('SINGLETON'if single else'TWO_OR_MORE') and origin['complete_cover_checked']is single
    first=f['first_actual_decision'];assert first['kind']=='FORCED' and first['row']==(0 if single else 1)
    equal(first['candidate'],certificate(checked,first['row'])['sole_candidate']);equal(f['forced_candidate'],first['candidate'])
    assert all(v['status']!='UNKNOWN'for r,v in checked['certificates'])
    assert set(dict(checked['certificates']))=={p[1]for p,v in points(checked['state']['t']).items()if v==0}
    selected_append(checked['state'],placed['state'],f['forced_candidate'])
    transition=placed['last_transition'];proof=next(p for p in transition['rows']if p['row']==row)
    assert transition['schema']=='unit-row-channel4-checked-domain-transition-v2' and transition['version']=='unit-row-channel4-routed-support-transition-v2'
    assert transition['before_state_sha256']==sha(checked['state']) and transition['after_state_sha256']==sha(placed['state'])
    assert transition['marking_id']==mid and transition['input_epoch']==binding['language_epoch']
    assert transition['collision_ledger_equal']is proof['retain']is True
    assert transition['before_collision_ledger_sha256']==transition['after_collision_ledger_sha256']
    assert proof['before_projection_sha256']==proof['after_projection_sha256']
    cur=f['transferred_receipt'];equal(cur,certificate(placed,row))
    assert cur['schema']=='unit-row-channel4-transferred-domain-classification-v2' and cur['version']==ENGINE_VERSION
    assert cur['state_sha256']==sha(placed['state']) and cur['row']==row and cur['marking_id']==mid
    equal(cur['original_receipt'],origin)
    equal(cur['origin_protocol'],{'schema':origin['schema'],'version':origin['version']})
    equal(cur['origin_coverage'],{'kind':'MARKED_AWARE_NONIMP_FIBRES','nonimp_fibre_cover_checked':single})
    for k in('status','accepted_local_evidence','complete_cover_checked','degree_exact','candidate_keys'):equal(cur[k],origin[k])
    assert cur['previous_evidence_sha256']==sha(origin)
    equal(cur['transfer_chain'],[{'before_state_sha256':sha(checked['state']),'after_state_sha256':sha(placed['state']),'transition_sha256':sha(transition)}])
    equal(cur['transition'],dict(transition,rows=[proof]))
    old=origin['checked_candidates'];new=f['current_packets'];assert len(old)==len(new)==(1 if single else 2)
    for a,b in zip(old,new):equal(core(a),core(b));packet(b,placed['state'])
    assert [o['occupied']for c in old for o in c['read_obligations']]==([False]if single else[False,False])
    assert [o['occupied']for c in new for o in c['read_obligations']]==([True]if single else[False,True])
    if single:equal(cur['sole_candidate'],new[0])
    else:
        assert cur['degree_exact']is cur['sole_candidate']is None and cur['complete_cover_checked']is False
        observed=dict(placed['exposed_candidates'])
        for key,c in zip(cur['candidate_keys'],new):equal(observed[canonical(key).decode()]['candidate'],c)
    second=f['second_actual_decision'];after=snapshot(f['after_second_decision']);equal(after['state'],placed['state'])
    equal(certificate(after,row),cur)
    assert set(dict(after['certificates']))=={p[1]for p,v in points(after['state']['t']).items()if v==0}
    assert all(v['status']not in('UNKNOWN','ZERO')for r,v in after['certificates'])
    if single:assert second['kind']=='FORCED'and second['row']==1;equal(second['candidate'],new[0])
    else:equal(second,{'kind':'BRANCH','row':0})
    equal(f['inner_after'],checked);equal(f['outer_after'],before)
    assert all(cur[k]is False for k in FALSE_FLAGS)

def cursor_stream(record):
    current=state(record['state']);row=record['row'];before=snapshot(record['before']);after=snapshot(record['after'])
    equal(before['state'],current);equal(after['state'],current)
    marked=record['actual_log']['marked_cursors'];original=record['actual_log']['original_cursors']
    assert len(marked)==len(original)==1
    mc,oc=marked[0]['context'],original[0]['context'];equal(mc['state'],current)
    equal(mc['original_context'],oc);assert mc['state_sha256']==sha(current)
    assert mc['context_sha256']==sha({k:v for k,v in mc.items()if k!='context_sha256'})
    assert oc['context_sha256']==sha({k:v for k,v in oc.items()if k!='context_sha256'})
    assert mc['row']==oc['row']==row and mc['marking_id']==mid and mc['language_binding']==oc['language_binding']==binding
    assert mc['input_epoch']==oc['input_epoch']==binding['language_epoch'] and oc['state_sha256']==sha(oc['state'])
    assert mc['schema']=='unit-row-channel4-fallback-context-v1'and mc['version']=='unit-row-channel4-filtered-six-rule-fallback-v1'
    assert oc['schema']=='unit-row-all-six-fallback-context-v1'and oc['version']=='unit-row-complete-lazy-six-rule-fallback-v1'
    for log,ctx,marked_level in((marked[0],mc,True),(original[0],oc,False)):
        events=log['events'];assert events and events[-1]['kind']=='EOF' and all(v['kind']=='CANDIDATE'for v in events[:-1])
        for i,v in enumerate(events[:-1]):
            assert v['context_sha256']==ctx['context_sha256'] and v['ordinal']==i and v['independently_checked']is False
        c=events[-1]['completion'];assert events[-1]['context_sha256']==ctx['context_sha256']
        assert c['context_sha256']==ctx['context_sha256'] and c['state_sha256']==ctx['state_sha256']
        assert c['row']==row and c['input_epoch']==binding['language_epoch'] and c['yielded_candidates']==len(events)-1 and c['rules_completed']==RULES
        assert c['complete_fallback_proposed']is True
        for k in('independently_checked','degree_zero_or_singleton_accepted',*FALSE_FLAGS):assert c[k]is False
        if marked_level:assert c['marking_id']==mid
    me,oe=marked[0]['events'],original[0]['events'];mcands=[x['candidate']for x in me[:-1]]
    equal(record['items'],[{'kind':'CANDIDATE','candidate':c}for c in mcands]+[{'kind':'EOF','completion':me[-1]['completion']}])
    equal(record['checked_candidates'],mcands);equal(record['completion'],me[-1]['completion'])
    equal(record['completion']['original_completion'],oe[-1]['completion'])
    basekeys=[canonical(x['candidate']['placement_key'])for x in oe[:-1]];positions=[]
    for c in mcands:
        packet(c,current);key=canonical(c['base_tile']['placement_key']);assert basekeys.count(key)==1
        i=basekeys.index(key);positions.append(i);equal(c['base_tile'],core(oe[i]['candidate']))
    assert positions==sorted(positions)
    slot=dict(after['cursors'])[row];equal(slot['context'],mc);equal(slot['completion'],record['completion'])
    equal(slot['candidates'],mcands);equal(slot['keys'],[c['placement_key']for c in mcands])
    cover=record['actual_log']['covers'][0]
    equal(cover['state'],current);assert cover['row']==row
    equal(cover['completion'],record['completion']);equal(cover['checked_candidates'],mcands)
    equal(cover['receipt'],record['fresh_cover_receipt'])
    r=record['fresh_cover_receipt']
    if r is not None:
        logged_receipt(record['actual_log'],r,current,row);assert r['complete_cover_checked']is True
        actual=[canonical(c['placement_key'])for c in mcands];expected=[canonical(k)for k in r['candidate_keys']]
        assert len(actual)==len(set(actual))and len(expected)==len(set(expected))and set(actual)==set(expected)
    return me,oe

families=data['families']
if mode=='router-protocol':
    assert set(families)=={'ROUTING_PROTOCOL'};f=families['ROUTING_PROTOCOL'];q=f['queries']
    assert set(q)=={'ZERO','ONE','TWO','ABSENT','IMPLICATION'}
    for name,record in q.items():query_record(record);seed_join(f['seeds'][name],record['state'])
    for name,status,n in(('ZERO','ZERO',0),('ONE','SINGLETON',1),('TWO','TWO_OR_MORE',None)):
        r=q[name]['receipt'];assert r['schema']==NEW_SCHEMA and r['status']==status and r['degree_exact']==n
        assert r['complete_cover_checked']is r['nonimp_fibre_cover_checked']is(n is not None)
    for name in('ABSENT','IMPLICATION'):assert q[name]['receipt']['schema']=='unit-row-channel4-degree-evidence-check-v1'
    assert q['ABSENT']['receipt']['status']=='TWO_OR_MORE'and q['IMPLICATION']['receipt']['status']=='UNKNOWN'
    equal(f['seeds']['IMPLICATION'],[q['ONE']['receipt']['sole_candidate']['base_tile']])
    labels=['NEW_ON_ABSENT','LEGACY_ON_NONIMP','FORGED_language_binding','FORGED_state_sha256','FORGED_marking_id']
    assert [v['label']for v in f['failures']]==labels
    for i,bad in enumerate(f['failures']):
        if i==0:name='ABSENT';expected_proposal=q['ZERO']['proposal'];reason='marked degree router: checked implication/absent route requires exact legacy proposal protocol'
        elif i==1:name='ZERO';expected_proposal=q['ABSENT']['proposal'];reason='marked degree router: checked nonimp route requires exact new proposal protocol'
        else:
            name='ZERO';expected_proposal=json.loads(canonical(q['ZERO']['proposal']));field=labels[i].removeprefix('FORGED_')
            if field=='language_binding':expected_proposal[field]['language_epoch']='0'*64
            else:expected_proposal[field]='0'*64
            reason='marked-aware fibre evidence: whole original/marked current context'
        equal(bad['state'],q[name]['state']);assert bad['row']==q[name]['row'];equal(bad['failing_proposal'],expected_proposal)
        assert bad['exception_type']=='ValueError'and bad['rejected']is True and bad['returned_receipt']is None
        assert bad['actual_reason']==bad['expected_reason']==reason
elif mode=='global-forced-dead':
    assert set(families)=={'GLOBAL_FORCED_DEAD'};f=families['GLOBAL_FORCED_DEAD'];r,ev=search_result(f,'EXHAUSTED')
    seed_join(f['seeds'],f['initial_state']);assert r['trace_complete']is True
    lineage=[x for x in ev if x['kind']in('DECISION','TRY','PLACE','RESTORE')]
    assert [x['kind']for x in lineage]==['DECISION','TRY','PLACE','DECISION','TRY','PLACE','DECISION','RESTORE','RESTORE']
    d1,t1,p1,d3,t3,p3,d2,u3,u1=lineage
    assert [d['decision']['kind']for d in(d1,d3,d2)]==['FORCED','FORCED','DEAD']
    assert [d['decision']['row']for d in(d1,d3,d2)]==[1,3,2]
    for d,t,p,depth,row in((d1,t1,p1,0,1),(d3,t3,p3,1,3)):
        assert t['depth']==depth and t['row']==p['row']==row and t['mode']=='FORCED'
        equal(t['key'],p['key']);equal(t['key'],d['decision']['candidate']['placement_key'])
        equal(d['decision']['candidate'],dict(d['evidence'])[row]['sole_candidate'])
        assert t['state_sha256']==d['state_sha256']
    for u,t,depth,row in((u3,t3,1,3),(u1,t1,0,1)):
        assert u['depth']==depth and u['row']==row and u['child_status']=='EXHAUSTED';equal(u['key'],t['key'])
    assert u3['state_sha256']==d3['state_sha256']and u1['state_sha256']==sha(f['initial_state'])
    states={sha(f['initial_state']):f['initial_state']}
    for q in f['actual_log']['queries']:assert q['state_sha256']==sha(q['state']);states[q['state_sha256']]=q['state']
    for d in(d1,d3,d2):assert d['state_sha256']in states
    selected_append(states[d1['state_sha256']],states[d3['state_sha256']],d1['decision']['candidate'])
    selected_append(states[d3['state_sha256']],states[d2['state_sha256']],d3['decision']['candidate'])
    assert p1['state_sha256']==d3['state_sha256']and p3['state_sha256']==d2['state_sha256']
    for d in(d1,d3):
        s=states[d['state_sha256']];assert set(dict(d['evidence']))=={p[1]for p,v in points(s['t']).items()if v==0}
        assert all(v['status']!='UNKNOWN'for row,v in d['evidence'])
    dead=f['actual_dead_receipt'];equal(dead,dict(d2['evidence'])[2]);logged_receipt(f['actual_log'],dead,states[d2['state_sha256']],2)
    assert dead['status']=='ZERO'and dead['degree_exact']==0 and dead['complete_cover_checked']is True
    q3=[q for q in f['actual_log']['queries']if q['row']==3];assert len(q3)>=2 and q3[0]['state_sha256']!=q3[1]['state_sha256']
    invalid=[x for x in ev if x['kind']=='INVALIDATE'];assert 3 in invalid[0]['rows']and invalid[0]['transition']['collision_ledger_equal']is False
    assert r['counts']['forced']==r['counts']['placements']==2 and r['counts']['branches']==0
elif mode in('singleton-transfer','two-transfer'):
    name='SINGLETON_TRANSFER'if mode=='singleton-transfer'else'TWO_TRANSFER';assert set(families)=={name};transfer_join(families[name],mode=='singleton-transfer')
elif mode=='short-EOF':
    assert set(families)=={'SHORT_EOF'};f=families['SHORT_EOF']
    z,_=cursor_stream(f['ZERO']);o,_=cursor_stream(f['ONE']);i,_=cursor_stream(f['IMPLICATION'])
    assert [v['kind']for v in z]==['EOF']and [v['kind']for v in o]==['CANDIDATE','EOF']and [v['kind']for v in i]==['EOF']
    assert f['ZERO']['fresh_cover_receipt']['status']=='ZERO'and f['ONE']['fresh_cover_receipt']['status']=='SINGLETON'
    assert f['IMPLICATION']['fresh_cover_receipt']is None
    query_record(f['implication_standalone_query']);equal(f['implication_standalone_query']['state'],f['IMPLICATION']['state'])
    assert f['implication_standalone_query']['receipt']['schema']=='unit-row-channel4-degree-evidence-check-v1'
    assert f['implication_standalone_query']['receipt']['status']=='UNKNOWN'and f['implication_standalone_query']['receipt']['complete_cover_checked']is False
    equal(f['implication_seed'],f['ONE']['fresh_cover_receipt']['sole_candidate']['base_tile'])
    seed_join([f['implication_seed']],f['IMPLICATION']['state'])
    labels=['MISSING_KEY','EXTRA_KEY','DUPLICATE_KEY','FORGED_state_sha256','FORGED_marking_id']
    assert [v['label']for v in f['failures']]==labels
    for n,bad in enumerate(f['failures']):
        record=f['ZERO']if n==1 else f['ONE'];completion=json.loads(canonical(record['completion']))
        candidates=[]if n==0 else f['ONE']['checked_candidates']*2 if n==2 else f['ONE']['checked_candidates']
        reason='lazy engine: fresh complete cover agrees with entire checked fallback stream'
        if n>=3:completion[labels[n].removeprefix('FORGED_')]='0'*64;reason='lazy engine: fresh completion/cover exact original context'
        equal(bad['state'],record['state']);assert bad['row']==record['row'];equal(bad['completion'],completion);equal(bad['checked_candidates'],candidates)
        assert bad['exception_type']=='ValueError'and bad['rejected']is True and bad['returned_receipt']is None
        assert bad['actual_reason']==bad['expected_reason']==reason
else:
    assert mode=='child-UNKNOWN'and set(families)=={'CHILD_UNKNOWN'};f=families['CHILD_UNKNOWN'];r,ev=search_result(f,'UNKNOWN')
    assert f['initial_state']['selected']==[]and sum(points(f['initial_state']['t']).values())==0
    assert r['reason']=='routed qualification native-first actual child degree interruption'and r['trace_complete']is False
    stops=f['actual_log']['interruptions'];assert len(stops)==1;stop=stops[0];state(stop['state'])
    assert stop['kind']=='DECLARED_ACTUAL_CHILD_DEGREE_INTERRUPTION'and stop['initial_selected_count']==0
    assert stop['selected_count']==len(stop['state']['selected'])>0 and type(stop['native_ns'])is int and g<=stop['native_ns']<body['joint_deadline_ns']
    assert stop['joint_began_ns']==g and stop['joint_deadline_ns']==body['joint_deadline_ns'];equal(r['last_observed_state'],stop['state'])
    decisions=[v for v in ev if v['kind']=='DECISION'];tries=[v for v in ev if v['kind']=='TRY'];places=[v for v in ev if v['kind']=='PLACE']
    equal(decisions[0]['decision'],{'kind':'BRANCH','row':0});assert tries and places
    assert tries[0]['depth']==0 and tries[0]['row']==places[0]['row']==0 and tries[0]['mode']=='BRANCH'
    equal(tries[0]['key'],places[0]['key'])
    cursors=[v for v in f['actual_log']['marked_cursors']if v['context']['row']==0 and v['context']['state_sha256']==sha(f['initial_state'])]
    assert cursors and cursors[0]['events'][0]['kind']=='CANDIDATE'and cursors[0]['events'][0]['ordinal']==0
    equal(cursors[0]['events'][0]['candidate']['placement_key'],tries[0]['key'])
    assert decisions[0]['event']<tries[0]['event']<places[0]['event']
    equal(stop['state']['selected'][-1],dict(places[-1]['key'],generation=1));assert places[-1]['state_sha256']==sha(stop['state'])
    assert r['counts']['branches']>=1 and r['counts']['restores']>=1

for k in('target_benchmark_search_performed','prior_StageC_suite_qualified','failure_marking_activated','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):assert data[k]is False
assert data['controlled_search_performed']is(mode in('global-forced-dead','child-UNKNOWN'))
for k in('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert result[k]is False
for k in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):assert body[k]is False
for k in('logical_proof_accepted','ROOT_resource_accepted'):assert stdout[k]is False
for k in('ROOT_resource_accepted','ROOT_primary_accepted'):assert native[k]is observation[k]is False


disposition=dict(schema='ROOT-routed-engine-qualification-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
 plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
 outputs=outputs,native_evidence=native_refs(external),tool_bracket=pin(HERE/('ROOT-MR-'+mode+'-tool-bracket-v1.json')),
 lossless_transport_concordance=pin(HERE/('ROOT-MR-'+mode+'-transport-concordance-v1.json')),raw_expanded=pin(expanded_path),
 complete_wire_verified=True,native_terminal_closed=True,native_resources_qualified=True,complete_returned_record=True,
 native_deadline_confirmed=False,original20_positive_native_gate_failed=False,owned_output_directory_exists=True,
 native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,aggregate_B_bytes=peak,terminal_T_bytes=peak,
 complete_Date_seconds=date,resource_rule='single-owned-process-native-terminal-v1; B=T',actual_closed=True,all_reaped=True,
 reported_case_count=len(expected_cases),qualified_case_count=len(expected_cases),unqualified_case_count=0,passed_cases=len(expected_cases),skipped_cases=0,
 case_names=list(expected_cases),endpoint_controls_literal_concordance_accepted=True,whole_engine_qualification_accepted=False,
 prior_StageC_suite_qualified=False,marking_id=mid,marking_sha256=sha(data['marking']),original_model_binding=binding,
 closure_helper=pin(Path(__file__).resolve()),reconciliation_scope='Saved native/wire/literal routed proposals/native receipts/full origin transfers/current packets/cursor and actual trace/checkpoint concordance only; no scientific function, membership, relation enumeration or semantic replay.',
 controlled_fixture_search_performed=data['controlled_search_performed'],target_search_performed=False,
 failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
 complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
 scientific_replay=False,ROOT_resource_accepted=False,
 remaining_gaps=['One purpose only; all six distinct20 windows/twelve essential cases must strictly close.','Original StageC6/9 and both failedMAIN attempts remain unchanged; no target discovery/marking activation/completeGCTS/causal benefit/RL claim.'])
out=HERE/('ROOT-MR-'+mode+'-disposition-v1.json')
with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(out),'qualified_cases':len(expected_cases),'native_ns':probe-start,'scientific_replay':False}))
