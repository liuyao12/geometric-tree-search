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

CURRENT_CONTRACT={'path': '/private/tmp/gcts-head-gated-ROOT-source-20261017/Source-contract-v1.json', 'sha256': 'e14d41aa80c624b67238e6511f27e519b6dcf8d24041be05fd82a0e498fb4afe', 'bytes': 19869}


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


LEGACY_PHASES=('BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS', 'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE', 'BEFORE_MARKING_CHECK', 'BEFORE_POOL_READ', 'BEFORE_ENGINE', 'BEFORE_PROVIDER', 'AFTER_PROVIDER', 'AFTER_ENGINE', 'BEFORE_OUTPUT')
CALLBACK_PHASES=('P1_ENTER','P1_DELEGATE_RETURN','P1_CALLBACK_READY',
    'P2_ENTER','P2_DELEGATE_RETURN','P2_CALLBACK_READY',
    'C1_ENTER','C1_DELEGATE_RETURN','C1_CALLBACK_READY',
    'C2_ENTER','C2_DELEGATE_RETURN','C2_CALLBACK_READY',
    'C3_ENTER','C3_DELEGATE_RETURN','C3_CALLBACK_READY')
SEARCH_PHASES=('SEARCH_RETURN_OBSERVED','POSTSEARCH_SNAPSHOT_READY')
PHASES=LEGACY_PHASES+CALLBACK_PHASES+SEARCH_PHASES
PROVIDER_COUNTERS=('planned_assignments','attempted_assignments','binding_attempts',
    'ground_environment_proposals','distinct_environment_attempts','full_expansions',
    'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
    'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
    'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
    'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
PROVIDER_DIAGNOSTIC_MAX_BYTES=81988
PHASE_LINE_MAX_BYTES=75
PHASE_TOTAL_MAX_BYTES=1913


def read_phases(raw, launch, terminal):
    need(type(raw)is bytes and len(raw)<=65536, 'bounded full native stderr')
    need(type(launch)is int and type(terminal)is int and 0<=launch<=terminal<2**63,
         'literal phase external clock bounds')
    prefix=b'COMPONENT_INVENTORY_PHASE '
    phases=[];tail=[];stopped=False;last_index=-1;last_stamp=launch;wire_bytes=0
    seen=set();stack=[];ordinals={'P':0,'C':0};group_stage={}
    lines=raw.splitlines(keepends=True)
    for line_index,line in enumerate(lines):
        if line.startswith(prefix) and line.endswith(b'\n'):
            need(not stopped, 'no complete phase after stderr tail')
            need(len(line)<=PHASE_LINE_MAX_BYTES, 'bounded complete phase line')
            parts=line[:-1].split(b' ')
            need(len(parts)==3 and parts[0]==prefix[:-1], 'literal phase fields')
            label=parts[1].decode('ascii');number=parts[2]
            need(label in PHASES and label not in seen and 1<=len(number)<=19
                 and number.isdigit() and (number==b'0' or not number.startswith(b'0')),
                 'unique literal phase and canonical signed64 timestamp')
            stamp=int(number)
            need(last_stamp<=stamp<=terminal and stamp<2**63, 'nondecreasing native phase clock join')
            if label in LEGACY_PHASES:
                index=LEGACY_PHASES.index(label)
                need(index>last_index, 'inherited reached-site order')
                if label=='BEFORE_PROVIDER':
                    need(not stack and 'P1_ENTER' not in seen
                         and 'SEARCH_RETURN_OBSERVED' not in seen, 'first-only provider entry site')
                elif label=='AFTER_PROVIDER':
                    need('P1_DELEGATE_RETURN' in seen and 'P1_CALLBACK_READY' not in seen
                         and stack and stack[-1]=='P1', 'first-only provider copied-return site')
                elif label in ('AFTER_ENGINE','BEFORE_OUTPUT'):
                    need('POSTSEARCH_SNAPSHOT_READY' in seen,
                         'completed search/snapshot reached before outer site')
                last_index=index
            elif label in CALLBACK_PHASES:
                need('BEFORE_ENGINE' in seen and 'SEARCH_RETURN_OBSERVED' not in seen,
                     'callback stages occur in the search interval')
                group,stage=label.split('_',1)
                role=group[0];ordinal=int(group[1])
                if stage=='ENTER':
                    need(not stack, 'synchronous callback groups do not nest')
                    need(ordinal==ordinals[role]+1, 'per-role callback entry ordinal')
                    if group=='P1':need('BEFORE_PROVIDER' in seen, 'first provider outer site precedes delegate')
                    ordinals[role]=ordinal;stack.append(group);group_stage[group]='ENTER'
                elif stage=='DELEGATE_RETURN':
                    need(stack and stack[-1]==group and group_stage[group]=='ENTER',
                         'nested callback delegate-return order')
                    group_stage[group]='DELEGATE_RETURN'
                else:
                    need(stack and stack[-1]==group and group_stage[group]=='DELEGATE_RETURN',
                         'nested callback ready order')
                    if group=='P1':need('AFTER_PROVIDER' in seen, 'first provider old copied-return site')
                    group_stage[group]='CALLBACK_READY';stack.pop()
            elif label=='SEARCH_RETURN_OBSERVED':
                # search catches TimeoutError, including membership subclasses:
                # one entered callback may unwind without returning or logging.
                need('BEFORE_ENGINE' in seen and len(stack)<=1,
                     'search return may retain one unfinished callback group')
            else:
                need('SEARCH_RETURN_OBSERVED' in seen, 'postsearch snapshot follows search return')
            wire_bytes+=len(line)
            need(wire_bytes<=PHASE_TOTAL_MAX_BYTES, 'bounded complete fixed phase wire')
            seen.add(label);last_stamp=stamp;phases.append({'stage':label,'native_ns':stamp})
        else:
            # A partial final phase can be retained as raw tail, never completed.
            if line.startswith(prefix) or (line and prefix.startswith(line)):
                need(line_index==len(lines)-1 and not line.endswith(b'\n'), 'only a final incomplete phase tail')
                possible=False
                for label in PHASES:
                    head=prefix+label.encode('ascii')+b' '
                    if head.startswith(line):possible=True
                    elif line.startswith(head):
                        number=line[len(head):]
                        if (len(number)<=19 and (not number or number.isdigit())
                                and (not number or number==b'0' or not number.startswith(b'0'))
                                and (not number or int(number)<2**63)):
                            possible=True
                need(possible and len(line)<PHASE_LINE_MAX_BYTES, 'literal incomplete phase prefix only')
            stopped=True;tail.append(line)
    need(len(phases)<=30, 'finite fixed phase sites')
    return phases,b''.join(tail)


def validate_positive_callback_phases(phases, pipeline):
    # Counts come only from the full authenticated returned record, never failure slots.
    need(type(pipeline)is dict and type(pipeline.get('observations'))is dict,
         'full returned callback observations')
    observations=pipeline['observations']
    providers=observations.get('provider_calls');consumers=observations.get('consumer_calls')
    need(type(providers)is list and type(consumers)is list
         and len(providers)<=2 and len(consumers)<=3, 'exact current full-record callback count bounds')
    labels={item['stage']for item in phases}
    wanted=set(LEGACY_PHASES)-{'BEFORE_PROVIDER','AFTER_PROVIDER'}
    wanted.update(SEARCH_PHASES)
    need(wanted<=labels, 'full returned outer setup/search/snapshot/output sites')
    unfinished=[]
    for role,count in (('P',len(providers)),('C',len(consumers))):
        maximum=2 if role=='P' else 3
        for ordinal in range(1,maximum+1):
            group=role+str(ordinal)
            entered=group+'_ENTER'in labels
            delegated=group+'_DELEGATE_RETURN'in labels
            ready=group+'_CALLBACK_READY'in labels
            if ordinal<=count:
                need(entered and delegated, 'full logged ordinal follows actual delegate-return site')
            if ready:need(ordinal<=count, 'ready site has an already appended full observation')
            if entered and not ready:unfinished.append(group)
            if entered and ordinal>count:
                need(ordinal==count+1 and not ready, 'one unlogged final callback prefix only')
    need(len(unfinished)<=1, 'at most one unwound incomplete callback in full returned record')
    if providers:need('AFTER_PROVIDER'in labels, 'first logged provider passed old copied-return site')
    need(phases and phases[0]['stage']=='BEFORE_PLAN_READ' and phases[-1]['stage']=='BEFORE_OUTPUT'
         and labels<=set(PHASES), 'complete outer sites with truthful callback prefixes')


def read_failure_diagnostic(owned,plan,plan_raw,contract,launch,terminal,phases):
    if not owned.exists():
        return {'complete_pair':False,'reason':'no owned diagnostic directory'}
    names=sorted(p.name for p in owned.iterdir())
    if names!=['diagnostic-completion.json','unknown-diagnostic.json']:
        return {'complete_pair':False,'reason':'incomplete diagnostic pair','files':names}
    diagnostic_raw=read(owned/'unknown-diagnostic.json',PROVIDER_DIAGNOSTIC_MAX_BYTES)
    completion_raw=read(owned/'diagnostic-completion.json',1024)
    need(diagnostic_raw.endswith(b'\n')and completion_raw.endswith(b'\n'), 'complete diagnostic LF')
    marker=decode(completion_raw);diagnostic=decode(diagnostic_raw)
    marker_keys={'schema','file','sha256','bytes','diagnostic_only','positive_joint_gate_accepted',
                 'ROOT_resource_accepted','terminal_exit2_and_external_failure_closure_required'}
    need(type(marker)is dict and len(marker)==len(marker_keys)
         and all(type(key)is str for key in marker) and set(marker)==marker_keys,
         'exact builtin diagnostic completion fields')
    need(type(marker['schema'])is str and marker['schema']in
         ('unit-row-controls-last-context-completion-v1','unit-row-controls-provider-returns-completion-v2'),
         'explicit legacy or provider-return completion schema')
    provider_journal=marker['schema']=='unit-row-controls-provider-returns-completion-v2'
    need(type(marker['file'])is str and marker['file']=='unknown-diagnostic.json'
         and type(marker['sha256'])is str and marker['sha256']==raw_pin(diagnostic_raw)['sha256']
         and type(marker['bytes'])is int and marker['bytes']==len(diagnostic_raw)
         and marker['diagnostic_only']is True and marker['positive_joint_gate_accepted']is False
         and marker['ROOT_resource_accepted']is False
         and marker['terminal_exit2_and_external_failure_closure_required']is True
         and (provider_journal or len(diagnostic_raw)<=16384),
         'same complete builtin failure diagnostic bytes')
    outer_keys={'context','diagnostic','last_observations'}
    if provider_journal:outer_keys.add('provider_returns')
    need(type(diagnostic)is dict and len(diagnostic)==len(outer_keys)
         and all(type(key)is str for key in diagnostic) and set(diagnostic)==outer_keys,
         'exact builtin diagnostic object')
    context,labels,slots=diagnostic['context'],diagnostic['diagnostic'],diagnostic['last_observations']
    need(type(context)is dict and all(type(key)is str for key in context)
         and type(labels)is dict and all(type(key)is str for key in labels),
         'builtin context and labels before field access')
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
    if provider_journal:
        expected_labels={'schema':'unit-row-controls-provider-returns-diagnostic-v2',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LITERAL_PROVIDER_RETURN_SCALARS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'LITERAL_RETURNED_SCALARS_ONLY_NOT_FULL_RECEIPTS',
            'provider_return_summaries_are_unvalidated_scalars':True,
            'last_observation_is_active_failure_frame':False,'callback_return_to_engine_proved':False,
            'offers_accepted':False,'current_state_accepted':False,'failure_cause_established':False,
            'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}
        need(set(labels)==set(expected_labels)
             and all(type(labels[key])is type(value) and labels[key]==value
                     for key,value in expected_labels.items()), 'literal V2 unqualified scalar-only labels')
    else:
        need(labels['schema']=='unit-row-controls-last-context-diagnostic-v1'
             and labels['diagnostic_only']is True and labels['returned_control_record']is False
             and labels['failure_kind']=='TimeoutError'
             and all(labels[key]is False for key in ('last_observation_is_active_failure_frame',
                  'live_state_or_proof_trajectory_accepted','positive_joint_gate_accepted','logical_proof_accepted',
                  'exact_point_board_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted',
                  'RL_accepted','ROOT_resource_accepted')), 'raw scalar diagnostic has no proof or cause authority')
    need(type(slots)is dict and len(slots)==4 and all(type(key)is str for key in slots)
         and set(slots)=={'proposer','fallback','completion','validator'}
         and slots['validator']is None, 'fixed4 entry observations; validator unwrapped')
    for role,value in slots.items():
        if value is None:continue
        need(type(value)is dict and len(value)==4 and all(type(key)is str for key in value)
             and set(value)=={'stage','row','selected_count','native_ns'}
             and type(value['stage'])is str and value['stage']==role.upper()+'_NATIVE_STEP'
             and type(value['row'])is int and -1<=value['row']<24
             and type(value['selected_count'])is int and -1<=value['selected_count']<=24
             and type(value['native_ns'])is int and began<=value['native_ns']<deadline
             and value['native_ns']<=terminal, 'literal bounded entry data')
    returned=None
    if provider_journal:
        returned=diagnostic['provider_returns']
        need(type(returned)is list and len(returned)==2, 'two nullable builtin provider-return slots')
        phase_stamps={item['stage']:item['native_ns']for item in phases}
        keys={'ordinal','native_ns','batch_status','instance_count','provider_reason','provider_steps','accounting'}
        for index,value in enumerate(returned):
            if value is None:continue
            need(type(value)is dict and len(value)==7 and all(type(key)is str for key in value)
                 and set(value)==keys, 'exact builtin provider-return fields')
            counts=value['accounting']
            need(type(value['ordinal'])is int and value['ordinal']==index+1
                 and type(value['native_ns'])is int and began<=value['native_ns']<deadline
                 and value['native_ns']<=terminal
                 and type(value['batch_status'])is str and len(value['batch_status'])<=64
                 and type(value['instance_count'])is int and 0<=value['instance_count']<=1
                 and type(value['provider_reason'])is str and len(value['provider_reason'])<=256
                 and type(value['provider_steps'])is int and 0<=value['provider_steps']<=1000000
                 and type(counts)is dict and len(counts)==20 and all(type(key)is str for key in counts)
                 and set(counts)==set(PROVIDER_COUNTERS)
                 and all(type(counts[key])is int and 0<=counts[key]<=1000000 for key in PROVIDER_COUNTERS),
                 'literal bounded unvalidated provider-return scalars')
            group='P'+str(index+1)
            need(group+'_DELEGATE_RETURN'in phase_stamps
                 and phase_stamps[group+'_DELEGATE_RETURN']<=value['native_ns']
                 and (group+'_CALLBACK_READY'not in phase_stamps
                      or value['native_ns']<=phase_stamps[group+'_CALLBACK_READY']),
                 'nullable scalar timestamp joins reached delegate and optional ready sites')
    need(all(began<=phase['native_ns']<deadline for phase in phases), 'complete phase samples within original20')
    result={'complete_pair':True,'diagnostic':dict(path=str(owned/'unknown-diagnostic.json'),**raw_pin(diagnostic_raw)),
        'completion':dict(path=str(owned/'diagnostic-completion.json'),**raw_pin(completion_raw)),
        'context':context,'last_observations':slots,'last_observation_is_active_failure_frame':False,
        'failure_cause_established':False,'qualified_case_count':0,'reported_case_count':None}
    if provider_journal:
        result.update(provider_returns=returned,provider_return_summaries_are_unvalidated_scalars=True,
            callback_return_to_engine_proved=False,offers_accepted=False,current_state_accepted=False)
    return result


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
             and body['version']=='ROOT-receiver-inference-probe-cold-v3-head-gated'
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
        validate_positive_callback_phases(phases,pipeline)
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
