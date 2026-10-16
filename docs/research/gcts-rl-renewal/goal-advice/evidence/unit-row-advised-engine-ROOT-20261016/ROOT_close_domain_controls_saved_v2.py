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
mode='domain-controls'
plan_path=HERE/'ROOT-domain-controls-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'domain-controls-owned-v1';external=HERE/'domain-controls-external-v1'
bracket=read(HERE/'ROOT-domain-controls-tool-bracket-v1.json')
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
transport=read(HERE/'ROOT-domain-controls-transport-concordance-v1.json')
assert transport['plan']==pp and transport['encoded_file']==outputs[0] and transport['all_full_record_bytes_retained'] is True
result=read(check(transport['expanded_file']));controls=result['controls'];cases=controls['cases']
assert result['purpose']=='unit-row-advised-domain-controls' and result['search'] is None and result['found_validation'] is None
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert result['search_work_bounds']=={'maximum_nodes':128,'maximum_events':2000}
assert controls['schema']=='unit-row-retained-domain-controls-v1' and controls['all_declared_cases_completed'] is True
assert controls['original_height']==24 and controls['original_root_generations']==0 and controls['no_target_search_call'] is True
contract_path=HERE.parent/'unit-row-advised-domain-controls-source-20261015/Source-contract-v2.json'
assert pin(contract_path)['sha256']=='2290c598eac6d39e8e164787668971cda88962f3b689353169038919dd8dff63'
expected={c['case'] for c in read(contract_path)['cases']}
assert len(cases)==17 and {c['case'] for c in cases}==expected and all(c['status']=='PASSED' for c in cases)
by={c['case']:c['observed'] for c in cases}
def sha(x):return hashlib.sha256(canonical(x)).hexdigest()
def slot(snapshot,row):return dict(snapshot['cursors'])[row]
def proof(snapshot,row):return next(x for x in snapshot['last_transition']['rows'] if x['row']==row)
def archive_has(slot,old):
 return any(all(canonical(entry[k])==canonical(old[k]) for k in ('context','keys','candidates','completion')) for entry in slot['context_archive'])
o=by['retained-domain-refreshes-only-read-occupancy'];before=o['before'];after=o['after']
assert proof(after,3)['retain'] is True and after['last_transition']['collision_ledger_equal'] is True
assert proof(after,3)['read_occupancy_changes']==[1] and after['row_versions'][3]==before['row_versions'][3]
assert after['row_versions'][1]>before['row_versions'][1]
a,b=slot(before,3),slot(after,3)
assert canonical(a['keys'])==canonical(b['keys']) and canonical(a['context'])==canonical(b['context']) and canonical(a['completion'])==canonical(b['completion'])
assert archive_has(b,a) and all(v['occupied'] is True for c in b['candidates'] for v in c['read_obligations'])
t=by['old-receipt-unchanged-explicit-transfer'];receipt=t['original_receipt'];trans=t['current_transfer']
assert receipt['schema']=='unit-row-degree-evidence-check-v2' and receipt['status']=='MANY' and receipt['degree_exact']==2
assert trans['schema']=='unit-row-transferred-domain-classification-v1' and canonical(trans['original_receipt'])==canonical(receipt)
assert receipt['state_sha256']==sha(before['state']) and trans['state_sha256']==sha(after['state']) and receipt['state_sha256']!=trans['state_sha256']
f=by['refresh-independent-current-packets-input-unchanged'];assert canonical(f['current'])==canonical(b['candidates'])
for name,reason in [('refresh-forged-core-rejected','unchanged entire core'),('refresh-duplicate-full-key-rejected','unique known full keys'),('current-illegal-old-candidate-refresh-rejected','retained candidate whole current legality'),('transition-stale-epoch-rejected','private epoch/profile'),('transition-Boolean-row-rejected','literal sorted distinct queried rows')]:
 x=by[name];assert x['exception_type']=='ValueError' and reason in x['reason']
r=by['repeated-retention-before-replay-does-not-relabel-archive'];s=slot(r['after_two_transitions'],3)
assert archive_has(s,r['old_slot']) and canonical(s['context'])==canonical(r['old_slot']['context']) and canonical(s['completion'])==canonical(r['old_slot']['completion'])
c=by['fresh-full-prefix-replay-before-current-EOF'];events=c['actual_new_cursor']['events']
assert [e['kind'] for e in events]==['CANDIDATE','CANDIDATE','EOF'] and [e['ordinal'] for e in events[:-1]]==[0,1]
assert c['returned']['kind']=='EOF' and archive_has(c['new_slot'],a)
m=by['multiple-transitions-preserve-literal-context-EOF-archives'];ms=slot(m['after_second'],3);prior=slot(m['before_second'],3)
assert m['returned']['kind']=='EOF' and archive_has(ms,a) and archive_has(ms,prior)
assert len(dict(m['after_second']['certificates'])[3]['transfer_chain'])==3
p=by['fresh-prefix-replay-before-new-candidate'];assert p['first']['kind']==p['second']['kind']=='CANDIDATE'
assert [e['ordinal'] for e in p['actual_new_cursor']['events']]==[0,1]
assert p['first']['candidate']['placement_key']!=p['second']['candidate']['placement_key']
n=by['nonempty-archive-checkpoint-rollback-and-repeat-continuation']
assert canonical(n['checkpoint_snapshot'])==canonical(n['restored_snapshot'])
assert slot(n['checkpoint_snapshot'],3)['context_archive']
assert canonical(n['original_continuation'])==canonical(n['repeated_continuation'])
assert [e['kind'] for e in n['actual_fresh_cursor']['events']]==['CANDIDATE','CANDIDATE']
assert [e['ordinal'] for e in n['actual_fresh_cursor']['events']]==[0,1]
assert canonical(slot(n['after_repeated_continuation'],3)['context_archive'])==canonical(slot(n['checkpoint_snapshot'],3)['context_archive'])
i=by['interrupted-retained-replay-never-EOF'];assert i['exception_type']=='CallbackExhausted' and canonical(i['before'])==canonical(i['after'])
assert len(i['actual_cursor']['events'])==1 and i['actual_cursor']['events'][0]['kind']=='CANDIDATE' and i['actual_cursor']['interrupted_after_candidates']==1
r=by['same-UG-prototype-remote-marks-retain-earlier-invalidate-affected'];assert proof(r['after'],1)['retain'] is True
assert r['after']['last_transition']['collision_ledger_equal'] is True and all(proof(r['after'],row)['retain'] is False for row in (3,4,5))
x=by['local-exclusion-stable-ledger-invalidates-own-row']['transition'];rows={v['row']:v for v in x['rows']}
assert x['collision_ledger_equal'] is True and rows[1]['retain'] is False and rows[3]['retain'] is True
x=by['new-global-prototype-ledger-invalidates-all-domains'];assert x['after']['last_transition']['collision_ledger_equal'] is False
assert all(v['retain'] is False for v in x['after']['last_transition']['rows']) and x['after']['certificates']==x['after']['cursors']==x['after']['exposed_candidates']==[]
assert all(controls[k] is False for k in ('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','exact_point_board_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted'))
out={'schema':'ROOT-retained-domain-controls-disposition-v1','plan':pp,'outputs':outputs,'controls_accepted':True,'passed_cases':17,'skipped_cases':0,
 'complete_wire_verified':True,'lossless_transport_concordance':pin(HERE/'ROOT-domain-controls-transport-concordance-v1.json'),
 'native_resources_qualified':True,'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,
 'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,'language_binding':body['language_binding'],
 'resource_rule':'single-owned-process-native-terminal-v1; B=T','scope':'Seventeen original-language retained-domain, full receipt/context/EOF archive, remote invalidation, known-packet refresh and exact rollback controls. One explicit real-replay interruption seam. Manual transactions, no target discovery or accepted full scheduler trajectory.',
 'conformance_gaps':['Conservative sufficient support/global-collision-ledger relation, no minimal dependency oracle or full reference incremental conformance.','No general independent all-six EOF/exhaustion cover.','Specialized fixed unit rows, no fractional/shared positive support or full mathematical logic.'],
 'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'logical_proof_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'broad_goal_complete':False,
 'prior_raw_cap_UNKNOWN_preserved':True,'old_actuals_UNKNOWNs_and_finite_negatives_preserved':True,'previous_goal_turn':'progress','current_goal_turn':'progress',
 'reconciliation_scope':'Whole saved decoded bytes, marker/wire/source/context/native and raw observed field concordance only; no mathematical/control/checker/kernel/search replay.'}
q=HERE/'ROOT-domain-controls-disposition-v1.json'
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'passed':17,'skipped':0,'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date}))
