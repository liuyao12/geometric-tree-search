from pathlib import Path
import ast, hashlib, json, difflib
D=Path('/private/tmp/gcts-first-admission-diagnostic-source-20261017')
C=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017/callback_stage_receiver_cold_v1.py')
R=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017/ROOT_read_callback_stage_receiver_saved_v1.py')
cold=C.read_text(); reader=R.read_text()
def region(text,name):
    n=next(n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    return ''.join(text.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
writer=region(cold,'save_failure_diagnostic')+'\n'
parent_writer=writer
branch=writer[writer.index("    elif failure_kind == 'CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2':"):writer.index('    else:\n        available = capture')]
new=branch.replace("CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2", "CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3",1)
new=new.replace('len(capture) != 2','len(capture) != 3',1).replace("{'legacy','provider_returns'}", "{'legacy','provider_returns','engine_milestones'}",1)
label_start=new.index('        labels = encoded(')
# Keep V2 scalar validation verbatim; journal metadata is an additive branch.
new=new[:label_start]+'''        stages = ('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
            'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
        milestones = capture['engine_milestones']
        if type(milestones) is not list or len(milestones) != 4:
            raise ValueError('fixed four raw engine milestone slots')
        headers = []; captured = 0; ended = False; previous_ns = began_ns
        for index in range(4):
            failure_gate()
            item = milestones[index]
            if item is None:
                ended = True; headers.append(None); continue
            if (ended or type(item) is not dict or len(item) != 4
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','stage','native_ns','record'}
                    or type(item['ordinal']) is not int or item['ordinal'] != index+1
                    or type(item['stage']) is not str or item['stage'] != stages[index]
                    or type(item['native_ns']) is not int
                    or not previous_ns<=item['native_ns']<began_ns+20000000000
                    or not 0<=item['native_ns']<=9223372036854775807
                    or type(item['record']) is not dict):
                raise ValueError('literal monotone-prefix raw milestone headers')
            headers.append({'ordinal':index+1,'stage':item['stage'],'native_ns':item['native_ns']})
            previous_ns=item['native_ns']; captured+=1
        journal = [b'null',b'null',b'null',b'null']; journal_bytes = 21
        serialized = 0; prefix_reason = 'ALL_CAPTURED_RECORDS_SAVED'
        for index in range(captured):
            failure_gate()
            try:
                item_raw = encoded(milestones[index],3*1048576)
            except ValueError:
                prefix_reason = 'NEXT_RECORD_OUTPUT_BOUND_OR_BUILTIN_TYPE'; break
            if journal_bytes+len(item_raw)-4 > 3*1048576:
                prefix_reason = 'ENGINE_JOURNAL_AGGREGATE_BYTE_LIMIT'; break
            journal[index]=item_raw; journal_bytes+=len(item_raw)-4; serialized+=1
        journal_raw=b'['+b','.join(journal)+b']'
        if len(journal_raw)!=journal_bytes:raise ValueError('literal journal byte accounting')
        labels = encoded({'schema':'unit-row-controls-engine-milestones-diagnostic-v3',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LITERAL_ENGINE_MILESTONE_RECORDS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'LITERAL_RETURNED_SCALARS_AND_RAW_ENGINE_RECORDS_ONLY',
            'provider_return_summaries_are_unvalidated_scalars':True,
            'engine_milestone_records_are_unvalidated':True,
            'captured_headers':headers,'captured_record_count':captured,
            'serialized_record_count':serialized,'omitted_record_count':captured-serialized,
            'next_omitted_ordinal':serialized+1 if serialized<captured else None,
            'engine_record_prefix_reason':prefix_reason,'engine_journal_bytes':journal_bytes,
            'last_observation_is_active_failure_frame':False,'callback_return_to_engine_proved':False,
            'offers_accepted':False,'current_state_accepted':False,'failure_cause_established':False,
            'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},65536)
        raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels
               +b',"last_observations":'+encoded(observations,4096)
               +b',"provider_returns":'+encoded(summaries,8192)
               +b',"engine_milestones":'+journal_raw+b'}\\n')
'''
writer=writer.replace('    else:\n        available = capture',new+'    else:\n        available = capture',1)
writer=writer.replace("else 'unit-row-search-failure-diagnostic-completion-v1'),", "else 'unit-row-controls-engine-milestones-completion-v3' if failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3' else 'unit-row-search-failure-diagnostic-completion-v1'),",1)
(D/'save_failure_diagnostic_v3.fragment.py').write_text(writer)
(D/'parent-writer.fragment.py').write_text(parent_writer)
# Reader: retain current authority/version literals for Root integration only.
parent_reader=reader
reader=reader.replace('PHASES=LEGACY_PHASES+CALLBACK_PHASES+SEARCH_PHASES', '''MILESTONE_PHASES=('M1_PLAN_READY','M2_EVENT_READY','M3_PLACE_RETURN','M4_CHILD_DECISION')
MILESTONE_STAGES=('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
    'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
MILESTONE_FIELDS=(('pre_state','decision','decision_event','plan','prototype_census'),
    ('state','pending_preferences','event'),('state','transition','invalidation_event','place_event'),
    ('state','decision','decision_event','prototype_census'))
MILESTONE_ENGINE_VERSION='lazy-unit-row-global-engine-v13-receptor-family-preferences-v8-first-admission-journal'
MILESTONE_JOURNAL_MAX_BYTES=3*1048576
DIAGNOSTIC_MAX_BYTES=4*1048576+131072
PHASES=LEGACY_PHASES+CALLBACK_PHASES+SEARCH_PHASES+MILESTONE_PHASES''',1)
# Compute fixed literal wire bound from literal AST assignments only.
tree=ast.parse(reader); env={}
for n in tree.body:
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('LEGACY_PHASES','CALLBACK_PHASES','SEARCH_PHASES','MILESTONE_PHASES'):
        env[n.targets[0].id]=ast.literal_eval(n.value)
labels=sum((env[k] for k in ('LEGACY_PHASES','CALLBACK_PHASES','SEARCH_PHASES','MILESTONE_PHASES')),())
line_max=max(len(b'COMPONENT_INVENTORY_PHASE ')+len(s.encode('ascii'))+1+19+1 for s in labels)
total=sum(len(b'COMPONENT_INVENTORY_PHASE ')+len(s.encode('ascii'))+1+19+1 for s in labels)
assert line_max==75 and len(labels)==34
reader=reader.replace('PHASE_TOTAL_MAX_BYTES=1913','PHASE_TOTAL_MAX_BYTES='+str(total),1)
reader=reader.replace("                    if group=='P1':need('BEFORE_PROVIDER' in seen, 'first provider outer site precedes delegate')", "                    if group=='P1':need('BEFORE_PROVIDER' in seen, 'first provider outer site precedes delegate')\n                    if group in ('P2','C2','C3') and any(item in seen for item in MILESTONE_PHASES):\n                        need('M4_CHILD_DECISION' in seen, 'later callback follows the completed milestone prefix')",1)
reader=reader.replace("            elif label=='SEARCH_RETURN_OBSERVED':", '''            elif label in MILESTONE_PHASES:
                index=MILESTONE_PHASES.index(label)
                need('BEFORE_ENGINE'in seen and 'C1_CALLBACK_READY'in seen and not stack
                     and 'SEARCH_RETURN_OBSERVED'not in seen
                     and not any(item+'_ENTER'in seen for item in ('P2','C2','C3'))
                     and all(item in seen for item in MILESTONE_PHASES[:index]),
                     'fixed first-root milestone prefix before later callbacks/search return')
            elif label=='SEARCH_RETURN_OBSERVED':''',1)
reader=reader.replace("need(len(phases)<=30, 'finite fixed phase sites')", "need(len(phases)<=34, 'finite fixed phase sites')",1)
helper='''def validate_engine_milestones(slots, phases, began, deadline, terminal, headers=None):
    # Literal wire structure only. No state/decision/plan is mathematically checked.
    need(type(slots)is list and len(slots)==4, 'fixed four nullable raw milestone records')
    need(all(type(value)is int for value in (began,deadline,terminal))
         and deadline==began+20000000000, 'literal milestone original20 window')
    stamps={item['stage']:item['native_ns']for item in phases}
    supplied_headers=headers is not None
    if supplied_headers:
        need(type(headers)is list and len(headers)==4, 'fixed captured-header list')
    else:
        headers=[]
        for value in slots:
            if value is None:headers.append(None)
            else:
                need(type(value)is dict and all(type(key)is str for key in value), 'builtin raw record wrapper')
                need(set(value)=={'ordinal','stage','native_ns','record'}, 'exact raw record wrapper fields')
                headers.append({key:value[key]for key in ('ordinal','stage','native_ns')})
    captured=0;ended=False;previous=began
    for index,header in enumerate(headers):
        if header is None:ended=True;continue
        need(not ended and type(header)is dict and len(header)==3
             and all(type(key)is str for key in header)
             and set(header)=={'ordinal','stage','native_ns'}
             and type(header['ordinal'])is int and header['ordinal']==index+1
             and type(header['stage'])is str and header['stage']==MILESTONE_STAGES[index]
             and type(header['native_ns'])is int
             and previous<=header['native_ns']<deadline and header['native_ns']<=terminal,
             'literal monotone captured milestone header prefix')
        phase=MILESTONE_PHASES[index]
        need(phase in stamps and stamps[phase]<=header['native_ns']
             and (index==3 or MILESTONE_PHASES[index+1]not in stamps
                  or header['native_ns']<=stamps[MILESTONE_PHASES[index+1]])
             and ('SEARCH_RETURN_OBSERVED'not in stamps or header['native_ns']<=stamps['SEARCH_RETURN_OBSERVED']),
             'nullable raw capture timestamp joins reached marker, next stage and search return')
        previous=header['native_ns'];captured+=1
    # A later marker requires the earlier capture to have returned, but its own
    # post-marker native tick may fail before its raw slot is stored.
    for index in range(1,4):
        if MILESTONE_PHASES[index]in stamps:
            need(all(headers[j]is not None for j in range(index)), 'prior captures before a later milestone marker')
    serialized=0;ended=False
    common={'schema','stage','engine_version','depth','diagnostic_only','scientific_acceptance'}
    for index,value in enumerate(slots):
        if value is None:ended=True;continue
        need(not ended and type(value)is dict and len(value)==4
             and all(type(key)is str for key in value)
             and set(value)=={'ordinal','stage','native_ns','record'}, 'complete serialized wrapper prefix')
        need(headers[index]is not None and all(type(value[key])is type(headers[index][key])
             and value[key]==headers[index][key]for key in ('ordinal','stage','native_ns')),
             'serialized wrapper retains exact captured scalar header')
        record=value['record']
        need(type(record)is dict and all(type(key)is str for key in record)
             and set(record)==common|set(MILESTONE_FIELDS[index])
             and type(record['schema'])is str and record['schema']=='unit-row-first-family-engine-milestone-v1'
             and type(record['stage'])is str and record['stage']==MILESTONE_STAGES[index]
             and type(record['engine_version'])is str and record['engine_version']==MILESTONE_ENGINE_VERSION
             and type(record['depth'])is int and record['depth']==(1 if index==3 else 0)
             and record['diagnostic_only']is True and record['scientific_acceptance']is False,
             'literal current engine stage/version/depth/field schema only')
        pending=[record]
        while pending:
            item=pending.pop();kind=type(item)
            if item is None or kind in (bool,int,str):continue
            if kind is list:pending.extend(item)
            elif kind is dict:
                need(all(type(key)is str for key in item), 'raw record string keys')
                pending.extend(item.values())
            else:need(False, 'raw milestone builtin JSON types only')
        serialized+=1
    need(serialized<=captured and (supplied_headers or serialized==captured), 'captured vs serialized literal prefixes')
    return {'captured_headers':headers,'captured_record_count':captured,'serialized_record_count':serialized}


'''
reader=reader.replace('def read_failure_diagnostic(',helper+'def read_failure_diagnostic(',1)
reader=reader.replace("diagnostic_raw=read(owned/'unknown-diagnostic.json',PROVIDER_DIAGNOSTIC_MAX_BYTES)","diagnostic_raw=read(owned/'unknown-diagnostic.json',DIAGNOSTIC_MAX_BYTES)",1)
reader=reader.replace("('unit-row-controls-last-context-completion-v1','unit-row-controls-provider-returns-completion-v2'),", "('unit-row-controls-last-context-completion-v1','unit-row-controls-provider-returns-completion-v2',\n          'unit-row-controls-engine-milestones-completion-v3'),",1)
reader=reader.replace("    provider_journal=marker['schema']=='unit-row-controls-provider-returns-completion-v2'", "    engine_journal=marker['schema']=='unit-row-controls-engine-milestones-completion-v3'\n    provider_journal=engine_journal or marker['schema']=='unit-row-controls-provider-returns-completion-v2'",1)
reader=reader.replace("and (provider_journal or len(diagnostic_raw)<=16384),", "and (len(diagnostic_raw)<=DIAGNOSTIC_MAX_BYTES if engine_journal else\n              len(diagnostic_raw)<=PROVIDER_DIAGNOSTIC_MAX_BYTES if provider_journal else len(diagnostic_raw)<=16384),",1)
reader=reader.replace("    if provider_journal:outer_keys.add('provider_returns')", "    if provider_journal:outer_keys.add('provider_returns')\n    if engine_journal:outer_keys.add('engine_milestones')",1)
reader=reader.replace("        need(set(labels)==set(expected_labels)", '''        if engine_journal:
            expected_labels.update(schema='unit-row-controls-engine-milestones-diagnostic-v3',
                qualification='UNQUALIFIED_LITERAL_ENGINE_MILESTONE_RECORDS',
                callback_context='LITERAL_RETURNED_SCALARS_AND_RAW_ENGINE_RECORDS_ONLY',
                engine_milestone_records_are_unvalidated=True)
        metadata_keys={'captured_headers','captured_record_count','serialized_record_count',
            'omitted_record_count','next_omitted_ordinal','engine_record_prefix_reason','engine_journal_bytes'} if engine_journal else set()
        need(set(labels)==set(expected_labels)|metadata_keys''',1)
reader=reader.replace("    need(all(began<=phase['native_ns']<deadline for phase in phases)", '''    milestone_summary=None
    if engine_journal:
        milestone_summary=validate_engine_milestones(diagnostic['engine_milestones'],phases,began,deadline,terminal,
            labels['captured_headers'])
        captured=milestone_summary['captured_record_count'];serialized=milestone_summary['serialized_record_count']
        journal_raw=json.dumps(diagnostic['engine_milestones'],ensure_ascii=True,separators=(',', ':'),allow_nan=False).encode('ascii')
        need(all(type(labels[key])is int for key in ('captured_record_count','serialized_record_count',
                  'omitted_record_count','engine_journal_bytes'))
             and labels['captured_record_count']==captured and labels['serialized_record_count']==serialized
             and labels['omitted_record_count']==captured-serialized
             and type(labels['engine_record_prefix_reason'])is str
             and labels['engine_record_prefix_reason']in ('ALL_CAPTURED_RECORDS_SAVED',
                 'NEXT_RECORD_OUTPUT_BOUND_OR_BUILTIN_TYPE','ENGINE_JOURNAL_AGGREGATE_BYTE_LIMIT')
             and labels['engine_journal_bytes']==len(journal_raw)<=MILESTONE_JOURNAL_MAX_BYTES,
             'literal ASCII insertion-order whole journal bound/counts')
        if captured==serialized:
            need(labels['next_omitted_ordinal']is None
                 and labels['engine_record_prefix_reason']=='ALL_CAPTURED_RECORDS_SAVED', 'no omitted captured records')
        else:
            need(type(labels['next_omitted_ordinal'])is int and labels['next_omitted_ordinal']==serialized+1
                 and labels['engine_record_prefix_reason']!='ALL_CAPTURED_RECORDS_SAVED', 'explicit whole-record omitted suffix')
    need(all(began<=phase['native_ns']<deadline for phase in phases)''',1)
reader=reader.replace("    return result\n\n\ndef main", '''    if engine_journal:
        result.update(engine_milestones=diagnostic['engine_milestones'],
            engine_milestone_serialization={key:labels[key]for key in metadata_keys},
            engine_milestone_records_are_unvalidated=True,engine_milestone_semantic_acceptance=False)
    return result


def main''',1)
reader=reader.replace('        validate_positive_callback_phases(phases,pipeline)', '''        validate_positive_callback_phases(phases,pipeline)
        validate_engine_milestones(payload['engine_milestones'],phases,
            body['joint_began_ns'],body['joint_deadline_ns'],terminal)''',1)
(D/'first_admission_saved_reader_v3.py').write_text(reader)
(D/'parent-saved-reader.py').write_text(parent_reader)
# Parse and compile without execution; no generated functions are invoked.
for name,text in [('writer',writer),('reader',reader)]:
    ast.parse(text);compile(text,str(D/name),'exec')
print(json.dumps({'writer_bytes':len(writer.encode()),'reader_bytes':len(reader.encode()),'phase_count':len(labels) if False else len(env['LEGACY_PHASES'])+len(env['CALLBACK_PHASES'])+len(env['SEARCH_PHASES'])+len(env['MILESTONE_PHASES']),'line_max':line_max,'total_max':total}))
