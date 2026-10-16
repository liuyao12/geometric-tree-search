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
assert len(cases)==17 and len({c['case'] for c in cases})==17
passed=[c for c in cases if c['status']=='PASSED'];skipped=[c for c in cases if c['status']=='SKIPPED']
assert len(passed)==17 and not skipped
expected=['late-global-ZERO-before-earlier-singleton','global-forced-before-branch',
 'real-EOF-singleton-without-independent-cover-UNKNOWN','real-EOF-singleton-current-cover-FORCED',
 'interrupted-zero-prefix-not-ZERO','interrupted-one-prefix-not-SINGLETON','unseen-remote-key-invalidated',
 'remote-singleton-stream-cover-key-agreement','omitted-stream-survivor-rejected',
 'rollback-revives-unseen-key-and-cursor-position','exact-ordered-child-alternatives-and-restoration',
 'assumed-exclusions-change-context-not-universe','UNKNOWN-child-never-excluded',
 'callback-exhaustion-poisons-real-cursor','abort-poisons-real-cursor',
 'synthetic-varied-generation-and-ROW-TIE','synthetic-global-priority-with-UNKNOWN']
assert [c['case'] for c in cases]==expected
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
result_out={'schema':'ROOT-unit-row-global-engine-controls-disposition-v1','plan':pp,'outputs':outputs,
 'controls_accepted':True,'passed_cases':17,'skipped_cases':0,'complete_wire_verified':True,'native_resources_qualified':True,
 'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes':peak,'terminal_T_bytes':peak,
 'complete_Date_seconds':date,'language_binding':body['language_binding'],'resource_rule':'single-owned-process-native-terminal-v1; B=T',
 'scope':'Original17 controls on current retained-domain engine; constructed original-language global/remote/cursor/rollback cases, declared incomplete transport seams and two separate NONLOGICAL scheduler calibrations. No target search in this endpoint.',
 'conformance_gaps':['Current sufficient retention with conservative global-ledger invalidation, no full reference conformance.','General all-six independent EOF/exhaustion certifier absent.','Specialized24unit rows only.'],
 'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'logical_proof_accepted':False,'GCTS_marking_activated':False,
 'RL_accepted':False,'GCTS_advantage_claimed':False,'broad_goal_complete':False,'previous_goal_turn':'progress',
 'old_UNKNOWNs_and_finite_negative_preserved':True,'reconciliation_scope':'Whole saved raw bytes, complete receipts/wire/native/caller metadata only; no Source/kernel/checker/model/word/degree replay.'}
result_out['lossless_transport_concordance']=pin(HERE/'ROOT-original-controls-transport-concordance-v1.json')
out=HERE/'ROOT-original-controls-disposition-v1.json'
with out.open('x') as f:json.dump(result_out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'disposition':pin(out),'passed':len(passed),'skipped':len(skipped),
    'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date}))
