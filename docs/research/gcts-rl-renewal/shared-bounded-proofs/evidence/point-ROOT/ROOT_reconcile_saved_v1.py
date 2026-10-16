"""Whole saved bytes/native/receipt concordance only; no Source or semantic replay."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    path=Path(ref['path']);assert path.is_absolute() and path==path.resolve() and pin(path)==ref;return path
plan_path=ROOT/'ROOT-plan-v1.json';plan=read(plan_path);plan_pin=pin(plan_path)
owned=ROOT/'point-owned-v1';external=ROOT/'point-external-v1'
assert plan['output_directory']==str(owned)
bracket_path=ROOT/'ROOT-tool-bracket-v1.json';bracket=read(bracket_path)
assert bracket['plan_sha256']==plan_pin['sha256'] and bracket['plan_bytes']==plan_pin['bytes']
assert bracket['tool_exit_code']==0 and bracket['tool_session_id'] is None
date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
names=['point-board.json','word-checks.json','controls.json','response.jsonl']
assert sorted(p.name for p in owned.iterdir())==sorted(names)
outputs=[pin(owned/name) for name in names]
wire=(owned/'response.jsonl').read_bytes();lines=wire.splitlines(keepends=True)
assert len(lines)==2 and all(line.endswith(b'\n') for line in lines)
body,completion=map(json.loads,lines)
assert completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['body_sha256']==hashlib.sha256(lines[0]).hexdigest() and completion['body_bytes']==len(lines[0])
assert completion['exit_zero_and_coordinator_deadline_required'] is True
assert body['schema']=='shared-bounded-point-board-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
assert body['plan']=={k:plan_pin[k] for k in ('sha256','bytes')} and body['sources']==plan['sources'] and body['inputs']==plan['inputs']
assert body['invocation_id']==plan['invocation_id'] and body['limits']==plan['limits']
assert body['outputs']==outputs[:3]
for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(ref)
stdout_raw=(external/'meter-stdout.txt').read_bytes();assert stdout_raw.endswith(b'\n') and len(stdout_raw.splitlines())==1
stdout=json.loads(stdout_raw)
assert stdout['outputs']==outputs and stdout['response']==outputs[-1] and stdout['pending_external'] is True
assert not (external/'meter-stderr.txt').read_bytes() and not (external/'postterminal-probe-stderr.txt').read_bytes()
native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
for rec in (once,observation):assert rec['plan_sha256']==plan_pin['sha256'] and rec['plan_bytes']==plan_pin['bytes'] and rec['invocation_id']==plan['invocation_id']
assert observation['meter_returncode']==0 and observation['probe_returncode']==0
probe=int((external/'postterminal-probe-stdout.txt').read_bytes());assert probe==observation['postterminal_native_probe_ns']
assert native['caller_returncode']==0 and native['wait4_status']==0 and native['all_reaped'] is True and native['caller_pid']==native['wait4_pid']
assert native['error'] is None and native['interrupted'] is False and native['cancellation_forwarded'] is False
start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns'];g=body['joint_began_ns']
assert type(g) is int and start<=g<terminal<=probe and body['joint_deadline_ns']==g+20000000000
assert terminal-start==native['caller_kernel_elapsed_ns'] and 0<probe-start<20000000000
total=native['wait4_usage'][2];assert type(total) is int and total==native['caller_kernel_peak_bytes'] and 0<total<=536870912
declaration=read(check(plan['inputs']['declaration']));profile=read(check(plan['inputs']['profile']))
logical={k:declaration[k] for k in ('theory','parameters','ordered_Gamma','target','height')}
binding={'profile_name':profile['profile_name'],'profile_sha256':plan['inputs']['profile']['sha256'],
 'declaration_sha256':plan['inputs']['declaration']['sha256'],'logical_input_sha256':sha(logical),'source_bindings_sha256':sha(plan['sources'])}
binding['language_epoch']=sha(binding)
board=read(owned/'point-board.json');words=read(owned/'word-checks.json');controls=read(owned/'controls.json')
assert board['private_language_binding']==words['private_language_binding']==body['language_binding']==binding
original=read(check(plan['inputs']['word_source']))['candidate']['commands'];assert len(original)==17 and original[-1]['formula']==declaration['target']
assert words['original_commands']==original and words['word_source']==plan['inputs']['word_source']
packet=board['packet'];point=board['independent_point_receipt'];padded=point['checked_padded_commands']
assert len(padded)==24 and padded==packet['padded_commands'] and padded[-1]['formula']==declaration['target']
assert point['source_word_sha256']==packet['source_word_sha256']==sha(original) and point['padded_commands_sha256']==packet['padded_commands_sha256']==sha(padded)
assert point['packet_sha256']==sha(packet) and point['input_epoch']==packet['input_epoch']==binding['language_epoch']
assert point['source_word_length']==packet['source_word_length']==17 and point['padding_rows']==packet['padding_rows']==7
assert point['height']==packet['height']==point['tile_count']==point['placement_identity_count']==point['required_point_count']==24
assert len(packet['tiles'])==24 and len(point['unit_totals'])==24 and all(item[1]==1 for item in point['unit_totals'])
assert board['positive_point_board_verified'] is True and point['exact_point_board_accepted'] is True and point['whole_unit_target_verified'] is True and point['literal_marking_union_verified'] is True
for kind,commands in [('original',original),('padded',padded)]:
    member=words[kind+'_membership'];word=words[kind+'_independent_word']
    assert member['completed'] is True and member['all_commands_in_language'] is True and member['exact_target'] is True and member['original_Gamma_preserved'] is True
    assert member['binding']==binding and member['commands_sha256']==sha(commands) and member['command_count']==len(commands) and len(member['rows'])==len(commands)
    assert word['completed'] is True and word['original_Gamma_target_sequent_accepted'] is True and word['commands_sha256']==sha(commands)
    assert word['original_ordered_Gamma']==declaration['ordered_Gamma'] and word['parameters']==declaration['parameters'] and word['target']==declaration['target'] and word['theory_sha256']==sha(declaration['theory']) and len(word['rows'])==len(commands)
    assert words[kind+'_word_checked'] is True and body[kind+'_word_checked'] is True
expected=['Boolean-coordinate','Boolean-weight','Boolean-source','Boolean-index','stale-epoch','stale-preimage','wrong-offset','wrong-input','wrong-source-index','wrong-target-boundary','wrong-outside-boundary','duplicate-row','missing-row','conflicting-mark']
assert controls['case_count']==len(controls['controls'])==body['packet_controls_rejected']==14
assert [r['case'] for r in controls['controls']]==expected and all(r['rejected'] is True and r['observed']['exception_type']=='ValueError' for r in controls['controls'])
assert controls['all_controls_rejected'] is True and controls['no_NA'] is True and controls['resource_failures_propagate'] is True
assert body['source_word_commands']==17 and body['padded_word_commands']==24 and body['positive_point_board_verified'] is True
result={
 'schema':'ROOT-shared-bounded-positive-point-board-disposition-v1','invocation_id':plan['invocation_id'],'plan':plan_pin,'outputs':outputs,
 'complete_wire_verified':True,'native_resources_qualified':True,'resource_rule':'single-owned-process-native-terminal-v1; B=T',
 'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,'terminal_T_bytes':total,'aggregate_B_bytes':total,'complete_Date_seconds':date,
 'language_binding':binding,'logical_target_accepted':True,'original_word_commands':17,'padded_word_commands':24,'padding_rows':7,
 'positive_point_board_accepted':True,'physical_rows':24,'unit_target_points':24,'marking_point_count':point['marking_point_count'],'marking_occurrence_count':point['marking_occurrence_count'],
 'prototype_identity_count':point['prototype_identity_count'],'packet_controls_rejected':14,'control_scope':'Exact reconstruction rejections; no negative accumulator-branch coverage claimed.',
 'search_rerun':False,'new_theorem_discovery':False,'complete_GCTS_model_accepted':False,'complete_ground_counts_accepted':False,
 'complete_legacy_embedding_accepted':False,'GCTS_marking_activated':False,'GCTS_search_trajectory_accepted':False,'native_Wang_palette_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
 'old_finite_negative_and_UNKNOWNs_unchanged':True,'broad_goal_complete':False,
 'cost_scope':'Separate complete cold verification stage. Earlier search and failed attempt remain separate; no joint20s claim.',
 'reconciliation_scope':'Whole saved bytes, fixed authority/bindings, completed point/logical receipt and native/wire/caller metadata only; no Source/kernel/checker/point/model replay.',
 'bracket':pin(bracket_path),'native_terminal':pin(external/'native-terminal.json'),'postterminal_observation':pin(external/'observation.json')}
out=ROOT/'ROOT-point-board-disposition-v1.json'
with out.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'disposition':pin(out),'positive_point_board_accepted':True,'native_seconds':(probe-start)/1e9,'B_bytes':total,'Date_seconds':date,'marking_points':point['marking_point_count'],'marking_occurrences':point['marking_occurrence_count'],'controls_rejected':14}))
