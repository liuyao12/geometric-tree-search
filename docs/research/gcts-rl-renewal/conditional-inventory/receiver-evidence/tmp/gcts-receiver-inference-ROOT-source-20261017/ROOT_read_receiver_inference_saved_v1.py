"""Root saved-only byte/native/transport reconciliation; no project imports.

Never calls a clock, search, proof checker, collector, miner or provider. The
lossless payload remains the measured caller's evidence, not a replay receipt.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib

CURRENT_CONTRACT={'path': '/private/tmp/gcts-receiver-inference-ROOT-source-20261017/Source-contract-v1.json', 'sha256': '8af2329d5a56c7aa0da665bf1152714bae9f5d8051d2e6a8507d94132d5491ad', 'bytes': 17884}


def need(ok, why):
    if not ok:
        raise ValueError('pipeline saved closure: '+why)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')


def unique(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'duplicate JSON key')
        value[key] = item
    return value


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def raw_pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def read(path, maximum=16777216):
    path = Path(path)
    need(path.is_absolute() and path == path.resolve() and path.is_file() and not path.is_symlink(),
         'literal canonical regular input')
    need(path.stat().st_size <= maximum, 'whole input size bound')
    with path.open('rb') as stream:
        raw = stream.read(maximum+1)
        need(len(raw) <= maximum and stream.read(1) == b'', 'whole bounded EOF')
    return raw


def pinned(ref):
    raw = read(ref['path'])
    need(raw_pin(raw) == {key: ref[key] for key in ('sha256', 'bytes')}, 'full raw pin')
    return raw


def write(path, value):
    raw = canonical(value)+b'\n'
    with Path(path).open('xb') as stream:
        stream.write(raw)
    return dict(path=str(path), **raw_pin(raw))


PHASES=('BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS', 'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE', 'BEFORE_MARKING_CHECK', 'BEFORE_POOL_READ', 'BEFORE_ENGINE', 'BEFORE_PROVIDER', 'AFTER_PROVIDER', 'AFTER_ENGINE', 'BEFORE_OUTPUT')

def read_phases(raw, launch, terminal):
    need(len(raw)<=65536, 'bounded full native stderr')
    prefix=b'COMPONENT_INVENTORY_PHASE '
    phases=[];tail=[];stopped=False;last_index=-1
    for line in raw.splitlines(keepends=True):
        if not stopped and line.startswith(prefix) and line.endswith(b'\n'):
            need(len(line)<=96, 'bounded complete phase line')
            parts=line[:-1].split(b' ')
            need(len(parts)==3 and parts[0]==prefix[:-1], 'literal phase fields')
            label=parts[1].decode('ascii');number=parts[2]
            need(label in PHASES and PHASES.index(label)>last_index and number.isdigit()
                 and (number==b'0' or not number.startswith(b'0')), 'unique ordered literal phase')
            stamp=int(number);need(type(stamp)is int and launch<=stamp<=terminal<2**63, 'native phase clock join')
            last_index=PHASES.index(label);phases.append({'stage':label,'native_ns':stamp})
        else:
            stopped=True;tail.append(line)
    need(len(phases)<=13, 'finite fixed phase sites')
    return phases,b''.join(tail)


def read_failure_diagnostic(owned,plan,plan_raw,contract,launch,terminal,phases):
    if not owned.exists():
        return {'complete_pair':False,'reason':'no owned diagnostic directory'}
    names=sorted(p.name for p in owned.iterdir())
    if names!=['diagnostic-completion.json','unknown-diagnostic.json']:
        return {'complete_pair':False,'reason':'incomplete diagnostic pair','files':names}
    diagnostic_raw=read(owned/'unknown-diagnostic.json',16384)
    completion_raw=read(owned/'diagnostic-completion.json',1024)
    need(diagnostic_raw.endswith(b'\n')and completion_raw.endswith(b'\n'), 'complete diagnostic LF')
    marker=decode(completion_raw);diagnostic=decode(diagnostic_raw)
    need(marker['schema']=='unit-row-controls-last-context-completion-v1'
         and marker['file']=='unknown-diagnostic.json'
         and marker['sha256']==raw_pin(diagnostic_raw)['sha256']and marker['bytes']==len(diagnostic_raw)
         and marker['diagnostic_only']is True and marker['positive_joint_gate_accepted']is False
         and marker['ROOT_resource_accepted']is False
         and marker['terminal_exit2_and_external_failure_closure_required']is True,
         'same complete builtin failure diagnostic bytes')
    context,labels,slots=diagnostic['context'],diagnostic['diagnostic'],diagnostic['last_observations']
    need(context['schema']=='ROOT-receptor-inference-probe-diagnostic-context-v1'
         and context['invocation_id']==plan['invocation_id']and context['purpose']==plan['purpose']
         and context['plan']==raw_pin(plan_raw)and context['sources']==plan['sources']
         and context['inputs']==plan['inputs']and context['source_contract']==plan['source_contract']
         and context['original_model_binding']==contract['original_model_binding']
         and context['reported_case_count']is None and type(context['qualified_case_count'])is int
         and context['qualified_case_count']==0 and context['diagnostic_only']is True
         and all(context[key]is False for key in ('positive_joint_gate_accepted','engine_qualified',
             'logical_proof_accepted','complete_GCTS_model_accepted','RL_accepted','GCTS_advantage_claimed')),
         'exact diagnostic original/current authority; zero qualification')
    began,deadline=context['joint_began_ns'],context['joint_deadline_ns']
    need(type(began)is int and type(deadline)is int and launch<=began<=terminal
         and deadline==began+20000000000, 'exact original diagnostic window')
    need(labels['schema']=='unit-row-controls-last-context-diagnostic-v1'
         and labels['diagnostic_only']is True and labels['returned_control_record']is False
         and labels['failure_kind']=='TimeoutError'
         and all(labels[key]is False for key in ('last_observation_is_active_failure_frame',
              'live_state_or_proof_trajectory_accepted','positive_joint_gate_accepted','logical_proof_accepted',
              'exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
              'RL_accepted','ROOT_resource_accepted')), 'raw scalar diagnostic has no proof or cause authority')
    need(type(slots)is dict and set(slots)=={'proposer','fallback','completion','validator'}
         and slots['validator']is None, 'fixed4 entry observations; validator unwrapped')
    for role,value in slots.items():
        if value is None:continue
        need(set(value)=={'stage','row','selected_count','native_ns'}
             and value['stage']==role.upper()+'_NATIVE_STEP'
             and type(value['row'])is int and -1<=value['row']<24
             and type(value['selected_count'])is int and -1<=value['selected_count']<=24
             and type(value['native_ns'])is int and began<=value['native_ns']<deadline
             and value['native_ns']<=terminal, 'literal bounded entry data')
    need(all(began<=phase['native_ns']<deadline for phase in phases), 'complete phase samples within original20')
    return {'complete_pair':True,'diagnostic':dict(path=str(owned/'unknown-diagnostic.json'),**raw_pin(diagnostic_raw)),
        'completion':dict(path=str(owned/'diagnostic-completion.json'),**raw_pin(completion_raw)),
        'context':context,'last_observations':slots,'last_observation_is_active_failure_frame':False,
        'failure_cause_established':False,'qualified_case_count':0,'reported_case_count':None}


def main(argv):
    need(len(argv) == 5, 'plan, external directory, tool bracket, expanded path, disposition path')
    plan_path, external_path, bracket_path, expanded_path, disposition_path = map(Path, argv)
    plan_raw = read(plan_path); plan = decode(plan_raw); external = external_path
    source = {role: pinned(ref) for role, ref in plan['sources'].items()}
    for ref in plan['inputs'].values(): pinned(ref)
    need(plan['source_contract']==CURRENT_CONTRACT, 'literal frozen current operative Source capsule')
    contract = decode(pinned(plan['source_contract']))
    need(contract['schema'] == 'ROOT-receiver-inference-probe-Source-contract-v1'
         and contract['sources'] == plan['sources'] and contract['inputs'] == plan['inputs']
         and contract['limits'] == plan['limits'], 'exact current operative contract')
    grant = decode(pinned(plan['ROOT_authorization']))
    need(grant['actual_execution_authorized'] is True and grant['maximum_actual_invocations'] == 1
         and all(grant[key] == plan[key] for key in ('invocation_id','purpose','sources','inputs',
             'source_contract','reviews','runtime','limits','resource_rule','output_directory')),
         'whole once grant joins current plan')
    for role, ref in plan['reviews'].items():
        review = decode(pinned(ref))
        need(review['scope'] == 'ROOT-receiver-inference-probe-Source'
             and review['source'] == plan['sources']['intake'] and review['sources'] == plan['sources']
             and review['source_contract'] == plan['source_contract'] and review['source_only'] is True
             and review['source_review_passed'] is True and review['scientific_calls'] == 0,
             'current whole Source review')
    pinned(plan['runtime'])
    inventory = sorted(p.name for p in external.iterdir())
    need(inventory == sorted(['ONCE.json','meter-stdout.txt','meter-stderr.txt','native-terminal.json',
         'observation.json','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt']),
         'complete native once output inventory')
    raw = {name: read(external/name) for name in inventory}
    once, meter, observation = (decode(raw[key]) for key in ('ONCE.json','native-terminal.json','observation.json'))
    need(once['schema']=='ROOT-ordinary-once-consumed-v1'
         and observation['schema']=='ROOT-ordinary-external-observation-v1'
         and observation['measurement_only']is True
         and observation['ROOT_primary_accepted']is observation['ROOT_resource_accepted']is False,
         'unchanged native once observation schemas and authority')
    bracket_raw = read(bracket_path); bracket = decode(bracket_raw)
    left,right=bracket['tool_session_id'],bracket['observed_session_id']
    need((left is None and right is None) or
         (type(left)is int and type(right)is int and left>0 and left==right), 'literal same native tool handle')
    for item in (once, observation):
        need(item['plan_sha256'] == raw_pin(plan_raw)['sha256']
             and item['plan_bytes'] == len(plan_raw) and item['invocation_id'] == plan['invocation_id']
             and item['purpose'] == plan['purpose'], 'actual once/native plan join')
    need(bracket['schema'] == 'ROOT-complete-tool-Date-bracket-v1'
         and bracket['plan_sha256'] == raw_pin(plan_raw)['sha256'] and bracket['plan_bytes'] == len(plan_raw)
         and bracket['tool_session_id'] == bracket['observed_session_id']
         and bracket['unchanged_actual_restarted'] is False
         and type(bracket['began_Date_ms']) is int and type(bracket['ended_Date_ms']) is int
         and 0 <= bracket['ended_Date_ms']-bracket['began_Date_ms'] <= 91000
         and bracket['complete_Date_seconds'] == (bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
         and type(bracket['tool_exit_code'])is int and bracket['tool_exit_code'] in (0,2),
         'whole same-handle tool bracket')
    need(meter['schema'] == 'ROOT-Q-native-terminal-meter-v1'
         and meter['version']=='Q-external-native-terminal-meter-Source-v2-global-clock'
         and meter['CLOCK_DOMAIN']=='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
         and type(meter['caller_pid'])is int and meter['caller_pid']>0
         and type(meter['wait4_pid'])is int
         and meter['all_reaped'] is True and meter['caller_pid'] == meter['wait4_pid']
         and meter['error'] is None and meter['interrupted'] is False
         and meter['cancellation_forwarded'] is False
         and meter['utility_argv'] == [plan['runtime']['path'],'-I','-S','-B',
              plan['sources']['intake']['path'],str(plan_path)], 'exact native wait4 terminal scope')
    launch, terminal = meter['caller_launch_began_ns'], meter['caller_terminal_observed_ns']
    probe = observation['postterminal_native_probe_ns']
    need(all(type(value)is int and 0<=value<2**63 for value in
         (launch,terminal,probe,observation['external_began_ns'],meter['meter_began_ns']))
         and type(meter['caller_kernel_elapsed_ns'])is int
         and meter['caller_kernel_elapsed_ns']==terminal-launch, 'literal native clock fields')
    need(all(type(value) is int for value in (launch,terminal,probe,meter['caller_kernel_peak_bytes']))
         and observation['external_began_ns'] <= meter['meter_began_ns'] <= launch <= terminal <= probe
         and probe-launch < 55000000000 and 0 <= meter['caller_kernel_peak_bytes'] < 536870912
         and raw['postterminal-probe-stdout.txt'] == (str(probe)+'\n').encode('ascii')
         and raw['postterminal-probe-stderr.txt'] == b'', 'native failure-window closure and exact postprobe')
    need(all(type(v)is int for v in (meter['caller_returncode'],observation['meter_returncode'],
                 observation['probe_returncode']))
         and meter['caller_returncode'] == observation['meter_returncode'] == bracket['tool_exit_code']
         and observation['probe_returncode'] == 0 and type(meter['wait4_status'])is int
         and meter['wait4_status']==meter['caller_returncode']*256, 'native/tool exit concordance')
    phases,phase_tail=read_phases(raw['meter-stderr.txt'],launch,terminal)
    summary = {'schema':'ROOT-receptor-inference-probe-disposition-v1',
        'plan':dict(path=str(plan_path), **raw_pin(plan_raw)),
        'source_contract':plan['source_contract'], 'actual_closed':True, 'all_reaped':True,
        'native_launch_to_postprobe_ns':probe-launch, 'aggregate_B_bytes':meter['caller_kernel_peak_bytes'],
        'status':'UNKNOWN', 'complete_wire_verified':False, 'native_resources_qualified':False,
        'receiver_probe_record_complete':False,'reported_theorem_count':0,
        'logical_proof_accepted':False,'whole_engine_qualified':False,
        'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
        'scientific_replay':False,'phase_observations':phases,
        'stderr_tail_sha256':raw_pin(phase_tail),'failure_diagnostic':None,
        'current_frontier_viability_checked':False,
        'native_files':{name:dict(path=str(external/name), **raw_pin(content))for name,content in raw.items()},
        'tool_bracket':dict(path=str(bracket_path), **raw_pin(bracket_raw))}
    if meter['caller_returncode'] == 0:
        need(probe-launch < 20000000000 and phase_tail==b'', 'strict whole positive20 and complete phase wire')
        final_lines = raw['meter-stdout.txt'].splitlines(keepends=True)
        need(len(final_lines)==1 and final_lines[0].endswith(b'\n'), 'whole final line')
        final = decode(final_lines[0])
        need(final['schema']=='ROOT-receptor-inference-probe-final-observation-v1'
             and final['pending_external']is True
             and canonical(final)+b'\n'==final_lines[0], 'current canonical final wire')
        owned = Path(plan['output_directory'])
        need(sorted(p.name for p in owned.iterdir()) == ['engine-result.json','response.jsonl'], 'whole owned pair')
        output_raw={ref['path']:pinned(ref) for ref in final['outputs']}
        need([ref['path'] for ref in final['outputs']] == [str(owned/'engine-result.json'),str(owned/'response.jsonl')]
             and final['response'] == final['outputs'][1], 'exact final paths/order')
        response_raw = output_raw[str(owned/'response.jsonl')]; lines = response_raw.splitlines(keepends=True)
        need(len(lines)==2 and all(line.endswith(b'\n')for line in lines), 'whole two-line response')
        body, completion = map(decode, lines)
        need(completion['schema']=='Q-clean-verifier-response-completion-v1'
             and completion['exit_zero_and_coordinator_deadline_required']is True
             and completion['body_sha256']==raw_pin(lines[0])['sha256'] and completion['body_bytes']==len(lines[0])
             and body['schema']=='ROOT-receptor-inference-probe-response-body-v1'
             and body['version']=='ROOT-receiver-inference-probe-cold-v1'
             and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
             and body['limits']==plan['limits'] and body['resource_rule']==plan['resource_rule']
             and body['CLOCK_DOMAIN']=='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
             and body['plan']==raw_pin(plan_raw) and body['sources']==plan['sources'] and body['inputs']==plan['inputs']
             and body['outputs']==[final['outputs'][0]] and body['invocation_id']==plan['invocation_id']
             and body['joint_deadline_ns']==body['joint_began_ns']+20000000000
             and launch<=body['joint_began_ns']<=terminal<body['joint_deadline_ns']
             and canonical(body)+b'\n'==lines[0] and canonical(completion)+b'\n'==lines[1],
             'whole response/current-source/native concordance')
        encoded_raw=output_raw[str(owned/'engine-result.json')]; envelope=decode(encoded_raw)
        need(set(envelope)=={'schema','encoding','expanded_bytes','expanded_sha256','compressed_bytes',
                 'compressed_sha256','payload_base64'} and envelope['encoding']=='zlib+base64'
             and envelope['schema']=='ROOT-unit-row-lossless-result-envelope-v1'
             and canonical(envelope)+b'\n'==encoded_raw and len(encoded_raw)<=4194304,
             'unchanged full canonical lossless envelope')
        compressed=base64.b64decode(envelope['payload_base64'],validate=True)
        need(envelope['compressed_bytes']==len(compressed)
             and envelope['compressed_sha256']==raw_pin(compressed)['sha256'], 'whole compressed SHA/length')
        decoder=zlib.decompressobj(); expanded=decoder.decompress(compressed,16777217)
        need(len(expanded)<=16777216 and decoder.eof and decoder.unused_data==b'' and decoder.unconsumed_tail==b'',
             'bounded whole zlib stream')
        need(envelope['expanded_sha256']==raw_pin(expanded)['sha256']
             and envelope['expanded_bytes']==len(expanded), 'whole expanded SHA/length')
        evidence=decode(expanded)
        need(canonical(evidence)+b'\n'==expanded and evidence['schema']=='ROOT-receptor-inference-probe-result-v1'
             and evidence['sources']==plan['sources'] and evidence['inputs']==plan['inputs']
             and evidence['purpose']==plan['purpose'], 'full canonical current payload')
        payload=evidence['receiver_probe'];pipeline=payload['receiver']
        need(all(body['joint_began_ns']<=x['native_ns']<body['joint_deadline_ns']for x in phases), 'positive phase samples original20')
        need(phases[0]['stage']=='BEFORE_PLAN_READ' and phases[-1]['stage']=='BEFORE_OUTPUT'
             and (pipeline['status']!='RECEIVER_PROBE_RECORDED' or [x['stage']for x in phases if x['stage'] not in ('BEFORE_PROVIDER','AFTER_PROVIDER')]==[x for x in PHASES if x not in ('BEFORE_PROVIDER','AFTER_PROVIDER')]),
             'ordered reached sites; full inventory requires all required sites; provider sites are conditional')
        need(payload['schema']=='ROOT-receptor-inference-probe-payload-v1'
             and payload['original_model_sources']==contract['original_model_sources']
             and payload['original_model_inputs']==contract['original_model_inputs']
             and payload['original_model_binding']==contract['original_model_binding']
             and all(payload[key]is False for key in ('new_theorem_discovered','logical_proof_accepted',
                 'engine_activated','family_library_activated','whole_engine_qualified','complete_GCTS_model_accepted',
                 'scheduler_or_rollback_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted')),
             'whole original model/payload/false broad flags')
        need(evidence['language_binding']==body['language_binding']==body['original_model_binding']
             ==contract['original_model_binding']
             and all(item[key]is False for item in (evidence,body,final)
                 for key in ('logical_proof_accepted','ROOT_resource_accepted')),
             'original epoch and strong authority remain unchanged and false')
        need(pipeline['schema']=='ROOT-receiver-inference-evidence-v1'
             and pipeline['status']=='RECEIVER_PROBE_RECORDED',
             'conditional inventory evidence only; no semantic replay by saved reader')
        with expanded_path.open('xb')as stream:stream.write(expanded)
        summary.update(status=pipeline['status'],complete_wire_verified=True,native_resources_qualified=True,
            receiver_probe_record_complete=pipeline['status']=='RECEIVER_PROBE_RECORDED',
            expanded=dict(path=str(expanded_path),**raw_pin(expanded)),outputs=final['outputs'])
    else:
        summary['failure_diagnostic']=read_failure_diagnostic(Path(plan['output_directory']),plan,plan_raw,contract,launch,terminal,phases)
    print(json.dumps({'disposition':write(disposition_path,summary),'status':summary['status'],
        'receiver_probe_record_complete':summary['receiver_probe_record_complete'],
        'native_launch_to_postprobe_ns':probe-launch,'aggregate_B_bytes':meter['caller_kernel_peak_bytes']},sort_keys=True))


if __name__ == '__main__':
    main(sys.argv[1:])
