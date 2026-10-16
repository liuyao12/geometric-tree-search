"""Minimal latest-adapter-context successor assembly. Raw Source/AST/JSON only."""
import ast,hashlib,json,difflib
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(n,x):
 p=HERE/n
 if p.exists():assert read(p)==x;return pin(p)
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
parent=BASE/'unit-row-continuation-progress-cold-ROOT-source-20261016/unit_row_continuation_progress_cold_v11.py';pc=parent.parent/'Source-contract-v11.json'
assert pin(parent)['sha256']=='9a04d3729b1317db3f1b0580d94c0b051700a7f499f9a76601ed4a8e03d7074f' and pin(pc)['sha256']=='ce31a1c47709bc8887df8da488a90313d336d7aaf46f40fd4fbf091cca6e13e7'
prior=read(pc);old=parent.read_text();text=old;edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1,a[:100]
 text=text.replace(a,b,1);edits.append({'before':a,'after':b})
replace("VERSION='unit-row-continuation-progress-cold-v11'","VERSION='unit-row-latest-context-cold-v12'")
replace("SCOPE='unit-row-continuation-progress-cold-Source'","SCOPE='unit-row-latest-context-cold-Source'")
replace("contract['schema'] == 'unit-row-continuation-progress-cold-Source-contract-v11'","contract['schema'] == 'unit-row-latest-context-cold-Source-contract-v12'")
replace('    native_tick = tick\n','    native_tick = tick\n    latest_callbacks = {\'proposer\':None,\'fallback\':None,\'completion\':None,\'validator\':None}\n')
for name,role,signature,rowvalue in [
 ('proposer_adapter','proposer','*,language,state,row,tick','row'),
 ('fallback_adapter','fallback','*,language,state,row,tick','row'),
 ('certify_adapter','completion','*,language,state,row,completion,checked_candidates,tick','row'),
 ('validate_advice_adapter','validator','*,state,decision,batch,tick',"decision.get('row') if type(decision) is dict else None")]:
 a='    def '+name+'('+signature+'):\n        injected_tick = tick\n        def step():\n            native_tick()\n            injected_tick()\n'
 b='    def '+name+'('+signature+'):\n        injected_tick = tick\n        observed_row = '+rowvalue+'\n        diagnostic_row = observed_row if type(observed_row) is int and 0<=observed_row<24 else -1\n        selected_argument = state.get(\'selected\') if type(state) is dict else None\n        diagnostic_selected = len(selected_argument) if type(selected_argument) is list and len(selected_argument)<=24 else -1\n        def step():\n            diagnostic_native_ns = native_tick()\n            latest_callbacks['+repr(role)+'] = ('+repr(role.upper()+'_NATIVE_STEP')+',diagnostic_row,diagnostic_selected,diagnostic_native_ns)\n            injected_tick()\n'
 replace(a,b)
# Existing failure writer: add an explicit progress-only branch, retaining the old
# search branch byte-for-byte apart from indentation and one completion schema choice.
a=text.index("    available = capture['returned'] is True\n");z=text.index("    if len(raw) > 4*1048576+131072:",a)
oldbranch=text[a:z]
newbranch='''    if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS':
        roles = ('proposer','fallback','completion','validator')
        if type(capture) is not dict or set(capture) != set(roles):
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
        raw = b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"last_observations":'+encoded(observations,4096)+b'}\\n'
        if len(raw)>16384:raise ValueError('whole controls-context diagnostic16KiB bound')
    else:
'''+''.join('    '+line if line.strip() else line for line in oldbranch.splitlines(keepends=True))
replace(oldbranch,newbranch)
replace("marker = encoded({'schema':'unit-row-search-failure-diagnostic-completion-v1',","marker = encoded({'schema':('unit-row-controls-last-context-completion-v1' if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS' else 'unit-row-search-failure-diagnostic-completion-v1'),")
original_invoke="        payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,\n            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)\n"
replacement='''        diagnostic_run = Path(plan['output_directory'])
        need(diagnostic_run.is_absolute() and diagnostic_run == diagnostic_run.resolve()
            and not diagnostic_run.exists(), 'fresh canonical controls output before delegation')
        diagnostic_path = str(diagnostic_run)
        diagnostic_context = canonical({'purpose':plan['purpose'],'invocation_id':plan['invocation_id'],
            'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
            'language_binding':decode(binding_raw),'joint_began_ns':EARLY_G,
            'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,'limits':LIMITS})
        failure_writer = save_failure_diagnostic
        failure_writer_state = anchor_fn(failure_writer)
        controls_timeout_type = TimeoutError
        try:
            payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,
                boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        except BaseException as control_error:
            if type(control_error) is controls_timeout_type:
                try:
                    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                            or same is not same_fn or same_fn.__code__ is not same_code
                            or not same_fn(failure_writer,failure_writer_state)):
                        raise RuntimeError('original raw controls-context writer changed')
                    failure_writer(diagnostic_path,diagnostic_context,latest_callbacks,
                        'CONTROLS_TIMEOUT_LAST_SCALARS',EARLY_G)
                except BaseException:
                    pass
            raise
'''
replace(original_invoke,replacement)
path=HERE/'unit_row_latest_context_cold_v12.py'
if path.exists():assert path.read_bytes()==text.encode()
else:
 with path.open('xb') as f:f.write(text.encode())
compile(ast.parse(text),str(path),'exec');inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1
 inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
# Scientific/positive paths and unchanged helper inventory remain exactly located.
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',"
assert text[text.index(tail):]==old[old.index(tail):]
search_start='        diagnostic_run = Path(plan[\'output_directory\'])\n'
startold=old.index('    else:\n'+search_start,old.index('    is_controls ='))
startnew=text.index('    else:\n'+search_start,text.index('    is_controls ='))
assert text[startnew:text.index('    result_raw = canonical(',startnew)]==old[startold:old.index('    result_raw = canonical(',startold)]
tree=ast.parse(text);otree=ast.parse(old);defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)];odefs=[n for n in otree.body if isinstance(n,ast.FunctionDef)]
assert [n.name for n in defs]==[n.name for n in odefs]
unchanged=[]
for a,b in zip(defs,odefs):
 if a.name not in ('main','save_failure_diagnostic'):
  assert ast.get_source_segment(text,a)==ast.get_source_segment(old,b);unchanged.append(a.name)
source=pin(path);sources=dict(prior['sources'],intake=source)
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
assert len(sources)==17 and all(sources[k]==prior['sources'][k] for k in sources if k!='intake')
delta=save('Source-delta-v12.json',{'schema':'ROOT-latest-context-cold-Source-delta-v12','parent':pin(parent),'source':source,'edits':edits,'full_raw_AST_inverse_recovers_parent':True,'scope':'Own3IDs; four fixed scalar slots and four native-first adapter steps; explicit controls TimeoutError raw retention using existing bounded native failure writer; no scientific dependency/input/limit change.'})
(HERE/'caller11-to-caller12-forward.patch').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),text.splitlines(keepends=True),fromfile='caller11',tofile='caller12')))
c=dict(prior,schema='unit-row-latest-context-cold-Source-contract-v12',scope='unit-row-latest-context-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-latest-context-cold-typed-Source-review-v12',scope=c['scope'],source=source,sources=sources)
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
c['unchanged_top_level_helpers']=unchanged;c['unchanged_failure_writer']=False
c['latest_context_successor']={'roles':['proposer','fallback','completion','validator'],'slot_count':4,'fields':['stage','row','selected_count','native_ns'],'slot_value':'None or exact4tuple; diagnostic fields only. No history, generated count, step limit or call ID.','row_bounds':[-1,23],'selected_count_bounds':[-1,24],'unavailable_context':-1,'context':'row/count captured from exact builtin adapter entry arguments, not live engine state. Missing/malformed optional context records unavailable; no new scientific rejection. Four separate roles can report different old entry states and different native times; no single-state authority.','update':'Existing native_tick() result assigned; overwrite same role tuple BEFORE unchanged injected_tick(). No added clock/native call, engine/snapshot/model call, semantic/hash/copy or liveIO in step. Existing step returnNone/delegate kwargs/count/identity/exceptions unchanged. Extra scalar work remains charged original20.','ownership':'One caller-main-owned dict outside engine checkpoints/rollback; not passed to engine, not part of proof/state/selection. Fallback step retained by actual cursor can update its old entry context during later cursor work.','failure':'Only selected captured builtin TimeoutError escaping controls invoke triggers best-effort existing captured-native failure55 writer, explicit new failure_kind and progress-only branch/schema. Preencoded currentcontext before delegation; rawdata never a control record, target proof or active failure frame. Rethrow original; exit2/external terminal remains required. No project call/lateguard/model/snapshot after20. Non-timeout path unchanged.','raw_file':'unknown-diagnostic.json','completion_file':'diagnostic-completion.json','raw_schema':'unit-row-controls-last-context-diagnostic-v1','completion_schema':'unit-row-controls-last-context-completion-v1','maximum_raw_bytes':16384,'maximum_completion_bytes':1024,'completion':'Full rawbytes/SHA/LF+completionmarker+actualexit2/reap/nativefailure55/owned60/512MiB/caller90+1 required. Partialunsupportedcapture/writerfault remains inventory only, UNKNOWN unchanged.','search_failure_route_byte_exact':True,'existing_search_writer_branch_erasure_exact':True,'old_controls6_phase_progress_wires_unchanged':True,'all_original43_checks_unchanged':True,'runtime_qualification_inherited':False,'fit_prediction':False,'scientific_acceptance':False}
c['diagnostics']=prior['diagnostics']
c['latest_context_successor']['adviser_internal_fallback_coverage']=False
c['latest_context_successor']['blind_spot']='adviser_adapter passes raw fallback/iter_syntax with adviser.step, bypassing fallback_adapter. Four slots do not identify adviser-internal enumeration. Root role context may be stale during any uninstrumented guard/rollback/search work.'
cr=save('Source-contract-v12.json',c)
save('static-evidence-v12.json',{'source':source,'source_contract':cr,'edits':len(edits),'whole_raw_AST_inverse':True,'unchanged_raw_top_level_helpers':unchanged,'same17tophelpers_no_newhelper':len(defs)-1==17,'old_target_search_route_raw_exact':True,'positive_response_native_exit_tail_exact':True,'other16Sources_input2_alllimits_exact':True,'compile_only':True,'scientific_calls':0,'scientific_acceptance':False})
hr=save('handoff-v12.json',{'schema':'ROOT-latest-context-cold-Source-handoff-v12','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'expected_consumer_cases':43,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
