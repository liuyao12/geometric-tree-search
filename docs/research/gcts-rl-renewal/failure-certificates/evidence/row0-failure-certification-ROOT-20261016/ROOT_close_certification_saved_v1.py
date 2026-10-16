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
mode='certification'
plan_path=HERE/'ROOT-certification-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'certification-owned-v1';external=HERE/'certification-external-v1'
bracket=read(HERE/'ROOT-certification-tool-bracket-v1.json')
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
transport=read(HERE/'ROOT-certification-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));cert=result['certification']
contract=read(check(plan['source_contract']))
assert len(plan['sources'])==7 and len(plan['inputs'])==8
assert plan['purpose']=='unit-row-first-DEAD0-certification'
assert contract['sources']==plan['sources'] and contract['inputs']==plan['inputs']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs']
assert result['purpose']==plan['purpose'] and result['language_binding']==body['language_binding']==contract['original_model_binding']
assert result['controls'] is result['search'] is result['found_validation'] is None
assert cert['schema']=='ROOT-first-DEAD0-certification-payload-v1'
assert cert['original_model_sources']==contract['original_model_sources']
assert cert['original_model_binding']==contract['original_model_binding']
for ref in cert['original_model_sources'].values():check(ref)
assert cert['sample_count']==2 and cert['control_count']==12
assert cert['all_controls_completed'] is cert['local_contexts_freshly_checked'] is cert['row0_projection_certificates_checked'] is True
cases=cert['controls'];samples=cert['samples']
assert len(cases)==12 and [c['case'] for c in cases]==contract['controls']
assert all(c['status']=='PASSED' for c in cases)
assert len(samples)==2 and [s['arm'] for s in samples]==['canonical','advised']
declaration=read(check(plan['inputs']['declaration']))
original_binding=contract['original_model_binding']
def ascii_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()
projection_flags=('logical_proof_accepted','exact_point_board_accepted','target_impossibility_accepted',
    'complete_GCTS_model_accepted','marking_activation_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted')
summary=[]
for sample in samples:
    arm=sample['arm'];state=sample['state'];selection=sample['selection']
    old_plan=read(check(plan['inputs'][arm+'_plan']))
    old_doc=read(check(plan['inputs'][arm+'_prefix']))
    assert old_plan['sources']==contract['original_model_sources']
    assert old_doc['context']['sources']==contract['original_model_sources']
    assert old_doc['context']['language_binding']==original_binding
    assert selection['dead_event_index']==5 and selection['place_event_index']==4
    assert selection['selected_prefix_events']==old_doc['events_prefix'][:6]
    assert old_doc['events_prefix'][5]['decision']=={'kind':'DEAD','row':0}
    assert selection['selected_key']==old_doc['events_prefix'][4]['key']
    assert state['excluded']==[] and len(state['selected'])==1
    assert state['selected'][0]==dict(selection['selected_key'],generation=1)
    assert state['generation']==[[[0,r],0] for r in range(24)]
    assert state['height']==24 and state['input_epoch']==original_binding['language_epoch']
    assert sample['state_sha256']==selection['expected_state_sha256']==hashlib.sha256(canonical(state)).hexdigest()
    assert sample['state_sha256']==old_doc['events_prefix'][4]['state_sha256']==old_doc['events_prefix'][5]['state_sha256']
    assert sample['original_model_binding']==original_binding
    marks=dict((tuple(p),v)for p,v in state['m']);totals=dict((tuple(p),v)for p,v in state['t'])
    assert set(totals)=={(0,r)for r in range(24)} and totals[(0,0)]==0 and totals[(0,23)]==1
    assert marks[(1,0)]==['formula',canonical(sample['literal']).decode()]
    assert marks[(1,23)]==['formula',canonical(declaration['target']).decode()]
    proposal,receipt=sample['fresh_proposal'],sample['fresh_receipt']
    assert proposal['state']==state and proposal['state_sha256']==sample['state_sha256']
    assert proposal['kind']=='NON_IMP_ASSIGNED_PREFIX_COVER' and proposal['complete_cover_proposed'] is True
    assert proposal['row']==0 and proposal['candidates']==[] and proposal['rejections']==[]
    assert proposal['language_binding']==original_binding
    assert proposal['coverage']=={'axiom_labels_seen':sorted(declaration['theory']['axioms']),
        'Gamma_occurrences_seen':list(range(len(declaration['ordered_Gamma']))),'UG_prior_rows_seen':[],'ordered_MP_pairs_seen':[]}
    assert receipt['schema']=='unit-row-degree-evidence-check-v2' and receipt['status']=='ZERO'
    assert receipt['state_sha256']==sample['state_sha256'] and receipt['input_epoch']==state['input_epoch']
    assert receipt['complete_cover_checked'] is receipt['accepted_local_evidence'] is True
    assert type(receipt['row'])is int and receipt['row']==0
    assert type(receipt['degree_exact'])is int and receipt['degree_exact']==0
    assert receipt['candidate_keys']==[] and receipt['sole_candidate'] is None
    assert all(receipt[k]is False for k in('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'))
    pc,pr=sample['projection_certificate'],sample['projection_check']
    assert pc['schema']=='unit-row-row-zero-projection-certificate-v1' and pc['status']=='FORBIDDEN'
    assert pc['literal']==sample['literal'] and pc['row']==0 and pc['height']==24
    assert pc['literal_sha256']==ascii_sha(sample['literal'])
    assert pc['model_authority']['binding']==original_binding
    assert pc['model_authority']['source_bindings']==contract['original_model_sources']
    assert pc['model_authority']['declaration']==declaration
    assert pc['model_authority_sha256']==ascii_sha(pc['model_authority'])
    assert pc['ordered_Gamma_census']==[] and declaration['ordered_Gamma']==[]
    assert [a['name']for a in pc['named_axiom_census']]==sorted(declaration['theory']['axioms'])
    for ax in pc['named_axiom_census']:
        assert ax['formula']==declaration['theory']['axioms'][ax['name']] and ax['equals_demand']is False
        assert ax['primitive_membership']['status']=='MEMBER' and ax['primitive_membership']['binding']==original_binding
    assert [r['rule']for r in pc['rule_exclusions']]==['axiom','assumption','instantiate','eq_subst','mp','generalize']
    assert all(r['excluded']is True for r in pc['rule_exclusions'])
    assert pc['projection']=={'kind':'NO_ORIGINAL_TILE_AT_ROW_ZERO_WITH_THIS_OUTPUT_LITERAL',
        'complete_exact_board_cannot_assign_this_literal_at_output_zero':True,'remote_markings_used':False,
        'selected_placements_used':False,'branch_exclusions_used':False,'saved_ZERO_receipts_used':False}
    assert pr['projection_accepted']is pr['compared_full_certificate']is pr['independently_checked']is True
    assert pr['recomputed_certificate']==pc and pr['certificate_sha256']==ascii_sha(pc)
    assert all(pc[k]is False and pr[k]is False for k in projection_flags)
    assert sample['saved_receipts_accepted']is sample['old_trajectory_accepted']is False
    summary.append({'arm':arm,'state_sha256':sample['state_sha256'],'literal':sample['literal'],
        'local_degree':0,'row0_projection':'FORBIDDEN','projection_certificate_sha256':ascii_sha(pc)})
ax=next(c for c in cases if c['case']=='original-AX-is-not-forbidden')
assert ax['certificate']['status']=='NOT_CERTIFIED' and ax['check']['projection_accepted']is False
assert ax['certificate']['named_axiom_census'][0]['equals_demand']is True
for item in(c for c in cases if c['case'].startswith('projection-forged-')):
    assert item['reason']=='row-zero projection: complete certificate matches original authority/literal/census/six-rule reasons'
for key in('saved_receipts_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
           'failure_marking_activated','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):
    assert cert[key]is False
for key in('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):
    assert result[key]is False
for key in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
           'failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):
    assert body[key]is False
disposition={'schema':'ROOT-row0-failure-certification-disposition-v1',
    'previous_goal_turn':'progress','current_goal_turn':'progress','plan':pp,'outputs':outputs,
    'lossless_transport_concordance':pin(HERE/'ROOT-certification-transport-concordance-v1.json'),
    'complete_wire_verified':True,'native_resources_qualified':True,
    'native_launch_to_postprobe_ns':probe-start,'native_worker_lifetime_ns':terminal-start,
    'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,
    'resource_rule':'single-owned-process-native-terminal-v1; B=T',
    'actual_closed':True,'all_reaped':True,'passed_cases':12,'skipped_cases':0,
    'fresh_local_contexts_accepted':2,'input_scoped_row0_projection_certificates_accepted':2,
    'samples':summary,'original_model_binding':original_binding,
    'reconciliation_scope':'Whole saved literal bytes/response/native/proposal/certificate/census comparisons only; no scientific/model/checker replay.',
    'projection_verification_disclosure':'Fresh full-certificate recomputation uses same trusted structural module; c354 full-context degree check is separately authored.',
    'logical_proof_accepted':False,'target_impossibility_accepted':False,'old_trajectory_accepted':False,
    'failure_marking_activated':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
    'complete_GCTS_model_accepted':False,'broad_goal_complete':False,
    'remaining_gaps':['No marking compiled/activated or graph-pruning gain measured.','Input-scoped row0 lemma only; no arbitrary-row/binder/translation generalization.',
        'Current unit-row specialization lacks full reference conformance and universal fixed Wang palette.','Turtle/Penrose/PA/Hilbert/RL/infinite-plane/substitution goals remain open.']}
p=HERE/'ROOT-certification-disposition-v1.json'
with p.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(p),'passed_cases':12,'local_contexts':2,'projection_certificates':2,
    'native_ns':probe-start,'aggregate_B_bytes':peak,'scientific_replay':False}))
