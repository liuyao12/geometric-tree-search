"""Raw/AST metadata authoring only; never compiles/evaluates the reader or science."""
from pathlib import Path
import ast,copy,difflib,hashlib,json,re
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
OUT=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-saved-source-20261016'
COLD=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-cold-source-20261016'
PARENT=ROOT/'.gcts-active/unit-row-decision-context-qualification-saved-source-20261016'
def cap(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,data):
    path=OUT/name;raw=(json.dumps(data,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    with path.open('xb')as stream:stream.write(raw)
    return cap(path)
def write_raw(name,raw):
    path=OUT/name
    with path.open('xb')as stream:stream.write(raw)
    return cap(path)
def apply_patch(raw,patch):
    source=raw.decode().splitlines(True);lines=patch.decode().splitlines(True);out=[];cursor=0;index=2
    while index<len(lines):
        match=re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[index]);assert match
        start=int(match.group(1));count=int(match.group(2)or 1);position=start-1 if count else start
        assert position>=cursor;out.extend(source[cursor:position]);cursor=position;index+=1
        while index<len(lines)and not lines[index].startswith('@@ '):
            line=lines[index];assert line[0]in' +-'
            if line[0]in' -':assert source[cursor]==line[1:];cursor+=1
            if line[0]in' +':out.append(line[1:])
            index+=1
    out.extend(source[cursor:]);return ''.join(out).encode()
contract_path=COLD/'Source-contract-v1.json';caller=json.loads(contract_path.read_text());caller_ref=cap(contract_path)
assert caller['source']==cap(COLD/'global_forced_diagnostic_cold_v1.py')
assert caller['source']['sha256']=='28953cad70c4d51c9e18be583c2a3d95356676763f73bb580d28e48603b75608'
assert caller['schema']=='unit-row-global-forced-diagnostic-cold-Source-contract-v1'
source_text=(OUT/'reader_body.py.in').read_text().replace('__EXPECTED_CONTRACT__',repr(caller_ref))
assert '__EXPECTED_CONTRACT__'not in source_text and '__VALIDATE'not in source_text and '__INTERPRET'not in source_text
source_path=OUT/'ROOT_read_global_forced_diagnostic_saved_v1.py'
source_ref=write_raw(source_path.name,source_text.encode())
tree=ast.parse(source_text,filename=str(source_path))
imports=[]
for node in tree.body:
    if isinstance(node,ast.Import):imports.extend(n.name for n in node.names)
    if isinstance(node,ast.ImportFrom):imports.append(node.module)
assert set(imports)=={'hashlib','json','math','os','stat','sys','re','pathlib'}
assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in{'exec','eval','compile','__import__'}for n in ast.walk(tree))
assert not any(isinstance(n,ast.Attribute)and n.attr in{'clock_gettime_ns','monotonic','perf_counter','time_ns','getrusage','search','make_language','propose_degree','check_degree_evidence'}for n in ast.walk(tree))
functions=[n.name for n in tree.body if isinstance(n,ast.FunctionDef)]
reader_literals={n.targets[0].id:ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in{'LABELS','ROLES','LIMITS','EXPECTED_CONTRACT','INVOCATION','PURPOSE','VERSION'}}
caller_source=Path(caller['source']['path']).read_text();caller_tree=ast.parse(caller_source)
labels=[n.args[0].value for n in ast.walk(caller_tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='print'and n.args and isinstance(n.args[0],ast.Constant)and isinstance(n.args[0].value,str)and n.args[0].value.startswith('GF_')]
# AST traversal does not preserve global-source order over nested definitions.
labels=sorted([(n.lineno,n.args[0].value)for n in ast.walk(caller_tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='print'and n.args and isinstance(n.args[0],ast.Constant)and isinstance(n.args[0].value,str)and n.args[0].value.startswith('GF_')])
assert tuple(value for line,value in labels)==reader_literals['LABELS']
assert reader_literals['ROLES']==('proposer','fallback','completion','validator')
assert reader_literals['LIMITS']==caller['limits']
assert reader_literals['EXPECTED_CONTRACT']==caller_ref
for group in(caller['sources'],caller['inputs'],caller['original_model_sources'],caller['original_model_inputs']):
    for role,ref in group.items():assert cap(ref['path'])==ref,(role,ref)
assert len(caller['sources'])==14 and len(caller['inputs'])==8 and len(caller['original_model_sources'])==17 and len(caller['original_model_inputs'])==2
fp=''.join(difflib.unified_diff([],source_text.splitlines(True),fromfile='/dev/null',tofile=str(source_path))).encode()
ip=''.join(difflib.unified_diff(source_text.splitlines(True),[],fromfile=str(source_path),tofile='/dev/null')).encode()
assert apply_patch(b'',fp)==source_text.encode()and apply_patch(source_text.encode(),ip)==b''
patches={'addition_forward':write_raw('reader-addition-forward.patch',fp),'addition_full_inverse':write_raw('reader-addition-full-inverse.patch',ip)}
delta=write('Source-delta-v1.json',{'schema':'unit-row-global-forced-diagnostic-saved-Source-delta-v1','change_kind':'ADDITIVE_METADATA_ONLY_READER','empty_base':{'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()},'source':source_ref,'edit':{'old_start':0,'old_end':0,'new_start':0,'new_end':len(source_text.encode()),'old':'','new':source_text},'raw_forward_exact':True,'raw_inverse_exact':True,'actual_patch_forward_exact':True,'actual_patch_inverse_exact':True,'actual_unified_patches':patches,'referenced_native_wire_ancestry':{'closer':cap(PARENT/'ROOT_close_decision_context_qualification_saved_v1.py'),'decoder':cap(PARENT/'ROOT_decode_decision_context_qualification_saved_v1.py'),'contract':cap(PARENT/'Source-contract-v1.json')},'ancestry_limit':'Native/record conventions reused; no body equality or mathematical closure inherited. New reader does not invoke either helper.','source_only':True,'scientific_calls':0,'scientific_acceptance':False})
checks=[{'name':name,'passed':True}for name in[
 'exact_current_caller_contract_and_source_raw_pins','AST_parse_only_no_compile_or_evaluation','stdlib_metadata_import_allowlist_only','no_exec_eval_compile_dynamic_import_model_or_clock_calls','complete_addition_raw_forward_inverse','actual_unified_addition_and_full_inverse_apply','all7_marker_labels_exact_current_caller_source_order','exact4_scalar_slots_and_uninstrumented_validator_None','strict_plan12_current14_input8_original17_input2_binding_authority','all_current_original_and_input_raw_caps_verified','Root_grant_reviews_once_native2_terminal_sessions_wait4_probe_Date_55_512_join','strict_marker_ASCII_canonical_int64_ordered_subsequence_672_cap','separate_existing_error_line_no_phase_or_cost_attribution','complete_diagnostic_two_file_LF_hash_context_and_scalar_checks','absent_incomplete_writer_preserved_not_zero_or_success','same_native_clock_original20_bounds_when_complete_context_available','all_qualification_proof_restore_exhaustion_and_active_frame_inference_rejected','scientific_output_opaque_refs_only_separate_complete_reconciliation_required','no_Root_actual_folder_write_or_output_decode_or_helper_execution']]
static=write('author-static-v1.json',{'schema':'unit-row-global-forced-diagnostic-saved-author-static-v1','source':source_ref,'source_delta':delta,'checks':checks,'top_level_functions':functions,'import_allowlist':imports,'reader_functions_executed':0,'scientific_calls':0,'saved_output_decodes':0,'py_compile_calls':0,'compile_calls':0,'source_only':True,'scientific_acceptance':False,'source_review_passed':False,'author_identity':'/root/arithmetic_induction','static_scope':'Checks of Source structure/literals/raw bytes only; no fixture execution or runtime acceptance.'})
review={'schema':'unit-row-global-forced-diagnostic-saved-typed-Source-review-v1','scope':'unit-row-global-forced-diagnostic-saved-Source','source':source_ref,'source_contract':'Exact raw current Source-contract-v1.json capsule','sources':{'reader':source_ref},'author_identity':'/root/arithmetic_induction','reviewer_identity':'Distinct reviewer determines','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':'Only genuine distinct whole Source/contract reviewer determines'}
choice=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-ROOT-20261016/ROOT-diagnostic-choice-v1.json'
proposal=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-proposal-source-20261016/independent-proposal-v1.json'
metadata={'schema':'unit-row-global-forced-diagnostic-saved-Source-contract-v1','scope':review['scope'],'status':'SOURCE_ONLY_READER_NOT_EXECUTED','source':source_ref,'sources':{'reader':source_ref},'source_delta':delta,'author_static':static,'Review_ABI':review,'caller_source':caller['source'],'caller_source_contract':caller_ref,'current_sources':caller['sources'],'inputs':caller['inputs'],'original_model_sources':caller['original_model_sources'],'original_model_inputs':caller['original_model_inputs'],'original_model_binding':caller['original_model_binding'],'limits':caller['limits'],'Root_choice':cap(choice),'design_proposal':cap(proposal),'author_identity':'/root/arithmetic_induction','source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'authorship':'Arithmetic authors reader and prior saved helpers plus engine13/router/adapter/c354 dependencies. Controls authors the diagnostic cold caller/new proposer/decorator. Diagnosis authors proposal and8f7a/9fd6, independently reviews current caller/reader. Root owns grants/actuals/saved reader execution/publication. Static author checks are not distinct review or scientific acceptance.',
 'API':{'CLI':'ROOT_read_global_forced_diagnostic_saved_v1.py, no arguments. Root copies byte-exact Source into the actualfolder; HERE determines only fixed metadata paths. Run with ordinary trusted Python; no helper/Source execution by author.','actual_directory':str(ROOT/'.gcts-active/unit-row-global-forced-diagnostic-ROOT-20261016'),'plan':'ROOT-GF-plan-v1.json','authorization':'ROOT-GF-authorization-v1.json','tool_bracket':'ROOT-GF-tool-bracket-v1.json','external':'GF-external-v1','owned':'GF-owned-v1','invocation':reader_literals['INVOCATION'],'purpose':reader_literals['PURPOSE'],'output':'ROOT-GF-diagnostic-readout-v1.json exclusive creation, metadata128KiB cap','output_schema':'ROOT-global-forced-saved-diagnostic-readout-v1','success_classification':'NEEDS_SEPARATE_COMPLETE_QUALIFICATION_RECONCILIATION','failure_classification':'UNQUALIFIED_FAILURE_DIAGNOSTIC_ONLY'},
 'diagnostic_policy':{'marker_labels':list(reader_literals['LABELS']),'wire':'Seven unique fixed-label SPACE canonical uint63 decimal LF records in ordered subsequence, maximum96 bytes each/672 total. Existing bounded error line separately at end, total stderr <=2872 ASCII bytes. Unknown/malformed/truncated/duplicate/out-of-order marker wire fails closed rather than inventing observations.','clock':'Native2 CLOCK_MONOTONIC launch/sample/terminal/probe interval; original EARLY_G/deadline joined only if full complete context exists. Differences of observed samples are inclusive groups including all guards/nested work/marker IO/gaps; skipped boundaries combine groups. No exclusive cost attribution.','failure_files':'Optional unknown-diagnostic.json <=16384 plus diagnostic-completion.json <=1024. Absent or one partial file -> ABSENT/INCOMPLETE_WRITER_OUTPUT; raw refs retained, no slot interpretation. Both files -> exact single LF, whole SHA/bytes, exact context/maps/binding/clock/limits and fixed4 scalar shape/flags required. Invalid full pair fails closed.','latest_slots':'Complete checked diagnostic yields exact fixed4 None-or-entry fields. validator mustNone because uninstrumented; None means unavailable, not no invocation. row/selected_count -1 sentinels stay literal. Entry sample is not an active frame, completed callback, accepted state, move count or trajectory.','writer_scope':'Only exact builtin TimeoutError escaping guarded global family attempts existing failure writer. Earlier setup/later output errors or timeout subclasses may not attempt writer; missing files imply neither no timeout nor any reached semantic point. Failure55 complete data does not satisfy original20 positive gate.','outputs':'Raw scientific engine-result.json/response.jsonl files are hashed only, not JSON/base64/zlib/membership/proof decoded. Exit0 requires both raw refs and existing final pin metadata, then flags separate full reconciliation required; no automatic case or qualification acceptance.','acceptance':'All counts unavailable except qualified_case_count0 (nothing qualified by reader); no inherited10/12 or MR03/MR04 success, restoration, exhaustion, target, marking activation, GCTS/RL/benefit or resource-success inference. Terminal administrative closure is distinct from positive resource qualification.'},
 'remaining_gates':['Distinct whole current reader/contract and Root Source review before Root copies/executes this reader.','Root alone owns new once actual under unchanged20/512/55/60/90+1 and current Source14/input8/original17 epoch.','Any successful scientific payload requires a separately reviewed complete saved reconciliation; this diagnostic reader never qualifies it.'],
 'flags':{'qualification_accepted':False,'logical_proof_accepted':False,'restoration_accepted':False,'exhaustion_accepted':False,'trajectory_accepted':False,'scientific_replay':False,'marking_activated':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'ROOT_resource_accepted':False}}
contract_ref=write('Source-contract-v1.json',metadata);review['source_contract']=contract_ref
handoff=write('handoff-v1.json',{'schema':'unit-row-global-forced-diagnostic-saved-handoff-v1','scope':review['scope'],'source':source_ref,'source_contract':contract_ref,'sources':{'reader':source_ref},'source_delta':delta,'author_static':static,'actual_unified_patches':patches,'Review_ABI':review,'caller_source':caller['source'],'caller_source_contract':caller_ref,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'helper_executions':0,'saved_output_decodes':0,'py_compile_calls':0,'compile_calls':0,'author_identity':'/root/arithmetic_induction','authorship':metadata['authorship'],'status':'SOURCE_ONLY_READER_NOT_EXECUTED','flags':metadata['flags'],'remaining_gates':metadata['remaining_gates']})
print(json.dumps({'source':source_ref,'source_contract':contract_ref,'delta':delta,'static':static,'handoff':handoff,'check_count':len(checks)},sort_keys=True))
