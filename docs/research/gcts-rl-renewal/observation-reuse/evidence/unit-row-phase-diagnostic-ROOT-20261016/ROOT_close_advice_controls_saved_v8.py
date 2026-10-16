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
phase_spec=read(HERE.parent/'unit-row-phase-diagnostic-controls-source-20261016/Source-contract-v3.json')['phase_stderr']
assert (external/'meter-stderr.txt').read_bytes()==''.join(x+'\n' for x in phase_spec['ordered_literals']).encode('ascii')
assert not (external/'postterminal-probe-stderr.txt').read_bytes()
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
transport=read(HERE/'ROOT-advice-controls-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));controls=result['controls'];cases=controls['cases']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert result['purpose']=='unit-row-advised-advice-controls' and result['search'] is None and result['found_validation'] is None
contract=read(HERE.parent/'unit-row-phase-diagnostic-controls-source-20261016/Source-contract-v3.json')
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
fixture=art['fixture'];attempt=art['fixture_advice_attempt'];batch=attempt['actual_adviser_return'];receipt=fixture['receipt'];selection=receipt['selection']
assert canonical(attempt['state'])==canonical(fixture['state']) and canonical(batch)==canonical(fixture['batch'])
assert batch['status']=='READY' and batch['reason'] is None and batch['limits']=={'maximum_work':50000,'maximum_proposals':8,'maximum_demands':5,'maximum_terms':1,'maximum_rounds':3}
assert 0<batch['work']['guarded_steps']<=batch['limits']['maximum_work'] and batch['work']['rounds']==3 and len(batch['proposals'])>=2
assert batch['state_sha256']==attempt['pre_advice_state_sha256']==sha(fixture['state'])==receipt['state_sha256']
assert batch['binding']==receipt['binding']==body['language_binding'] and receipt['input_sha256']==sha(batch) and receipt['mode']=='ADVICE_BATCH'
assert batch['decision']==receipt['decision']==fixture['decision']=={'kind':'BRANCH','row':0}
assert canonical(selection['anchor'])==canonical(batch['proposals'][0]['members'][0]['candidate'])
future=selection['future_keys'];assert [k['translation'][1] for k in future]==[2,8]
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
rr=art['remote_receipts'];bad=art['remote_fixture']['invalidated_pending_key']
assert any(canonical(x['key'])==canonical(bad) and x['reason']=='whole_remote_or_metadata_mark_conflict' for r in rr for x in r['rejections'])
fb=by['rejected-pending-hint-preserves-canonical-choice']['actual_fallback_event'];assert fb['mode']=='CANONICAL_FALLBACK' and fb['rejected_keys']
fr=art['forced_retirement'];r=fr['search'];assert r['status']=='UNKNOWN' and r['root_restored'] and r['stack_restored'] and r['root_snapshot_sha256']==r['final_snapshot_sha256']
assert {e['row'] for e in r['events'] if e['kind']=='TRY' and e['mode']=='FORCED'}>={2,8}
retired=by['global-forced-fill-retires-family-before-fresh-advice']['retired_keys'];assert {canonical(k) for k in retired}=={canonical(k) for k in future}
assert any(e['kind']=='ADVICE' and {canonical(k) for k in e['retired_keys']}=={canonical(k) for k in future} and e['pending_preferences'] is None for e in r['events'])
assert art['dead_search']['status']=='EXHAUSTED' and art['dead_search']['counts']['advice_calls']==0 and art['forced_search']['counts']['advice_calls']==0
life=art['family_retirement'];rejection=life['actual_rejection'];inner_before=rejection['owned_inner_snapshot'];pending=inner_before['pending_preferences']
abandoned_event=rejection['abandonment_event'];abandoned=abandoned_event['abandoned_family'];req=rejection['batch'];rr=rejection['actual_receipt']
assert any(canonical(e)==canonical(abandoned_event) for e in art['remote_search']['events'])
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
   assert cb['before_child_adoption_and_placement'] is True and cb['decision']==attempt['actual_decision']
   assert canonical(cb['snapshot']['state'])==canonical(attempt['state'])
   cr=cb['receipt'];assert cr['mode']=='PENDING_KEYS' and cr['selection'] is not None and cr['rejections']==[]
   assert cr['input_sha256']==sha(cb['request']) and cr['state_sha256']==sha(attempt['state']) and cr['decision']==attempt['actual_decision']
   assert canonical(attempt['finished_outer_before'])==canonical(attempt['finished_outer_after']) and attempt['restored_sha256']==sha(attempt['finished_outer_after'])
   ax=attempt['declaration']['selected_original_AX_record'];assert any(canonical(x)==canonical(ax) for x in attempt['state']['selected']) and ax['translation']==[0,1]
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
out={'schema':'ROOT-advice-consumer-controls-disposition-v8','plan':pp,'outputs':outputs,'status':'QUALIFIED_LOCAL_CONSUMER_CONTROLS' if qualified else 'PARTIAL_LOCAL_CONSUMER_CONTROLS_TARGETS_NOT_ADMITTED','controls_accepted':qualified,'passed_cases':passed,'skipped_cases':skipped,'declared_cases':43,'all_advice_consumer_gates_qualified':qualified,'additional_coverage_gaps':coverage,
 'complete_wire_verified':True,'lossless_transport_concordance':pin(HERE/'ROOT-advice-controls-transport-concordance-v1.json'),
 'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,'language_binding':body['language_binding'],'resource_rule':'single-owned-process-native-terminal-v1; B=T','all_reaped':True,'actual_closed':True,
 'actual_adviser_return':{'status':batch['status'],'reason':batch['reason'],'limits':batch['limits'],'work':batch['work'],'proposals':len(batch['proposals']),'independently_validated':True},
 'selected_family':{'anchor_row':0,'future_rows':[2,8],'scheme':batch['proposals'][0]['scheme'],'snapshot_sha256':sha(inner)},
 'scope':'Current original-language43-case controls: all case names/checks preserved, exact whole report-only receipt reuse and genuine accepted scheduled context component; actual skips unqualified. No target or theorem discovery/full trajectory claim.',
 'family_retirement_evidence':{'all_eight_prior_lifecycle_cases_reconciled':True,'abandonment_event_sha256':sha(abandoned_event),'actual_rejected_keys':len(rr['rejections']),'abandoned_pending_keys':len(pending['pending_keys']),'different_legal_future_key_checked':True,'same_branch_fresh_calls':1,'later_fresh_calls':len(calls)},
 'fair_interface_evidence':{'prior_quality_case_names':new_quality_names,'new_source_case_names':fibre_names,'actual_returned_batch_sha256':sha(batch),'source_scoring_rows_reconciled':True,'replacement_passed':replacement_cases[0]['status']=='PASSED','no_generation_inferred_from_topk_absence':True,'finite_index_dynamic_calibration':False,'multi_term_control_calibration':False},
 'observation_reuse_evidence':{'counts':counts,'report_sites':len(sites),'full_used_origins':len(entries),'full_authorities':len(authorities),'all_saved_raw_joins_verified':True,'occupied_context_saved_joins_verified':'actual_callback' in component_attempts['occupied_compatible_UI_source'],'scientific_replay':False},
 'conformance_gaps':['No full graph/trajectory conformance or arbitrary all-six EOF authority.','Fixed24unit rows, no fractional/shared positive support or universal fixed Wang palette.','Hand-written advice, no learned/RL/lemma inventory or proof-search gain.','Finite heuristic pools/rounds plus one-best-anchor dedup can omit interfaces.'],
 'target_admission_qualified':qualified,'broad_goal_complete':False,'previous_goal_turn':'progress','current_goal_turn':'progress','scientific_replay':False}
q=HERE/'ROOT-advice-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'passed':passed,'skipped':skipped,'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date,'target_admission_qualified':qualified}))
