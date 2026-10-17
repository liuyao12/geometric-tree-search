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
