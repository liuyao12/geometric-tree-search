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
