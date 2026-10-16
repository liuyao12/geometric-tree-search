"""Source/raw/AST metadata only. Does not invoke saved or scientific helpers."""
from pathlib import Path
import ast,copy,difflib,hashlib,json,re
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
OUT=ROOT/'.gcts-active/unit-row-decision-context-qualification-saved-source-20261016'
PARENT=ROOT/'.gcts-active/unit-row-routed-engine-qualification-saved-source-20261016'
COLD=ROOT/'.gcts-active/unit-row-decision-context-qualification-cold-source-20261016'
def cap(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,data):
    raw=(json.dumps(data,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode();path=OUT/name
    with path.open('xb')as f:f.write(raw)
    return cap(path)
def rawwrite(name,raw):
    path=OUT/name
    with path.open('xb')as f:f.write(raw)
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
old_contract=json.loads((PARENT/'Source-contract-v3.json').read_text())
caller=json.loads((COLD/'Source-contract-v1.json').read_text())
assert cap(COLD/'Source-contract-v1.json')['sha256']=='105cc90ec4a8993410563dc1d6c9bd3fce62b5e5f0cd9696a13e229737fa26cd'
assert caller['source']['sha256']=='dd4edc8a204b9407a27e8c2d09d0a795accd6d6028e509ed96cabd879621f325'
assert caller['sources']['engine']['sha256']=='40adc4fef7d5930ad49100149c1ca6390b1894f88c52f6fb38d97d914b00ce10'
assert len(caller['sources'])==14 and len(caller['inputs'])==8 and len(caller['original_model_sources'])==17
assert caller['original_model_sources']==old_contract['original_model_sources']
assert caller['original_model_inputs']==old_contract['original_model_inputs']
assert caller['original_model_binding']==old_contract['original_model_binding']
assert caller['inputs']==old_contract['inputs']
assert caller['API']['purpose_modes_and_ordered_cases']==old_contract['API']['purpose_modes_and_ordered_cases']
assert caller['limits']==old_contract['limits']
assert {k for k in caller['sources'] if caller['sources'][k]!=old_contract['current_sources'][k]}=={'intake','engine'}
for group in(caller['sources'],caller['inputs'],caller['original_model_sources'],caller['original_model_inputs']):
    for role,packet in group.items():assert cap(packet['path'])==packet,(role,packet)
roles={
 'decoder':('ROOT_decode_routed_engine_qualification_saved_v1.py','ROOT_decode_decision_context_qualification_saved_v1.py'),
 'closer':('ROOT_close_routed_engine_qualification_saved_v3.py','ROOT_close_decision_context_qualification_saved_v1.py')}
oldcap=repr(old_contract['caller_source_contract']);newcap=repr(cap(COLD/'Source-contract-v1.json'))
# Capsule repr in Source is path/sha/bytes order, independent of sorted JSON metadata order.
oldcap=repr({k:old_contract['caller_source_contract'][k]for k in('path','sha256','bytes')})
newcap=repr({k:cap(COLD/'Source-contract-v1.json')[k]for k in('path','sha256','bytes')})
replacements=[(oldcap,newcap),
 ('38f8f86f5af3474a0eed6fac7ff89c5d9c2b327d1413a2164be24ca8d7ea6e60','dd4edc8a204b9407a27e8c2d09d0a795accd6d6028e509ed96cabd879621f325'),
 ('unit-row-routed-engine-qualification-cold-Source','unit-row-decision-context-qualification-cold-Source'),
 ('unit-row-routed-engine-qualification-cold-v1','unit-row-decision-context-qualification-cold-v1'),
 ('lazy-unit-row-global-engine-v12-routed-marked-aware-degree','lazy-unit-row-global-engine-v13-decision-local-checked-state')]
changes={};patches={};function_report={};parents={};sources={}
for role,(oldname,newname)in roles.items():
    old_path=PARENT/oldname;new_path=OUT/newname
    old,new=old_path.read_bytes(),new_path.read_bytes();ot,nt=old.decode(),new.decode()
    assert cap(old_path)==old_contract['sources'][role]
    expected=ot
    for previous,current in replacements:expected=expected.replace(previous,current)
    assert expected==nt
    reverted=nt
    for previous,current in reversed(replacements):reverted=reverted.replace(current,previous)
    assert reverted==ot
    compile(nt,str(new_path),'exec',dont_inherit=True)
    before,after=ast.parse(ot),ast.parse(nt)
    assert ast.dump(ast.parse(reverted),include_attributes=False)==ast.dump(before,include_attributes=False)
    def funcs(tree,text):return {n.name:(ast.dump(n,include_attributes=False),ast.get_source_segment(text,n))for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    bf,af=funcs(before,ot),funcs(after,nt);assert set(bf)==set(af)
    changed=[k for k in bf if bf[k]!=af[k]];unchanged=[k for k in bf if k not in changed]
    assert changed==([]if role=='decoder'else['auth_plan']),changed
    function_report[role]={'function_count':len(bf),'changed':changed,'unchanged_raw_AST':unchanged,
       'all_functions_raw_AST_exact_after_authority_literal_inverse':True}
    ol,nl=old.splitlines(True),new.splitlines(True);oo=[0];nn=[0]
    for line in ol:oo.append(oo[-1]+len(line))
    for line in nl:nn.append(nn[-1]+len(line))
    edits=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(None,ol,nl,autojunk=False).get_opcodes():
        if tag=='equal':continue
        edits.append({'old_start':oo[i],'old_end':oo[j],'new_start':nn[k],'new_end':nn[l],
          'old':b''.join(ol[i:j]).decode(),'new':b''.join(nl[k:l]).decode()})
    fwd=old
    for e in reversed(edits):assert fwd[e['old_start']:e['old_end']]==e['old'].encode();fwd=fwd[:e['old_start']]+e['new'].encode()+fwd[e['old_end']:]
    inv=new
    for e in reversed(edits):assert inv[e['new_start']:e['new_end']]==e['new'].encode();inv=inv[:e['new_start']]+e['old'].encode()+inv[e['new_end']:]
    assert fwd==new and inv==old
    fp=''.join(difflib.unified_diff(ot.splitlines(True),nt.splitlines(True),fromfile=str(old_path),tofile=str(new_path))).encode()
    ip=''.join(difflib.unified_diff(nt.splitlines(True),ot.splitlines(True),fromfile=str(new_path),tofile=str(old_path))).encode()
    assert apply_patch(old,fp)==new and apply_patch(new,ip)==old
    patches[role]={'forward':rawwrite(role+'-forward.patch',fp),'inverse':rawwrite(role+'-full-inverse.patch',ip)}
    changes[role]={'parent':cap(old_path),'source':cap(new_path),'edits':edits,'raw_forward_exact':True,'raw_inverse_exact':True,'whole_AST_inverse_exact':True,'patch_forward_exact':True,'patch_inverse_exact':True,'actual_unified_patches':patches[role]}
    parents[role]=cap(old_path);sources[role]=cap(new_path)
closer=(OUT/roles['closer'][1]).read_text();tree=ast.parse(closer)
assert len([n for n in ast.walk(tree)if isinstance(n,ast.Name)and n.id=='expected_cases'and isinstance(n.ctx,ast.Store)])==1
assert 'expected_cases=tuple('in closer and 'case_names=list(expected_cases)'in closer
assert 'expected_proposal='in closer
assert len([n for n in ast.walk(tree)if isinstance(n,ast.Name)and n.id=='expected_proposal'and isinstance(n.ctx,ast.Store)])==3
# Every exact body except the two-authority-literal auth_plan is inherited, including
# native failure/null counts, aggregate, session joins and all scientific-record joins.
checks=[
 {'name':'corrected_parent_V3_and_decoder_raw_pins','passed':True},
 {'name':'compile_only_no_helper_evaluation','passed':True},
 {'name':'only_declared_authority_literal_substitutions','passed':True},
 {'name':'complete_raw_forward_inverse_both_helpers','passed':True},
 {'name':'actual_unified_forward_inverse_all_four_patches','passed':True},
 {'name':'whole_AST_inverse_both_helpers','passed':True},
 {'name':'decoder_all9_functions_raw_AST_exact','passed':True},
 {'name':'closer_all24_functions_accounted_only_auth_plan_authorities_change','passed':True},
 {'name':'failure_and_aggregate_and_mathrecord_functions_raw_AST_exact','passed':True},
 {'name':'immutable_expected_cases_one_store_expected_proposal_separate','passed':True},
 {'name':'truthful_session_None_or_matching_positive_exactint_gates_unchanged','passed':True},
 {'name':'native_wire_canonical_zlib_caps_response_output_gates_unchanged','passed':True},
 {'name':'all_six_modes_twelve_cases_and_schema_ids_unchanged','passed':True},
 {'name':'current14_only_intake_engine_changed','passed':True},
 {'name':'input8_original17_input2_binding_limits_exact_unchanged','passed':True},
 {'name':'all_current_original_input_caps_raw_verified','passed':True},
 {'name':'no_root_actual_folder_writes_or_helper_output_decoding','passed':True},
 {'name':'no_scientific_import_evaluation_function_model_clock_actual','passed':True}]
delta=write('Source-delta-v1.json',{'schema':'unit-row-decision-context-qualification-saved-Source-delta-v1','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'helpers':changes,'function_preservation':function_report,'literal_substitutions':[{'old':a,'new':b}for a,b in replacements]})
static=write('author-static-v1.json',{'schema':'unit-row-decision-context-qualification-saved-author-static-v1','author_identity':'/root/arithmetic_induction','sources':sources,'source_delta':delta,'checks':checks,'function_preservation':function_report,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':False,'helper_executions':0,'saved_output_decodes':0,'note':'Author Source/raw/AST checks only; not independent review or runtime/scientific acceptance.'})
api=copy.deepcopy(old_contract['API'])
api['actual_directory']='Root copies both byte-exact helpers into .gcts-active/unit-row-decision-context-ROOT-20261016; HERE is that actual folder. Run Python with assertions enabled, no -O/PYTHONOPTIMIZE. No author execution or output decode.'
api['decoder_CLI']='ROOT_decode_decision_context_qualification_saved_v1.py mode; six unchanged plain modes. Complete positive owned encoded records only, never nonzero/no-return outputs.'
api['closer_CLI']='ROOT_close_decision_context_qualification_saved_v1.py mode or aggregate; six unchanged modes/paths/schema IDs.'
api['scope']='Current engine13 six/twelve scoped controls only. All old engine12 actuals and dispositions stay immutable and incomplete; no retroactive qualification, original StageC9 promotion, target/proof/activation/GCTS/RL/benefit claim.'
review={'schema':'unit-row-decision-context-qualification-saved-typed-Source-review-v1','scope':'unit-row-decision-context-qualification-saved-helpers-Source','source':sources['closer'],'source_contract':'Exact raw current Source-contract-v1.json capsule','sources':sources,'author_identity':'/root/arithmetic_induction','reviewer_identity':'Distinct reviewer determines','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':'Only genuine distinct whole current helper/contract reviewer determines'}
contract={'schema':'unit-row-decision-context-qualification-saved-helpers-Source-contract-v1','scope':review['scope'],'status':'SOURCE_ONLY_NOT_EXECUTED','author_identity':'/root/arithmetic_induction','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source':sources['closer'],'sources':sources,'parent_helpers':parents,'parent_source_contract':cap(PARENT/'Source-contract-v3.json'),'source_delta':delta,'author_static':static,'Review_ABI':review,'API':api,
 'caller_source':caller['source'],'caller_source_contract':cap(COLD/'Source-contract-v1.json'),'current_sources':caller['sources'],'inputs':caller['inputs'],'original_model_sources':caller['original_model_sources'],'original_model_inputs':caller['original_model_inputs'],'original_model_binding':caller['original_model_binding'],'limits':caller['limits'],
 'authorship':'Arithmetic authors these saved helper successors and their corrected V3 ancestry, engine13/engine12/router/oldadapter/c354. Controls authors the current cold caller and new proposer; diagnosis authors new checker/verifier and decision-context proposal. A distinct reviewer must disclose these dependencies. Root alone owns actuals, grants, output decoding, saved closure and publication. No author helper/scientific execution or data decoding.',
 'implementation_delta':'Decoder fixed current caller contract capsule only. Closer fixed current caller contract capsule, two caller Source hashes, two review scopes plus one cold contract schema, one cold VERSION and one ENGINE_VERSION13 literal. No native/wire/session/case/record/aggregate/failure joins changed; auth_plan body differs only its caller hash and review-scope authorities.',
 'preserved_corrections':{'session':'Both session fields None OR matching positive exact int IDs with unchanged terminal/native/once/pid/wait4/Date checks; bool rejected. No bracket relabel or cold rerun.','declared_cases':'Immutable expected_cases tuple exactly one Store; negative expected_proposal separate; final counts/list case_names from expected_cases only. Parent V1/V2 negatives and V3 correction remain historical unchanged.'},
 'conformance_and_gaps':'Saved literal concordance only, no mathematical reenumeration/member/legality/proof replay. Full MR04 actual twoTRY/twoPLACE/twoRESTORE lineage and all native origin/census/current packets/rollback/cursor/fresh-cover joins remain inherited. Nonzero no-return countsNone/zero qualified/no inferred progress even if partial work happened. All12 across six distinct original20 endpoints required; no combined20/same-process all12 claim. Engine13 Source-only context lifetime guard audit does not establish hostile reentrancy/ABA runtime coverage.',
 'remaining_gates':['Distinct whole current helper/contract peer and Root reviews before any Root copy/use.','Root alone may decode positive complete-owned records and run saved closure against fresh current Source-bound actuals.','All six endpoint administrative closures/all twelve positive cases needed for current scoped engine qualification; old failed actuals and aggregates never relabeled.'],
 'flags':{'scientific_replay':False,'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False,'marking_activated':False}}
contractcap=write('Source-contract-v1.json',contract)
review['source_contract']=contractcap
handoff=write('handoff-v1.json',{'schema':'unit-row-decision-context-qualification-saved-handoff-v1','scope':review['scope'],'source':sources['closer'],'source_contract':contractcap,'sources':sources,'source_delta':delta,'author_static':static,'actual_unified_patches':patches,'Review_ABI':review,'caller_source':caller['source'],'caller_source_contract':cap(COLD/'Source-contract-v1.json'),'parent_helpers':parents,'parent_source_contract':cap(PARENT/'Source-contract-v3.json'),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'helper_executions':0,'saved_output_decodes':0,'author_identity':'/root/arithmetic_induction','status':'SOURCE_ONLY_NOT_EXECUTED','authorship':contract['authorship'],'flags':contract['flags'],'remaining_gates':contract['remaining_gates']})
print(json.dumps({'sources':sources,'source_contract':contractcap,'delta':delta,'static':static,'handoff':handoff,'raw_edit_counts':{k:len(v['edits'])for k,v in changes.items()},'function_report':function_report},sort_keys=True))
