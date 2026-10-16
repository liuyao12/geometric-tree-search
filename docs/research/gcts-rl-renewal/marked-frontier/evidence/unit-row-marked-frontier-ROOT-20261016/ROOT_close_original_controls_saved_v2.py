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
mode='original-controls'
plan_path=HERE/'ROOT-original-controls-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'original-controls-owned-v1';external=HERE/'original-controls-external-v1'
bracket=read(HERE/'ROOT-original-controls-tool-bracket-v1.json')
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
transport=read(HERE/'ROOT-original-controls-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));controls=result['controls'];cases=controls['cases']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert controls['all_declared_cases_completed'] is True
assert len(cases)==23 and len({c['case'] for c in cases})==23
passed=[c for c in cases if c['status']=='PASSED'];skipped=[c for c in cases if c['status']=='SKIPPED']
assert len(passed)==23 and not skipped
expected=['late-global-ZERO-before-earlier-singleton','global-forced-before-branch',
 'real-EOF-singleton-without-independent-cover-UNKNOWN','real-EOF-singleton-current-cover-FORCED',
 'interrupted-zero-prefix-not-ZERO','interrupted-one-prefix-not-SINGLETON','unseen-remote-key-invalidated',
 'remote-singleton-stream-cover-key-agreement','omitted-stream-survivor-rejected',
 'rollback-revives-unseen-key-and-cursor-position','exact-ordered-child-alternatives-and-restoration',
 'assumed-exclusions-change-context-not-universe','UNKNOWN-child-never-excluded',
 'callback-exhaustion-poisons-real-cursor','abort-poisons-real-cursor',
 'synthetic-varied-generation-and-ROW-TIE','synthetic-global-priority-with-UNKNOWN']
assert [c['case'] for c in cases[:17]]==expected
by={c['case']:c['observed'] for c in cases}
late=by[expected[0]];assert late['decision']=={'kind':'DEAD','row':2}
certs=dict(late['after']['certificates']);assert certs[0]['status']=='SINGLETON' and certs[2]['status']=='ZERO'
assert late['before']['state']==late['after']['state']
assert by[expected[1]]['decision']['kind']=='FORCED' and by[expected[1]]['decision']['row']==0
noauthority=by[expected[2]];assert noauthority['decision']['kind']=='UNKNOWN'
assert len(dict(noauthority['snapshot']['cursors'])[0]['keys'])==1
assert dict(noauthority['snapshot']['cursors'])[0]['completion']['independently_checked'] is False
assert by[expected[3]]['decision']['kind']=='FORCED'
for index,count in ((4,0),(5,1)):
 o=by[expected[index]];assert o['exception_type']=='CallbackExhausted'
 assert sum(e['kind']=='CANDIDATE' for e in o['actual_cursor_events'])==count
 assert not any(e['kind']=='EOF' for e in o['actual_cursor_events'])
remote=by[expected[6]];assert remote['after']['revision']==remote['before']['revision']+1
assert all(b==a+1 for a,b in zip(remote['before']['row_versions'],remote['after']['row_versions']))
assert remote['after']['cursors']==remote['after']['certificates']==remote['after']['exposed_candidates']==[]
assert 'whole original point legality' in remote['stale_reverse_rejection']['reason']
sole=by[expected[7]];receipt=sole['independent_receipt']
assert receipt['status']=='SINGLETON' and receipt['complete_cover_checked'] is True and receipt['missing_mark_cover_checked'] is True
assert receipt['state_sha256']==hashlib.sha256(canonical(sole['state'])).hexdigest()
assert receipt['input_epoch']==body['language_binding']['language_epoch']
assert receipt['candidate_keys']==[sole['checked_candidates'][0]['placement_key']]
assert by[expected[8]]['exception_type']=='ValueError' and 'complete cover agrees' in by[expected[8]]['reason']
restored=by[expected[9]];assert restored['restored']==remote['before'] and restored['cursor_replays_observed']>=1
assert restored['second']['kind']=='CANDIDATE' and restored['EOF']['kind']=='EOF'
children=by[expected[10]]['children'];assert len(children)==2
for c in children:
 assert c['decision']['kind']=='DEAD' and c['before']==c['restored']
assert len({canonical(c['alternative']['candidate']['placement_key']) for c in children})==2
u=by[expected[12]];r=u['bounded_search_result'];assert r['status']=='UNKNOWN' and r['found'] is None
assert r['root_restored'] is True and r['stack_restored'] is True and u['before']==u['restored']
assert r['root_snapshot_sha256']==r['final_snapshot_sha256']==hashlib.sha256(canonical(u['before'])).hexdigest()
assert r['counts']['branches']>=1 and r['counts']['placements']>=1
assert any(e['kind']=='TRY' for e in r['events']) and not any(e['kind']=='EXCLUDE' for e in r['events'])
assert r['trace_complete'] is False and r['last_observed_state']['selected']
for c in cases:
 if c['case'].startswith('synthetic-'):assert 'NONLOGICAL' in c['scope']
assert controls['original_height']==24 and controls['original_root_generations']==0
assert all(controls[k] is False for k in ('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted',
 'exact_point_board_accepted','GCTS_advantage_accepted','trajectory_accepted','RL_accepted','ROOT_resource_accepted'))
assert result['purpose']=='unit-row-advised-original-controls' and result['search'] is None and result['found_validation'] is None
assert result['search_work_bounds']=={'maximum_nodes':128,'maximum_events':2000}
# Six added policy cases are saved literal observations. Never replay degree,
# membership, a point model, or a primitive word in this closer.
contract_current=read(check(plan['source_contract']))
assert len(plan['sources'])==17 and len(plan['inputs'])==2
assert contract_current['sources']==plan['sources'] and contract_current['inputs']==plan['inputs'] and contract_current['limits']==plan['limits']
assert contract_current['Review_ABI']['sources']==plan['sources'] and contract_current['Review_ABI']['source']==plan['sources']['intake']
policy_spec=contract_current['marked_frontier_successor']
control_contract=read(check(policy_spec['components']['controls']['source_contract']))
assert policy_spec['components']['controls']['source']==plan['sources']['controls'] and policy_spec['components']['engine']['source']==plan['sources']['engine']
added=[x['case'] for x in control_contract['additional_cases']]
assert len(added)==6 and [x['case'] for x in cases]==expected+added
assert controls['schema']=='unit-row-lazy-global-controls-v1' and controls['version']==control_contract['result']['version']
assert controls['original_case_count']==17 and controls['new_policy_case_count']==6 and controls['prospective_case_count']==23
assert policy_spec['original_control_cases']==23 and policy_spec['retention_control_cases']==17 and policy_spec['advice_control_cases']==43
assert controls['variant']=='ROW-BASELINE-AND-ASSIGNED-OUTPUT-BRANCH-TIE-CONTROLS'
assert all(result[k] is False for k in ('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'))
assert all(body[k] is False for k in ('ROOT_resource_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','RL_accepted','GCTS_advantage_claimed'))
mark='ASSIGNED-OUTPUT-THEN-ROW'
def policy(snapshot,mode):
 p=snapshot['scheduler_policy']
 assert set(p)=={'schema','branch_tie','authority_sha256','policy_sha256'}
 assert p['schema']=='unit-row-owned-branch-tie-policy-v1' and p['branch_tie']==mode and p['authority_sha256']==snapshot['authority_sha256']
 for k in ('authority_sha256','policy_sha256'):
  assert type(p[k]) is str and len(p[k])==64 and all(c in '0123456789abcdef' for c in p[k])
 assert snapshot['state']['generation']==[[[0,r],0] for r in range(24)]
 assert snapshot['state']['input_epoch']==body['language_binding']['language_epoch']
 return p
abstract=by[added[0]]
assert abstract['abstract_evidence']=={'0':{'status':'MANY','degree_exact':10},'1':{'status':'MANY','degree_exact':2},'2':{'status':'TWO_OR_MORE','degree_exact':None}}
assert abstract['earlier_generation']=={'kind':'BRANCH','row':0} and abstract['assigned_same_generation']=={'kind':'BRANCH','row':2}
assert abstract['two_assigned']=={'kind':'BRANCH','row':1} and abstract['all_absent']=={'kind':'BRANCH','row':0}
priority=by[added[1]]
assert priority=={'dead':{'kind':'DEAD','row':1},'forced':{'kind':'FORCED','row':1},'unresolved':{'kind':'UNKNOWN','row':None,'unresolved_rows':[1]}}
assert all('NONLOGICAL' in c['scope'] for c in cases[17:19])
comparison=by[added[2]];initial=comparison['initial_state'];seeds=comparison['seed'];row_snapshot=comparison['ROW_snapshot'];warm=comparison['MARK_snapshot']
assert len(seeds)==4 and [x['placement_key']['translation'] for x in seeds]==[[0,1],[0,2],[0,4],[0,7]]
assert canonical(initial['selected'])==canonical([x['selection_record'] for x in seeds])
assert canonical(row_snapshot['state'])==canonical(initial)==canonical(warm['state'])
assert comparison['ROW_decision']=={'kind':'BRANCH','row':0} and comparison['MARK_decision']=={'kind':'BRANCH','row':3}
row_policy=policy(row_snapshot,'ROW');mark_policy=policy(warm,mark)
assert row_policy['authority_sha256']==mark_policy['authority_sha256']
declaration=read(check(plan['inputs']['declaration']));first_ax=sorted(declaration['theory']['axioms'])[0];formula=declaration['theory']['axioms'][first_ax]
for seed in seeds[:2]:
 pre=seed['placement_key']['type_preimage'];assert pre['primitive_witness']=={'rule':'axiom','name':first_ax,'formula':formula}
 assert pre['ordered_premise_formulas']==pre['ordered_offsets']==[]
 assert canonical(seed['selection_record'])==canonical(dict(seed['placement_key'],generation=1))
for seed,read_row in zip(seeds[2:],(3,6)):
 pre=seed['placement_key']['type_preimage'];w=pre['primitive_witness']
 assert w['rule']=='generalize' and pre['ordered_offsets']==[-1] and len(pre['ordered_premise_formulas'])==1
 assert seed['placement_key']['translation'][1]-1==read_row and w['formula'][0]=='all'
 assert canonical(w['formula'][2])==canonical(pre['ordered_premise_formulas'][0])
marks={tuple(p):v for p,v in initial['m']};totals={tuple(p):v for p,v in initial['t']}
assert (1,0) not in marks and marks[(1,3)]==marks[(1,6)]==['formula',canonical(seeds[2]['placement_key']['type_preimage']['ordered_premise_formulas'][0]).decode()]
assert all(totals[(0,r)]==0 for r in (0,3,6))
assert marks[(1,23)]==['formula',canonical(declaration['target']).decode()]
certificates=dict(warm['certificates']);assert set(certificates)=={r for r in range(24) if totals[(0,r)]==0}
assert all(x['status'] in ('MANY','TWO_OR_MORE') for x in certificates.values())
readonly=by[added[3]]
assert canonical(readonly['warm'])==canonical(warm)==canonical(readonly['repeated_snapshot'])==canonical(readonly['restored_warm'])
assert canonical(readonly['cold']['state'])==canonical(initial) and readonly['repeated_decision']==comparison['MARK_decision']
assert policy(readonly['cold'],mark)==mark_policy
retie=by[added[4]];fill=retie['fill'];changed=retie['changed'];classified=retie['classified']
assert retie['next_decision']=={'kind':'BRANCH','row':6} and retie['restored_decision']==comparison['MARK_decision']
assert fill['placement_key']['translation']==[0,3] and fill['placement_key']['type_preimage']['primitive_witness']['rule']=='generalize'
assert fill['placement_key']['type_preimage']['ordered_offsets']==[-2]
assert canonical(fill['placement_key']['type_preimage']['ordered_premise_formulas'])==canonical([formula])
assert canonical(changed['state']['selected'])==canonical(initial['selected']+[fill['selection_record']])
assert canonical(classified['state'])==canonical(changed['state']) and canonical(retie['restored'])==canonical(warm)
assert dict((tuple(p),v) for p,v in changed['state']['t'])[(0,3)]==1 and dict((tuple(p),v) for p,v in changed['state']['t'])[(0,6)]==0
assert policy(changed,mark)==policy(classified,mark)==mark_policy
observed_priority=by[added[5]]['decisions'];assert len(observed_priority)==2
for record,decision in zip(observed_priority,({'kind':'DEAD','row':2},{'kind':'FORCED','row':0})):
 assert {k:record['decision'][k] for k in ('kind','row')}==decision and canonical(record['before']['state'])==canonical(record['after']['state'])
 assert policy(record['before'],mark)==policy(record['after'],mark)==mark_policy
actual_dead=dict(observed_priority[0]['after']['certificates']);actual_forced=dict(observed_priority[1]['after']['certificates'])
assert actual_dead[0]['status']=='SINGLETON' and actual_dead[2]['status']=='ZERO' and actual_forced[0]['status']=='SINGLETON'
assert canonical(observed_priority[1]['decision']['candidate'])==canonical(actual_forced[0]['sole_candidate'])
policy_evidence={'old17_checks_preserved':True,'new_policy_case_names':added,'default_ROW_and_MARK_saved_joined':True,'ROW_initial_row':0,'MARK_initial_row':3,'MARK_after_fill_row':6,'MARK_after_rollback_row':3,'fixed24_root_generations':0,'new_cases_are_separate':True,'synthetic_cases_nonlogical':True,'original_language_cases_not_a_search_trajectory':True,'whole_warm_snapshot_restored':True,'scientific_replay':False}

result_out={'schema':'ROOT-unit-row-global-engine-controls-disposition-v2-original23','plan':pp,'outputs':outputs,
 'controls_accepted':True,'passed_cases':23,'skipped_cases':0,'complete_wire_verified':True,'native_resources_qualified':True,
 'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'terminal_T_bytes':peak,
 'complete_Date_seconds':date,'language_binding':body['language_binding'],'resource_rule':'single-owned-process-native-terminal-v1; B=T',
 'scope':'Current original23 = seventeen preserved ROW controls plus six separately counted marking-aware BRANCH tie controls. Literal full snapshots/current receipts/native wire only, no model/degree/word replay, target result or full search trajectory.',
 'conformance_gaps':['Current sufficient retention with conservative global-ledger invalidation, no full reference conformance.','General all-six independent EOF/exhaustion certifier absent.','Specialized24unit rows only.'],
 'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'logical_proof_accepted':False,'GCTS_marking_activated':False,
 'RL_accepted':False,'GCTS_advantage_claimed':False,'broad_goal_complete':False,'previous_goal_turn':'progress',
 'old_UNKNOWNs_and_finite_negative_preserved':True,'reconciliation_scope':'Whole saved raw bytes, complete receipts/wire/native/caller metadata only; no Source/kernel/checker/model/word/degree replay.'}
result_out['policy_evidence']=policy_evidence
result_out['original_case_count']=17;result_out['new_policy_case_count']=6
result_out['author_identity']='/root/arithmetic_induction'
result_out['author_overlap']='Author owns inherited engine8/adviser/c354/transition and earlier saved closers, not engine9/originalcontrols2/Rootcaller17; no independent semantic replay or own scientific acceptance.'
result_out['lossless_transport_concordance']=pin(HERE/'ROOT-original-controls-transport-concordance-v1.json')
out=HERE/'ROOT-original-controls-disposition-v1.json'
with out.open('x') as f:json.dump(result_out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'disposition':pin(out),'passed':len(passed),'skipped':len(skipped),
    'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date}))
