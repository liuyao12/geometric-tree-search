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
transport=read(HERE/'ROOT-advice-controls-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));controls=result['controls'];cases=controls['cases']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert result['purpose']=='unit-row-advised-advice-controls' and result['search'] is None and result['found_validation'] is None
contract=read(HERE.parent/'unit-row-goal-advice-controls-source-20261016/Source-contract-v1.json')
assert controls['schema']=='unit-row-goal-advice-controls-v1' and controls['all_declared_cases_completed'] is True
assert [x['case'] for x in cases]==contract['cases'] and len(cases)==22
passed=[x for x in cases if x['status']=='PASSED'];skipped=[x for x in cases if x['status']=='SKIPPED']
assert len(passed)==controls['passed']==2 and len(skipped)==controls['skipped']==20
assert [x['case'] for x in passed]==contract['cases'][-2:]
assert {x['observed']['reason'] for x in skipped}=={'Actual bounded adviser returned no current READY proposal: UNKNOWN'}
assert controls['all_advice_consumer_gates_qualified'] is False and controls['additional_coverage_gaps']==[]
assert controls['unqualified_consumer_gates']==contract['cases'][:-2]
assert not any(x in controls['artifacts'] for x in ('fixture','quota_UNKNOWN','empty_search','quota_search'))
dead=controls['artifacts']['dead_search'];forced=controls['artifacts']['forced_search']
assert dead['status']=='EXHAUSTED' and dead['found'] is None and dead['root_restored'] is True
assert not any(e['kind']=='ADVICE' for e in dead['events'])
assert forced['status']=='UNKNOWN' and forced['found'] is None and forced['root_restored'] is True
assert forced['counts']['forced']==1 and not any(e['kind']=='ADVICE' for e in forced['events'])
assert all(controls[k] is False for k in ('complete_GCTS_model_accepted','degree_or_EOF_accepted','scheduler_accepted','logical_proof_accepted','exact_point_board_accepted','trajectory_accepted','learned_marking_accepted','RL_accepted','ROOT_resource_accepted'))
out={'schema':'ROOT-advice-consumer-controls-disposition-v1','plan':pp,'outputs':outputs,
 'status':'UNQUALIFIED_CONSUMER_COVERAGE','controls_accepted':False,'passed_cases':len(passed),'skipped_cases':len(skipped),
 'all_advice_consumer_gates_qualified':False,'additional_coverage_gaps':controls['additional_coverage_gaps'],
 'complete_wire_verified':True,'lossless_transport_concordance':pin(HERE/'ROOT-advice-controls-transport-concordance-v1.json'),
 'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,
 'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,'language_binding':body['language_binding'],
 'resource_rule':'single-owned-process-native-terminal-v1; B=T','all_reaped':True,'actual_closed':True,
 'scope':'Two actual global priority controls passed; twenty adviser/currentpending/rollback consumer cases skipped for genuine UNKNOWN advice. No target search admitted.',
 'observation':'UNKNOWN status saved as skip reason only; harness did not retain actual partial adviser batch, so cause/work counts/partial proposal counts are unavailable.',
 'target_arms_admitted':False,'logical_proof_accepted':False,'GCTS_search_trajectory_accepted':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'broad_goal_complete':False,
 'previous_goal_turn':'progress','current_goal_turn':'progress','old_UNKNOWNs_preserved':True,
 'reconciliation_scope':'Whole saved wire/source/marker/native/status/receipt field concordance only; no scientific functions or proof replay.'}
q=HERE/'ROOT-advice-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'passed':len(passed),'skipped':len(skipped),'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date}))
