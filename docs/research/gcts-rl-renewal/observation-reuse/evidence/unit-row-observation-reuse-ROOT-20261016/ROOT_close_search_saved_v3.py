"""Saved raw diagnostic/native/wire concordance only; no scientific replay."""
from pathlib import Path
import collections
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r

assert len(sys.argv)==2 and sys.argv[1] in ('canonical-search','advised-search')
mode=sys.argv[1]
p=HERE/('ROOT-'+mode+'-plan-v1.json');plan=read(p);pp=pin(p)
bracket=read(HERE/('ROOT-'+mode+'-tool-bracket-v1.json'))
assert bracket['plan_sha256']==pp['sha256'] and bracket['plan_bytes']==pp['bytes']
assert bracket['tool_exit_code']==2 and bracket['tool_session_id'] is None
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<date<60 and date+1<90
for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(ref)
external=HERE/(mode+'-external-v1');owned=HERE/(mode+'-owned-v1')
assert sorted(x.name for x in owned.iterdir())==['diagnostic-completion.json','unknown-diagnostic.json']
assert not (external/'meter-stdout.txt').read_bytes()
assert (external/'meter-stderr.txt').read_bytes()==b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete local-degree controls original20/500 reserve unfinished\n'
assert not (external/'postterminal-probe-stderr.txt').read_bytes()
native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
for v in (observation,once):
    assert v['plan_sha256']==pp['sha256'] and v['plan_bytes']==pp['bytes']
    assert v['invocation_id']==plan['invocation_id'] and v['purpose']==plan['purpose']
assert observation['meter_returncode']==2 and observation['probe_returncode']==0
probe=int((external/'postterminal-probe-stdout.txt').read_bytes());assert probe==observation['postterminal_native_probe_ns']
assert native['caller_returncode']==2 and native['wait4_status']==512 and native['all_reaped'] is True
assert native['caller_pid']==native['wait4_pid'] and native['error'] is None
assert native['interrupted'] is False and native['cancellation_forwarded'] is False
start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns']
peak=native['wait4_usage'][2]
assert type(peak) is int and 0<peak==native['caller_kernel_peak_bytes']<536870912
assert terminal-start==native['caller_kernel_elapsed_ns'] and start<terminal<=probe
assert probe-start<55000000000 and probe-start>20000000000
raw=(owned/'unknown-diagnostic.json').read_bytes();marker=read(owned/'diagnostic-completion.json')
assert raw.endswith(b'\n') and marker['file']=='unknown-diagnostic.json'
assert marker['schema']=='unit-row-search-failure-diagnostic-completion-v1'
assert marker['sha256']==hashlib.sha256(raw).hexdigest() and marker['bytes']==len(raw)
assert marker['diagnostic_only'] is True and marker['terminal_exit2_and_external_failure_closure_required'] is True
assert marker['positive_joint_gate_accepted'] is marker['ROOT_resource_accepted'] is False
data=json.loads(raw);context=data['context'];d=data['diagnostic'];m=data['returned_metadata'];events=data['events_prefix']
assert context['plan']=={k:pp[k] for k in ('sha256','bytes')}
for key in ('sources','inputs','purpose','invocation_id','limits'):assert context[key]==plan[key]
g=context['joint_began_ns'];assert context['joint_deadline_ns']==g+20000000000
assert start<=g<d['engine_return_observed_ns']<terminal<=probe<g+55000000000
assert d['schema']=='unit-row-search-failure-diagnostic-v1' and d['diagnostic_only'] is True
assert d['qualification']=='UNQUALIFIED_UNKNOWN_RAW_PREFIX' and d['failure_kind']=='TimeoutError'
assert d['capture_available'] is d['capture_is_builtin_dict'] is d['metadata_saved'] is True
assert d['metadata_omission_reason'] is None and d['event_prefix_reason']=='ALL_RETURNED_EVENTS_SAVED'
assert d['saved_event_count']==d['returned_event_count']==len(events) and d['omitted_event_count']==0
assert [e['event'] for e in events]==list(range(len(events)))
assert m['schema']=='unit-row-lazy-global-search-result-v1' and m['status']=='UNKNOWN'
assert m['found'] is None and m['trace_complete'] is False
assert m['input_epoch']==context['language_binding']['language_epoch']
assert all(d[k] is False for k in ('positive_joint_gate_accepted','logical_proof_accepted','exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','RL_accepted','ROOT_resource_accepted'))
assert all(m[k] is False for k in ('logical_proof_accepted','exact_point_board_accepted','complete_candidate_graph_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted'))
assert m['branch_advice_enabled'] is (mode=='advised-search')
last=m['last_observed_state'];assert last['input_epoch']==m['input_epoch'] and last['height']==24
observations={'qualification':'UNQUALIFIED_PRODUCER_OBSERVATIONS_ONLY','counts':m['counts'],
 'event_count':len(events),'event_kinds':dict(collections.Counter(e['kind'] for e in events)),
 'decision_kinds':dict(collections.Counter(e['decision']['kind'] for e in events if e['kind']=='DECISION')),
 'interrupted_selected_rows':[r['translation'][1] for r in last['selected']],
 'interrupted_rule_counts':dict(collections.Counter(r['type_preimage']['primitive_witness']['rule'] for r in last['selected'])),
 'interrupted_axiom_names':[r['type_preimage']['primitive_witness'].get('name') for r in last['selected']],
 'interrupted_excluded_count':len(last['excluded']),
 'producer_root_restored':m['root_restored'],'producer_stack_restored':m['stack_restored'],
 'producer_root_snapshot_sha256':m['root_snapshot_sha256'],'producer_final_snapshot_sha256':m['final_snapshot_sha256']}
out={'schema':'ROOT-unit-row-diagnostic-search-UNKNOWN-disposition-v1','plan':pp,'status':'UNKNOWN',
 'actual_closed':True,'all_reaped':True,'failure_lifecycle_verified':True,'native_resources_qualified':False,
 'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'aggregate_B_bytes_observed':peak,
 'terminal_T_bytes_observed':peak,'complete_Date_seconds':date,'resource_rule':'single-owned-process-native-terminal-v1; B=T',
 'complete_diagnostic_bytes_and_marker_verified':True,'diagnostic_only':True,'observations':observations,
 'outputs':[pin(owned/n) for n in ('unknown-diagnostic.json','diagnostic-completion.json')],
 'raw_evidence':[pin(x) for x in sorted(external.iterdir())],
 'scope':'CurrentSource17 observation-reuse callerV7, same original right-two target/profile/all-six inventory/24root points. Original success20s. Canonical/advised stages separately owned; no word/donor/library/proof route.',
 'arm':mode,'advice_enabled_observed':m['branch_advice_enabled'],
 'reason':'Original native20s deadline; inherited failure-only path saved actual returned raw producer data then rethrew exit2. No success/proof/trajectory admission.',
 'root_or_stack_restoration_runtime_verified':False,'logical_proof_accepted':False,'GCTS_search_trajectory_accepted':False,
 'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'nonprovability_claimed':False,
 'original_trace_free_UNKNOWN_preserved':True,'broad_goal_complete':False,'previous_goal_turn':'progress','current_goal_turn':'progress',
 'reconciliation_scope':'Whole saved bytes/marker/context/source pins/native lifecycle only. No model, checker, search, word, proof or trajectory replay.',
 'next_action':'Preserve UNKNOWN and late-data qualification. Current3control stages qualified; preserve finite-prefix and one-best-anchor diversity limitations, no unchanged actual restart.'}
q=HERE/('ROOT-'+mode+'-disposition-v1.json')
with q.open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'disposition':pin(q),'native_seconds':(probe-start)/1e9,'B_bytes_observed':peak,'Date_seconds':date,'saved_events':len(events),'reported_counts':m['counts'],'qualification':observations['qualification']}))
