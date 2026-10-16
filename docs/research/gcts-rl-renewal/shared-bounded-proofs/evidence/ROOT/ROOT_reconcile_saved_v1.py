"""Root saved-wire/native reconciliation only; no Source/checker/model replay."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    path=Path(ref['path']);assert path.is_absolute() and path==path.resolve() and pin(path)==ref
    return path
def close(index):
    assert type(index) is int and 1<=index<=9
    plan_path=ROOT/('ROOT-plan-v%d.json'%index);plan=read(plan_path);plan_pin=pin(plan_path)
    owned=Path(plan['output_directory']);external=ROOT/('ordinary-external-v%d'%index)
    assert owned==ROOT/('ordinary-owned-v%d'%index)
    bracket_path=ROOT/('ROOT-tool-bracket-v%d.json'%index);bracket=read(bracket_path)
    assert bracket['plan_sha256']==plan_pin['sha256'] and bracket['plan_bytes']==plan_pin['bytes']
    assert bracket['tool_exit_code']==0 and bracket['tool_session_id'] is None
    date=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
    assert date==bracket['complete_Date_seconds'] and 0<=date<=60 and date+1<=90
    assert sorted(p.name for p in owned.iterdir())==['response.jsonl','search-result.json','word-check.json']
    response=owned/'response.jsonl';wire=response.read_bytes();lines=wire.splitlines(keepends=True)
    assert len(lines)==2 and all(line.endswith(b'\n') for line in lines)
    body,completion=map(json.loads,lines)
    assert completion['schema']=='Q-clean-verifier-response-completion-v1'
    assert completion['body_sha256']==hashlib.sha256(lines[0]).hexdigest() and completion['body_bytes']==len(lines[0])
    assert completion['exit_zero_and_coordinator_deadline_required'] is True
    assert body['schema']=='shared-bounded-ordinary-response-body-v1' and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
    assert body['plan']=={key:plan_pin[key] for key in ('sha256','bytes')} and body['sources']==plan['sources'] and body['inputs']==plan['inputs']
    assert body['invocation_id']==plan['invocation_id'] and body['limits']==plan['limits']
    for ref in [*plan['sources'].values(),*plan['inputs'].values(),plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values(),plan['runtime']]:check(ref)
    assert len(body['outputs'])==2 and {Path(ref['path']).name for ref in body['outputs']}=={'search-result.json','word-check.json'}
    for ref in body['outputs']:assert check(ref).parent==owned
    stdout_raw=(external/'meter-stdout.txt').read_bytes()
    assert stdout_raw.endswith(b'\n') and len(stdout_raw.splitlines())==1
    stdout=json.loads(stdout_raw)
    outputs=[pin(owned/name) for name in ('search-result.json','word-check.json','response.jsonl')]
    assert stdout['outputs']==outputs and stdout['response']==pin(response) and stdout['pending_external'] is True
    assert not (external/'meter-stderr.txt').read_bytes() and not (external/'postterminal-probe-stderr.txt').read_bytes()
    native=read(external/'native-terminal.json');observation=read(external/'observation.json');once=read(external/'ONCE.json')
    assert once['plan_sha256']==plan_pin['sha256'] and once['plan_bytes']==plan_pin['bytes'] and once['invocation_id']==plan['invocation_id']
    assert observation['plan_sha256']==plan_pin['sha256'] and observation['plan_bytes']==plan_pin['bytes'] and observation['invocation_id']==plan['invocation_id']
    assert observation['meter_returncode']==0 and observation['probe_returncode']==0
    probe=int((external/'postterminal-probe-stdout.txt').read_bytes())
    assert probe==observation['postterminal_native_probe_ns']
    assert native['caller_returncode']==0 and native['wait4_status']==0 and native['all_reaped'] is True
    assert native['caller_pid']==native['wait4_pid'] and native['error'] is None and native['interrupted'] is False and native['cancellation_forwarded'] is False
    start=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns'];g=body['joint_began_ns']
    assert type(g) is int and start<=g<terminal<=probe and body['joint_deadline_ns']==g+20000000000
    assert terminal-start==native['caller_kernel_elapsed_ns'] and 0<probe-start<20000000000
    total=native['wait4_usage'][2]
    assert type(total) is int and total==native['caller_kernel_peak_bytes'] and 0<total<=536870912
    declaration=read(check(plan['inputs']['declaration']));profile=read(check(plan['inputs']['profile']))
    logical={key:declaration[key] for key in ('theory','parameters','ordered_Gamma','target','height')}
    binding={'profile_name':profile['profile_name'],'profile_sha256':plan['inputs']['profile']['sha256'],
             'declaration_sha256':plan['inputs']['declaration']['sha256'],
             'logical_input_sha256':sha(logical),'source_bindings_sha256':sha(plan['sources'])}
    binding['language_epoch']=sha(binding)
    proposal=read(owned/'search-result.json');checked=read(owned/'word-check.json')
    assert proposal['binding']==checked['language_binding']==body['language_binding']==binding
    assert checked['profile_source']==plan['inputs']['profile'] and checked['declaration_source']==plan['inputs']['declaration']
    candidate=proposal['candidate'];positive=candidate is not None
    assert body['search_status']==proposal['status']
    assert checked['word_checked'] is positive and body['word_membership_checked'] is positive and body['independent_word_checked'] is positive
    if positive:
        commands=candidate['commands'];membership=checked['word_membership'];word=checked['independent_word']
        assert proposal['status']=='CANDIDATE_NOT_VERIFIED' and candidate['binding']==binding
        assert type(commands) is list and 1<=len(commands)<=24 and commands[-1]['formula']==declaration['target']
        assert membership['completed'] is True and membership['all_commands_in_language'] is True and membership['exact_target'] is True
        assert membership['binding']==binding and membership['commands_sha256']==sha(commands) and membership['command_count']==len(commands) and len(membership['rows'])==len(commands)
        assert word['completed'] is True and word['original_Gamma_target_sequent_accepted'] is True and word['commands_sha256']==sha(commands)
        assert word['original_ordered_Gamma']==declaration['ordered_Gamma'] and word['parameters']==declaration['parameters'] and word['target']==declaration['target']
        assert word['theory_sha256']==sha(declaration['theory']) and len(word['rows'])==len(commands)
    else:
        assert proposal['status']=='UNKNOWN' and checked['word_membership'] is None and checked['independent_word'] is None
        assert proposal['incompleteness']['negative_certificate'] is False and proposal['incompleteness']['complete_language_enumeration'] is False
    result={'schema':'ROOT-shared-bounded-ordinary-disposition-v1','invocation_id':plan['invocation_id'],
            'plan':plan_pin,'outputs':outputs,'complete_wire_verified':True,
            'native_resources_qualified':True,'resource_rule':'single-owned-process-native-terminal-v1; B=T',
            'native_worker_lifetime_ns':terminal-start,'native_launch_to_postprobe_ns':probe-start,
            'terminal_T_bytes':total,'aggregate_B_bytes':total,'complete_Date_seconds':date,
            'language_binding':binding,'target_proof_accepted':positive,
            'search_status':'CHECKED_POSITIVE_WORD' if positive else 'UNKNOWN_HEURISTIC_LIMIT',
            'word_commands':len(candidate['commands']) if positive else None,
            'producer_counters_untrusted':proposal['counters'],'heuristic_limits':proposal['search_limits'],
            'search_incompleteness':proposal['incompleteness'],
            'old_finite_negative_and_UNKNOWNs_unchanged':True,
            'complete_ground_counts_accepted':False,'complete_legacy_embedding_accepted':False,
            'complete_GCTS_model_accepted':False,'GCTS_marking_activated':False,
            'full24_accepted':False,'trajectory_accepted':False,'native_Wang_palette_accepted':False,
            'GCTS_advantage_claimed':False,'RL_accepted':False,'broad_goal_complete':False,
            'reconciliation_scope':'Whole saved bytes, fixed authority/bindings, logical receipt and native/wire/caller metadata only; no Source/kernel/checker execution or model decode.',
            'bracket':pin(bracket_path),'native_terminal':pin(external/'native-terminal.json'),'postterminal_observation':pin(external/'observation.json')}
    output=ROOT/('ROOT-ordinary-disposition-v%d.json'%index)
    with output.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'disposition':pin(output),'target_proof_accepted':positive,
                      'status':result['search_status'],'native_seconds':(probe-start)/1000000000,
                      'B_bytes':total,'Date_seconds':date,'word_commands':result['word_commands']}))

if __name__=='__main__':
    assert len(sys.argv)==2
    close(int(sys.argv[1]))
