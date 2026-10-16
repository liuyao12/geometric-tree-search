"""Saved literal A/B/C evidence and resource concordance only; no scientific replay."""
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
assert all(x['status']=='PASSED' for x in cases[:30]) and all(x['status'] in ('PASSED','SKIPPED') for x in cases)
passed=sum(x['status']=='PASSED' for x in cases);skipped=sum(x['status']=='SKIPPED' for x in cases)
assert controls['passed']==passed and controls['skipped']==skipped and passed+skipped==43
assert controls['unqualified_consumer_gates']==[x['case'] for x in cases if x['status']=='SKIPPED']
qualified=skipped==0 and controls['additional_coverage_gaps']==[]
assert controls['all_advice_consumer_gates_qualified'] is qualified
art=controls['artifacts'];by={x['case']:x['observed'] for x in cases}
def sha(x):return hashlib.sha256(canonical(x)).hexdigest()
strong=('logical_proof_accepted','exact_point_board_accepted','degree_or_EOF_accepted','scheduler_accepted','complete_GCTS_model_accepted','trajectory_accepted','learned_marking_accepted','RL_accepted','ROOT_resource_accepted')
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

fixture=art['fixture'];attempt=art['fixture_advice_attempt'];batch=attempt['actual_adviser_return'];receipt=fixture['receipt'];selection=receipt['selection']
assert canonical(attempt['state'])==canonical(fixture['state']) and canonical(batch)==canonical(fixture['batch'])
assert batch['status']=='READY' and batch['reason'] is None and batch['limits']=={'maximum_work':50000,'maximum_proposals':8,'maximum_demands':5,'maximum_terms':1,'maximum_rounds':3}
assert 0<batch['work']['guarded_steps']<=batch['limits']['maximum_work'] and batch['work']['rounds']==3 and len(batch['proposals'])>=2
assert batch['state_sha256']==attempt['pre_advice_state_sha256']==sha(fixture['state'])==receipt['state_sha256']
assert batch['binding']==receipt['binding']==body['language_binding'] and receipt['input_sha256']==sha(batch) and receipt['mode']=='ADVICE_BATCH'
assert batch['decision']==receipt['decision']==fixture['decision']=={'kind':'BRANCH','row':0}
assert canonical(selection['anchor'])==canonical(batch['proposals'][0]['members'][0]['candidate'])
future=selection['future_keys'];assert future and len({canonical(k) for k in future})==len(future)
assert all(p['installed'] is False and p['logical_proof_accepted'] is False for p in batch['proposals'])
obligations=[o for p in batch['proposals'] for o in p['ordered_PENDING_obligations']]
assert obligations and all(o['status']=='PENDING' and o['fact_accepted'] is False for o in obligations)
for x in by['malformed-batch-controls']['mutations']:assert x['result']['exception_type']=='ValueError'
assert any(x['mutation']=='swapped-ordered-ports' for x in by['malformed-batch-controls']['mutations'])
assert by['later-ranked-malformed-proposal-rejected']['exception_type']=='ValueError'
for name in ('UNKNOWN-rejected-by-executable-validator','adviser-ValueError-propagates','validator-ValueError-propagates'):
 assert by[name]['exception_type']=='ValueError'
for x in by['pending-request-malformed-controls']['checks']:assert x['result']['exception_type']=='ValueError'
unknown_names=('empty_search','quota_search','callback_timeout_search','adoption_search','pending_continuation_search','remote_search','forced_search')
for name in unknown_names:
 r=art[name];assert r['status']=='UNKNOWN' and r['found'] is None and r['root_restored'] is True and r['stack_restored'] is True
 assert r['root_snapshot_sha256']==r['final_snapshot_sha256'] and not any(e['kind']=='EXCLUDE' for e in r['events'])
assert not any(e['kind']=='TRY' for e in art['callback_timeout_search']['events'])
canonical_key=art['canonical_first']['event']['candidate']['placement_key']
for name in ('empty_search','quota_search'):
 assert canonical(next(e for e in art[name]['events'] if e['kind']=='TRY')['key'])==canonical(canonical_key)
assert art['quota_UNKNOWN']['status']=='UNKNOWN' and art['quota_search']['counts']['advice_unknown']>=1
inner=art['genuine_inner_snapshot'];assert canonical(inner['pending_preferences']['pending_keys'])==canonical(future)
assert len(inner['state']['selected'])==len(fixture['state']['selected'])+1
assert canonical(inner['state'])==canonical(art['adoption_search']['last_observed_state'])
for k in future:assert not any(all(canonical(r[f])==canonical(k[f]) for f in ('tile_type_id','type_preimage','translation')) for r in inner['state']['selected'])
assert canonical(by['public-rollback-restores-genuine-nonempty-pending']['actual_pending_keys'])==canonical(future)
for name in ('adviser-ValueError-propagates','validator-ValueError-propagates','first-search-exact-root-restoration','pending-search-exact-inner-root-restoration'):
 x=by[name];assert x['before_sha256']==x['after_sha256']
pr=art['pending_selection_receipts'];assert pr and any(x['selection'] is not None and x['mode']=='PENDING_KEYS' for x in pr)
assert art['pending_continuation_search']['counts']['pending_selected']>=1
# Paired fixture B is distinct from original fixture A above. These are saved
# literal joins only; no candidate, degree, point or mathematical replay.
sibling=art['pending_success_fixture'];lineage=art['pending_continuation_lineage']
assert sibling['schema']=='unit-row-paired-pending-success-fixture-v1' and sibling['original_fixture_ref']=='fixture'
assert sibling['eligibility_qualified'] is True and sibling['no_future_preinstallation'] is True
assert sibling['pending_selection_observed'] is True
assert sibling['continuation_search_ref']=='pending_continuation_search' and sibling['pending_receipts_ref']=='pending_selection_receipts'
sibling_state=sibling['state'];seeds=sibling['seeds'];assert len(seeds)==3
assert [x['placement_key']['translation'] for x in seeds]==[[0,9],[0,1],[0,2]]
assert canonical(seeds[0])==canonical(fixture['derived_from']['selected_future_UG'])
assert sibling['derived_from']['AX_name']==fixture['derived_from']['AX_name'] and sibling['derived_from']['duplicate_source_rows']==[1,2]
assert sibling['derived_from']['eligible_parameter']==fixture['derived_from']['eligible_parameter'] and sibling['derived_from']['original_target_boundary_preserved'] is True
assert canonical(sibling['derived_from']['selected_future_UG'])==canonical(seeds[0])
original_declaration=read(check(plan['inputs']['declaration']));ax_name=fixture['derived_from']['AX_name']
ax_formula=original_declaration['theory']['axioms'][ax_name]
for seed in seeds[1:]:
 key=seed['placement_key'];pre=key['type_preimage']
 assert pre['primitive_witness']=={'rule':'axiom','name':ax_name,'formula':ax_formula}
 assert pre['ordered_premise_formulas']==pre['ordered_offsets']==[]
 assert canonical(seed['selection_record'])==canonical(dict(key,generation=1))
assert canonical(sibling_state['selected'])==canonical([x['selection_record'] for x in seeds])
assert sibling_state['input_epoch']==body['language_binding']['language_epoch'] and sibling_state['height']==24
assert sibling_state['generation']==fixture['state']['generation'] and sibling_state['excluded']==fixture['state']['excluded']
assert canonical(sibling['outer_before']['state'])==canonical(sibling_state)==canonical(sibling['search_before']['state'])
assert canonical(sibling['outer_before'])==canonical(sibling['outer_after'])
assert sibling['outer_restoration']['before_sha256']==sibling['outer_restoration']['after_sha256']==sha(sibling['outer_before'])
sibling_batch=sibling['whole_actual_batch'];sibling_receipt=sibling['whole_actual_receipt'];sibling_selection=sibling['selection']
assert sibling_batch['status']=='READY' and sibling_batch['reason'] is None and sibling_batch['proposals']
assert sibling_batch['version']==batch['version'] and sibling_batch['limits']==batch['limits']
assert 0<sibling_batch['work']['guarded_steps']<=50000
assert sibling['decision']==sibling_batch['decision']==sibling_receipt['decision']=={'kind':'BRANCH','row':0}
assert sibling_batch['binding']==sibling_receipt['binding']==body['language_binding']
assert sibling_batch['state_sha256']==sibling_receipt['state_sha256']==sha(sibling_state) and sibling_receipt['input_sha256']==sha(sibling_batch)
assert sibling_receipt['mode']=='ADVICE_BATCH' and sibling_receipt['rejections']==[]
assert all(p['installed'] is False and p['logical_proof_accepted'] is False for p in sibling_batch['proposals'])
assert all(o['status']=='PENDING' and o['fact_accepted'] is False for p in sibling_batch['proposals'] for o in p['ordered_PENDING_obligations'])
assert canonical(sibling_selection)==canonical(sibling_receipt['selection']) and sibling_selection['future_keys']
assert canonical(sibling_selection['anchor'])==canonical(sibling_batch['proposals'][0]['members'][0]['candidate'])
sibling_inner=sibling['inner_snapshot'];sibling_future=sibling_selection['future_keys'];sibling_pending=sibling_inner['pending_preferences']
sibling_anchor=sibling_selection['anchor'];sibling_key=sibling_anchor['placement_key'];sibling_family=sibling_pending['family_id']
assert canonical(sibling_inner['state']['selected'])==canonical(sibling_state['selected']+[sibling_anchor['selection_record']])
assert canonical(sibling_pending['pending_keys'])==canonical(sibling_future) and canonical(sibling_pending['anchor_key'])==canonical(sibling_key)
assert sibling_pending['binding']==body['language_binding'] and sibling_pending['origin']==sibling_selection['origin']
assert sibling_family==sha({'binding':body['language_binding'],'origin':sibling_selection['origin'],'anchor_key':sibling_key,'future_keys':sibling_future})
assert sibling_pending['lineage']==[{'mode':'ADVICE_BATCH','key':sibling_key,'state_sha256':sha(sibling_state)}]
for k in sibling_future:assert not any(all(canonical(rec[f])==canonical(k[f]) for f in ('tile_type_id','type_preimage','translation')) for rec in sibling_inner['state']['selected'])
sibling_adoption=sibling['adoption_search']
assert sibling_adoption['status']=='UNKNOWN' and sibling_adoption['found'] is None and sibling_adoption['root_restored'] is True and sibling_adoption['stack_restored'] is True
assert sibling_adoption['root_snapshot_sha256']==sibling_adoption['final_snapshot_sha256']==sha(sibling['search_before'])
assert canonical(sibling_adoption['last_observed_state'])==canonical(sibling_inner['state'])
assert not any(e['kind']=='EXCLUDE' for e in sibling_adoption['events'])
adoption_tries=[(i,e) for i,e in enumerate(sibling_adoption['events']) if e['kind']=='TRY']
adoption_advice=[(i,e) for i,e in enumerate(sibling_adoption['events']) if e['kind']=='ADVICE']
adoption_places=[(i,e) for i,e in enumerate(sibling_adoption['events']) if e['kind']=='PLACE']
assert len(adoption_tries)==len(adoption_advice)==len(adoption_places)==1
assert adoption_tries[0][0]<adoption_advice[0][0]<adoption_places[0][0]
assert adoption_tries[0][1]['mode']=='BRANCH' and adoption_tries[0][1]['row']==adoption_places[0][1]['row']==0
assert all(canonical(x[1]['key'])==canonical(sibling_key) for x in (adoption_tries[0],adoption_advice[0],adoption_places[0]))
assert adoption_advice[0][1]['mode']=='ADVICE_BATCH' and adoption_advice[0][1]['family_id']==sibling_family and canonical(adoption_advice[0][1]['pending_preferences'])==canonical(sibling_pending)
assert canonical(sibling['continuation_before'])==canonical(sibling_inner)
assert sibling['inner_restoration']['before_sha256']==sibling['inner_restoration']['after_sha256']==sha(sibling_inner)
assert lineage=={'fixture_ref':'pending_success_fixture','family_id':sibling_family,'inner_snapshot_sha256':sha(sibling_inner),'original_fixture_used':False}
continuation=art['pending_continuation_search'];pending_calls=sibling['pending_calls']
assert canonical(sibling['continuation_search'])==canonical(continuation)
assert continuation['root_snapshot_sha256']==continuation['final_snapshot_sha256']==sha(sibling_inner)
assert pending_calls and canonical([x['receipt'] for x in pending_calls])==canonical(pr)
assert continuation['counts']['pending_selected']>=1
successful_calls=[];pending_event_joins=[]
for call in pending_calls:
 st,d,req,rec=(call[k] for k in ('state','decision','request','receipt'))
 assert d['kind']=='BRANCH' and req['decision']==rec['decision']==d
 assert req['schema']=='unit-row-pending-preference-request-v1' and req['family_id']==sibling_family
 assert req['binding']==rec['binding']==body['language_binding'] and req['state_sha256']==rec['state_sha256']==sha(st)
 assert rec['input_sha256']==sha(req) and rec['mode']=='PENDING_KEYS'
 assert canonical(st['selected'][:len(sibling_state['selected'])])==canonical(sibling_state['selected'])
 assert all(k['translation']==[0,d['row']] and canonical(k) in {canonical(x) for x in sibling_future} for k in req['keys'])
 if rec['selection'] is None or rec['rejections']:continue
 chosen=rec['selection']['anchor']['placement_key']
 assert rec['selection']['future_keys']==[] and rec['selection']['origin']=={'family_id':sibling_family}
 assert canonical(chosen) in {canonical(k) for k in req['keys']}
 successful_calls.append(call)
 matches=[(i,e) for i,e in enumerate(continuation['events']) if e['kind']=='ADVICE' and e['mode']=='PENDING_KEYS' and e['family_id']==sibling_family and canonical(e['key'])==canonical(chosen)]
 assert matches
 for i,e in matches:
  assert e['abandoned_family'] is None and e['rejected_keys']==[] and e['origin']=={'family_id':sibling_family}
  assert i>1 and continuation['events'][i-1]['kind']=='TRY' and continuation['events'][i-1]['mode']=='BRANCH'
  assert continuation['events'][i-2]['kind']=='DECISION' and continuation['events'][i-2]['decision']==d
  assert all(continuation['events'][j]['state_sha256']==sha(st) for j in (i-2,i-1,i))
  assert continuation['events'][i-1]['row']==d['row'] and canonical(continuation['events'][i-1]['key'])==canonical(chosen)
  later=next((j for j in range(i+1,len(continuation['events'])) if continuation['events'][j]['kind'] in ('PLACE','RESTORE','TRY')),None)
  assert later is not None and continuation['events'][later]['kind']=='PLACE' and continuation['events'][later]['row']==d['row'] and canonical(continuation['events'][later]['key'])==canonical(chosen)
  pending_event_joins.append({'callback_state_sha256':sha(st),'decision':d,'request_sha256':sha(req),'receipt_sha256':sha(rec),'DECISION_index':i-2,'TRY_index':i-1,'ADVICE_index':i,'PLACE_index':later,'key':chosen})
 assert canonical(rec['selection']['anchor']['selection_record']) in {canonical(x) for x in continuation['last_observed_state']['selected']}
assert successful_calls and pending_event_joins
assert by['pending-key-real-current-row-selection']=={'fixture':'pending_success_fixture','search':'pending_continuation_search','receipts':'pending_selection_receipts','lineage':'pending_continuation_lineage'}
restore_by=by['pending-search-exact-inner-root-restoration']
assert restore_by['fixture']=='pending_success_fixture' and restore_by['before_sha256']==restore_by['after_sha256']==sha(sibling_inner)
# C is an explicitly control-only structural subselection with its own receipt,
# family and engine snapshots. Equal seed point states do not merge A and C.
assert len(plan['sources'])==17 and len(plan['inputs'])==2
assert contract_current['sources']==plan['sources'] and contract_current['inputs']==plan['inputs'] and contract_current['limits']==plan['limits']
assert contract_current['Review_ABI']['sources']==plan['sources'] and contract_current['Review_ABI']['source']==plan['sources']['intake']
case_records={x['case']:x for x in cases}
c_fixture,c_join=C_fixture_join(art,body['language_binding'],required=True)
c_remote_join,remote_events=C_remote_join(art,body['language_binding'],c_fixture,case_records,required=True)
c_inner=c_fixture['inner_snapshot'];c_family=c_fixture['family_id'];c_future=c_fixture['selection']['future_keys']
rr=art['remote_receipts'];bad=art['remote_fixture']['invalidated_pending_key']
fb=by['rejected-pending-hint-preserves-canonical-choice']['actual_fallback_event']
fr=art['forced_retirement'];r=fr['search'];assert fr['fixture_ref']=='selective_C_fixture' and fr['family_id']==c_family
assert r['status']=='UNKNOWN' and r['found'] is None and r['root_restored'] is True and r['stack_restored'] is True
assert r['root_snapshot_sha256']==r['final_snapshot_sha256']==sha(fr['before']) and not any(e['kind']=='EXCLUDE' for e in r['events'])
assert canonical(fr['before']['pending_preferences'])==canonical(c_inner['pending_preferences'])
forced_prefix=art['remote_search']['events'];assert fr['event_prefix_ref']=='remote_search.events'
assert fr['event_prefix_count']==fr['fresh_event_start']==len(forced_prefix) and canonical(r['events'][:len(forced_prefix)])==canonical(forced_prefix)
forced_events=r['events'][len(forced_prefix):]
c_rows={k['translation'][1] for k in c_future}
assert {e['row'] for e in forced_events if e['kind']=='TRY' and e['mode']=='FORCED'}>=c_rows
retired=by['global-forced-fill-retires-family-before-fresh-advice']['retired_keys'];assert {canonical(k) for k in retired}=={canonical(k) for k in c_future}
assert any(e['kind']=='ADVICE' and {canonical(k) for k in e['retired_keys']}=={canonical(k) for k in c_future} and e['pending_preferences'] is None for e in forced_events)
assert fr['new_adviser_calls'] and all(dict((tuple(p),v) for p,v in call['state']['t'])[(0,row)]==1 for call in fr['new_adviser_calls'] for row in c_rows)
assert art['dead_search']['status']=='EXHAUSTED' and art['dead_search']['counts']['advice_calls']==0 and art['forced_search']['counts']['advice_calls']==0
life=art['family_retirement'];rejection=life['actual_rejection'];inner_before=rejection['owned_inner_snapshot'];pending=inner_before['pending_preferences']
abandoned_event=rejection['abandonment_event'];abandoned=abandoned_event['abandoned_family'];req=rejection['batch'];rr=rejection['actual_receipt']
assert rejection['fixture_ref']=='selective_C_fixture' and pending['family_id']==c_family
assert canonical(pending)==canonical(c_inner['pending_preferences'])
assert canonical(inner_before['state'])==canonical(art['remote_fixture']['before']['state']) and canonical(inner_before['pending_preferences'])==canonical(art['remote_fixture']['before']['pending_preferences'])
assert any(canonical(e)==canonical(abandoned_event) for e in remote_events)
assert rr['mode']=='PENDING_KEYS' and rr['state_sha256']==sha(rejection['state']) and rr['input_sha256']==sha(req)
assert canonical(inner_before['state'])==canonical(rejection['state']) and rr['decision']==rejection['decision']==req['decision']
assert abandoned['schema']=='unit-row-advisory-family-abandonment-v1' and abandoned['family_id']==pending['family_id']==req['family_id']
assert abandoned['branch_row']==req['decision']['row'] and abandoned['reason']=='DEFINITE_CURRENT_PENDING_MEMBER_REJECTION'
assert canonical(abandoned['pending_keys'])==canonical(pending['pending_keys'])
assert {canonical(k) for k in abandoned['rejected_keys']}=={canonical(x['key']) for x in rr['rejections']}
remaining=[k for k in pending['pending_keys'] if canonical(k) not in {canonical(x['key']) for x in rr['rejections']}]
assert remaining and abandoned_event['mode']=='CANONICAL_FALLBACK' and abandoned_event['pending_preferences'] is None
component=rejection['different_future_key_component_check'];component_receipt=component['receipt']
assert component_receipt['selection'] is not None and component_receipt['rejections']==[] and component_receipt['mode']=='PENDING_KEYS'
assert canonical(component_receipt['selection']['anchor']['placement_key']) in {canonical(k) for k in remaining}
fresh=life['same_branch_fresh_batch'];assert fresh['mode']=='PRIOR22' and canonical(fresh['state'])==canonical(rejection['state']) and fresh['decision']==rejection['decision']
assert fresh['actual_return']['status']=='READY' and fresh['actual_return']['proposals']==[]
new_names=read(HERE.parent/'unit-row-advice-family-retirement-controls-source-20261016/Source-contract-v1.json')['new_cases'];assert len(new_names)==8
assert by[new_names[0]]['old_family_keys']==len(pending['pending_keys']) and by[new_names[0]]['actually_rejected_keys']==len(rr['rejections'])
assert by[new_names[1]]['fresh_calls']==1 and by[new_names[2]]['EXCLUDE_events']==0
assert canonical(by[new_names[2]]['actual_child_state'])==canonical(art['remote_search']['last_observed_state'])
assert {canonical(k) for k in by[new_names[2]]['remaining_keys_never_installed']}=={canonical(k) for k in remaining}
for key in remaining:assert not any(all(canonical(x[f])==canonical(key[f]) for f in ('tile_type_id','type_preimage','translation')) for x in by[new_names[2]]['actual_child_state']['selected'])
success=[e for e in art['pending_continuation_search']['events'] if e['kind']=='ADVICE' and e['mode']=='PENDING_KEYS']
assert success and canonical(success)==canonical(by[new_names[3]]['actual_successful_events']) and all(e['abandoned_family'] is None for e in success)
assert by[new_names[3]]['fixture_ref']=='pending_success_fixture' and canonical(by[new_names[3]]['lineage'])==canonical(lineage)
assert life['successful_continuity_context']=={'fixture_ref':'pending_success_fixture','lineage':lineage,'original_rejection_fixture_ref':'selective_C_fixture','distinct_control_contexts':True}
assert by[new_names[4]]['inner_snapshot_sha256']==by[new_names[4]]['restored_sha256']==sha(inner_before)
for name,mode in ((new_names[5],'VALUE_ERROR'),(new_names[6],'TIMEOUT')):
 x=by[name];assert x['before_sha256']==x['after_sha256']==sha(inner_before)
 cb=x['actual_callback'];assert cb['mode']==mode and canonical(cb['state'])==canonical(rejection['state']) and cb['decision']==rejection['decision'] and 'actual_return' not in cb
assert by[new_names[5]]['exception_type']=='ValueError' and by[new_names[5]]['reason']=='declared replacement adviser ValueError after definite rejection'
interrupted=by[new_names[6]]['actual_result'];assert interrupted['status']=='UNKNOWN' and interrupted['found'] is None and interrupted['root_restored'] and interrupted['stack_restored'] and not any(e['kind']=='EXCLUDE' for e in interrupted['events'])
follow=life['follow_on_search'];calls=follow['actual_adviser_calls'];result_follow=follow['actual_result']
assert len(calls)==2 and calls[0]['decision']==rejection['decision'] and calls[1]['decision']['kind']=='BRANCH' and calls[1]['decision']['row']>calls[0]['decision']['row']
assert all(c['actual_return']['status']=='UNKNOWN' for c in calls)
assert follow['before_sha256']==follow['after_sha256']==sha(inner_before) and follow['actual_child_snapshot']['pending_preferences'] is None
assert result_follow['status']=='UNKNOWN' and result_follow['found'] is None and not any(e['kind']=='EXCLUDE' for e in result_follow['events'])
assert result_follow['root_restored'] and result_follow['stack_restored']
strong=('logical_proof_accepted','exact_point_board_accepted','degree_or_EOF_accepted','scheduler_accepted','complete_GCTS_model_accepted','trajectory_accepted','learned_marking_accepted','RL_accepted','ROOT_resource_accepted')
assert all(controls[k] is False and batch[k] is False and receipt[k] is False for k in strong)
assert all(sibling_batch[k] is False and sibling_receipt[k] is False and all(c['receipt'][k] is False for c in pending_calls) for k in strong)
assert all(result[k] is False for k in ('complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','ROOT_resource_accepted'))
assert all(body[k] is False for k in ('ROOT_resource_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','logical_proof_accepted','RL_accepted','GCTS_advantage_claimed'))
quality=art['fair_interface'];scoring=quality['scoring']
assert scoring['actual_batch_sha256']==sha(batch) and scoring['actual_independent_receipt']['input_sha256']==sha(batch)
assert len(scoring['recomputed_rows'])==len(batch['proposals'])
for proposal,row in zip(batch['proposals'],scoring['recomputed_rows']):
 assert canonical(proposal['score'])==canonical(row['score']) and canonical(proposal['ranking_features'])==canonical(row['features'])
 assert len(proposal['score'])==5 and len(proposal['ranking_features'])==7
assert all(x['status']=='PASSED' for x in cases[30:35])
for index,count in ((1,4),(2,3)):
 mutations=by[new_quality_names[index]]['mutations'];assert len(mutations)==count
 assert all(x['result']['exception_type']=='ValueError' and x['result']['reason'].startswith('advice consumer: ') for x in mutations)
assert by[new_quality_names[3]]['exception_type']=='ValueError'
for x in by[new_quality_names[4]].values():assert x['exception_type']=='ValueError'
assert controls['no_generation_claim_from_topk_absence'] is True and controls['control_only_real_order_preserving_suppression_never_target_policy'] is True
replacement_cases=cases[37:40];assert len({x['status'] for x in replacement_cases})==1
if replacement_cases[0]['status']=='PASSED':
 replacement=quality['replacement'];whole=replacement['whole_actual_batch'];executed=replacement['executed_batch'];index=replacement['control_only_selected_index']
 assert canonical(executed['proposals'])==canonical([whole['proposals'][index]])
 for key in whole:
  if key!='proposals':assert canonical(whole[key])==canonical(executed[key])
 assert replacement['whole_actual_receipt']['input_sha256']==sha(whole) and replacement['executed_receipt']['input_sha256']==sha(executed)
 assert replacement['fixture_ref']=='selective_C_fixture' and replacement['before']['pending_preferences']['family_id']==c_family
 assert canonical(replacement['actual_rejection']['state'])==canonical(rejection['state']) and replacement['actual_rejection']['decision']==rejection['decision']
 replacement_prefix=life['follow_on_search']['actual_result']['events']
 assert replacement['event_prefix_ref']=='family_retirement.follow_on_search.actual_result.events'
 assert replacement['event_prefix_count']==replacement['fresh_event_start']==len(replacement_prefix)
 assert canonical(replacement['actual_result']['events'][:len(replacement_prefix)])==canonical(replacement_prefix)
 replacement_events=replacement['actual_result']['events'][len(replacement_prefix):]
 replacement_advice=[e for e in replacement_events if e['kind']=='ADVICE' and e['abandoned_family'] is not None]
 assert len(replacement_advice)==1 and replacement_advice[0]['mode']=='ADVICE_BATCH' and replacement_advice[0]['abandoned_family']['family_id']==c_family
 assert canonical(replacement_advice[0]['pending_preferences'])==canonical(replacement['child']['pending_preferences'])
 replacement_selection=replacement['executed_receipt']['selection'];replacement_pending=replacement['child']['pending_preferences']
 assert replacement_selection['origin']==replacement_pending['origin'] and canonical(replacement_selection['anchor']['placement_key'])==canonical(replacement_pending['anchor_key'])
 assert canonical(replacement_selection['future_keys'])==canonical(replacement_pending['pending_keys']) and replacement_pending['family_id']!=c_family
 assert canonical(replacement['child']['state']['selected'])==canonical(replacement['before']['state']['selected']+[replacement_selection['anchor']['selection_record']])
 assert canonical(replacement['before'])==canonical(replacement['after'])
 assert replacement['actual_result']['status']=='UNKNOWN' and replacement['actual_result']['root_restored'] and replacement['actual_result']['stack_restored']
 assert replacement['child']['pending_preferences']['pending_keys']
 rollback=by[new_quality_names[-1]]
 assert rollback['new_child_snapshot_sha256']==rollback['restored_child_sha256'] and rollback['old_parent_sha256']==rollback['restored_parent_sha256']
else:
 assert 'replacement' not in quality
 assert all(x['observed']['reason'] for x in replacement_cases)
component_attempts=quality['component_attempts']
for label,attempt in component_attempts.items():
 assert attempt['authority_accepted'] is False
 if 'whole_actual_batch' in attempt:
  ab=attempt['whole_actual_batch'];assert ab['state_sha256']==sha(attempt['state']) and ab['decision']==attempt['actual_decision']
  assert canonical(attempt['before']['state'])==canonical(attempt['state'])==canonical(attempt['after_decision']['state'])
  if label=='occupied_compatible_UI_source':
   cb=attempt['actual_callback'];assert canonical(cb['snapshot'])==canonical(attempt['before'])==canonical(attempt['after_decision'])
   assert attempt['fixture_ref']=='pending_success_fixture' and attempt['paired_family_id']==sibling_family
   assert cb['snapshot']['pending_preferences']['family_id']==sibling_family
   assert canonical(cb['snapshot']['state']['selected'][:len(sibling_state['selected'])])==canonical(sibling_state['selected'])
   assert any(canonical(cb['snapshot']['state'])==canonical(call['state']) and all(canonical(cb[k])==canonical(call[k]) for k in ('decision','request','receipt')) for call in successful_calls)
   assert canonical(attempt['finished_outer_before'])==canonical(sibling['outer_after'])
   assert cb['before_child_adoption_and_placement'] is True and cb['decision']==attempt['actual_decision']
   assert canonical(cb['snapshot']['state'])==canonical(attempt['state'])
   cr=cb['receipt'];assert cr['mode']=='PENDING_KEYS' and cr['selection'] is not None and cr['rejections']==[]
   assert cr['input_sha256']==sha(cb['request']) and cr['state_sha256']==sha(attempt['state']) and cr['decision']==attempt['actual_decision']
   assert canonical(attempt['finished_outer_before'])==canonical(attempt['finished_outer_after']) and attempt['restored_sha256']==sha(attempt['finished_outer_after'])
   ax=attempt['declaration']['selected_original_AX_record'];assert any(canonical(x)==canonical(ax) for x in attempt['state']['selected']) and ax['translation']==[0,1]
   assert canonical(ax)==canonical(seeds[1]['selection_record']) and attempt['declaration']['AX_name_from_actual_original_fixture']==ax_name
   occupied_anchor=cr['selection']['anchor']['placement_key'];occupied_pre=occupied_anchor['type_preimage'];occupied_row=attempt['actual_decision']['row']
   assert occupied_pre['primitive_witness']['rule']=='mp' and occupied_row+occupied_pre['ordered_offsets'][0]==1 and canonical(occupied_pre['ordered_premise_formulas'][0])==canonical(ax_formula)
  else:assert attempt['restored_sha256']==sha(attempt['before'])
  if 'whole_actual_receipt' in attempt:
   ar=attempt['whole_actual_receipt'];assert ar['input_sha256']==sha(ab) and ar['state_sha256']==sha(attempt['state']) and ar['decision']==attempt['actual_decision']
if cases[35]['status']=='PASSED':
 reopening=quality['reopening'];entry=reopening['actual_batch'];index=reopening['proposal_index'];proposal=entry['batch']['proposals'][index]
 assert reopening['independent_receipt']['input_sha256']==sha(entry['batch']) and reopening['recomputed']['features']['reopens_root'] is True
 assert reopening['recomputed']['features']['quality_class']==proposal['score'][0]==0 and proposal['installed'] is False
if cases[40]['status']=='PASSED':
 occupied=component_attempts['occupied_compatible_UI_source'];assert 'whole_actual_receipt' in occupied
 assert by[fibre_names[0]]['actual_matches']
if cases[41]['status']=='PASSED':
 incompatible=quality['incompatible_read'];ab=incompatible['whole_actual_batch'];ar=incompatible['whole_actual_receipt']
 assert ar['input_sha256']==sha(ab) and incompatible['conflicting_original_reads']
 assert canonical(incompatible['actual_rejection']['state'])==canonical(life['actual_rejection']['state'])
if cases[42]['status']=='PASSED':
 missing=quality['missing_source'];entry=missing['actual_batch'];ab=entry['batch'];ar=missing['whole_actual_receipt'];o=ab['proposals'][missing['proposal_index']]['ordered_PENDING_obligations'][missing['obligation_index']]
 assert ar['input_sha256']==sha(ab) and o['occupied'] is False and o['status']=='PENDING' and o['fact_accepted'] is False
 assert missing['missing_literal_point']==[1,o['row']]
reuse=quality['report_observation_reuse'];counts=reuse['counts'];sites=reuse['sites'];entries=reuse['entries'];authorities=reuse['authorities']
assert all(type(x) is int and x>=0 for x in counts.values()) and counts['report_hits']+counts['report_misses']==len(sites)
assert sum(x['reused'] is True for x in sites)==counts['report_hits'] and sum(x['reused'] is False for x in sites)==counts['report_misses']
assert len({x['origin_fresh_call'] for x in entries})==len(entries) and {x['origin_fresh_call'] for x in entries}=={x['origin_fresh_call'] for x in sites}
assert len({x['sha256'] for x in authorities})==len(authorities)
auth={x['sha256']:x['value'] for x in authorities}
for key,value in auth.items():
 assert sha(value)==key and value['source_bindings']==plan['sources'] and value['binding']==body['language_binding']
 assert value['declaration']==read(check(plan['inputs']['declaration'])) and value['policy']==read(check(plan['inputs']['profile']))
 assert value['validator_version']=='unit-row-independent-advice-consumer-validator-v3-compatible-fibres-versions'
 assert value['parameters']==value['declaration']['parameters'] and value['Gamma']==value['declaration']['ordered_Gamma'] and value['target']==value['declaration']['target'] and value['theory']==value['declaration']['theory']
 for keyset in ('forbidden','parameter_set','input_names','binder_names'):assert value[keyset]==sorted(set(value[keyset]))
origins={x['origin_fresh_call']:x for x in entries}
for number,x in origins.items():
 assert type(number) is int and 1<=number<=counts['fresh_calls'] and x['authority_sha256'] in auth
 st,d,ab,ar=x['state'],x['decision'],x['batch'],x['receipt']
 assert ab['status']=='READY' and ar['mode']=='ADVICE_BATCH' and ar['binding']==body['language_binding'] and ar['decision']==d==ab['decision']
 assert ar['state_sha256']==sha(st)==ab['state_sha256'] and ar['input_sha256']==sha(ab) and all(ar[k] is False for k in strong)
for x in sites:
 assert x['site'] in ('fixture-scoring','returned-batch-observation','reopening-observation','incompatible-read-observation','missing-source-observation') and type(x['reused']) is bool
 y=origins[x['origin_fresh_call']]
 for field,key in (('state','state_sha256'),('decision','decision_sha256'),('batch','batch_sha256'),('receipt','receipt_sha256')):assert sha(y[field])==x[key]
 if x['site']=='fixture-scoring':reference={'state':fixture['state'],'decision':fixture['decision'],'batch':fixture['batch'],'receipt':scoring['actual_independent_receipt']}
 elif x['site']=='reopening-observation':
  z=quality['reopening'];reference=dict(z['actual_batch'],receipt=z['independent_receipt'])
 elif x['site']=='incompatible-read-observation':
  z=quality['incompatible_read'];reference={'state':z['actual_rejection']['state'],'decision':z['actual_rejection']['decision'],'batch':z['whole_actual_batch'],'receipt':z['whole_actual_receipt']}
 elif x['site']=='missing-source-observation':
  z=quality['missing_source'];reference=dict(z['actual_batch'],receipt=z['whole_actual_receipt'])
 else:
  observations=quality['returned_observations']['batches'];assert any(z['batch_sha256']==x['batch_sha256'] and z['state_sha256']==x['state_sha256'] and z['independent_receipt_sha256']==x['receipt_sha256'] for z in observations);continue
 for key in ('state','decision','batch','receipt'):assert canonical(y[key])==canonical(reference[key])
coverage=list(controls['additional_coverage_gaps'])+[{'case':x['case'],'reason':x['observed']['reason']} for x in cases if x['status']=='SKIPPED']
out={'schema':'ROOT-advice-consumer-controls-disposition-v16-ABC','plan':pp,'outputs':outputs,'status':'QUALIFIED_LOCAL_CONSUMER_CONTROLS' if qualified else 'PARTIAL_LOCAL_CONSUMER_CONTROLS_TARGETS_NOT_ADMITTED','controls_accepted':qualified,'passed_cases':passed,'skipped_cases':skipped,'declared_cases':43,'all_advice_consumer_gates_qualified':qualified,'additional_coverage_gaps':coverage,
 'unqualified_continuation_observations':progress,'unqualified_native_timeline':native_timeline,'continuation_record_cap':24,'continuation_pairing_claimed':False,
 'complete_wire_verified':True,'lossless_transport_concordance':pin(HERE/'ROOT-advice-controls-transport-concordance-v1.json'),
 'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,'language_binding':body['language_binding'],'resource_rule':'single-owned-process-native-terminal-v1; B=T','all_reaped':True,'actual_closed':True,
 'actual_adviser_return':{'status':batch['status'],'reason':batch['reason'],'limits':batch['limits'],'work':batch['work'],'proposals':len(batch['proposals']),'independently_validated':True},
 'selected_family':{'fixture_ref':'fixture','role':'original first-ranked batch and anchor-only adoption','anchor_row':selection['anchor']['placement_key']['translation'][1],'future_rows':[k['translation'][1] for k in future],'scheme':batch['proposals'][0]['scheme'],'snapshot_sha256':sha(inner)},
 'selective_C_fixture_evidence':dict(c_join,remote=c_remote_join,retirement_fresh_event_start=len(forced_prefix),retirement_fresh_events=len(forced_events)),
 'paired_fixture_evidence':{'fixture_ref':'pending_success_fixture','original_fixture_ref':'fixture','distinct_control_contexts':True,'seed_state_sha256':sha(sibling_state),'seed_candidates_sha256':sha(seeds),'whole_actual_batch_sha256':sha(sibling_batch),'whole_actual_receipt_sha256':sha(sibling_receipt),'family_id':sibling_family,'future_rows':[k['translation'][1] for k in sibling_future],'inner_snapshot_sha256':sha(sibling_inner),'actual_pending_calls':len(pending_calls),'successful_pending_calls':len(successful_calls),'literal_event_joins':pending_event_joins,'inner_and_outer_restored':True,'scientific_replay':False},
 'scope':'Current original-language43-case controls: explicit A first-ranked adoption, B pending success and control-only C selective remote/forced contexts; all case names/checks preserved, exact whole report-only receipt reuse and genuine accepted scheduled context component; actual skips unqualified. No target or theorem discovery/full trajectory claim.',
 'family_retirement_evidence':{'all_eight_prior_lifecycle_cases_reconciled':True,'abandonment_event_sha256':sha(abandoned_event),'actual_rejected_keys':len(rr['rejections']),'abandoned_pending_keys':len(pending['pending_keys']),'different_legal_future_key_checked':True,'same_branch_fresh_calls':1,'later_fresh_calls':len(calls)},
 'fair_interface_evidence':{'prior_quality_case_names':new_quality_names,'new_source_case_names':fibre_names,'actual_returned_batch_sha256':sha(batch),'source_scoring_rows_reconciled':True,'replacement_passed':replacement_cases[0]['status']=='PASSED','no_generation_inferred_from_topk_absence':True,'finite_index_dynamic_calibration':False,'multi_term_control_calibration':False},
 'observation_reuse_evidence':{'counts':counts,'report_sites':len(sites),'full_used_origins':len(entries),'full_authorities':len(authorities),'all_saved_raw_joins_verified':True,'occupied_context_saved_joins_verified':'actual_callback' in component_attempts['occupied_compatible_UI_source'],'scientific_replay':False},
 'conformance_gaps':['No full graph/trajectory conformance or arbitrary all-six EOF authority.','Fixed24unit rows, no fractional/shared positive support or universal fixed Wang palette.','Hand-written advice, no learned/RL/lemma inventory or proof-search gain.','Finite heuristic pools/rounds plus one-best-anchor dedup can omit interfaces.'],
 'target_admission_qualified':qualified,'broad_goal_complete':False,'previous_goal_turn':'progress','current_goal_turn':'progress','scientific_replay':False,'author_identity':'/root/arithmetic_induction','author_overlap':'Author owns paired adviser/engine/c354 and saved closer antecedents. This helper checks saved literal wire/resource/fixture lineage; no independent semantic replay or new scientific acceptance.'}
q=HERE/'ROOT-advice-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'passed':passed,'skipped':skipped,'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date,'target_admission_qualified':qualified}))
