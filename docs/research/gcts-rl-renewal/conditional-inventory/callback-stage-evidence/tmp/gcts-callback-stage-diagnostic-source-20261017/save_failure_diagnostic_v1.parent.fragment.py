def save_failure_diagnostic(output_path, context_raw, capture, failure_kind, began_ns, *,
        _clock=CLOCK, _clock_id=CLOCK_ID, _usage=resource.getrusage, _self_id=resource.RUSAGE_SELF,
        _open=os.open, _mkdir=os.mkdir, _write=os.write, _close=os.close,
        _escape=json.encoder.encode_basestring_ascii, _hash=hashlib.sha256,
        _flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW):
    """Best-effort raw builtin data ONLY. No late authority or scientific calls.

    This helper never supplies a positive result. A complete two-file diagnostic
    still requires Root's separate terminal/failure-window reconciliation.
    """
    def failure_gate():
        # Captured native endpoints; no original20 Source callback is invoked.
        peak = _usage(_self_id).ru_maxrss
        now = _clock(_clock_id)
        if (type(_clock) is not types.BuiltinFunctionType or type(_clock_id) is not int
                or type(_escape) is not types.BuiltinFunctionType
                or peak >= 524288000 or not began_ns <= now < began_ns+55000000000):
            raise TimeoutError('failure-only diagnostic window/resource unfinished')
        return now
    def encoded(value, maximum):
        # Exact builtin containers only: no arbitrary iterator/property/default
        # hook, repr, __str__, or project encoder can execute on this path.
        chunks = []; size = 0; nodes = 0
        def append(raw):
            nonlocal size
            size += len(raw)
            if size > maximum: raise ValueError('diagnostic byte bound')
            chunks.append(raw)
        def visit(item, depth):
            nonlocal nodes
            nodes += 1
            if nodes > 200000 or depth > 128: raise ValueError('diagnostic structure bound')
            if nodes % 64 == 1: failure_gate()
            kind = type(item)
            if item is None: append(b'null')
            elif kind is bool: append(b'true' if item else b'false')
            elif kind is int:
                if item.bit_length() > 4096: raise ValueError('diagnostic integer bound')
                append(str(item).encode('ascii'))
            elif kind is str:
                if len(item) > 262144: raise ValueError('diagnostic string bound')
                append(_escape(item).encode('ascii'))
            elif kind is list or kind is dict:
                append(b'[' if kind is list else b'{')
                for index, entry in enumerate(item if kind is list else item.items()):
                    if index: append(b',')
                    if kind is dict:
                        key, child = entry
                        if type(key) is not str: raise ValueError('diagnostic string key required')
                        visit(key, depth+1); append(b':'); visit(child, depth+1)
                    else: visit(entry, depth+1)
                append(b']' if kind is list else b'}')
            else: raise ValueError('non-builtin diagnostic value')
        visit(value, 0); failure_gate()
        return b''.join(chunks)
    failure_gate()
    # context_raw was encoded before the untrusted search delegation.
    if type(context_raw) is not bytes or len(context_raw) > 65536:
        raise ValueError('bounded predelegation diagnostic context')
    if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS':
        roles = ('proposer','fallback','completion','validator')
        if type(capture) is not dict or not all(type(key) is str for key in capture) or set(capture) != set(roles):
            raise ValueError('fixed builtin last-context slots')
        observations = {}
        for role in roles:
            item = capture[role]
            if item is None:
                observations[role] = None
                continue
            if type(item) is not tuple or len(item) != 4:
                raise ValueError('fixed scalar last-context tuple')
            stage,row,selected,native_ns = item
            if (type(stage) is not str or stage != role.upper()+'_NATIVE_STEP'
                    or type(row) is not int or not -1<=row<24
                    or type(selected) is not int or not -1<=selected<=24
                    or type(native_ns) is not int or not began_ns<=native_ns<began_ns+20000000000
                    or not 0<=native_ns<=9223372036854775807):
                raise ValueError('bounded builtin last-context fields')
            observations[role] = {'stage':stage,'row':row,'selected_count':selected,'native_ns':native_ns}
        labels = encoded({'schema':'unit-row-controls-last-context-diagnostic-v1',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LAST_ADAPTER_NATIVE_OBSERVATIONS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'ENTRY_ARGUMENT_ROW_AND_SELECTED_COUNT_AT_LAST_SUCCESSFUL_EXISTING_NATIVE_CHECK',
            'last_observation_is_active_failure_frame':False,'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},4096)
        raw = b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"last_observations":'+encoded(observations,4096)+b'}\n'
        if len(raw)>16384:raise ValueError('whole controls-context diagnostic16KiB bound')
    else:
        available = capture['returned'] is True
        value = capture['payload'] if available else None
        metadata = None; metadata_saved = False; total_events = None; event_raw = []
        prefix_reason = 'NO_RETURNED_RECORD'; metadata_reason = None
        if type(value) is dict and all(type(key) is str for key in value):
            try:
                metadata = encoded({key: item for key,item in value.items() if key != 'events'}, 1048576)
                metadata_saved = True
            except ValueError:
                metadata_reason = 'BUILTIN_METADATA_OUTPUT_BOUND_OR_TYPE'
            events = value.get('events')
            if type(events) is list:
                total_events = len(events); used = 0; prefix_reason = 'ALL_RETURNED_EVENTS_SAVED'
                for event in events:
                    if len(event_raw) >= 2000:
                        prefix_reason = 'DIAGNOSTIC_EVENT_PREFIX_LIMIT'; break
                    try: raw = encoded(event, 262144)
                    except ValueError:
                        prefix_reason = 'NEXT_EVENT_OUTPUT_BOUND_OR_TYPE'; break
                    if used+len(raw)+1 > 3*1048576:
                        prefix_reason = 'DIAGNOSTIC_EVENT_BYTE_LIMIT'; break
                    event_raw.append(raw); used += len(raw)+1
            else: prefix_reason = 'RETURNED_EVENTS_NOT_BUILTIN_LIST'
        elif available: metadata_reason = 'RETURNED_VALUE_NOT_BUILTIN_STRING_KEY_DICT'
        # These labels are caller observations, never claims trusted from the payload.
        labels = encoded({'schema':'unit-row-search-failure-diagnostic-v1',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_UNKNOWN_RAW_PREFIX',
            'capture_available':available,'capture_is_builtin_dict':type(value) is dict,
            'engine_return_observed_ns':capture['returned_ns'], 'failure_kind':failure_kind,
            'metadata_saved':metadata_saved,'metadata_omission_reason':metadata_reason,
            'returned_event_count':total_events,'saved_event_count':len(event_raw),
            'omitted_event_count':None if total_events is None else total_events-len(event_raw),
            'event_prefix_reason':prefix_reason,'may_include_post_deadline_unwind':True,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}, 65536)
        raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"returned_metadata":'
               +(metadata if metadata_saved else b'null')+b',"events_prefix":['
               +b','.join(event_raw)+b']}\n')
    if len(raw) > 4*1048576+131072: raise ValueError('whole diagnostic output bound')
    def write(name, content):
        failure_gate()
        fd = _open(output_path+'/'+name, _flags, 0o600)
        try:
            offset = 0
            while offset < len(content):
                failure_gate()
                count = _write(fd,content[offset:offset+65536])
                if count <= 0: raise OSError('diagnostic output unfinished')
                offset += count
        finally: _close(fd)
        failure_gate()
    failure_gate(); _mkdir(output_path, 0o700)
    write('unknown-diagnostic.json',raw)
    marker = encoded({'schema':('unit-row-controls-last-context-completion-v1' if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS' else 'unit-row-search-failure-diagnostic-completion-v1'),
        'file':'unknown-diagnostic.json','sha256':_hash(raw).hexdigest(),'bytes':len(raw),
        'diagnostic_only':True,'positive_joint_gate_accepted':False,
        'ROOT_resource_accepted':False,'terminal_exit2_and_external_failure_closure_required':True}, 1024)+b'\n'
    write('diagnostic-completion.json',marker)
    failure_gate()

