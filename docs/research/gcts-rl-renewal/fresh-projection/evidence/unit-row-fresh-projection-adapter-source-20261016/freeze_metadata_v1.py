"""Raw/AST/compile-without-evaluation metadata only; no scientific Source execution."""
from pathlib import Path
import ast,copy,difflib,hashlib,json,re
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
OUT=ROOT/'.gcts-active/unit-row-fresh-projection-adapter-source-20261016'
OLD=ROOT/'.gcts-active/unit-row-channel4-engine-source-20261016/marked_unit_row_adapter_v1.py'
NEW=OUT/'marked_unit_row_adapter_v2.py'
COLD=ROOT/'.gcts-active/unit-row-decision-context-qualification-cold-source-20261016/Source-contract-v1.json'
ENGINE_CONTRACT=ROOT/'.gcts-active/unit-row-decision-context-engine-source-20261016/Source-contract-v1.json'
def cap(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
    path=OUT/name;raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
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
old,new=OLD.read_bytes(),NEW.read_bytes();ot,nt=old.decode(),new.decode()
assert cap(OLD)['sha256']=='821fe692dc7a118cdc3355d3128ecdf08287abf229365b97a04341e0dc4cb7f9'
assert cap(NEW)['sha256']=='a1971d01cc1291af4b5508c81e3ef06bec17ee794d0a5d95b102d730ce0a3f7c'
a,b=ast.parse(ot),ast.parse(nt);compile(nt,str(NEW),'exec',dont_inherit=True)
def funcs(tree,text):
    result={}
    for node in tree.body:
        if isinstance(node,ast.FunctionDef):result[node.name]=(node,ast.get_source_segment(text,node))
        if isinstance(node,ast.ClassDef):
            for fn in node.body:
                if isinstance(fn,ast.FunctionDef):result[node.name+'.'+fn.name]=(fn,ast.get_source_segment(text,fn))
    return result
bf,af=funcs(a,ot),funcs(b,nt)
changed=[key for key in bf if ast.dump(bf[key][0],include_attributes=False)!=ast.dump(af[key][0],include_attributes=False)or bf[key][1]!=af[key][1]]
assert changed==['MarkedSemantics.base_state','MarkedSemantics.private_state']
assert set(af)-set(bf)=={'MarkedSemantics._fresh_base_projection'}
unchanged=[key for key in bf if key not in changed]
oldfn=bf['MarkedSemantics.base_state'][0];helper=af['MarkedSemantics._fresh_base_projection'][0]
assert [ast.dump(n,include_attributes=False)for n in oldfn.body[:-1]]==[ast.dump(n,include_attributes=False)for n in helper.body[:-1]]
assert isinstance(oldfn.body[-1].value,ast.Subscript)and ast.dump(oldfn.body[-1].value.value,include_attributes=False)==ast.dump(helper.body[-1].value,include_attributes=False)
assert isinstance(oldfn.body[-1].value.slice,ast.Constant)and oldfn.body[-1].value.slice.value==0
expected_helper=bf['MarkedSemantics.base_state'][1].replace('def base_state(','def _fresh_base_projection(',1).replace('return self.base.private_state(language, base, tick)[0]','return self.base.private_state(language, base, tick)',1)
assert expected_helper==af['MarkedSemantics._fresh_base_projection'][1]
expected_wrapper='def base_state(self, language, state, tick):\n        return self._fresh_base_projection(language, state, tick)[0]'
assert af['MarkedSemantics.base_state'][1]==expected_wrapper
oldprivate=bf['MarkedSemantics.private_state'][1];newprivate=af['MarkedSemantics.private_state'][1]
previous='''        base = self.base_state(language, s, tick)
        _, t, _, _, _, base_names = self.base.private_state(language, base, tick)'''
current='''        projection = self._fresh_base_projection(language, s, tick)
        base, t, base_names = projection[0], projection[1], projection[5]'''
assert oldprivate.replace(previous,current,1)==newprivate
assert 'dict(base_names)'in newprivate and 'self.verifier.check_marked_state('in newprivate
assert len([n for n in ast.walk(b)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='_fresh_base_projection'])==2
# Exactly three complete raw regions: explicit implementation identity, fresh
# helper/public wrapper, and two private-state statements.
anchor=b"VERSION = 'unit-row-channel4-point-adapter-v1'\n";position=old.index(anchor)+len(anchor)
base_start=old.index(b'    def base_state(');base_end=old.index(b'    def initial_state(',base_start)
newbase_start=new.index(b'    def _fresh_base_projection(');newbase_end=new.index(b'    def initial_state(',newbase_start)
private_start=old.index(previous.encode())
edits=[{'label':'implementation_tag_only','old_start':position,'old_end':position,'old':'','new':"IMPLEMENTATION_VERSION = 'unit-row-channel4-point-adapter-fresh-projection-v2'\n"},
 {'label':'exact_old_body_to_fresh_helper_and_public_wrapper','old_start':base_start,'old_end':base_end,'old':old[base_start:base_end].decode(),'new':new[newbase_start:newbase_end].decode()},
 {'label':'same_call_tuple_consumption_only','old_start':private_start,'old_end':private_start+len(previous.encode()),'old':previous,'new':current}]
shift=0
for edit in edits:
    edit['new_start']=edit['old_start']+shift;edit['new_end']=edit['new_start']+len(edit['new'].encode());shift+=len(edit['new'].encode())-len(edit['old'].encode())
    assert old[edit['old_start']:edit['old_end']]==edit['old'].encode()and new[edit['new_start']:edit['new_end']]==edit['new'].encode()
forward=old
for e in reversed(edits):forward=forward[:e['old_start']]+e['new'].encode()+forward[e['old_end']:]
inverse=new
for e in reversed(edits):inverse=inverse[:e['new_start']]+e['old'].encode()+inverse[e['new_end']:]
assert forward==new and inverse==old and ast.dump(ast.parse(inverse.decode()),include_attributes=False)==ast.dump(a,include_attributes=False)
fp=''.join(difflib.unified_diff(ot.splitlines(True),nt.splitlines(True),fromfile=str(OLD),tofile=str(NEW))).encode()
ip=''.join(difflib.unified_diff(nt.splitlines(True),ot.splitlines(True),fromfile=str(NEW),tofile=str(OLD))).encode()
assert apply_patch(old,fp)==new and apply_patch(new,ip)==old
patches={'forward':write_raw('adapter-forward.patch',fp),'full_inverse':write_raw('adapter-full-inverse.patch',ip)}
parent=json.loads(COLD.read_text());engine=json.loads(ENGINE_CONTRACT.read_text())
assert cap(COLD)['sha256']=='105cc90ec4a8993410563dc1d6c9bd3fce62b5e5f0cd9696a13e229737fa26cd'
oldcomponents={k:v for k,v in parent['sources'].items()if k!='intake'};components=copy.deepcopy(oldcomponents);components['marked_adapter']=cap(NEW)
assert len(components)==13 and {k for k in components if components[k]!=oldcomponents[k]}=={'marked_adapter'}
for role,packet in engine['sources'].items():assert oldcomponents[role]==packet
assert oldcomponents['clean_support']==parent['original_model_sources']['clean_support']
# Freshly read current scientific Source files only. Original input/profile and
# historical acceptance buffers are not redundantly re-read by this metadata pass.
for role,packet in components.items():assert cap(packet['path'])==packet
assert parent['original_model_sources']==engine['original_model_sources']and parent['original_model_inputs']==engine['original_model_inputs']and parent['original_model_binding']==engine['original_model_binding']
oldconstants={n.targets[0].id:ast.dump(n.value,include_attributes=False)for n in a.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
newconstants={n.targets[0].id:ast.dump(n.value,include_attributes=False)for n in b.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
assert all(newconstants[k]==v for k,v in oldconstants.items())and set(newconstants)-set(oldconstants)=={'IMPLEMENTATION_VERSION'}
assert [ast.dump(n,include_attributes=False)for n in a.body if isinstance(n,(ast.Import,ast.ImportFrom))]==[ast.dump(n,include_attributes=False)for n in b.body if isinstance(n,(ast.Import,ast.ImportFrom))]
delta=write('Source-delta-v1.json',{'schema':'unit-row-fresh-projection-adapter-Source-delta-v1','parent':cap(OLD),'source':cap(NEW),'edits':edits,'raw_forward_exact':True,'raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_forward_exact':True,'actual_patch_inverse_exact':True,'actual_unified_patches':patches,'changed_existing_callables':changed,'added_callables':['MarkedSemantics._fresh_base_projection'],'unchanged_callables_raw_AST':unchanged,'old_helper_body_exact_except_fulltuple_return':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
checks=[{'name':name,'passed':True}for name in['exact_parent_current_adapter_capsules','compile_without_evaluation_only','three_complete_raw_regions_forward_inverse_exact','actual_unified_patches_both_directions_exact','whole_AST_inverse_exact','old_base_body_verbatim_moved_except_return_index','public_base_state_fresh_wrapper_index0_only','private_state_only_two_statement_replacement','tuple_indices0_1_5_exact_and_dict_names_preserved','independent9fd_check_and_whole_private_state_tail_raw_exact','all_other_existing_callables_raw_AST_exact','all_public_protocol_constants_unchanged_only_implementation_tag_added','exact_two_local_helper_callsites_no_supplied_context_parameter','all_current13_sources_fresh_raw_caps_verified_only_adapter_changed','original17_input2_binding_and_input8_literal_ancestry_unchanged','router_engine13_and_independent_authorities_unchanged','imports_hashlib_json_unchanged_no_scientific_evaluation','no_model_helper_clock_test_py_compile_actual_or_resource_counter_reset']]
static=write('author-static-v1.json',{'schema':'unit-row-fresh-projection-adapter-author-static-v1','source':cap(NEW),'source_delta':delta,'checks':checks,'unchanged_existing_callable_count':len(unchanged),'unchanged_existing_callables':unchanged,'current_component_sources':components,'metadata_read_scope':'Fresh raw current13 Source buffers verified. Original17/input2 and prior acceptance/input8 capsules compared to frozen parent compositions, not mislabeled fresh profile/acceptance reads. No live metadata handle duplicated.','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':False,'compile_without_evaluation':True,'py_compile_calls':0,'author_identity':'/root/arithmetic_induction'})
review={'schema':'unit-row-fresh-projection-adapter-composite-typed-Source-review-v1','scope':'unit-row-fresh-projection-adapter-composite-Source','source':cap(NEW),'source_contract':'Exact raw current Source-contract-v1.json capsule','sources':components,'author_identity':'/root/arithmetic_induction','reviewer_identity':'Distinct reviewer determines','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':'Only genuine distinct whole current adapter/composition reviewer determines'}
contract={'schema':'unit-row-fresh-projection-adapter-composite-Source-contract-v1','scope':review['scope'],'status':'SOURCE_ONLY_UNMEASURED_NOT_ACTIVATED','source':cap(NEW),'sources':components,'current_component_sources':components,'parent_component_sources':oldcomponents,'source_delta':delta,'author_static':static,'Review_ABI':review,'parent_adapter':cap(OLD),'parent_caller_source_contract':cap(COLD),'parent_engine13_source_contract':cap(ENGINE_CONTRACT),'original_model_sources':parent['original_model_sources'],'original_model_inputs':parent['original_model_inputs'],'original_model_binding':parent['original_model_binding'],'inputs':parent['inputs'],'limits':parent['limits'],'Root_choice':cap(ROOT/'.gcts-active/unit-row-fresh-projection-ROOT-20261016/ROOT-implementation-choice-v1.json'),'design_proposal':cap(ROOT/'.gcts-active/unit-row-global-forced-next-step-proposal-source-20261016/independent-proposal-v1.json'),'master':cap(ROOT/'docs/basic-tiling-algorithm.md'),'author_identity':'/root/arithmetic_induction','source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'authorship':'Arithmetic authors adapter2 and old821fe/engine13/router/c354 ancestry. Controls authors proposal/currentparent cold caller4316/decorator, diagnosis8f7a/9fd6. Root owns Source review/grants/actuals/publication. Prior engine13 reviews are historical and do not review this updated composite; fresh whole Root/distinct adapter+current13 reviews required. Author static checks are not peer or runtime acceptance.',
 'API':{'IMPLEMENTATION_VERSION':'unit-row-channel4-point-adapter-fresh-projection-v2','module_VERSION':'unit-row-channel4-point-adapter-v1','semantics_VERSION':'unit-row-channel4-filtered-degree-semantics-v1','transition_VERSION':'unit-row-channel4-support-transition-v1','fallback_VERSION':'unit-row-channel4-filtered-six-rule-fallback-v1','native_receipt_SCHEMA':'unit-row-channel4-degree-evidence-check-v1','public_methods':'Exact keyword/positional and returned data protocols unchanged. Publicbase_state(language,state,tick) performs a fresh private projection then returns tuple[0]. Newcaller checks IMPLEMENTATION_VERSION along with unchanged public versions; no fake receipt/version normalization.','private_helper':'_fresh_base_projection(self,language,state,tick) has the oldbase_state body verbatim except returning the complete fresh c354.private_state tuple. Only base_state and same-call markedprivate_state call it. No supplied checked context or cached handle.','composition':'Current13 from olddd4e caller sources minusintake; onlymarked_adapter replaced. Engine13/router/newproposer/newchecker/legacyc960/c354/fallback/decorator/verifier/membership/kernel/clean_support rawexact. Futurecaller adds its own currentintake for14; never changes original semantic17/input2 epoch.','qualification':'All six scopes/twelve essentials remain required under newRoot-granted cold actuals with same native20/512/55/60/90+1, no target or oldfailure rerun claim.'},
 'equivalence_and_ownership':{
 'fresh_validation':'Each helper call begins with the same tree copy, exact marked schema/channel/inventory/preimage validation and full selected/excluded key reconstruction, then one complete c354.private_state(language,base,tick). No validation before its successful return is removed.',
 'idempotence_argument':'c354.private_state starts with a fresh builtin tree copy, checks exact original schema/epoch/height/root generations/complete t domain/key inventories, rebuilds every original primitive, full key and named preimage ledger, checks duplicate/collision/capacity and whole fixed-plus-selected t/m equality, then returns(s,t,m,selected,excluded,names). Calling it on its returned s under the same original authority copies identical ordered arrays/keys and reconstructs equal integer maps, key sets and full-preimage ledger. This is Source reasoning about returned values, not an executed equivalence test or assumed hash injectivity.',
 'same_call_values':'Old markedprivate_state used the first s as base and a second validation only for t andbase_names. New code uses that SAME fresh tuple indices0/1/5. Its packets, fullmarks, selected/excludeddecorated sets, and independent9fd whole marked-state check are unchanged. No canonicalization/order/model change is introduced.',
 'ownership':'The tuple exists only as a private synchronous local. Its integer t map and string-valued name ledger are newly rebuilt; dict(base_names) keeps later original/decorated collision updates private. The normalized base data used in the existing verifier packet is unchanged; the tuple itself is never stored onself, receipt, snapshot, checkpoint, cursor or passed as a proposer/checker authority. Public base_state returns only fresh[0], not the full tuple. No engine13 checked context is shared.',
 'independence':'Every independent9fd marking/tile/fullstate reconstruction, c354 legacy degree check,8f7a independent census, membership/rule rebuild, fullpoint legality, collision ledger, obligations, canonicalcursor/EOF, transition and rollback call outside this one immediate duplicate remains raw exact. No removed second-check tuple is accepted as a new receipt.',
 'trust_and_resources':'Trusted synchronous pinned language/native tick authority is unchanged during the call; no hostile tick/reentrancy/ABA guarantee. All remaining callback/authority/membership/resource errors propagate. Removing one traversal changes work and may change finite-budget outcomes; no claim of identical tick counts, exception timing, fit or speedup. No parser visit counter reset, persistent cache, cross-call or proposer-checker reuse.'},
 'conformance_and_gaps':'Baseuniverse/sixrules/pointmodel/channel4 markings/dependencies/complete covers/canonicalorder/global DEAD-UNKNOWN-FORCED-earliestgeneration/reference branch policy/exactrollback/proof validation unchanged. Currenthistorical10/12 engine qualification and all prior failed suites stay immutable/uncompleted, not inherited into this composition. Source equivalence reasoning is not new runtime qualification or targetdiscovery/GCTS/RL/benefit evidence.',
 'remaining_gates':['Genuine whole current adapter/composite Source Root and distinct review.','Fresh reviewed current caller with implementationtag and exactcurrent14/input8/original17 authority, separately granted once endpoints for all6/all12 under unchanged bounds.','Root alone decides later matched target/ordinary comparison after qualification; no scientific activation from this Source packet.'],
 'flags':{'engine_qualified':False,'logical_proof_accepted':False,'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,'trajectory_accepted':False,'marking_activated':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False,'runtime_executed':False}}
contractref=write('Source-contract-v1.json',contract);review['source_contract']=contractref
handoff=write('handoff-v1.json',{'schema':'unit-row-fresh-projection-adapter-handoff-v1','scope':review['scope'],'source':cap(NEW),'source_contract':contractref,'sources':components,'current_component_sources':components,'source_delta':delta,'author_static':static,'actual_unified_patches':patches,'Review_ABI':review,'parent_adapter':cap(OLD),'parent_caller_source_contract':cap(COLD),'parent_engine13_source_contract':cap(ENGINE_CONTRACT),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'py_compile_calls':0,'author_identity':'/root/arithmetic_induction','authorship':contract['authorship'],'status':contract['status'],'flags':contract['flags'],'remaining_gates':contract['remaining_gates']})
print(json.dumps({'source':cap(NEW),'source_contract':contractref,'source_delta':delta,'static':static,'handoff':handoff,'unchanged_callables':len(unchanged),'static_checks':len(checks)},sort_keys=True))
