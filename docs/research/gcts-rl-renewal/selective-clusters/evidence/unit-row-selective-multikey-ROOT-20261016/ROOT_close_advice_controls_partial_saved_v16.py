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
# Saved literal C joins only. These routines never call a scientific endpoint.
def C_component(component,key,family_id,binding,*,rejected):
 st=component['state'];decision={'kind':'BRANCH','row':key['translation'][1]}
 request={'schema':'unit-row-pending-preference-request-v1','binding':binding,'state_sha256':sha(st),'decision':decision,'family_id':family_id,'keys':[key]}
 assert component['component_only'] is True and component['scheduler_authority'] is False
 assert component['decision']==decision and component['request']==request
 receipt=component['receipt']
 assert receipt['schema']=='unit-row-advice-validation-v1' and receipt['mode']=='PENDING_KEYS'
 assert receipt['binding']==binding and receipt['decision']==decision and receipt['state_sha256']==sha(st) and receipt['input_sha256']==sha(request)
 assert all(receipt[k] is False for k in strong)
 if rejected:
  assert receipt['selection'] is None and receipt['rejections']==[{'key':key,'reason':'whole_remote_or_metadata_mark_conflict'}]
 else:
  assert receipt['rejections']==[] and receipt['selection'] is not None
  assert canonical(receipt['selection']['anchor']['placement_key'])==canonical(key)
 return receipt

def C_fixture_join(art,binding,*,required):
 if 'selective_C_fixture' not in art:
  assert not required
  return None,{'artifact_present':False,'scientific_replay':False}
 c=art['selective_C_fixture'];a=art['fixture'];assert c['schema']=='unit-row-selective-multikey-C-fixture-v1'
 assert c['original_A_fixture_ref']=='fixture' and type(c['adoption_qualified']) is bool
 assert c['selection_criteria']=={'minimum_future_keys':2,'unoccupied_external_read':True,'exact_remote_conflict':True,'first_different_future_key_legal':True,'original_proposal_order':True,'no_rank_formula_row_or_word_literal':True}
 assert canonical(c['state'])==canonical(a['state'])
 assert canonical(c['seeds'])==canonical([a['derived_from']['selected_future_UG']])
 assert canonical(c['state']['selected'])==canonical([x['selection_record'] for x in c['seeds']])
 assert c['state']['input_epoch']==binding['language_epoch'] and c['state']['height']==24
 summary={'artifact_present':True,'fixture_ref':'selective_C_fixture','whole_artifact_sha256':sha(c),'adoption_qualified':c['adoption_qualified'],'control_only_original_order_subselection':True,'scientific_replay':False}
 if 'whole_actual_batch' in c:
  whole=c['whole_actual_batch'];assert whole['binding']==binding and whole['state_sha256']==sha(c['state'])
  assert whole['decision']=={'kind':'BRANCH','row':0} and all(whole[k] is False for k in strong)
 if 'whole_actual_receipt' in c:
  wr=c['whole_actual_receipt'];assert whole['status']=='READY' and whole['reason'] is None and whole['proposals']
  assert wr['mode']=='ADVICE_BATCH' and wr['binding']==binding and wr['state_sha256']==sha(c['state']) and wr['input_sha256']==sha(whole)
  assert wr['decision']==whole['decision'] and wr['rejections']==[] and all(wr[k] is False for k in strong)
 if 'selected_original_index' in c:
  index=c['selected_original_index'];assert type(index) is int and 0<=index<len(whole['proposals'])
  attempts=c['selector_attempts'];assert [x['original_index'] for x in attempts]==list(range(index+1))
  assert all(x['eligible'] is False and type(x['reason']) is str and x['reason'] for x in attempts[:-1])
  assert attempts[-1]['eligible'] is True and attempts[-1]['reason']=='first_actual_selectively_conflicting_external_port'
  executed=c['executed_batch'];assert set(executed)==set(whole) and canonical(executed['proposals'])==canonical([whole['proposals'][index]])
  for k in whole:
   if k!='proposals':assert canonical(executed[k])==canonical(whole[k])
  er=c['executed_receipt'];selection=c['selection'];assert er['mode']=='ADVICE_BATCH' and er['rejections']==[]
  assert er['binding']==binding and er['state_sha256']==sha(c['state']) and er['decision']==whole['decision'] and er['input_sha256']==sha(executed)
  assert all(er[k] is False for k in strong) and canonical(selection)==canonical(er['selection'])
  anchor=selection['anchor'];anchor_key=anchor['placement_key'];future=selection['future_keys'];proposal=executed['proposals'][0]
  assert canonical(anchor_key)==canonical(proposal['anchor_full_key'])
  assert canonical(future)==canonical([m['candidate']['placement_key'] for m in proposal['members'] if canonical(m['candidate']['placement_key'])!=canonical(anchor_key)]) and len(future)>=2
  assert all(p['installed'] is False and p['logical_proof_accepted'] is False for p in executed['proposals'])
  assert all(o['status']=='PENDING' and o['fact_accepted'] is False for o in proposal['ordered_PENDING_obligations'])
  component=c['selector_component'];bad=component['bad_key'];survivor=component['survivor_key']
  assert component['component_only'] is True and component['no_future_member_installed'] is True
  assert canonical(bad) in {canonical(k) for k in future} and canonical(survivor)==canonical(next(k for k in future if canonical(k)!=canonical(bad)))
  assert canonical(component['bad_check']['state'])==canonical(component['survivor_check']['state'])
  assert canonical(component['bad_check']['state']['selected'])==canonical(component['hypothetical_inner_state']['selected']+[component['remote']['selection_record']])
  C_component(component['bad_check'],bad,'C-selector-component',binding,rejected=True)
  C_component(component['survivor_check'],survivor,'C-selector-component',binding,rejected=False)
  summary.update(selected_original_index=index,whole_actual_batch_sha256=sha(whole),whole_actual_receipt_sha256=sha(wr),executed_subset_sha256=sha(executed),executed_receipt_sha256=sha(er),future_rows=[k['translation'][1] for k in future])
 if not c['adoption_qualified']:
  assert not required
  assert type(c['eligibility_gap']) is str and c['eligibility_gap']
  return c,summary
 assert 'selected_original_index' in c
 before=c['outer_before'];search_before=c['search_before'];inner=c['inner_snapshot'];pending=inner['pending_preferences'];family=c['family_id']
 assert c['actual_initial_decision']==whole['decision'] and canonical(before['state'])==canonical(c['state'])==canonical(search_before['state'])
 assert canonical(before)==canonical(c['outer_after'])
 assert c['outer_restoration']['before_sha256']==c['outer_restoration']['after_sha256']==sha(before)
 assert canonical(inner['state'])==canonical(component['hypothetical_inner_state'])
 assert canonical(inner['state']['selected'])==canonical(c['state']['selected']+[anchor['selection_record']])
 assert canonical(pending['pending_keys'])==canonical(future) and canonical(pending['anchor_key'])==canonical(anchor_key)
 assert pending['binding']==binding and pending['origin']==selection['origin']
 assert family==pending['family_id']==sha({'binding':binding,'origin':selection['origin'],'anchor_key':anchor_key,'future_keys':future})
 assert pending['lineage']==[{'mode':'ADVICE_BATCH','key':anchor_key,'state_sha256':sha(c['state'])}]
 installed={canonical({k:r[k] for k in ('tile_type_id','type_preimage','translation')}) for r in inner['state']['selected']}
 assert all(canonical(k) not in installed for k in future)
 adoption=c['adoption_search'];assert adoption['status']=='UNKNOWN' and adoption['found'] is None and adoption['root_restored'] is True and adoption['stack_restored'] is True
 assert adoption['root_snapshot_sha256']==adoption['final_snapshot_sha256']==sha(search_before)
 assert canonical(adoption['last_observed_state'])==canonical(inner['state']) and not any(e['kind']=='EXCLUDE' for e in adoption['events'])
 tries=[(i,e) for i,e in enumerate(adoption['events']) if e['kind']=='TRY'];advice=[(i,e) for i,e in enumerate(adoption['events']) if e['kind']=='ADVICE'];places=[(i,e) for i,e in enumerate(adoption['events']) if e['kind']=='PLACE']
 assert len(tries)==len(advice)==len(places)==1 and tries[0][0]<advice[0][0]<places[0][0]
 assert tries[0][1]['mode']=='BRANCH' and tries[0][1]['row']==places[0][1]['row']==whole['decision']['row']
 assert all(canonical(x[1]['key'])==canonical(anchor_key) for x in (tries[0],advice[0],places[0]))
 assert advice[0][1]['mode']=='ADVICE_BATCH' and advice[0][1]['family_id']==family and canonical(advice[0][1]['pending_preferences'])==canonical(pending)
 assert c['adoption_restoration']['before_sha256']==c['adoption_restoration']['after_sha256']==sha(inner)
 if 'remote_outer_restoration' in c:assert c['remote_outer_restoration']['before_sha256']==c['remote_outer_restoration']['after_sha256']==sha(before)
 summary.update(family_id=family,inner_snapshot_sha256=sha(inner),anchor_only_adoption=True,own_inner_and_outer_restored=True)
 return c,summary

def C_remote_join(art,binding,c,case_records,*,required):
 names=('remote-mark-invalidates-pending-key','rejected-pending-hint-preserves-canonical-choice')
 assert case_records[names[0]]['status']==case_records[names[1]]['status']
 summary={'artifact_present':'remote_eligibility' in art,'fixture_ref':'selective_C_fixture','component_is_scheduler_authority':False,'engine_lifecycle_accepted_here':False,'scientific_replay':False}
 if 'remote_eligibility' not in art:
  assert not required and all(case_records[n]['status']=='SKIPPED' for n in names)
  assert all(k not in art for k in ('remote_search','remote_receipts','remote_fixture'))
  return summary,[]
 calibration=art['remote_eligibility'];assert c is not None and c['adoption_qualified'] is True
 inner=c['inner_snapshot'];family=inner['pending_preferences'];fid=family['family_id'];pending=family['pending_keys']
 before=calibration['before_decision'];bad=calibration['bad_key'];survivor=calibration['survivor_key'];remote=calibration['remote']
 assert calibration['schema']=='unit-row-remote-rejection-eligibility-v2-C-normalization' and calibration['fixture_ref']=='selective_C_fixture' and calibration['family_id']==fid
 assert calibration['component_only'] is True and calibration['component_decision_is_scheduler_authority'] is False
 assert canonical(bad)==canonical(c['selector_component']['bad_key']) and canonical(survivor)==canonical(c['selector_component']['survivor_key']) and canonical(remote)==canonical(c['selector_component']['remote'])
 assert canonical(before['state']['selected'])==canonical(inner['state']['selected']+[remote['selection_record']]) and canonical(before['pending_preferences'])==canonical(family)
 initial={'state':before['state'],'decision':calibration['component_request']['decision'],'request':calibration['component_request'],'receipt':calibration['component_receipt'],'component_only':True,'scheduler_authority':False}
 C_component(initial,bad,fid,binding,rejected=True)
 assert canonical(calibration['initial_survivor_check']['state'])==canonical(before['state'])
 C_component(calibration['initial_survivor_check'],survivor,fid,binding,rejected=False)
 previous=before;normalization=calibration['normalization'];assert type(normalization) is list and len(normalization)<=24
 for step in normalization:
  assert set(step)=={'actual_decision','before','after_decision','candidate','after'} and canonical(step['before'])==canonical(previous)
  decision=step['actual_decision'];assert decision['kind']=='FORCED' and canonical(decision['candidate'])==canonical(step['candidate'])
  assert canonical(step['after_decision']['state'])==canonical(step['before']['state'])
  assert canonical(step['after_decision']['pending_preferences'])==canonical(family)==canonical(step['after']['pending_preferences'])
  assert canonical(step['after']['state']['selected'])==canonical(step['before']['state']['selected']+[step['candidate']['selection_record']])
  assert step['candidate']['placement_key']['translation'][1]==decision['row']
  previous=step['after']
 if 'after_decision' in calibration:
  after=calibration['after_decision'];decision=calibration['actual_global_decision']
  assert canonical(after['pending_preferences'])==canonical(family) and type(decision) is dict and decision['kind'] in ('DEAD','FORCED','BRANCH','UNKNOWN','SOLVED')
  if calibration['eligible_actual_branch'] or not normalization or decision['kind']!='FORCED':
   assert canonical(after['state'])==canonical(previous['state'])
  else:
   assert canonical(after)==canonical(normalization[-1]['after_decision']) and canonical(decision)==canonical(normalization[-1]['actual_decision'])
 assert type(calibration['eligible_actual_branch']) is bool and type(calibration['normal_search_started']) is bool
 if calibration['eligible_actual_branch']:
  assert calibration['normalization_complete'] is True and decision=={'kind':'BRANCH','row':bad['translation'][1]}
  assert calibration['normal_search_started'] is True and canonical(calibration['normal_search_before'])==canonical(after)
  for field,key,rejected in (('final_bad_check',bad,True),('final_survivor_check',survivor,False)):
   assert canonical(calibration[field]['state'])==canonical(after['state']);C_component(calibration[field],key,fid,binding,rejected=rejected)
 else:
  assert not required and calibration['normal_search_started'] is False
 if 'eligibility_gap' in calibration:assert type(calibration['eligibility_gap']) is str and calibration['eligibility_gap']
 fresh=[]
 if case_records[names[0]]['status']=='PASSED':
  assert calibration['eligible_actual_branch'] is True and 'eligibility_gap' not in calibration
  search=art['remote_search'];fixture=art['remote_fixture'];receipts=art['remote_receipts'];prefix=c['adoption_search']['events']
  assert fixture['fixture_ref']=='selective_C_fixture' and fixture['family_id']==fid
  assert canonical(fixture['before'])==canonical(after) and canonical(fixture['remote'])==canonical(remote) and canonical(fixture['invalidated_pending_key'])==canonical(bad) and canonical(fixture['surviving_pending_key'])==canonical(survivor)
  assert fixture['event_prefix_ref']=='selective_C_fixture.adoption_search.events' and fixture['event_prefix_count']==fixture['fresh_event_start']==len(prefix)
  assert canonical(search['events'][:len(prefix)])==canonical(prefix);fresh=search['events'][len(prefix):]
  assert search['status']=='UNKNOWN' and search['found'] is None and search['root_restored'] is True and search['stack_restored'] is True
  assert search['root_snapshot_sha256']==search['final_snapshot_sha256']==sha(after) and not any(e['kind']=='EXCLUDE' for e in search['events'])
  assert any(canonical(x['key'])==canonical(bad) and x['reason']=='whole_remote_or_metadata_mark_conflict' for r in receipts for x in r['rejections'])
  fallback=case_records[names[1]]['observed']['actual_fallback_event'];assert any(canonical(e)==canonical(fallback) for e in fresh)
  assert fallback['kind']=='ADVICE' and fallback['mode']=='CANONICAL_FALLBACK' and fallback['rejected_keys']
  assert fallback['abandoned_family']['family_id']==fid and canonical(fallback['abandoned_family']['pending_keys'])==canonical(pending)
 else:
  assert not required and all(k not in art for k in ('remote_search','remote_receipts','remote_fixture'))
 summary.update(whole_artifact_sha256=sha(calibration),eligible_actual_branch=calibration['eligible_actual_branch'],normal_search_started=calibration['normal_search_started'],normalization_placements=len(normalization),live_rejection_reported=case_records[names[0]]['status']=='PASSED',fresh_event_start=len(c['adoption_search']['events']),fresh_events=len(fresh),family_id=fid)
 return summary,fresh

case_records={x['case']:x for x in cases}
c_fixture,c_join=C_fixture_join(art,body['language_binding'],required=False)
remote_join,remote_events=C_remote_join(art,body['language_binding'],c_fixture,case_records,required=False)
# Returned C lineage remains recorded even when any other required case skips.
# These are saved concordance checks, not independent point/degree semantics.
if 'family_retirement' in art and 'actual_rejection' in art['family_retirement']:
 rejection=art['family_retirement']['actual_rejection']
 assert c_fixture is not None and c_fixture['adoption_qualified'] is True
 assert rejection['fixture_ref']=='selective_C_fixture' and rejection['owned_inner_snapshot']['pending_preferences']['family_id']==c_fixture['family_id']
 assert canonical(rejection['owned_inner_snapshot']['state'])==canonical(art['remote_fixture']['before']['state']) and canonical(rejection['owned_inner_snapshot']['pending_preferences'])==canonical(art['remote_fixture']['before']['pending_preferences'])
 assert any(canonical(e)==canonical(rejection['abandonment_event']) for e in remote_events)
if 'forced_retirement' in art:
 fr=art['forced_retirement'];assert c_fixture is not None and c_fixture['adoption_qualified'] is True
 assert fr['fixture_ref']=='selective_C_fixture' and fr['family_id']==c_fixture['family_id']
 prefix=art['remote_search']['events'] if 'remote_search' in art else c_fixture['adoption_search']['events']
 assert fr['event_prefix_ref']==('remote_search.events' if 'remote_search' in art else 'selective_C_fixture.adoption_search.events')
 assert fr['event_prefix_count']==fr['fresh_event_start']==len(prefix) and canonical(fr['search']['events'][:len(prefix)])==canonical(prefix)
 assert fr['search']['root_snapshot_sha256']==fr['search']['final_snapshot_sha256']==sha(fr['before'])
if 'fair_interface' in art and 'replacement' in art['fair_interface']:
 replacement=art['fair_interface']['replacement'];assert c_fixture is not None
 assert replacement['fixture_ref']=='selective_C_fixture' and replacement['before']['pending_preferences']['family_id']==c_fixture['family_id']
 prefix=art['family_retirement']['follow_on_search']['actual_result']['events']
 assert replacement['event_prefix_ref']=='family_retirement.follow_on_search.actual_result.events'
 assert replacement['event_prefix_count']==replacement['fresh_event_start']==len(prefix)
 assert canonical(replacement['actual_result']['events'][:len(prefix)])==canonical(prefix)
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
output={'schema':'ROOT-advice-consumer-controls-partial-disposition-v16-ABC','status':'COMPLETE_RETURNED43_PARTIAL_CONTROLS_TARGETS_NOT_ADMITTED','plan':pp,'sources':plan['sources'],'inputs':plan['inputs'],'source_contract':plan['source_contract'],'controls_accepted':False,'target_admission_qualified':False,'all_advice_consumer_gates_qualified':False,'declared_cases':43,'reported_passed_cases':passed,'reported_skipped_cases':skipped,'all_case_labels':case_names,'case_statuses':[{'case':x['case'],'reported_status':x['status']} for x in cases],'essential_gaps':coverage,'additional_coverage_gaps':controls['additional_coverage_gaps'],'reported_PASSED_semantics_accepted_here':False,'full_returned_record_retained':True,'complete_wire_verified':True,'full_raw_evidence':{'outputs':outputs,'expanded_result':transport['expanded_file'],'transport_concordance':pin(HERE/'ROOT-advice-controls-transport-concordance-v1.json'),'native_terminal':pin(external/'native-terminal.json'),'observation':pin(external/'observation.json'),'tool_bracket':pin(HERE/'ROOT-advice-controls-tool-bracket-v1.json')},'selective_C_fixture_saved_concordance':c_join,'remote_calibration_saved_concordance':remote_join,'paired_saved_alias_concordance':paired_join,'artifact_keys':sorted(art),'unqualified_native_timeline':native_timeline,'unqualified_continuation_observations':progress,'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'complete_Date_seconds':date,'all_reaped':True,'actual_closed':True,'positive_closer14_used':False,'positive_closer16_used':False,'proof_search_or_target_result_accepted':False,'scientific_replay':False,'author_identity':'/root/arithmetic_induction','author_overlap':'Author owns adviser/engine/c354 and saved-only closer antecedents. This partial helper performs literal saved-wire/resource/metadata concordance only; no independent scientific replay or own-dependency proof acceptance.','scope':'Only complete returned current43 records with essential SKIPs/additional gaps; exact raw record remains authoritative. Component-shaped pending rejection is not a global engine rejection/branch/rollback test; absent tests are not inferred. Native/wire closure does not qualify controls, target, trajectory, learned marking or RL.'}
output.update({k:False for k in strong})
q=HERE/'ROOT-advice-controls-partial-disposition-v1.json'
with q.open('x') as f:json.dump(output,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'reported_passed':passed,'reported_skipped':skipped,'controls_accepted':False,'target_admission_qualified':False}))
