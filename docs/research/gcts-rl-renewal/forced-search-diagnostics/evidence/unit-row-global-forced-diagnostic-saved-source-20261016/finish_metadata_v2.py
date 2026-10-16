"""Raw/AST correction metadata only; no reader/fixture/Source evaluation or compile."""
from pathlib import Path
import ast,copy,difflib,hashlib,json,re
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
OUT=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-saved-source-20261016'
def cap(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
    path=OUT/name;raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    with path.open('xb')as stream:stream.write(raw)
    return cap(path)
def write_raw(name,raw):
    path=OUT/name
    # Prior metadata handle wrote these immutable patches before its read stalled.
    assert path.read_bytes()==raw
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
oldpath=OUT/'ROOT_read_global_forced_diagnostic_saved_v1.py';newpath=OUT/'ROOT_read_global_forced_diagnostic_saved_v2.py'
old,new=oldpath.read_bytes(),newpath.read_bytes();ot,nt=old.decode(),new.decode()
assert cap(oldpath)['sha256']=='4092c6869f028f09d7dbeee754894b41a7c3848fc71ca2f2a7ccc46b89d11f3e'
assert cap(newpath)['sha256']=='7f77ab7b2ac03ea3053d256f1a89773c70c314ae0402d28e288700a57155f1d6'
a,b=ast.parse(ot),ast.parse(nt)
oldfunc={n.name:(ast.dump(n,include_attributes=False),ast.get_source_segment(ot,n))for n in a.body if isinstance(n,ast.FunctionDef)}
newfunc={n.name:(ast.dump(n,include_attributes=False),ast.get_source_segment(nt,n))for n in b.body if isinstance(n,ast.FunctionDef)}
assert set(oldfunc)==set(newfunc)
changed=[n for n in oldfunc if oldfunc[n]!=newfunc[n]];assert changed==['main']
unchanged=[n for n in oldfunc if n not in changed]
ol,nl=old.splitlines(True),new.splitlines(True);oo=[0];nn=[0]
for line in ol:oo.append(oo[-1]+len(line))
for line in nl:nn.append(nn[-1]+len(line))
edits=[]
for tag,i,j,k,l in difflib.SequenceMatcher(None,ol,nl,autojunk=False).get_opcodes():
    if tag=='equal':continue
    edits.append({'old_start':oo[i],'old_end':oo[j],'new_start':nn[k],'new_end':nn[l],'old':b''.join(ol[i:j]).decode(),'new':b''.join(nl[k:l]).decode()})
forward=old
for e in reversed(edits):assert forward[e['old_start']:e['old_end']]==e['old'].encode();forward=forward[:e['old_start']]+e['new'].encode()+forward[e['old_end']:]
inverse=new
for e in reversed(edits):assert inverse[e['new_start']:e['new_end']]==e['new'].encode();inverse=inverse[:e['new_start']]+e['old'].encode()+inverse[e['new_end']:]
assert forward==new and inverse==old
assert ast.dump(ast.parse(inverse.decode()),include_attributes=False)==ast.dump(a,include_attributes=False)
fp=''.join(difflib.unified_diff(ot.splitlines(True),nt.splitlines(True),fromfile=str(oldpath),tofile=str(newpath))).encode()
ip=''.join(difflib.unified_diff(nt.splitlines(True),ot.splitlines(True),fromfile=str(newpath),tofile=str(oldpath))).encode()
assert apply_patch(old,fp)==new and apply_patch(new,ip)==old
patches={'forward':write_raw('reader-v1-to-v2-forward.patch',fp),'full_inverse':write_raw('reader-v2-to-v1-full-inverse.patch',ip)}
for begin,end in[("        need(line.endswith(b'\\n')","    diagnostic=None;"),("    diagnostic=None;","    intervals="),("    plan_path=","    stderr=")]:
    assert ot[ot.index(begin):ot.index(end)]==nt[nt.index(begin):nt.index(end)]
assert 'native_deadline_confirmed'not in nt and 'DEADLINE_LINE'not in nt
assert "'failure_cause_established':False"in nt and "'native_tick_timeout_line_observed':error_line==TICK_TIMEOUT_LINE.decode('ascii')"in nt and "'caller_lifetime_at_least20':terminal-start>=20000000000"in nt
parent=json.loads((OUT/'Source-contract-v1.json').read_text())
# V2 changes no authority capsule; the parent froze full raw checks. Repeated
# profile read stalled and was interrupted metadata-only; do not claim it passed.
caller_contract=json.loads(Path(parent['caller_source_contract']['path']).read_text())
assert caller_contract['sources']==parent['current_sources']
assert caller_contract['inputs']==parent['inputs']
assert caller_contract['original_model_sources']==parent['original_model_sources']
assert caller_contract['original_model_inputs']==parent['original_model_inputs']
assert caller_contract['original_model_binding']==parent['original_model_binding']
negpath=ROOT/'.gcts-active/unit-row-global-forced-diagnostic-saved-independent-source-20261016/typed-Source-review-v1.json'
delta=write('Source-delta-v2.json',{'schema':'unit-row-global-forced-diagnostic-saved-Source-delta-v2','parent':cap(oldpath),'source':cap(newpath),'edits':edits,'raw_forward_exact':True,'raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_forward_exact':True,'actual_patch_inverse_exact':True,'actual_unified_patches':patches,'changed_functions':changed,'unchanged_functions_raw_AST':unchanged,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
checks=[{'name':n,'passed':True}for n in['exact_immutable_parent_current_raw_pins','AST_only_no_compile_or_evaluation','full_four_region_raw_forward_and_inverse','actual_unified_patch_both_directions_exact','whole_AST_inverse_exact','only_main_function_changes_all_helpers_raw_AST_exact','all_complete_line_parser_grammar_order_native_checks_raw_exact','whole_plan_grant_source_native_session_once_prefix_raw_exact','whole_optional_failure_pair_scalar_context_block_raw_exact','bounded_final_nonLF_fragment_uninterpreted_only','old_deadline_cause_field_absent','timeout_line_and_lifetime_observations_separate_causeFalse','caller_contract_maps_binding_limits_unchanged','all_authority_maps_literal_equal_frozen_V1_and_current_caller_contract','no_reader_helper_outputdecode_model_clock_actual_or_py_compile']]
static=write('author-static-v2.json',{'schema':'unit-row-global-forced-diagnostic-saved-author-static-v2','source':cap(newpath),'source_delta':delta,'checks':checks,'changed_functions':changed,'unchanged_functions_raw_AST':unchanged,'compile_calls':0,'py_compile_calls':0,'reader_functions_executed':0,'saved_output_decodes':0,'scientific_calls':0,'scientific_acceptance':False,'source_only':True,'source_review_passed':False,'author_identity':'/root/arithmetic_induction'})
contract=copy.deepcopy(parent)
contract.update(schema='unit-row-global-forced-diagnostic-saved-Source-contract-v2',source=cap(newpath),sources={'reader':cap(newpath)},source_delta=delta,author_static=static,parent_source=cap(oldpath),parent_source_contract=cap(OUT/'Source-contract-v1.json'),preserved_v1_negative=cap(negpath))
contract['API']['CLI']='ROOT_read_global_forced_diagnostic_saved_v2.py, no arguments; Root copies byte-exact into fixed GF actualfolder. No author execution.'
contract['diagnostic_policy']['wire']='Strict complete-line fixed7 grammar/order/native checks unchanged. Optional final non-LF fragment <=2200 ASCII bytes is retained verbatim as uninterpreted string/byte count within whole raw stderr <=2872. No sample, label, error or timestamp is recognized from that tail. Malformed complete lines still fail closed.'
contract['diagnostic_policy']['failure_files']='Absent or one partial owned writer file remains ABSENT/INCOMPLETE_WRITER_OUTPUT with raw refs, no scalar interpretation. When BOTH expected writer files exist, the complete single-LF/hash/context/scalar pair must validate; a truncated or malformed complete-named pair intentionally fails closed rather than being interpreted. Optional stderr tail handling does not weaken owned diagnostic-pair validation.'
contract['diagnostic_policy']['timeout_observations']='native_tick_timeout_line_observed compares only the separately parsed complete error line to the fixed shared tick message. caller_lifetime_at_least20 is separately the inclusive native caller lifetime. failure_cause_established is alwaysFalse: same tick message covers cancellation/deadline/500MiB reserve, and failure55 writer work extends caller lifetime after the throw. No deadline/cause attribution is made.'
contract['metadata_read_limitation']='Initial metadata handle82858 and raw-only diagnostic31795 were interrupted at a repeated regular profile raw read; no scientific/helper/actual ran. V2 authority maps are literal-equal frozenV1/currentcallercontract; V1 full raw checks are historical, not mislabeled freshly repeated. Reader runtime still enforces every fresh raw capsule.'
contract['corrections']={'v1_preserved':True,'reported_by':['/root','/root/hilbert_ordering_diagnosis'],'partial_stderr_tail':'Honor caller-permitted bounded partial final stderr line without interpreting it. Complete-line parser unchanged.','attribution':'Remove native_deadline_confirmed; split literal line and elapsed observations, causeFalse.','scientific_acceptance':False}
review=contract['Review_ABI'];review.update(schema='unit-row-global-forced-diagnostic-saved-typed-Source-review-v2',source=cap(newpath),sources={'reader':cap(newpath)},source_contract='Exact raw current Source-contract-v2.json capsule')
contractref=write('Source-contract-v2.json',contract);review['source_contract']=contractref
handoff=write('handoff-v2.json',{'schema':'unit-row-global-forced-diagnostic-saved-handoff-v2','scope':contract['scope'],'source':cap(newpath),'source_contract':contractref,'sources':{'reader':cap(newpath)},'source_delta':delta,'author_static':static,'actual_unified_patches':patches,'Review_ABI':review,'caller_source':contract['caller_source'],'caller_source_contract':contract['caller_source_contract'],'parent_source':cap(oldpath),'parent_source_contract':cap(OUT/'Source-contract-v1.json'),'preserved_v1_negative':cap(negpath),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'helper_executions':0,'saved_output_decodes':0,'py_compile_calls':0,'compile_calls':0,'author_identity':'/root/arithmetic_induction','authorship':contract['authorship'],'status':contract['status'],'flags':contract['flags'],'remaining_gates':contract['remaining_gates']})
print(json.dumps({'source':cap(newpath),'source_contract':contractref,'delta':delta,'static':static,'handoff':handoff,'edits':len(edits),'unchanged_function_count':len(unchanged)},sort_keys=True))
