"""Partial returned43 saved wire/resource consistency only. No semantic replay.

Separately named from the immutable positive closer. Reported PASSED labels
are not independently accepted here. No scientific module is imported/called.
"""
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
mode='advice-controls'
plan_path=HERE/'ROOT-advice-controls-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'advice-controls-owned-v1';external=HERE/'advice-controls-external-v1'
bracket=read(HERE/'ROOT-advice-controls-tool-bracket-v1.json')
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
trace=(external/'meter-stderr.txt').read_bytes();prefix=trace
contract_current=read(check(plan['source_contract']))
control_spec=read(check(contract_current['continuation_progress_successor']['components']['advice_controls']['source_contract']))
spec=control_spec['phase_stderr'];progress_spec=control_spec['continuation_stderr']
lines=prefix.decode('ascii').splitlines();observed=[];sample_values=[];progress=[];native_timeline=[];rebuilt=[];phase_bytes=0;progress_bytes=0
for line in lines:
 if line.startswith(spec['prefix']):
  label,decimal=line.rsplit(' ',1);assert decimal.isascii() and decimal.isdigit() and len(decimal)<=19
  value=int(decimal);assert str(value)==decimal and 0<=value<=9223372036854775807
  observed.append(label);sample_values.append(value);rebuilt.append(label+' '+str(value)+'\n');phase_bytes+=len(rebuilt[-1])
  native_timeline.append({'kind':'phase','marker':label,'native_ns':value})
 else:
  assert line.startswith(progress_spec['prefix'])
  fields=line[len(progress_spec['prefix']):].split(' ');assert len(fields)==7
  stage=fields[0];assert stage in progress_spec['stages']
  nums=[]
  for decimal in fields[1:]:
   assert len(decimal)<=19 and (decimal=='-1' or decimal.isascii() and decimal.isdigit())
   v=int(decimal);assert str(v)==decimal;nums.append(v)
  ordinal,value,row,selected,pending,receipt=nums
  assert ordinal==len(progress)+1 and 1<=ordinal<=24 and 0<=value<=9223372036854775807 and 0<=row<24 and 0<=selected<=24
  assert pending in (0,1) if stage=='DEGREE_AFTER_SNAPSHOT' else pending==-1
  assert receipt in (0,1) if stage=='VALIDATOR_AFTER_DELEGATE' else receipt==-1
  assert 'UNQUALIFIED_PHASE_OBSERVATION P30_BEFORE_CONTINUATION_SEARCH_GROUP' in observed and 'UNQUALIFIED_PHASE_OBSERVATION P30_AFTER_CONTINUATION_SEARCH_GROUP' not in observed
  record={'kind':'continuation','stage':stage,'ordinal':ordinal,'native_ns':value,'row':row,'selected_count':selected,'pending_presence':pending,'receipt_selection':receipt}
  progress.append(record);native_timeline.append(record.copy())
  rebuilt.append(progress_spec['prefix']+stage+' '+' '.join(str(v) for v in nums)+'\n');assert len(rebuilt[-1])<=progress_spec['maximum_ascii_bytes_per_record_by_stage'][stage];progress_bytes+=len(rebuilt[-1])
assert prefix==''.join(rebuilt).encode('ascii') and len(observed)==len(set(observed)) and all(x in spec['ordered_literals'] for x in observed) and [spec['ordered_literals'].index(x) for x in observed]==sorted(spec['ordered_literals'].index(x) for x in observed) and len(observed)<=24 and phase_bytes<=spec['maximum_full_sequence_bytes'] and len(progress)<=progress_spec['total_record_cap'] and progress_bytes<=progress_spec['maximum_continuation_ascii_bytes'] and len(prefix)<=progress_spec['maximum_combined_diagnostic_ascii_bytes']
assert not (external/'postterminal-probe-stderr.txt').read_bytes()
native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
for v in (observation,once):assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes'] and v['invocation_id']==plan['invocation_id']
assert observation['meter_returncode']==observation['probe_returncode']==0
probe=int((external/'postterminal-probe-stdout.txt').read_bytes());assert probe==observation['postterminal_native_probe_ns']
assert native['caller_returncode']==native['wait4_status']==0 and native['all_reaped'] is True
assert native['caller_pid']==native['wait4_pid'] and native['error'] is None and native['interrupted'] is False and native['cancellation_forwarded'] is False
start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns'];g=body['joint_began_ns']
assert all(start<=x['native_ns']<=terminal for x in native_timeline) and [x['native_ns'] for x in native_timeline]==sorted(x['native_ns'] for x in native_timeline)
for i,x in enumerate(native_timeline):
 x['elapsed_from_launch_ns']=x['native_ns']-start;x['interval_since_previous_ns']=x['native_ns']-(native_timeline[i-1]['native_ns'] if i else start)
assert start<=g<terminal<=probe and body['joint_deadline_ns']==g+20000000000
assert terminal-start==native['caller_kernel_elapsed_ns'] and 0<probe-start<20000000000
peak=native['wait4_usage'][2];assert type(peak) is int and peak==native['caller_kernel_peak_bytes'] and 0<peak<=536870912
transport=read(HERE/'ROOT-advice-controls-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));controls=result['controls'];cases=controls['cases']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert result['purpose']=='unit-row-advised-advice-controls' and result['search'] is None and result['found_validation'] is None
contract=control_spec
base_fibres=read(HERE.parent/'unit-row-compatible-fibres-controls-source-20261016/Source-contract-v1.json')
prior=read(HERE.parent/'unit-row-fair-interface-cold-ROOT-source-20261016/Source-contract-v5.json')
prior_names=prior['fair_interface_successor']['cases'];fibre_names=base_fibres['new_cases'];case_names=prior_names+fibre_names
assert case_names==contract['all_case_names'] and contract['API']['expected_cases']==43
new_quality_names=read(HERE.parent/'unit-row-fair-interface-controls-source-20261016/Source-contract-v1.json')['new_cases']
assert controls['schema']=='unit-row-goal-advice-controls-v1' and controls['all_declared_cases_completed'] is True
assert [x['case'] for x in cases]==case_names and len(cases)==43 and len(prior_names)==40 and len(fibre_names)==3
assert all(x['status'] in ('PASSED','SKIPPED') for x in cases)
passed=sum(x['status']=='PASSED' for x in cases);skipped=sum(x['status']=='SKIPPED' for x in cases)
assert controls['passed']==passed and controls['skipped']==skipped and passed+skipped==43
assert controls['unqualified_consumer_gates']==[x['case'] for x in cases if x['status']=='SKIPPED']
qualified=skipped==0 and controls['additional_coverage_gaps']==[]
assert controls['all_advice_consumer_gates_qualified'] is qualified
art=controls['artifacts'];by={x['case']:x['observed'] for x in cases}
def sha(x):return hashlib.sha256(canonical(x)).hexdigest()
# Complete returned data may still have essential gaps. Never execute the
# positive closer, infer missing lifecycle evidence, or promote reported labels.
assert len(plan['sources'])==17 and len(plan['inputs'])==2
assert contract_current['sources']==plan['sources'] and contract_current['inputs']==plan['inputs'] and contract_current['limits']==plan['limits']
assert contract_current['Review_ABI']['sources']==plan['sources'] and contract_current['Review_ABI']['source']==plan['sources']['intake']
assert type(controls['declared_cases']) is int and controls['declared_cases']==43
assert type(controls['passed']) is type(controls['skipped']) is int
assert all(set(x)=={'case','status','observed','scope'} for x in cases)
assert all(type(x['case']) is str and type(x['status']) is str and type(x['observed']) is dict and type(x['scope']) is str for x in cases)
assert all(type(x['observed'].get('reason')) is str and x['observed']['reason'] for x in cases if x['status']=='SKIPPED')
assert type(controls['additional_coverage_gaps']) is list
assert all(type(x) is str and x for x in controls['additional_coverage_gaps'])
assert skipped>0 or controls['additional_coverage_gaps']
assert qualified is False and controls['all_advice_consumer_gates_qualified'] is False
assert result['complete_GCTS_model_accepted'] is False and result['GCTS_search_trajectory_accepted'] is False and result['logical_proof_accepted'] is False and result['ROOT_resource_accepted'] is False
assert all(body[k] is False for k in ('ROOT_resource_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','RL_accepted','GCTS_advantage_claimed'))
strong=('logical_proof_accepted','exact_point_board_accepted','degree_or_EOF_accepted','scheduler_accepted','complete_GCTS_model_accepted','trajectory_accepted','learned_marking_accepted','RL_accepted','ROOT_resource_accepted')
assert all(controls[k] is False for k in strong)
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()
remote_names=('remote-mark-invalidates-pending-key','rejected-pending-hint-preserves-canonical-choice')
case_records={x['case']:x for x in cases}
assert case_records[remote_names[0]]['status']==case_records[remote_names[1]]['status']
remote_join={'artifact_present':'remote_eligibility' in art,'engine_lifecycle_accepted':False,'component_is_scheduler_authority':False,'scientific_replay':False}
if 'remote_eligibility' in art:
 calibration=art['remote_eligibility'];before=calibration['before_decision'];after=calibration['after_decision']
 req=calibration['component_request'];rec=calibration['component_receipt'];bad=calibration['bad_key'];remote=calibration['remote'];decision=calibration['actual_global_decision']
 original=art['fixture'];original_inner=art['genuine_inner_snapshot'];family=original_inner['pending_preferences']
 assert calibration['schema']=='unit-row-remote-rejection-eligibility-v1' and calibration['original_fixture_ref']=='fixture'
 assert calibration['component_decision_is_scheduler_authority'] is False
 assert type(calibration['eligible_actual_branch']) is bool and type(calibration['normal_search_started']) is bool
 assert canonical(bad) in {canonical(k) for k in family['pending_keys']}
 assert canonical(before['pending_preferences'])==canonical(family)==canonical(after['pending_preferences'])
 assert canonical(before['state'])==canonical(after['state'])
 assert canonical(before['state']['selected'])==canonical(original_inner['state']['selected']+[remote['selection_record']])
 assert canonical(original_inner['state'])==canonical(art['adoption_search']['last_observed_state'])
 assert art['adoption_search']['root_snapshot_sha256']==art['adoption_search']['final_snapshot_sha256']
 assert by['first-search-exact-root-restoration']['before_sha256']==by['first-search-exact-root-restoration']['after_sha256']
 assert canonical(by['public-rollback-restores-genuine-nonempty-pending']['actual_pending_keys'])==canonical(family['pending_keys'])
 assert before['state']['input_epoch']==after['state']['input_epoch']==body['language_binding']['language_epoch']
 assert req=={'schema':'unit-row-pending-preference-request-v1','binding':body['language_binding'],'state_sha256':sha(before['state']),'decision':{'kind':'BRANCH','row':bad['translation'][1]},'family_id':family['family_id'],'keys':[bad]}
 assert rec['schema']=='unit-row-advice-validation-v1' and rec['mode']=='PENDING_KEYS' and rec['selection'] is None
 assert rec['binding']==body['language_binding'] and rec['decision']==req['decision'] and rec['state_sha256']==sha(before['state']) and rec['input_sha256']==sha(req)
 assert rec['rejections']==[{'key':bad,'reason':'whole_remote_or_metadata_mark_conflict'}] and all(rec[k] is False for k in strong)
 assert type(decision) is dict and decision['kind'] in ('DEAD','FORCED','BRANCH','UNKNOWN','SOLVED')
 eligible=decision=={'kind':'BRANCH','row':bad['translation'][1]}
 assert calibration['eligible_actual_branch'] is eligible and calibration['normal_search_started'] is eligible
 if not eligible:
  assert type(calibration['eligibility_gap']) is str and calibration['eligibility_gap']
  assert all(case_records[name]['status']=='SKIPPED' and case_records[name]['observed']['reason']==calibration['eligibility_gap'] for name in remote_names)
  assert all(name not in art for name in ('remote_search','remote_receipts','remote_fixture'))
 else:
  assert 'eligibility_gap' not in calibration
  if case_records[remote_names[0]]['status']=='PASSED':
   search=art['remote_search'];fixture=art['remote_fixture'];receipts=art['remote_receipts']
   assert canonical(fixture['before'])==canonical(after) and canonical(fixture['remote'])==canonical(remote) and canonical(fixture['invalidated_pending_key'])==canonical(bad)
   assert search['status']=='UNKNOWN' and search['found'] is None and search['root_restored'] is True and search['stack_restored'] is True
   assert search['root_snapshot_sha256']==search['final_snapshot_sha256']==sha(after) and not any(e['kind']=='EXCLUDE' for e in search['events'])
   assert any(canonical(x['key'])==canonical(bad) and x['reason']=='whole_remote_or_metadata_mark_conflict' for r in receipts for x in r['rejections'])
  else:
   assert all(name not in art for name in ('remote_search','remote_receipts','remote_fixture'))
 remote_join.update(actual_global_decision=decision,eligible_actual_branch=eligible,normal_search_started=calibration['normal_search_started'],family_id=family['family_id'],bad_key=bad,before_state_sha256=sha(before['state']),after_state_sha256=sha(after['state']),component_request_sha256=sha(req),component_receipt_sha256=sha(rec),whole_artifact_sha256=sha(calibration),source_artifact='controls.artifacts.remote_eligibility',literal_joins_verified=True)
else:
 assert all(case_records[name]['status']=='SKIPPED' for name in remote_names)
 assert all(name not in art for name in ('remote_search','remote_receipts','remote_fixture'))
 remote_join['reason']='No saved remote calibration artifact; use the exact SKIP reasons, never infer a component or live lifecycle.'
# Positive aliases are deliberately absent unless a real sibling selection was
# observed. A full returned UNKNOWN remains raw diagnostic evidence only.
paired_join={'artifact_present':'pending_success_fixture' in art,'pending_selection_accepted_here':False}
if 'pending_success_fixture' in art:
 sibling=art['pending_success_fixture'];observed=sibling['pending_selection_observed']
 assert sibling['schema']=='unit-row-paired-pending-success-fixture-v1' and type(observed) is bool
 paired_join.update(pending_selection_observed=observed,whole_artifact_sha256=sha(sibling),source_artifact='controls.artifacts.pending_success_fixture')
 if observed:
  lineage=art['pending_continuation_lineage'];continuation=art['pending_continuation_search'];inner=sibling['inner_snapshot']
  assert sibling['eligibility_qualified'] is True and sibling['no_future_preinstallation'] is True
  assert lineage=={'fixture_ref':'pending_success_fixture','family_id':inner['pending_preferences']['family_id'],'inner_snapshot_sha256':sha(inner),'original_fixture_used':False}
  assert canonical(sibling['continuation_search'])==canonical(continuation)
  assert canonical([x['receipt'] for x in sibling['pending_calls']])==canonical(art['pending_selection_receipts'])
  assert any(r['selection'] is not None for r in art['pending_selection_receipts'])
  assert continuation['root_restored'] is True and continuation['stack_restored'] is True and continuation['root_snapshot_sha256']==continuation['final_snapshot_sha256']==sha(sibling['continuation_before'])
 else:
  assert all(name not in art for name in ('pending_continuation_search','pending_selection_receipts','pending_continuation_lineage'))
  assert case_records['pending-key-real-current-row-selection']['status']=='SKIPPED'
coverage=[{'case':x['case'],'reported_status':x['status'],'reason':x['observed']['reason']} for x in cases if x['status']=='SKIPPED']
output={'schema':'ROOT-advice-consumer-controls-partial-disposition-v15','status':'COMPLETE_RETURNED43_PARTIAL_CONTROLS_TARGETS_NOT_ADMITTED','plan':pp,'sources':plan['sources'],'inputs':plan['inputs'],'source_contract':plan['source_contract'],'controls_accepted':False,'target_admission_qualified':False,'all_advice_consumer_gates_qualified':False,'declared_cases':43,'reported_passed_cases':passed,'reported_skipped_cases':skipped,'all_case_labels':case_names,'case_statuses':[{'case':x['case'],'reported_status':x['status']} for x in cases],'essential_gaps':coverage,'additional_coverage_gaps':controls['additional_coverage_gaps'],'reported_PASSED_semantics_accepted_here':False,'full_returned_record_retained':True,'complete_wire_verified':True,'full_raw_evidence':{'outputs':outputs,'expanded_result':transport['expanded_file'],'transport_concordance':pin(HERE/'ROOT-advice-controls-transport-concordance-v1.json'),'native_terminal':pin(external/'native-terminal.json'),'observation':pin(external/'observation.json'),'tool_bracket':pin(HERE/'ROOT-advice-controls-tool-bracket-v1.json')},'remote_calibration_saved_concordance':remote_join,'paired_saved_alias_concordance':paired_join,'artifact_keys':sorted(art),'unqualified_native_timeline':native_timeline,'unqualified_continuation_observations':progress,'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'complete_Date_seconds':date,'all_reaped':True,'actual_closed':True,'positive_closer14_used':False,'proof_search_or_target_result_accepted':False,'scientific_replay':False,'author_identity':'/root/arithmetic_induction','author_overlap':'Author owns adviser/engine/c354 and saved-only positive closer14. This partial helper performs literal saved-wire/resource/metadata concordance only; no independent scientific replay or own-dependency proof acceptance.','scope':'Only complete returned current43 records with essential SKIPs/additional gaps; exact raw record remains authoritative. Component-shaped pending rejection is not a global engine rejection/branch/rollback test; absent tests are not inferred. Native/wire closure does not qualify controls, target, trajectory, learned marking or RL.'}
output.update({k:False for k in strong})
q=HERE/'ROOT-advice-controls-partial-disposition-v1.json'
with q.open('x') as f:json.dump(output,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'reported_passed':passed,'reported_skipped':skipped,'controls_accepted':False,'target_admission_qualified':False}))
