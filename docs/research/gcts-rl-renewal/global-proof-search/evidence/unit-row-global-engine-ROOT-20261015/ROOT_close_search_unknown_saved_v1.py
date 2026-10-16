"""Complete saved failed-lifecycle reconciliation only; no scientific replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
plan_path=HERE/'ROOT-search-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
external=HERE/'search-external-v1';bracket=read(HERE/'ROOT-search-tool-bracket-v1.json')
assert pp['sha256']=='3694b48eda0bfb98b126f4fb475575d10b516fc18bac080c84e66e916a5cb751'
assert plan['purpose']=='unit-row-global-engine-search' and not (HERE/'search-owned-v1').exists()
assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes'] and bracket['tool_exit_code']==2 and bracket['tool_session_id'] is None
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<date<=60 and date+1<=90
for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(ref)
native=read(external/'native-terminal.json');obs=read(external/'observation.json');once=read(external/'ONCE.json')
for value in (obs,once):assert value['plan_sha256']==pp['sha256'] and value['plan_bytes']==pp['bytes'] and value['invocation_id']==plan['invocation_id']
assert obs['meter_returncode']==2 and obs['probe_returncode']==0
assert native['all_reaped'] is True and native['caller_returncode']==2 and native['wait4_status']==512
assert native['caller_pid']==native['wait4_pid'] and native['error'] is None and native['interrupted'] is False and native['cancellation_forwarded'] is False
assert not (external/'meter-stdout.txt').read_bytes() and not (external/'postterminal-probe-stderr.txt').read_bytes()
stderr=(external/'meter-stderr.txt').read_bytes()
assert stderr==b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete local-degree controls original20/500 reserve unfinished\n'
probe=int((external/'postterminal-probe-stdout.txt').read_bytes());assert probe==obs['postterminal_native_probe_ns']
start,terminal=native['caller_launch_began_ns'],native['caller_terminal_observed_ns']
assert start<terminal<=probe and terminal-start==native['caller_kernel_elapsed_ns'] and probe-start>20000000000
peak=native['wait4_usage'][2];assert type(peak) is int and peak==native['caller_kernel_peak_bytes'] and 0<peak<536870912
out={'schema':'ROOT-unit-row-global-search-UNKNOWN-disposition-v1','plan':pp,
 'status':'UNKNOWN','reason':'Original native20s deadline; worker exited2 before complete engine output. Positive native gate not qualified.',
 'actual_closed':True,'native_lifecycle_observation_verified':True,'all_reaped':True,'native_resources_qualified':False,
 'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,
 'resource_rule':'single-owned-process-native-terminal-v1; B=T','worker_exit_code':2,'complete_worker_result_available':False,
 'search_counts':None,'search_trace':None,'observed_prefix':None,'root_or_stack_restoration_runtime_verified':False,
 'scope':'One cold search from original right-two initialstate, same declaration/profile/all-six universe/height24, named ROW-TIE+ALL24-REBIND variant, node128/event2000 ceilings. No word/donor/library input.',
 'independent_proof_accepted':False,'GCTS_search_trajectory_accepted':False,'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
 'nonprovability_claimed':False,'old_UNKNOWNs_preserved':True,'broad_goal_complete':False,'previous_goal_turn':'progress',
 'raw_evidence':[pin(external/n) for n in ('ONCE.json','meter-stdout.txt','meter-stderr.txt','native-terminal.json','observation.json','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt')],
 'next_action':'Preserve unknown. Add bounded failure-only diagnostics without changing20s acceptance, and test a separately frozen retained-domain engine successor. Do not restart unchanged actual.'}
p=HERE/'ROOT-search-disposition-v1.json'
with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'disposition':pin(p),'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date,'status':'UNKNOWN'}))
