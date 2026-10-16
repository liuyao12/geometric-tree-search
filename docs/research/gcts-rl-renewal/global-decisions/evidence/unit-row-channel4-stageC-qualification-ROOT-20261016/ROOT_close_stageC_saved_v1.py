"""Whole saved evidence/resource concordance only. No degree or logical replay."""
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

EXPECTED_CONTRACT={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageC-cold-source-20261016/Source-contract-v1.json', 'sha256': 'b6e97354241cb1f367575080011136344fa93311d9a55b089794d1754fbdecba', 'bytes': 26294}
MODE_PURPOSE={'stageC-dead-transfer': 'unit-row-channel4-stageC-dead-transfer-controls', 'stageC-natural-unknown': 'unit-row-channel4-stageC-natural-unknown-controls', 'stageC-forced-transfer-child': 'unit-row-channel4-stageC-forced-transfer-child-controls', 'stageC-scheduler': 'unit-row-channel4-stageC-scheduler-controls'}
EXPECTED_CASES={'stageC-dead-transfer': ['C1-marking-created-complete-ZERO-global-DEAD', 'C3-owned-complete-ZERO-transfer-original-marked-wrapper', 'C2-later-complete-ZERO-before-earlier-complete-SINGLETON'], 'stageC-natural-unknown': ['C4-natural-partial-filter-real-EOF-UNKNOWN-blocks-FORCED'], 'stageC-forced-transfer-child': ['C5-genuine-all-frontier-FORCED-before-BRANCH', 'C6-complete-MANY-SINGLETON-transfer-then-reference-BRANCH', 'C7-actual-child-native-first-UNKNOWN-full-restoration'], 'stageC-scheduler': ['C8-NONLOGICAL-kernel-global-priority', 'C9-NONLOGICAL-kernel-earliest-generation-explicit-ties']}
LIMITS={'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

def native_refs(external):
    return {n:pin(external/n)for n in('ONCE.json','native-terminal.json','observation.json',
        'meter-stdout.txt','meter-stderr.txt','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt')}

def auth_plan(plan,pp,mode):
    assert plan['schema']=='ROOT-channel4-stageC-plan-v1' and plan['purpose']==MODE_PURPOSE[mode]
    assert plan['source_contract']==EXPECTED_CONTRACT and plan['limits']==LIMITS
    assert plan['resource_rule']=='single-owned-process-native-terminal-v1'
    contract=read(check(plan['source_contract']))
    assert contract['sources']==plan['sources'] and contract['inputs']==plan['inputs']
    assert len(plan['sources'])==11 and len(plan['inputs'])==8
    assert contract['source']==plan['sources']['intake'] and contract['source']['sha256']=='af02a6fd7e145c326eed47f1ddf1df7968ea52c5c470e01ab6a3d3ef5d71eb43'
    for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['runtime'],*contract['original_model_sources'].values(),*contract['original_model_inputs'].values()]:check(ref)
    assert len(contract['original_model_sources'])==17
    assert set(plan['reviews'])=={'ROOT','peer'}
    for role,ref in plan['reviews'].items():
        v=read(check(ref))
        assert v['scope']=='unit-row-channel4-stageC-cold-Source' and v['author_identity']=='/root/arithmetic_induction'
        assert v['source']==plan['sources']['intake'] and v['sources']==plan['sources'] and v['source_contract']==plan['source_contract']
        assert v['source_only']is v['source_review_passed']is True and type(v['scientific_calls'])is int and v['scientific_calls']==0 and v['scientific_acceptance']is False
        assert(v['reviewer_identity']=='/root'if role=='ROOT'else v['reviewer_identity']not in('/root','/root/arithmetic_induction'))
    grant=read(check(plan['ROOT_authorization']))
    assert grant['schema']=='ROOT-channel4-stageC-authorization-v1' and grant['author_identity']=='/root' and grant['actual_execution_authorized']is True
    assert type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
    for k in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):assert grant[k]==plan[k]
    return contract

def failure_only(mode):
    # No decoding or interpretation of any returned science. This endpoint has
    # an exact native TimeoutError and no complete owned result/response.
    assert mode=='stageC-forced-transfer-child'
    plan_path=HERE/('ROOT-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
    contract=auth_plan(plan,pp,mode);owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1')
    assert Path(plan['output_directory'])==owned
    bracket_path=HERE/('ROOT-'+mode+'-tool-bracket-v1.json');bracket=read(bracket_path)
    assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
    assert bracket['tool_exit_code']==2 and bracket['tool_session_id']is None
    date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
    assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
    native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
    for v in(observation,once):
        assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes'] and v['invocation_id']==plan['invocation_id'] and v['purpose']==plan['purpose']
    assert observation['meter_returncode']==2 and observation['probe_returncode']==0
    assert native['caller_returncode']==2 and native['wait4_status']==512 and native['all_reaped']is True
    assert native['caller_pid']==native['wait4_pid'] and native['error']is None and native['interrupted']is False and native['cancellation_forwarded']is False
    raw_probe=(external/'postterminal-probe-stdout.txt').read_bytes();probe=int(raw_probe)
    assert str(probe).encode()+b'\n'==raw_probe and probe==observation['postterminal_native_probe_ns']
    start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns']
    assert start<terminal<=probe and terminal-start==native['caller_kernel_elapsed_ns']
    assert 20000000000<=terminal-start<=probe-start<55000000000
    peak=native['wait4_usage'][2];assert type(peak)is int and peak==native['caller_kernel_peak_bytes'] and 0<peak<=536870912
    assert(external/'meter-stdout.txt').read_bytes()==b''
    stderr=(external/'meter-stderr.txt').read_bytes()
    assert stderr==b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete marking data controls original20/500 reserve unfinished\n'
    assert(external/'postterminal-probe-stderr.txt').read_bytes()==b''
    assert not owned.exists()  # Exact present actual; absence means NO observed case counts.
    prior=read(check(plan['inputs']['stageB_disposition']))
    assert prior['actual_closed']is prior['native_resources_qualified']is True
    for k in('ROOT_resource_accepted','ROOT_primary_accepted'):assert native[k]is observation[k]is False
    disposition=dict(schema='ROOT-channel4-stageC-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
        plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
        outputs=[],native_evidence=native_refs(external),tool_bracket=pin(bracket_path),
        actual_closed=True,all_reaped=True,native_terminal_closed=True,native_resources_qualified=False,complete_wire_verified=False,
        original20_positive_native_gate_failed=True,native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,
        aggregate_B_bytes=peak,terminal_T_bytes=peak,complete_Date_seconds=date,
        reported_case_count=None,passed_cases=None,skipped_cases=None,qualified_case_count=0,unqualified_case_count=3,
        case_names=EXPECTED_CASES[mode],endpoint_controls_literal_concordance_accepted=False,
        complete_returned_record=False,owned_output_directory_exists=False,whole_StageC_qualification_accepted=False,
        marking_id=prior['marking_id'],original_model_binding=contract['original_model_binding'],
        failure_kind='ORIGINAL_NATIVE20_UNKNOWN_NO_RETURNED_CASE_RECORD',raw_stderr=stderr.decode(),
        diagnostic_limit='No inference of C5/C6/C7 progress, deliberate-child occurrence, counters, decisions, cache transfer, rollback, trajectory or scientific success.',
        reconciliation_scope='Administrative whole saved raw native/once/tool/diagnostic closure only; positive20 gate FAILED. No result/model decoding or scientific replay.',
        closure_helper=pin(Path(__file__).resolve()),resource_rule='single-owned-process-native-terminal-v1; B=T',
        target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
        complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
        scientific_replay=False,ROOT_resource_accepted=False)
    out=HERE/('ROOT-'+mode+'-disposition-v1.json')
    with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':0,'reported_case_count':None,'positive_native_gate':False,'scientific_replay':False}))

def aggregate():
    records={};refs={};ids=[];plans=[];directories=[];qualified=[];unqualified=[]
    for mode,purpose in MODE_PURPOSE.items():
        p=HERE/('ROOT-'+mode+'-disposition-v1.json');v=read(p);refs[mode]=pin(p);records[mode]=v
        assert v['schema']=='ROOT-channel4-stageC-endpoint-disposition-v1' and v['mode']==mode and v['purpose']==purpose
        assert v['actual_closed']is v['all_reaped']is v['native_terminal_closed']is True
        assert v['whole_StageC_qualification_accepted']is False and v['case_names']==EXPECTED_CASES[mode]
        assert v['closure_helper']==pin(Path(__file__).resolve())
        plan=read(check(v['plan']));auth_plan(plan,v['plan'],mode)
        assert v['sources']==plan['sources'] and v['inputs']==plan['inputs'] and v['source_contract']==plan['source_contract']
        assert v['invocation_id']==plan['invocation_id'];ids.append(v['invocation_id']);plans.append(v['plan']['sha256']);directories.append(plan['output_directory'])
        for ref in v['native_evidence'].values():check(ref)
        check(v['tool_bracket'])
        for k in('target_search_performed','failure_marking_activated','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','scientific_replay','ROOT_resource_accepted'):assert v[k]is False
        if v['endpoint_controls_literal_concordance_accepted']:
            assert v['native_resources_qualified']is v['complete_wire_verified']is True
            assert v['qualified_case_count']==v['passed_cases']==len(EXPECTED_CASES[mode]) and v['unqualified_case_count']==0 and v['skipped_cases']==0
            for ref in v['outputs']:check(ref)
            assert len(v['outputs'])==2
            transport=read(check(v['lossless_transport_concordance']));check(v['raw_expanded'])
            assert transport['expanded_file']==v['raw_expanded'] and transport['encoded_file']==v['outputs'][0]
            qualified.extend(v['case_names'])
        else:
            assert mode=='stageC-forced-transfer-child' and v['failure_kind']=='ORIGINAL_NATIVE20_UNKNOWN_NO_RETURNED_CASE_RECORD'
            assert v['native_resources_qualified']is v['complete_wire_verified']is False
            assert v['reported_case_count']is v['passed_cases']is v['skipped_cases']is None
            assert v['qualified_case_count']==0 and v['unqualified_case_count']==len(EXPECTED_CASES[mode]) and v['outputs']==[]
            unqualified.extend(v['case_names'])
    assert len(ids)==len(set(ids))==len(plans)==len(set(plans))==len(directories)==len(set(directories))==4
    values=list(records.values())
    assert all(v['marking_id']==values[0]['marking_id'] and canonical(v['original_model_binding'])==canonical(values[0]['original_model_binding'])for v in values)
    assert len(qualified)+len(unqualified)==len(set(qualified+unqualified))==9
    full=not unqualified
    result=dict(schema='ROOT-channel4-stageC-disposition-v1',endpoints=refs,essential_case_count=9,
        endpoint_native_summary={m:{k:v[k]for k in('native_resources_qualified','native_launch_to_postprobe_ns','native_worker_lifetime_ns','aggregate_B_bytes','complete_Date_seconds')}for m,v in records.items()},
        qualified_case_count=len(qualified),unqualified_case_count=len(unqualified),qualified_case_names=qualified,unqualified_case_names=unqualified,
        all_four_endpoints_closed=True,all_essential_cases_qualified=full,StageC_qualification_accepted=full,
        no_combined20_claim=True,separate_original20_endpoint_count=4,unchanged_actual_restarted=False,
        current_sources=values[0]['sources'],current_inputs=values[0]['inputs'],source_contract=values[0]['source_contract'],
        marking_id=values[0]['marking_id'],original_model_binding=values[0]['original_model_binding'],
        closure_scope='Aggregate of FOUR reviewed-helper per-endpoint saved closures; no semantic replay or combined20 search-budget inference.',
        case_progress_limit='A no-record deadline contributes ZERO qualified cases and UNKNOWN reported counts, not a partial semantic result.',
        target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
        complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
        scientific_replay=False,ROOT_resource_accepted=False)
    out=HERE/'ROOT-stageC-disposition-v1.json'
    with out.open('x')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'disposition':pin(out),'qualified_cases':len(qualified),'unqualified_cases':len(unqualified),'StageC_qualified':full,'scientific_replay':False}))

assert len(sys.argv)==2 and sys.argv[1]in(*MODE_PURPOSE,'aggregate')
mode=sys.argv[1]
if mode=='aggregate':
    aggregate();sys.exit(0)
if mode=='stageC-forced-transfer-child'and read(HERE/(mode+'-external-v1')/'native-terminal.json')['caller_returncode']==2:
    failure_only(mode);sys.exit(0)

plan_path=HERE/('ROOT-'+mode+'-plan-v1.json');plan=read(plan_path);pp=pin(plan_path)
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1')
bracket=read(HERE/('ROOT-'+mode+'-tool-bracket-v1.json'))
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
transport=read(HERE/('ROOT-'+mode+'-transport-concordance-v1.json'))
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
assert transport['encoded_cap_bytes']==4194304 and transport['expanded_cap_bytes']==16777216
assert transport['strict_canonical_JSON_LF'] is transport['strict_base64_reencoded'] is transport['single_complete_zlib_stream'] is True
assert transport['trailing_or_unconsumed_bytes'] is False and transport['scientific_replay'] is False
expanded_path=check(transport['expanded_file']);result=read(expanded_path)
assert expanded_path.read_bytes()==canonical(result)+b'\n'
data=result['channel4_stageC'];contract=read(check(plan['source_contract']))
assert plan['source_contract']==EXPECTED_CONTRACT and contract['schema']=='unit-row-channel4-stageC-cold-Source-contract-v1'
assert len(plan['sources'])==11 and len(plan['inputs'])==8 and plan['schema']=='ROOT-channel4-stageC-plan-v1'
assert plan['purpose']==MODE_PURPOSE[mode] and plan['limits']==LIMITS
assert result['sources']==contract['sources']==plan['sources'] and result['inputs']==contract['inputs']==plan['inputs']
assert result['purpose']==plan['purpose'] and plan['sources']['intake']==contract['source']
assert contract['source']['sha256']=='af02a6fd7e145c326eed47f1ddf1df7968ea52c5c470e01ab6a3d3ef5d71eb43'
assert body['version']=='unit-row-channel4-degree-transfer-priority-child-cold-v1'
assert canonical(body)+b'\n'==lines[0] and canonical(completion)+b'\n'==lines[1]
binding=contract['original_model_binding']
assert result['language_binding']==body['language_binding']==body['original_model_binding']==binding
assert result['controls'] is result['search'] is result['found_validation'] is None
assert data['schema']=='ROOT-unit-row-channel4-stageC-payload-v1'
assert data['stage']=='GLOBAL_DEGREE_TRANSFER_PRIORITY_UNKNOWN_CHILD_OR_NONLOGICAL_KERNEL'
assert data['endpoint_purpose']==plan['purpose'] and data['all_four_endpoints_required'] is True
assert data['whole_StageC_qualification_accepted'] is False
assert data['original_model_sources']==contract['original_model_sources'] and len(data['original_model_sources'])==17
assert data['original_model_binding']==binding
for ref in data['original_model_sources'].values():check(ref)
for ref in contract['original_model_inputs'].values():check(ref)
assert contract['original_model_inputs']=={k:plan['inputs'][k]for k in('declaration','profile')}
assert set(plan['reviews'])=={'ROOT','peer'}
for role,ref in plan['reviews'].items():
    review=read(check(ref))
    assert review['scope']=='unit-row-channel4-stageC-cold-Source' and review['author_identity']=='/root/arithmetic_induction'
    assert review['source']==plan['sources']['intake'] and review['sources']==plan['sources'] and review['source_contract']==plan['source_contract']
    assert review['source_only'] is review['source_review_passed'] is True and type(review['scientific_calls'])is int and review['scientific_calls']==0
    assert review['scientific_acceptance'] is False
    assert (review['reviewer_identity']=='/root' if role=='ROOT'else review['reviewer_identity']not in('/root','/root/arithmetic_induction'))
grant=read(check(plan['ROOT_authorization']))
assert grant['schema']=='ROOT-channel4-stageC-authorization-v1' and grant['author_identity']=='/root'
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

def snapshot(value):
    state(value['state']);assert value['marking_id']==mid
    assert value['scheduler_policy']['branch_tie']=='ROW' and value['pending_preferences'] is None
    assert type(value['row_versions'])is list and len(value['row_versions'])==24 and all(type(n)is int for n in value['row_versions'])
    assert len({r for r,v in value['certificates']})==len(value['certificates'])
    return value

def cert(value,row):return dict(value['certificates'])[row]
def slot(value,row):
    assert len({r for r,v in value['cursors']})==len(value['cursors'])
    return dict(value['cursors'])[row]
def rowproof(value,row):
    rows=value['last_transition']['rows'];assert [p['row']for p in rows]==list(range(24));return rows[row]
def core(value):return {k:v for k,v in value.items()if k!='read_obligations'}

def receipt(value,s,row):
    assert value['marking_id']==mid and value['input_epoch']==binding['language_epoch']
    assert type(value['row'])is int and value['row']==row and value['state_sha256']==sha(s)
    assert value['status']in('ZERO','SINGLETON','MANY','TWO_OR_MORE','UNKNOWN')
    assert value['accepted_local_evidence']is(value['status']!='UNKNOWN')
    for k in('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert value[k]is False
    if value['complete_cover_checked']:
        assert type(value['degree_exact'])is int and value['degree_exact']==len(value['candidate_keys'])
        if value['status']=='ZERO':assert value['degree_exact']==0 and value['sole_candidate']is None
        elif value['status']=='SINGLETON':
            assert value['degree_exact']==1;equal(value['sole_candidate']['placement_key'],value['candidate_keys'][0])
        else:assert value['status']=='MANY' and value['degree_exact']>=2 and value['sole_candidate']is None
    else:
        assert value['degree_exact']is None and value['sole_candidate']is None
        assert value['status']in('TWO_OR_MORE','UNKNOWN')
    return value

def proposal_join(proposal,s,row,checked=None):
    assert proposal['schema']=='unit-row-channel4-degree-evidence-proposal-v1' and proposal['untrusted']is True
    equal(proposal['state'],s);assert proposal['state_sha256']==sha(s) and proposal['row']==row
    assert proposal['marking_id']==mid and proposal['input_epoch']==binding['language_epoch'];equal(proposal['language_binding'],binding)
    original=proposal['original_proposal'];base=original['state']
    assert base['schema']=='unit-row-implicit-private-state-v1' and base['input_epoch']==binding['language_epoch']
    equal(base['t'],s['t']);equal(base['m'],[v for v in s['m']if v[0][0]!=4]);equal(base['generation'],s['generation'])
    assert original['state_sha256']==sha(base) and original['row']==row;equal(original['language_binding'],binding)
    assert len(base['selected'])==len(s['selected'])
    for a,b in zip(base['selected'],s['selected']):
        equal(a['type_preimage'],b['type_preimage']['base_type_preimage']);equal(a['translation'],b['translation']);equal(a['generation'],b['generation'])
    if checked is not None:
        receipt(checked,s,row)
        equal(checked['candidate_keys'],[c['placement_key']for c in proposal['candidates']])
        equal(checked['marked_rejections'],proposal['marked_rejections'])
        base_receipt=checked['original_base_receipt']
        assert base_receipt['state_sha256']==sha(base) and base_receipt['row']==row and base_receipt['input_epoch']==binding['language_epoch']
        equal(base_receipt['candidate_keys'],[c['placement_key']for c in original['candidates']])
    return original

def logged_origin(log,s,row,checked):
    found=[q for q in log['queries']if q['row']==row and q['state_sha256']==sha(s)]
    assert found
    for q in found:proposal_join(q['proposal'],s,row,checked)
    return found[0]['proposal']

def transfer(before,after,row,origin):
    snapshot(before);snapshot(after);previous=receipt(cert(before,row),before['state'],row)
    current=receipt(cert(after,row),after['state'],row)
    assert current['schema']=='unit-row-channel4-transferred-domain-classification-v1'
    proof=rowproof(after,row);assert proof['retain']is True and after['last_transition']['collision_ledger_equal']is True
    equal(current['original_receipt'],origin);assert current['previous_evidence_sha256']==sha(previous)
    for k in('status','accepted_local_evidence','complete_cover_checked','degree_exact','candidate_keys','missing_mark_cover_checked'):equal(current[k],previous[k])
    chain=current['transfer_chain'];equal(chain[:-1],previous.get('transfer_chain',[]))
    assert chain[-1]=={'before_state_sha256':sha(before['state']),'after_state_sha256':sha(after['state']),'transition_sha256':sha(after['last_transition'])}
    equal(current['transition'],dict(after['last_transition'],rows=[proof]))
    if current['sole_candidate']is not None:equal(core(current['sole_candidate']),core(previous['sole_candidate']))
    return current

def context(value,s,marked=True):
    equal(value['state'],s);assert value['state_sha256']==sha(s)
    assert value['context_sha256']==sha({k:v for k,v in value.items()if k!='context_sha256'})
    assert value['input_epoch']==binding['language_epoch'];equal(value['language_binding'],binding)
    if marked:assert value['marking_id']==mid

def stream(log,s,n,marked):
    context(log['context'],s,marked);events=log['events']
    assert [e['kind']for e in events]==['CANDIDATE']*n+['EOF']
    assert [e['ordinal']for e in events[:-1]]==list(range(n))
    for e in events[:-1]:
        assert e['context_sha256']==log['context']['context_sha256'] and e['independently_checked']is False
    completion=events[-1]['completion']
    assert events[-1]['context_sha256']==log['context']['context_sha256']==completion['context_sha256']
    assert completion['state_sha256']==sha(s) and completion['row']==log['context']['row'] and completion['yielded_candidates']==n
    assert completion['independently_checked']is completion['degree_zero_or_singleton_accepted']is False
    for k in('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert completion[k]is False
    if marked:assert completion['marking_id']==mid
    return events

def selected_append(before,after,packet):
    equal(after['state']['selected'],before['state']['selected']+[packet['selection_record']])
    assert len(after['state']['selected'])==len(before['state']['selected'])+1

families=data['families']
if mode=='stageC-dead-transfer':
    assert set(families)=={'DEAD_ZERO_TRANSFER','DEAD_BEFORE_SINGLETON'}
    a=families['DEAD_ZERO_TRANSFER'];before=snapshot(a['before']);checked=snapshot(a['checked_snapshot'])
    equal(before['state'],a['initial_state']);equal(before['state'],checked['state'])
    assert a['actual_decision']=={'kind':'DEAD','row':1}
    assert cert(checked,0)['status']=='TWO_OR_MORE'
    origin=receipt(a['origin_marked_receipt'],checked['state'],1);equal(origin,cert(checked,1))
    assert origin['status']=='ZERO' and origin['degree_exact']==0 and origin['complete_cover_checked']is True
    assert origin['original_base_receipt']['status']=='SINGLETON' and origin['original_base_receipt']['complete_cover_checked']is True
    assert any(p==[4,0]and type(x)is int and type(y)is int and x!=y for z in origin['marked_rejections']for p,x,y in z['conflicting_points'])
    logged_origin(a['actual_log'],checked['state'],1,origin)
    after=snapshot(a['after_transfer']);selected_append(checked,after,a['policy_independent_post_DEAD_placement'])
    changed=transfer(checked,after,1,origin);equal(changed,a['transferred_receipt'])
    assert a['second_decision']=={'kind':'DEAD','row':1};equal(cert(a['after_second_decision'],1),changed)
    equal(a['restored'],checked)
    first=a['seeds'][0]['placement_key'];second=a['policy_independent_post_DEAD_placement']['base_tile']['placement_key']
    equal(first['type_preimage'],second['type_preimage']);assert first['tile_type_id']==second['tile_type_id'] and first['translation']!=second['translation']
    b=families['DEAD_BEFORE_SINGLETON'];before=snapshot(b['before']);after=snapshot(b['after'])
    equal(before['state'],b['initial_state']);equal(before['state'],after['state'])
    assert b['actual_decision']=={'kind':'DEAD','row':2}
    assert receipt(cert(after,0),after['state'],0)['status']=='SINGLETON'
    assert receipt(cert(after,2),after['state'],2)['status']=='ZERO'
    assert cert(after,0)['complete_cover_checked']is cert(after,2)['complete_cover_checked']is True
    for row in(0,2):logged_origin(b['actual_log'],after['state'],row,cert(after,row))
elif mode=='stageC-natural-unknown':
    assert set(families)=={'NATURAL_UNKNOWN'}
    a=families['NATURAL_UNKNOWN'];equal(a['size1_carrier'],[['bot']])
    before=snapshot(a['before']);after=snapshot(a['after_decision']);equal(before['state'],a['initial_state']);equal(after['state'],before['state']);equal(a['restored'],before)
    q=a['fresh_initial_partial'];equal(q['state'],before['state']);assert q['row']==3
    original=proposal_join(q['proposal'],before['state'],3,q['receipt'])
    assert original['kind']=='TWO_LEGAL_WITNESSES' and original['complete_cover_proposed']is False
    assert [[3+d for d in x['placement_key']['type_preimage']['ordered_offsets']]for x in original['candidates']]==[[0,2],[2,0]]
    assert q['receipt']['status']=='UNKNOWN' and q['receipt']['complete_cover_checked']is False and len(q['proposal']['candidates'])==1
    assert q['receipt']['original_base_receipt']['complete_cover_checked']is False
    assert a['actual_decision']['kind']=='UNKNOWN' and 3 in a['actual_decision']['unresolved_rows']
    assert cert(after,3)=={'status':'UNKNOWN'} and receipt(cert(after,1),after['state'],1)['status']=='SINGLETON'
    assert cert(after,1)['complete_cover_checked']is True
    frontier=[r for r,v in points(after['state']['t']).items()if v==0]
    assert set(dict(after['certificates']))=={p[1]for p in frontier}
    assert a['actual_decision']['unresolved_rows']==sorted(r for r,v in after['certificates']if v['status']=='UNKNOWN')
    log=a['actual_log'];logged_origin(log,after['state'],1,cert(after,1))
    originals=[x for x in log['original_cursors']if x['context']['row']==3]
    marked=[x for x in log['marked_cursors']if x['context']['row']==3]
    claims=[x for x in log['certifications']if x['row']==3]
    assert len(originals)==len(marked)==len(claims)==1
    oe=stream(originals[0],originals[0]['context']['state'],2,False);me=stream(marked[0],after['state'],1,True)
    equal(marked[0]['context']['original_context'],originals[0]['context']);equal(me[-1]['completion']['original_completion'],oe[-1]['completion'])
    equal(me[0]['candidate']['base_tile']['placement_key'],oe[1]['candidate']['placement_key'])
    equal(core(oe[1]['candidate']),me[0]['candidate']['base_tile'])
    equal(claims[0]['state'],after['state']);equal(claims[0]['completion'],me[-1]['completion'])
    equal(claims[0]['checked_candidates'],[me[0]['candidate']]);assert claims[0]['receipt']is None
    repeated=[x for x in log['queries']if x['row']==3 and x['state_sha256']==sha(after['state'])]
    assert len(repeated)==2
    for x in repeated:
        proposal_join(x['proposal'],after['state'],3)
        assert x['proposal']['original_proposal']['complete_cover_proposed']is False and len(x['proposal']['candidates'])==1
    assert log['interruptions']==[]  # No withheld delegate/mode-toggle seam.
elif mode=='stageC-forced-transfer-child':
    assert set(families)=={'FORCED_TRANSFER_CHILD'}
    a=families['FORCED_TRANSFER_CHILD'];before=snapshot(a['before']);checked=snapshot(a['checked_snapshot'])
    equal(before['state'],a['initial_state']);equal(checked['state'],before['state'])
    assert a['first_actual_decision']['kind']=='FORCED' and a['first_actual_decision']['row']==1
    equal(a['first_actual_decision']['candidate'],cert(checked,1)['sole_candidate'])
    frontier={p[1]for p,v in points(checked['state']['t']).items()if v==0}
    assert set(dict(checked['certificates']))==frontier and all(v['status']!='UNKNOWN'for r,v in checked['certificates'])
    origin={int(k):v for k,v in a['original_marked_receipts'].items()}
    for row,status,n in((1,'SINGLETON',1),(3,'MANY',2),(5,'SINGLETON',1)):
        equal(origin[row],cert(checked,row));receipt(origin[row],checked['state'],row)
        assert origin[row]['status']==status and origin[row]['degree_exact']==n and origin[row]['complete_cover_checked']is True
        logged_origin(a['actual_log'],checked['state'],row,origin[row])
    populated=snapshot(a['populated_before']);old=a['original_slot'];equal(old,slot(populated,3));equal(populated['state'],checked['state'])
    assert [x['kind']for x in a['initial_cursor_events']]==['CANDIDATE','CANDIDATE','EOF']
    for i in range(2):equal(a['initial_cursor_events'][i]['candidate'],old['candidates'][i])
    equal(a['initial_cursor_events'][-1]['completion'],old['completion'])
    one=snapshot(a['after_first_placement']);selected_append(populated,one,a['first_forced_candidate'])
    equal(a['first_forced_candidate'],a['first_actual_decision']['candidate'])
    m1=transfer(populated,one,3,origin[3]);s1=transfer(populated,one,5,origin[5])
    equal(m1,a['first_MANY_transfer']);equal(s1,a['first_SINGLETON_transfer'])
    five=snapshot(a['before_second_placement']);equal(five['state'],one['state'])
    equal(cert(five,3),m1);equal(cert(five,5),s1)
    assert a['second_actual_decision']['kind']=='FORCED' and a['second_actual_decision']['row']==5
    equal(a['second_actual_decision']['candidate'],s1['sole_candidate']);equal(a['second_forced_candidate'],s1['sole_candidate'])
    two=snapshot(a['after_second_placement']);selected_append(five,two,a['second_forced_candidate'])
    m2=transfer(five,two,3,origin[3]);equal(m2,a['second_MANY_transfer']);assert len(m2['transfer_chain'])==2 and 5 not in dict(two['certificates'])
    for current in(one,two):
        s=slot(current,3)
        equal(s['context_archive'],[{k:old[k]for k in('context','keys','candidates','completion')}])
        for k in('context','keys','completion'):equal(s[k],old[k])
        for oldc,newc in zip(old['candidates'],s['candidates']):equal(core(oldc),core(newc))
        assert all(o['occupied']is True for c in s['candidates']for o in c['read_obligations'])
        assert s['candidate_packets_state_sha256']==sha(current['state'])
    assert sorted(o['occupied']for c in old['candidates']for o in c['read_obligations'])==[False,True]
    root=snapshot(a['search_before']);equal(root['state'],two['state'])
    assert a['actual_branch_decision']=={'kind':'BRANCH','row':3}
    assert all(v['status']in('MANY','TWO_OR_MORE')for r,v in root['certificates'])
    found=a['controlled_search_result'];interruption=a['actual_interruption'];equal(a['actual_log']['interruptions'],[interruption])
    assert found['status']=='UNKNOWN' and found['reason']=='StageC native-first actual-child degree interruption'
    assert found['found']is None and found['root_restored']is found['stack_restored']is True and found['trace_complete']is False
    events=found['events'];assert [x['event']for x in events]==list(range(len(events))) and 0<len(events)<=2000
    tries=[x for x in events if x['kind']=='TRY'];assert tries
    assert any(x['kind']=='PLACE'and x['event']>tries[0]['event']for x in events)
    assert not any(x['kind']=='EXCLUDE'for x in events)
    assert interruption['kind']=='DECLARED_ACTUAL_CHILD_DEGREE_INTERRUPTION'
    assert type(interruption['row'])is int and 0<=interruption['row']<24
    assert type(interruption['native_ns'])is int and g<=interruption['native_ns']<body['joint_deadline_ns']
    assert interruption['joint_began_ns']==g and interruption['joint_deadline_ns']==body['joint_deadline_ns']
    assert interruption['selected_count']==len(interruption['state']['selected'])>len(root['state']['selected'])
    equal(found['last_observed_state'],interruption['state']);state(interruption['state'])
    assert found['counts']['branches']>=1 and found['counts']['restores']>=1 and found['counts']['nodes']<=128
    equal(a['search_restored'],root);equal(a['outer_after'],populated)
    assert found['root_snapshot_sha256']==sha(root)==found['final_snapshot_sha256']
    for k in('logical_proof_accepted','exact_point_board_accepted','complete_candidate_graph_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted'):assert found[k]is False
else:
    assert mode=='stageC-scheduler' and set(families)=={'NONLOGICAL_SCHEDULER'}
    a=families['NONLOGICAL_SCHEDULER'];p=a['priority'];v=a['generation_and_ties']
    equal(p['ZERO_input'],{'evidence':{'0':{'status':'UNKNOWN'},'1':{'status':'SINGLETON'},'9':{'status':'ZERO'}},'generations':[[0,0],[1,0],[9,9]]})
    equal(p['UNKNOWN_input'],{'evidence':{'0':{'status':'UNKNOWN'},'1':{'status':'SINGLETON'}},'generations':[[0,0],[1,0]]})
    equal(p['FORCED_input'],{'evidence':{'0':{'status':'MANY','degree_exact':2},'7':{'status':'SINGLETON'}},'generations':[[0,0],[7,9]]})
    assert p['ZERO_result']=={'kind':'DEAD','row':9} and p['UNKNOWN_result']=={'kind':'UNKNOWN','row':None,'unresolved_rows':[0]} and p['FORCED_result']=={'kind':'FORCED','row':7}
    equal(v['evidence'],{'0':{'status':'MANY','degree_exact':10},'2':{'status':'MANY','degree_exact':2}})
    equal(v['earlier_generations'],[[0,0],[2,1]]);equal(v['tied_generations'],[[0,0],[2,0]]);equal(v['assigned_output_rows'],[2])
    assert v['earlier_generation_result']==v['ROW_result']=={'kind':'BRANCH','row':0} and v['MARK_result']=={'kind':'BRANCH','row':2}
    assert all('NONLOGICAL'in c['scope']or'Synthetic'in c['scope']for c in data['controls'])

for k in('target_search_performed','failure_marking_activated','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):assert data[k]is False
assert data['controlled_child_search_performed']is(mode=='stageC-forced-transfer-child')
for k in('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert result[k]is False
for k in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):assert body[k]is False
disposition=dict(schema='ROOT-channel4-stageC-endpoint-disposition-v1',mode=mode,purpose=plan['purpose'],
 plan=pp,invocation_id=plan['invocation_id'],sources=plan['sources'],inputs=plan['inputs'],source_contract=plan['source_contract'],
 outputs=outputs,native_evidence=native_refs(external),tool_bracket=pin(HERE/('ROOT-'+mode+'-tool-bracket-v1.json')),lossless_transport_concordance=pin(HERE/('ROOT-'+mode+'-transport-concordance-v1.json')),
 raw_expanded=pin(expanded_path),complete_wire_verified=True,native_terminal_closed=True,native_resources_qualified=True,
 native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,aggregate_B_bytes=peak,terminal_T_bytes=peak,
 complete_Date_seconds=date,resource_rule='single-owned-process-native-terminal-v1; B=T',actual_closed=True,all_reaped=True,
 reported_case_count=len(expected),qualified_case_count=len(expected),unqualified_case_count=0,passed_cases=len(expected),skipped_cases=0,
 case_names=expected,endpoint_controls_literal_concordance_accepted=True,whole_StageC_qualification_accepted=False,
 marking_id=mid,marking_sha256=sha(data['marking']),original_model_binding=binding,
 closure_helper=pin(Path(__file__).resolve()),reconciliation_scope='Whole saved native/wire/typed literal state/receipt/transfer/cursor/restore concordance only; no scientific function, membership, relation scan, matcher or semantic replay.',
 target_search_performed=False,failure_marking_activated=False,logical_proof_accepted=False,exact_point_board_accepted=False,
 complete_GCTS_model_accepted=False,GCTS_search_trajectory_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
 scientific_replay=False,ROOT_resource_accepted=False,
 remaining_gaps=['Other StageC endpoints/all9 essential current-source findings still required; no combined20 claim.','No marked target result/benefit/full GCTS trajectory or general all-six EOF authority.'])
out=HERE/('ROOT-'+mode+'-disposition-v1.json')
with out.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(out),'qualified_cases':len(expected),'native_ns':probe-start,'scientific_replay':False}))
