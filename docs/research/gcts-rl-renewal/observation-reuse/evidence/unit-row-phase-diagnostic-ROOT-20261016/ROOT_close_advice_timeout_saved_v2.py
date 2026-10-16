"""Saved native/once failure lifecycle only; no model or scientific replay."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r
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
spec=read(HERE.parent/'unit-row-phase-diagnostic-controls-source-20261016/Source-contract-v3.json')['phase_stderr']
prefix=stderr[:-len(error_line)];observed=prefix.decode('ascii').splitlines()
assert prefix==''.join(x+'\n' for x in observed).encode('ascii') and observed==spec['ordered_literals'][:len(observed)] and len(observed)<=10 and len(prefix)<=spec['maximum_full_sequence_bytes']

assert n['caller_returncode']==2 and n['wait4_status']==512 and n['all_reaped'] is True and n['caller_pid']==n['wait4_pid']
assert n['error'] is None and n['interrupted'] is False and n['cancellation_forwarded'] is False
start=n['caller_launch_began_ns'];terminal=n['caller_terminal_observed_ns'];peak=n['wait4_usage'][2]
assert terminal-start==n['caller_kernel_elapsed_ns'] and start<terminal<=probe and 20000000000<probe-start<55000000000
assert type(peak) is int and 0<peak==n['caller_kernel_peak_bytes']<536870912
assert not (HERE/'advice-controls-owned-v1').exists()
for mode in ('canonical-search','advised-search'):assert not (HERE/('ROOT-'+mode+'-plan-v1.json')).exists()
out={'schema':'ROOT-phase-diagnostic-consumer-timeout-disposition-v1','plan':pp,'status':'UNKNOWN_NATIVE20_NO_RETURNED_CONTROL_RECORD','actual_closed':True,'all_reaped':True,'failure_lifecycle_verified':True,'controls_accepted':False,'native_resources_qualified':False,'all_advice_consumer_gates_qualified':False,'declared_cases':43,'passed_cases':None,'skipped_cases':None,'case_counts_accepted':False,'returned_control_record':False,'stage_or_phase_coverage_known':False,'unqualified_phase_prefix_available':bool(observed),'unqualified_observed_phase_markers':observed,'last_unqualified_marker':observed[-1] if observed else None,'phase_duration_known':False,'previous_actual_phase_attribution':False,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes_observed':peak,'terminal_T_bytes_observed':peak,'complete_Date_seconds':date,'resource_rule':'single-owned-process-native-terminal-v1; B=T','raw_evidence':[pin(x) for x in sorted(e.iterdir())],'target_admission_qualified':False,'target_plans_issued':0,'target_actuals_launched':0,'scope':'Fresh phase-instrumented43 currentSource17 stage did not complete original native20 gate; no encoded/expanded control record returned. Fixed bounded literal stderr prefix is producer reached-write diagnosis only. No case pass/skip count, completed phase, useful proposal, duration, logical proof, trajectory or native-positive admission inferred. No attribution to earlier uninstrumented actuals.','nonprovability_claimed':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,'scientific_replay':False,'previous_goal_turn':'progress','current_goal_turn':'progress','broad_goal_complete':False,'next_action':'Preserve this actual; do not restart unchanged or increase limits/remove cases. Diagnose/optimize a separately frozen reviewed Source successor under same endpoint, keeping full43 qualification and target scope.'}
q=HERE/'ROOT-advice-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'native_seconds':(probe-start)/1e9,'peak_observed':peak,'Date_seconds':date,'status':out['status']}))
