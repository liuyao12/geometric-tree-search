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


def main(argv):
    need(len(argv) == 5, 'plan, external directory, tool bracket, expanded path, disposition path')
    plan_path, external_path, bracket_path, expanded_path, disposition_path = map(Path, argv)
    plan_raw = read(plan_path); plan = decode(plan_raw); external = external_path
    source = {role: pinned(ref) for role, ref in plan['sources'].items()}
    for ref in plan['inputs'].values(): pinned(ref)
    contract = decode(pinned(plan['source_contract']))
    need(contract['schema'] == 'ROOT-engine-family-pipeline-cold-Source-contract-v1'
         and contract['sources'] == plan['sources'] and contract['inputs'] == plan['inputs']
         and contract['limits'] == plan['limits'], 'exact current operative contract')
    grant = decode(pinned(plan['ROOT_authorization']))
    need(grant['actual_execution_authorized'] is True and grant['maximum_actual_invocations'] == 1
         and all(grant[key] == plan[key] for key in ('invocation_id','purpose','sources','inputs',
             'source_contract','reviews','runtime','limits','resource_rule','output_directory')),
         'whole once grant joins current plan')
    for role, ref in plan['reviews'].items():
        review = decode(pinned(ref))
        need(review['scope'] == 'ROOT-engine-family-pipeline-cold-Source'
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
    bracket_raw = read(bracket_path); bracket = decode(bracket_raw)
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
         and bracket['tool_exit_code'] in (0,2), 'whole same-handle tool bracket')
    need(meter['schema'] == 'ROOT-Q-native-terminal-meter-v1'
         and meter['all_reaped'] is True and meter['caller_pid'] == meter['wait4_pid']
         and meter['error'] is None and meter['interrupted'] is False
         and meter['cancellation_forwarded'] is False
         and meter['utility_argv'] == [plan['runtime']['path'],'-I','-S','-B',
              plan['sources']['intake']['path'],str(plan_path)], 'exact native wait4 terminal scope')
    launch, terminal = meter['caller_launch_began_ns'], meter['caller_terminal_observed_ns']
    probe = observation['postterminal_native_probe_ns']
    need(all(type(value) is int for value in (launch,terminal,probe,meter['caller_kernel_peak_bytes']))
         and observation['external_began_ns'] <= meter['meter_began_ns'] <= launch <= terminal <= probe
         and probe-launch < 55000000000 and 0 <= meter['caller_kernel_peak_bytes'] < 536870912
         and raw['postterminal-probe-stdout.txt'] == (str(probe)+'\n').encode('ascii')
         and raw['postterminal-probe-stderr.txt'] == b'', 'native failure-window closure and exact postprobe')
    need(meter['caller_returncode'] == observation['meter_returncode'] == bracket['tool_exit_code']
         and observation['probe_returncode'] == 0, 'native/tool exit concordance')
    summary = {'schema':'ROOT-engine-family-pipeline-disposition-v1',
        'plan':dict(path=str(plan_path), **raw_pin(plan_raw)),
        'source_contract':plan['source_contract'], 'actual_closed':True, 'all_reaped':True,
        'native_launch_to_postprobe_ns':probe-launch, 'aggregate_B_bytes':meter['caller_kernel_peak_bytes'],
        'status':'UNKNOWN', 'complete_wire_verified':False, 'native_resources_qualified':False,
        'integration_path_accepted':False,'reported_theorem_count':0,
        'logical_proof_accepted':False,'whole_engine_qualified':False,
        'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
        'scientific_replay':False,
        'native_files':{name:dict(path=str(external/name), **raw_pin(content))for name,content in raw.items()},
        'tool_bracket':dict(path=str(bracket_path), **raw_pin(bracket_raw))}
    if meter['caller_returncode'] == 0:
        need(probe-launch < 20000000000 and raw['meter-stderr.txt'] == b'', 'strict whole positive20 window')
        final_lines = raw['meter-stdout.txt'].splitlines(keepends=True)
        need(len(final_lines)==1 and final_lines[0].endswith(b'\n'), 'whole final line')
        final = decode(final_lines[0])
        need(final['schema']=='ROOT-engine-family-pipeline-final-observation-v1'
             and canonical(final)+b'\n'==final_lines[0], 'current canonical final wire')
        owned = Path(plan['output_directory'])
        need(sorted(p.name for p in owned.iterdir()) == ['engine-result.json','response.jsonl'], 'whole owned pair')
        for ref in final['outputs']: pinned(ref)
        need([ref['path'] for ref in final['outputs']] == [str(owned/'engine-result.json'),str(owned/'response.jsonl')]
             and final['response'] == final['outputs'][1], 'exact final paths/order')
        response_raw = read(owned/'response.jsonl'); lines = response_raw.splitlines(keepends=True)
        need(len(lines)==2 and all(line.endswith(b'\n')for line in lines), 'whole two-line response')
        body, completion = map(decode, lines)
        need(completion['body_sha256']==raw_pin(lines[0])['sha256'] and completion['body_bytes']==len(lines[0])
             and body['schema']=='ROOT-engine-family-pipeline-response-body-v1'
             and body['plan']==raw_pin(plan_raw) and body['sources']==plan['sources'] and body['inputs']==plan['inputs']
             and body['outputs']==[final['outputs'][0]] and body['invocation_id']==plan['invocation_id']
             and body['joint_deadline_ns']==body['joint_began_ns']+20000000000
             and launch<=body['joint_began_ns']<=terminal<body['joint_deadline_ns']
             and canonical(body)+b'\n'==lines[0] and canonical(completion)+b'\n'==lines[1],
             'whole response/current-source/native concordance')
        encoded_raw=read(owned/'engine-result.json'); envelope=decode(encoded_raw)
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
        need(canonical(evidence)+b'\n'==expanded and evidence['schema']=='ROOT-engine-family-pipeline-result-v1'
             and evidence['sources']==plan['sources'] and evidence['inputs']==plan['inputs']
             and evidence['purpose']==plan['purpose'], 'full canonical current payload')
        pipeline=evidence['engine_family_pipeline']['pipeline']
        need(evidence['language_binding']==body['language_binding']==body['original_model_binding']
             ==contract['original_model_binding']
             and all(item[key]is False for item in (evidence,body,final)
                 for key in ('logical_proof_accepted','ROOT_resource_accepted')),
             'original epoch and strong authority remain unchanged and false')
        need(pipeline['status']in ('UNKNOWN','CHECKED_FRESH_BRANCH_PREFERENCE')
             and all(pipeline[key]is False for key in ('new_theorem_discovered','proof_accepted','engine_activated',
                 'family_library_activated','degree_or_EOF_accepted','whole_engine_qualified',
                 'complete_GCTS_model_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted')),
             'exact narrow result, no strong promotion')
        with expanded_path.open('xb')as stream:stream.write(expanded)
        summary.update(status=pipeline['status'],complete_wire_verified=True,native_resources_qualified=True,
            integration_path_accepted=pipeline['status']=='CHECKED_FRESH_BRANCH_PREFERENCE',
            expanded=dict(path=str(expanded_path),**raw_pin(expanded)),outputs=final['outputs'])
    print(json.dumps({'disposition':write(disposition_path,summary),'status':summary['status'],
        'integration_path_accepted':summary['integration_path_accepted'],
        'native_launch_to_postprobe_ns':probe-launch,'aggregate_B_bytes':meter['caller_kernel_peak_bytes']},sort_keys=True))


if __name__ == '__main__':
    main(sys.argv[1:])
