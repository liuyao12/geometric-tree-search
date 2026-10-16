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
plan_path=HERE/'ROOT-plan-v1.json';plan=read(plan_path);pp=pin(plan_path)
owned=HERE/'missing-owned-v1';external=HERE/'missing-external-v1'
bracket=read(HERE/'ROOT-tool-bracket-v1.json')
assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
assert bracket['tool_exit_code']==0 and bracket['tool_session_id'] is None
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
assert sorted(p.name for p in owned.iterdir())==['degree-controls.json','response.jsonl']
outputs=[pin(owned/n) for n in ('degree-controls.json','response.jsonl')]
lines=(owned/'response.jsonl').read_bytes().splitlines(keepends=True)
assert len(lines)==2 and all(x.endswith(b'\n') for x in lines)
body,completion=map(json.loads,lines)
assert completion['body_sha256']==hashlib.sha256(lines[0]).hexdigest() and completion['body_bytes']==len(lines[0])
assert completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True
assert body['schema']=='ROOT-unit-row-degree-controls-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
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
result=read(owned/'degree-controls.json');controls=result['controls'];cases=controls['cases']
assert result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['language_binding']==body['language_binding']
assert controls['all_declared_cases_completed'] is True
assert len(cases)==36 and len({c['case'] for c in cases})==36
passed=[c for c in cases if c['status']=='PASSED'];skipped=[c for c in cases if c['status']=='SKIPPED']
assert len(passed)==35 and [c['case'] for c in skipped]==['queried-row-metadata-conflict']
status={c['case']:c['observed']['receipt']['status'] for c in passed if 'receipt' in c['observed']}
assert status=={'initial-row0-two-named-AX':'TWO_OR_MORE','initial-final-universal-two-pending-UG':'TWO_OR_MORE',
    'covered-zero':'ZERO','imp-output-UNKNOWN':'UNKNOWN','missing-prefix-now-ZERO':'ZERO',
    'covered-original-AX-count':'SINGLETON','covered-many-UG-occurrences':'MANY',
    'assumed-exclusions-to-singleton':'SINGLETON','assumed-exclusions-to-zero':'ZERO',
    'missing42-two-MP-orders':'TWO_OR_MORE','missing42-assumed-singleton':'SINGLETON','missing42-assumed-zero':'ZERO','missing43-maxA0-zero':'ZERO'}
for c in passed:
    o=c['observed']
    if 'receipt' in o:
        r=o['receipt'];assert r['schema']=='unit-row-degree-evidence-check-v2';assert r['state_sha256']==o['proposal']['state_sha256'] and r['input_epoch']==body['language_binding']['language_epoch']
        assert r['accepted_local_evidence'] is (r['status']!='UNKNOWN')
        assert all(r[f] is False for f in ('complete_candidate_graph_accepted','scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'))
    elif c['case'].startswith('tiny-carrier-reference-'):
        assert o['maximum_nodes'] in (1,2) and o['count']==(1 if o['maximum_nodes']==1 else 37)
        assert o['actual']==o['reference'] and len(o['actual'])==o['count']
        assert hashlib.sha256(canonical(o['actual'])).hexdigest()==o['value_sha256']
    else:
        assert o['exception_type'] in ('ValueError','CallbackExhausted')
        if o['exception_type']=='CallbackExhausted':assert o['calls']==(1 if c['case']=='carrier-callback-exhaustion' else 17) and o['reason']=='CONTROL_CALLBACK_EXHAUSTED'
remote=next(c for c in cases if c['case']=='remote-formula-read-conflict')
assert 'whole candidate legality' in remote['observed']['reason'] and remote['observed']['fixture_checks']['actual_mark_conflict'] is True
assert sum(c['observed'].get('exception_type')=='ValueError' for c in passed)==17
assert sum(c['observed'].get('exception_type')=='CallbackExhausted' for c in passed)==3
missing=[]
for c in passed:
    r=c['observed'].get('receipt',{})
    if r.get('missing_mark_cover_checked'):
        assert r['complete_cover_checked'] is True and r['status'] in ('ZERO','SINGLETON')
        assert c['observed']['proposal']['fibre_cover']['completed'] is True
        missing.append(c['case'])
assert missing==['missing-prefix-now-ZERO','missing42-assumed-singleton','missing42-assumed-zero','missing43-maxA0-zero']
assert result['language_binding']['source_bindings_sha256']==hashlib.sha256(canonical(plan['sources'])).hexdigest()
result_out={'schema':'ROOT-unit-row-missing-mark-degree-controls-disposition-v1','plan':pp,'outputs':outputs,
    'local_controls_accepted':True,'passed_cases':len(passed),'skipped_cases':len(skipped),
    'positive_or_unknown_classifications':status,'invalid_evidence_rejections':17,'callback_exhaustions_propagated':3,'tiny_carrier_counts':[1,37],'independently_checked_missing_mark_covers':missing,
    'complete_wire_verified':True,'native_resources_qualified':True,
    'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,
    'aggregate_B_bytes':peak,'terminal_T_bytes':peak,'complete_Date_seconds':date,
    'language_binding':body['language_binding'],'resource_rule':'single-owned-process-native-terminal-v1; B=T',
    'scope':'Constructed original-theory local-degree fixtures including previously absent prefix marks, with original B12/N44 language; tiny carrier checks cover size1/2 only; pending reads are obligations, exclusions are assumed branch contexts. No theorem discovery or GCTS proof search.',
    'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'logical_proof_accepted':False,
    'GCTS_marking_activated':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'broad_goal_complete':False,
    'previous_goal_turn':'progress','old_UNKNOWNs_and_finite_negative_preserved':True,
    'reconciliation_scope':'Whole saved raw bytes, complete receipts/wire/native/caller metadata only; no Source/kernel/checker/model/word/degree replay.'}
out=HERE/'ROOT-degree-disposition-v1.json'
with out.open('x') as f:json.dump(result_out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'disposition':pin(out),'passed':len(passed),'skipped':len(skipped),
    'native_seconds':(probe-start)/1e9,'B_bytes':peak,'Date_seconds':date}))
