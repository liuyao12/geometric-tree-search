"""Saved native/once failure lifecycle only; no model or scientific replay."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
p=HERE/'ROOT-advice-controls-plan-v1.json';plan=read(p);pp=pin(p);e=HERE/'advice-controls-external-v1';b=read(HERE/'ROOT-advice-controls-tool-bracket-v1.json')
assert b['plan_sha256']==pp['sha256'] and b['plan_bytes']==pp['bytes'] and b['tool_exit_code']==2 and b['tool_session_id'] is None
date=(b['ended_Date_ms']-b['began_Date_ms'])/1000;assert date==b['complete_Date_seconds'] and 0<date<60 and date+1<90
for r in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(r)
n=read(e/'native-terminal.json');o=read(e/'observation.json');once=read(e/'ONCE.json')
for v in (o,once):
 assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes'] and v['invocation_id']==plan['invocation_id'] and v['purpose']==plan['purpose']
assert o['meter_returncode']==2 and o['probe_returncode']==0
probe=int((e/'postterminal-probe-stdout.txt').read_bytes());assert probe==o['postterminal_native_probe_ns']
assert not (e/'meter-stdout.txt').read_bytes() and not (e/'postterminal-probe-stderr.txt').read_bytes()
stderr=(e/'meter-stderr.txt').read_bytes();error_line=b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete local-degree controls original20/500 reserve unfinished\n'
assert stderr.endswith(error_line)
prefix=stderr[:-len(error_line)]
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

assert n['caller_returncode']==2 and n['wait4_status']==512 and n['all_reaped'] is True and n['caller_pid']==n['wait4_pid']
assert n['error'] is None and n['interrupted'] is False and n['cancellation_forwarded'] is False
start=n['caller_launch_began_ns'];terminal=n['caller_terminal_observed_ns'];peak=n['wait4_usage'][2]
assert all(start<=x['native_ns']<=terminal for x in native_timeline) and [x['native_ns'] for x in native_timeline]==sorted(x['native_ns'] for x in native_timeline)
for i,x in enumerate(native_timeline):
 x['elapsed_from_launch_ns']=x['native_ns']-start;x['interval_since_previous_ns']=x['native_ns']-(native_timeline[i-1]['native_ns'] if i else start)
samples=[{'marker':label,'native_ns':value,'elapsed_from_launch_ns':value-start,'previous_marker':observed[i-1] if i else None,'interval_since_previous_ns':value-(sample_values[i-1] if i else start)} for i,(label,value) in enumerate(zip(observed,sample_values))]
assert terminal-start==n['caller_kernel_elapsed_ns'] and start<terminal<=probe and 20000000000<probe-start<55000000000
assert type(peak) is int and 0<peak==n['caller_kernel_peak_bytes']<536870912
owned=HERE/'advice-controls-owned-v1';retained=None;inventory=[]
if owned.exists():
 assert owned.is_dir() and all(p.is_file() and not p.is_symlink() for p in owned.iterdir())
 inventory=[pin(p) for p in sorted(owned.iterdir())]
 if sorted(p.name for p in owned.iterdir())==['diagnostic-completion.json','unknown-diagnostic.json']:
  raw=(owned/'unknown-diagnostic.json').read_bytes();marker_raw=(owned/'diagnostic-completion.json').read_bytes()
  assert 0<len(raw)<=16384 and raw.endswith(b'\n') and raw.count(b'\n')==1 and 0<len(marker_raw)<=1025 and marker_raw.endswith(b'\n')
  def pairs(items):
   out={}
   for k,v in items:assert k not in out;out[k]=v
   return out
  record=json.loads(raw,object_pairs_hook=pairs);marker=json.loads(marker_raw,object_pairs_hook=pairs)
  assert set(record)=={'context','diagnostic','last_observations'}
  assert marker=={'schema':'unit-row-controls-last-context-completion-v1','file':'unknown-diagnostic.json','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'diagnostic_only':True,'positive_joint_gate_accepted':False,'ROOT_resource_accepted':False,'terminal_exit2_and_external_failure_closure_required':True}
  context=record['context'];g=context['joint_began_ns'];assert type(g) is int and start<=g<terminal and context['joint_deadline_ns']==g+20000000000
  for k in ('purpose','invocation_id','sources','inputs','limits'):assert context[k]==plan[k]
  assert context['plan']=={k:pp[k] for k in ('sha256','bytes')} and context['CLOCK_DOMAIN']=='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
  assert context['language_binding']==read(HERE/'ROOT-original-controls-disposition-v1.json')['language_binding']
  flags=record['diagnostic'];assert flags['schema']=='unit-row-controls-last-context-diagnostic-v1' and flags['diagnostic_only'] is True and flags['qualification']=='UNQUALIFIED_LAST_ADAPTER_NATIVE_OBSERVATIONS' and flags['failure_kind']=='TimeoutError'
  assert flags['callback_context']=='ENTRY_ARGUMENT_ROW_AND_SELECTED_COUNT_AT_LAST_SUCCESSFUL_EXISTING_NATIVE_CHECK'
  for k in ('returned_control_record','last_observation_is_active_failure_frame','live_state_or_proof_trajectory_accepted','positive_joint_gate_accepted','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','ROOT_resource_accepted'):assert flags[k] is False
  slots=record['last_observations'];assert set(slots)=={'proposer','fallback','completion','validator'}
  observations=[]
  for role,x in slots.items():
   if x is None:continue
   assert set(x)=={'stage','row','selected_count','native_ns'} and x['stage']==role.upper()+'_NATIVE_STEP'
   assert type(x['row']) is int and -1<=x['row']<24 and type(x['selected_count']) is int and -1<=x['selected_count']<=24
   assert type(x['native_ns']) is int and g<=x['native_ns']<g+20000000000 and x['native_ns']<=terminal and 0<=x['native_ns']<=9223372036854775807
   observations.append(dict(x,role=role,elapsed_from_launch_ns=x['native_ns']-start,last_observation_age_to_terminal_ns=terminal-x['native_ns'],last_observation_age_to_postprobe_ns=probe-x['native_ns']))
  observations.sort(key=lambda x:(x['native_ns'],x['role']))
  retained={'complete_raw_diagnostic_verified':True,'diagnostic_only':True,'files':inventory,'last_observations':observations,'unavailable_roles':[k for k,v in slots.items() if v is None],'context_native_began_ns':g,'context_native_deadline_ns':g+20000000000,'latest_record':observations[-1] if observations else None,'active_failure_frame_known':False,'live_state_or_proof_trajectory_accepted':False,'failure55_terminal_probe_resources_reconciled':True,'scientific_replay':False}

for mode in ('canonical-search','advised-search'):assert not (HERE/('ROOT-'+mode+'-plan-v1.json')).exists()
out={'schema':'ROOT-latest-context-consumer-timeout-disposition-v1','plan':pp,'status':'UNKNOWN_NATIVE20_NO_RETURNED_CONTROL_RECORD','actual_closed':True,'all_reaped':True,'failure_lifecycle_verified':True,'controls_accepted':False,'native_resources_qualified':False,'all_advice_consumer_gates_qualified':False,'declared_cases':43,'passed_cases':None,'skipped_cases':None,'case_counts_accepted':False,'returned_control_record':False,'stage_or_phase_coverage_known':False,'unqualified_phase_prefix_available':bool(observed),'unqualified_observed_phase_markers':observed,'last_unqualified_marker':observed[-1] if observed else None,'phase_duration_known':False,'unqualified_native_samples':samples,'unqualified_continuation_observations':progress,'unqualified_native_timeline':native_timeline,'continuation_record_cap':24,'continuation_pairing_claimed':False,'native_sample_read_intervals_concordant':True,'sample_reference':'Original captured nativeCLOCK_MONOTONIC reads returned by direct Rootmain.tick, relative to original external callerlaunch; intervals include output/checks/all intervening work, not exclusive-method costs. No new clock/G/reset, accepted cases or earlier attribution.','previous_actual_phase_attribution':False,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes_observed':peak,'terminal_T_bytes_observed':peak,'complete_Date_seconds':date,'resource_rule':'single-owned-process-native-terminal-v1; B=T','retained_latest_context':retained,'raw_diagnostic_inventory':inventory,'raw_evidence':[pin(x) for x in sorted(e.iterdir())],'target_admission_qualified':False,'target_plans_issued':0,'target_actuals_launched':0,'scope':'Fresh latest-context-instrumented43 currentSource17 stage did not complete original native20 gate; no encoded/expanded control record returned. Fixed bounded stderr phase/nativeint subsequence plus continuation stage/scalar records is diagnostic only. Native read differences are saved observations and not exclusive-method costs or qualified stage evidence. No case pass/skip count, completed phase, useful proposal, exclusive phase duration, logical proof, trajectory or native-positive admission inferred. No attribution to earlier uninstrumented actuals.','nonprovability_claimed':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,'scientific_replay':False,'previous_goal_turn':'progress','current_goal_turn':'progress','broad_goal_complete':False,'next_action':'Preserve this actual; do not restart unchanged or increase limits/remove cases. Diagnose/optimize a separately frozen reviewed Source successor under same endpoint, keeping full43 qualification and target scope.'}
q=HERE/'ROOT-advice-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'native_seconds':(probe-start)/1e9,'peak_observed':peak,'Date_seconds':date,'status':out['status'],'native_samples':samples,'continuation_observations':progress,'retained_latest_context':retained}))
