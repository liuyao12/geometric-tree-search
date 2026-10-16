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
mode='stageA'
plan_path=HERE/'ROOT-stageA-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'stageA-owned-v1';external=HERE/'stageA-external-v1'
bracket=read(HERE/'ROOT-stageA-tool-bracket-v1.json')
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
transport=read(HERE/'ROOT-stageA-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));data=result['channel4_stageA'];contract=read(check(plan['source_contract']))
assert len(plan['sources'])==11 and len(plan['inputs'])==8 and plan['purpose']=='unit-row-channel4-degree-cursor-controls'
assert result['sources']==plan['sources']and result['inputs']==plan['inputs']and result['purpose']==plan['purpose']
assert contract['sources']==plan['sources']and contract['inputs']==plan['inputs']
binding=contract['original_model_binding']
assert result['language_binding']==body['language_binding']==body['original_model_binding']==binding
assert body['version']=='unit-row-channel4-degree-cursor-cold-v2-guarded-sizes'
assert result['controls']is result['search']is result['found_validation']is None
assert data['schema']=='ROOT-unit-row-channel4-stageA-payload-v1'and data['stage']=='DEGREE_FILTER_ORDERED_CURSOR_EOF_ONLY'
assert data['original_model_sources']==contract['original_model_sources']and data['original_model_binding']==binding
for ref in contract['original_model_sources'].values():check(ref)
assert data['control_count']==23 and len(data['controls'])==23 and data['all_controls_completed']is True
assert [c['case']for c in data['controls']]==data['expected_cases']==contract['expected_cases']
assert all(c['status']=='PASSED'for c in data['controls'])
assert data['carriers']=={'proposer':[['bot']],'independent':[['bot']]}
old=read(check(plan['inputs']['marking_expanded']))['marking_data'];accepted=read(check(plan['inputs']['marking_disposition']))
assert data['marking']==old['marking']and data['marking']['marking_id']==accepted['marking_id']
assert hashlib.sha256(canonical(data['marking'])).hexdigest()==accepted['marking_sha256']
assert data['definition_check']['marking_checked']is True and data['definition_check']['marking']==data['marking']
assert data['root_state']['selected']==[]and data['root_state']['excluded']==[]
assert [[4,0],0]in data['root_state']['m']
expected={'UG-many':('MANY','MANY',2,2,2),'UG-one':('SINGLETON','SINGLETON',1,1,2),
 'UG-zero':('ZERO','ZERO',0,0,2),'deep43-zero':('ZERO','ZERO',0,0,2),
 'target-complete-filtered-zero':('SINGLETON','ZERO',1,0,1),
 'deep42-row2':('TWO_OR_MORE','UNKNOWN',2,1,2),'deep42-row3':('TWO_OR_MORE','UNKNOWN',2,0,3)}
assert set(data['fixtures'])==set(expected)
summary=[]
for name,(base_status,status,offered,survived,row)in expected.items():
 f=data['fixtures'][name];p=f['proposal'];r=f['receipt'];base=f['base_state'];state=f['state'];original=p['original_proposal']
 assert f['row']==p['row']==r['row']==row
 assert p['state']==state and original['state']==base
 assert p['state_sha256']==r['state_sha256']==hashlib.sha256(canonical(state)).hexdigest()
 assert original['state_sha256']==r['original_base_receipt']['state_sha256']==hashlib.sha256(canonical(base)).hexdigest()
 assert p['language_binding']==original['language_binding']==binding
 assert r['status']==status and r['original_base_receipt']['status']==base_status
 assert len(original['candidates'])==offered and len(p['candidates'])==survived
 assert r['candidate_keys']==[x['placement_key']for x in p['candidates']]
 assert r['marking_id']==p['marking_id']==state['marking_id']==data['marking']['marking_id']
 if status=='UNKNOWN':
  assert r['complete_cover_checked']is False and r['degree_exact']is None and r['sole_candidate']is None and r['accepted_local_evidence']is False
 else:
  assert r['complete_cover_checked']is True and r['degree_exact']==survived and r['accepted_local_evidence']is True
 for rejection in p['marked_rejections']:
  assert rejection['reason']=='whole_remote_or_metadata_mark_conflict'
  assert rejection['conflicting_points']==[[[4,0],0,1]]
 assert len(p['marked_rejections'])==offered-survived
 summary.append(dict(fixture=name,row=row,original_status=base_status,marked_status=status,
  original_offered=offered,marked_survivors=survived,complete_cover_checked=r['complete_cover_checked']))
assert data['fixtures']['target-complete-filtered-zero']['state']['excluded']==[]
stream_counts={'UG-many':(2,2,'MANY'),'UG-one':(1,1,'SINGLETON'),'UG-zero':(0,0,'ZERO'),
 'target-complete-filtered-zero':(1,0,'ZERO'),'deep42-row2':(2,1,None),'deep42-row3':(6,4,None)}
assert set(data['cursors'])==set(stream_counts)
stream_summary=[]
for name,(original_count,marked_count,status)in stream_counts.items():
 s=data['cursors'][name];f=data['fixtures'][name]
 assert s['fixture_ref']==name and s['state']==f['state']and s['base_state']==f['base_state']and s['row']==f['row']
 oe,me=s['original_events'],s['marked_events']
 assert len(oe)==original_count+1 and len(me)==marked_count+1 and oe[-1]['kind']==me[-1]['kind']=='EOF'
 assert [e['ordinal']for e in oe[:-1]]==list(range(original_count))and [e['ordinal']for e in me[:-1]]==list(range(marked_count))
 assert all(e['kind']=='CANDIDATE'for e in oe[:-1]+me[:-1])
 assert s['marked_context']['original_context']==s['original_context']
 assert s['marked_context']['state']==s['state']and s['original_context']['state']==s['base_state']
 assert me[-1]['completion']['original_completion']==oe[-1]['completion']
 assert me[-1]['completion']['yielded_candidates']==marked_count and oe[-1]['completion']['yielded_candidates']==original_count
 receipt=s['fresh_cover_receipt']
 if status is None:assert receipt is None
 else:
  assert receipt['status']==status and receipt['complete_cover_checked']is True and receipt['degree_exact']==marked_count
  assert {canonical(x['placement_key'])for x in [e['candidate']for e in me[:-1]]}=={canonical(k)for k in receipt['candidate_keys']}
 stream_summary.append(dict(fixture=name,original_cursor_count=original_count,marked_cursor_count=marked_count,fresh_complete_cover_status=status))
for key in ('later_graph_dependency_retention_rollback_scheduler_qualified','target_search_performed','failure_marking_activated',
 'engine_search_performed','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted',
 'GCTS_search_trajectory_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):assert data[key]is False
for key in ('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'):assert result[key]is False
for key in ('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
 'failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):assert body[key]is False
disposition=dict(schema='ROOT-channel4-stageA-disposition-v1',previous_goal_turn='progress',current_goal_turn='progress',
 plan=pp,outputs=outputs,lossless_transport_concordance=pin(HERE/'ROOT-stageA-transport-concordance-v1.json'),
 complete_wire_verified=True,native_resources_qualified=True,native_launch_to_postprobe_ns=probe-start,
 native_worker_lifetime_ns=terminal-start,aggregate_B_bytes=peak,terminal_T_bytes=peak,complete_Date_seconds=date,
 resource_rule='single-owned-process-native-terminal-v1; B=T',actual_closed=True,all_reaped=True,passed_cases=23,skipped_cases=0,
 local_degree_cursor_controls_accepted=True,fixture_count=7,cursor_contexts=6,fixtures=summary,cursors=stream_summary,
 marking_id=data['marking']['marking_id'],original_model_binding=binding,
 reconciliation_scope='Whole saved bytes/native/wire/proposal/receipt/context/candidate-key joins only; no matcher/model/checker or scientific replay.',
 later_engine_stages_qualified=False,target_search_performed=False,logical_proof_accepted=False,RL_accepted=False,
 GCTS_advantage_claimed=False,complete_GCTS_model_accepted=False,broad_goal_complete=False,
 remaining_gaps=['Possible-support transitions, reference counts, retained archives and exact rollback controls remain pending.',
  'Global engine decisions and UNKNOWN-child restoration remain unqualified.',
  'No marked target proof, matched search advantage, trained RL, full reference conformance or universal finite Wang palette.'])
p=HERE/'ROOT-stageA-disposition-v1.json'
with p.open('x')as f:json.dump(disposition,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(dict(disposition=pin(p),passed_cases=23,fixtures=7,cursor_contexts=6,native_ns=probe-start,aggregate_B_bytes=peak,scientific_replay=False)))
