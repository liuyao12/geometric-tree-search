"""Raw-byte/AST metadata authoring only. Never evaluates scientific Source."""
from pathlib import Path
import ast, copy, difflib, hashlib, json, re
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
OUT=ROOT/'.gcts-active/unit-row-decision-context-engine-source-20261016'
PARENT=ROOT/'.gcts-active/unit-row-marked-aware-router-engine-source-20261016'
old_path=PARENT/'lazy_unit_row_global_engine_v12.py'
new_path=OUT/'lazy_unit_row_global_engine_v13.py'
old,new=old_path.read_bytes(),new_path.read_bytes()
oldtext,newtext=old.decode(),new.decode()
oldcontract=json.loads((PARENT/'Source-contract-v1.json').read_text())
def cap(path):
    path=Path(path); raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,data):
    path=OUT/name
    raw=(json.dumps(data,sort_keys=True,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode()
    with path.open('xb') as f:f.write(raw)
    return cap(path)
def rawwrite(name,raw):
    path=OUT/name
    with path.open('xb') as f:f.write(raw)
    return cap(path)
def patch_apply(raw,patch):
    source=raw.decode().splitlines(keepends=True); lines=patch.decode().splitlines(keepends=True)
    out=[]; cursor=0; index=2
    while index<len(lines):
        match=re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[index])
        assert match,lines[index]
        start=int(match.group(1)); count=int(match.group(2) or 1)
        position=start-1 if count else start
        assert position>=cursor
        out.extend(source[cursor:position]); cursor=position; index+=1
        while index<len(lines) and not lines[index].startswith('@@ '):
            line=lines[index]; assert line[0] in ' +-'
            if line[0] in ' -':assert source[cursor]==line[1:]; cursor+=1
            if line[0] in ' +':out.append(line[1:])
            index+=1
    out.extend(source[cursor:])
    return ''.join(out).encode()
old_ast,new_ast=ast.parse(oldtext),ast.parse(newtext)
compile(newtext,str(new_path),'exec',dont_inherit=True)
def functions(tree,text):
    result={}
    def walk(body,prefix=''):
        for node in body:
            if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                key=prefix+node.name
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    result[key]=(ast.dump(node,include_attributes=False),ast.get_source_segment(text,node))
                if isinstance(node,ast.ClassDef):walk(node.body,key+'.')
    walk(tree.body)
    return result
before,after=functions(old_ast,oldtext),functions(new_ast,newtext)
changed=[key for key in before if before[key]!=after[key]]
added=sorted(set(after)-set(before))
assert changed==['LazyUnitRowEngine.decision'],changed
assert added==['LazyUnitRowEngine._candidate_from_decision_context']
unchanged=[key for key in before if key not in changed]
assert all(before[key]==after[key] for key in unchanged)
old_version="VERSION = 'lazy-unit-row-global-engine-v12-routed-marked-aware-degree'"
new_version="VERSION = 'lazy-unit-row-global-engine-v13-decision-local-checked-state'"
helper_start=new.index(b'    def _candidate_from_decision_context(')
helper_end=new.index(b'    def _observe(',helper_start)
old_dec_start=old.index(b'    def decision(self):\n')
old_dec_end=old.index(b'    def _word(self):\n',old_dec_start)
new_dec_start=new.index(b'    def decision(self):\n')
new_dec_end=new.index(b'    def _word(self):\n',new_dec_start)
# Three complete raw regions, not a lossy display diff.
edits=[{'label':'own_VERSION','old_start':old.index(old_version.encode()),
        'old_end':old.index(old_version.encode())+len(old_version),'old':old_version,'new':new_version},
       {'label':'private_checked_witness_helper','old_start':old.index(b'    def _observe('),
        'old_end':old.index(b'    def _observe('),'old':'','new':new[helper_start:helper_end].decode()},
       {'label':'decision_only','old_start':old_dec_start,'old_end':old_dec_end,
        'old':old[old_dec_start:old_dec_end].decode(),'new':new[new_dec_start:new_dec_end].decode()}]
offset=0
for edit in edits:
    assert old[edit['old_start']:edit['old_end']]==edit['old'].encode()
    edit['new_start']=edit['old_start']+offset
    edit['new_end']=edit['new_start']+len(edit['new'].encode())
    assert new[edit['new_start']:edit['new_end']]==edit['new'].encode()
    offset+=len(edit['new'].encode())-len(edit['old'].encode())
forward=old
for edit in reversed(edits):forward=forward[:edit['old_start']]+edit['new'].encode()+forward[edit['old_end']:]
inverse=new
for edit in reversed(edits):inverse=inverse[:edit['new_start']]+edit['old'].encode()+inverse[edit['new_end']:]
assert forward==new and inverse==old
fpatch=''.join(difflib.unified_diff(oldtext.splitlines(True),newtext.splitlines(True),fromfile=str(old_path),tofile=str(new_path))).encode()
ipatch=''.join(difflib.unified_diff(newtext.splitlines(True),oldtext.splitlines(True),fromfile=str(new_path),tofile=str(old_path))).encode()
assert patch_apply(old,fpatch)==new and patch_apply(new,ipatch)==old
patches={'forward':rawwrite('engine-forward.patch',fpatch),'inverse':rawwrite('engine-full-inverse.patch',ipatch)}
restored=copy.deepcopy(new_ast)
restored.body=[n for n in restored.body]
for n in restored.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets):
        n.value=ast.Constant(value='lazy-unit-row-global-engine-v12-routed-marked-aware-degree')
    if isinstance(n,ast.ClassDef) and n.name=='LazyUnitRowEngine':
        old_class=next(x for x in old_ast.body if isinstance(x,ast.ClassDef) and x.name==n.name)
        old_dec=next(x for x in old_class.body if isinstance(x,ast.FunctionDef) and x.name=='decision')
        n.body=[copy.deepcopy(old_dec) if isinstance(x,ast.FunctionDef) and x.name=='decision' else x
                for x in n.body if not (isinstance(x,ast.FunctionDef) and x.name=='_candidate_from_decision_context')]
assert ast.dump(restored,include_attributes=False)==ast.dump(old_ast,include_attributes=False)
sources=copy.deepcopy(oldcontract['sources']); sources['engine']=cap(new_path)
for mapping in (sources,oldcontract['original_model_sources'],oldcontract['original_model_inputs']):
    for role,packet in mapping.items():assert cap(packet['path'])==packet,(role,packet)
original_suffix=oldtext[oldtext.index("        for row in frontier:\n            if certificates[row]"):oldtext.index('    def _word(self):')]
new_suffix=newtext[newtext.index("        for row in frontier:\n            if certificates[row]"):newtext.index('    def _word(self):')]
assert original_suffix==new_suffix
helper=after[added[0]][1]
decision=next(n for n in ast.walk(new_ast) if isinstance(n,ast.FunctionDef) and n.name=='decision')
all_calls=[n for n in ast.walk(new_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_candidate_from_decision_context']
assert len(all_calls)==1 and all_calls[0] in list(ast.walk(decision))
assert 'private_state(' not in helper and 'check_collision(tile, dict(names))' in helper
assert all(token in helper for token in ('rebuild_tile(', 'legality(tile, t, m, selected, excluded)', 'with_obligations(tile, t, self.tick)', 'canonical(raw) == canonical(tile)'))
assert not any(isinstance(n,ast.Attribute) and isinstance(n.ctx,ast.Store) and n.attr in ('checked','current','state_object','state_literal','active') for n in ast.walk(decision))
assert any(isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and isinstance(x.value,ast.Constant) and x.value.value is False for x in n.finalbody) for n in ast.walk(decision))
assert [ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,(ast.Import,ast.ImportFrom))]==[ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,(ast.Import,ast.ImportFrom))]
checks=[
 {'name':'exact_parent_and_frozen_engine_capsules','passed':True},
 {'name':'compile_only_no_evaluation','passed':True},
 {'name':'three_complete_raw_regions_forward_and_inverse','passed':True},
 {'name':'actual_unified_forward_and_inverse_patches_apply','passed':True},
 {'name':'whole_AST_inverse_restores_parent','passed':True},
 {'name':'only_existing_decision_method_changed','passed':True},
 {'name':'one_new_private_checked_witness_helper','passed':True},
 {'name':'all_other_existing_callables_raw_AST_exact','passed':True,'count':len(unchanged),'names':unchanged},
 {'name':'ordinary_candidate_original_raw_AST_exact','passed':True},
 {'name':'firstpass_only_one_checked_helper_callsite','passed':True},
 {'name':'decision_fallback_schedule_emit_suffix_raw_exact','passed':True},
 {'name':'helper_no_private_state_reconstruction','passed':True},
 {'name':'per_candidate_names_copy_and_full_validation_preserved','passed':True},
 {'name':'context_no_engine_attribute_store','passed':True},
 {'name':'finally_disables_firstpass_context','passed':True},
 {'name':'independent_router_checker_and_current_other_sources_raw_pins','passed':True,'count':len(sources)-1},
 {'name':'original17_input2_raw_pins_and_binding_unchanged','passed':True},
 {'name':'imports_unchanged_hashlib_json_only','passed':True},
 {'name':'public_constructor_receipt_cursor_snapshot_result_schemas_unchanged','passed':True},
 {'name':'no_scientific_import_evaluation_function_clock_model_or_actual','passed':True}]
delta=write('Source-delta-v1.json',{'schema':'unit-row-decision-context-engine-Source-delta-v1','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'parent':cap(old_path),'source':cap(new_path),'edits':edits,'raw_forward_exact':forward==new,'raw_inverse_exact':inverse==old,'whole_AST_inverse_exact':True,'actual_unified_patches':patches,'actual_patch_forward_exact':True,'actual_patch_inverse_exact':True,'changed_existing_callables':changed,'added_callables':added,'unchanged_existing_callables':unchanged})
static=write('author-static-v1.json',{'schema':'unit-row-decision-context-engine-author-static-v1','author_identity':'/root/arithmetic_induction','source':cap(new_path),'parent':cap(old_path),'source_delta':delta,'checks':checks,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':False,'runtime_fit':'UNMEASURED; original20 unchanged; no cost or benefit claim','authorship':'Author static evidence, not distinct peer review or runtime qualification.'})
choice=ROOT/'.gcts-active/unit-row-decision-context-ROOT-20261016/ROOT-implementation-choice-v1.json'
qualification=ROOT/'.gcts-active/unit-row-decision-context-ROOT-20261016/ROOT-qualification-choice-v1.json'
proposal=ROOT/'.gcts-active/unit-row-decision-context-reuse-proposal-source-20261016/independent-proposal-v1.json'
master=ROOT/'docs/basic-tiling-algorithm.md'
review={'schema':'unit-row-decision-context-engine-typed-Source-review-v1','scope':'unit-row-decision-context-engine-Source','source':cap(new_path),'source_contract':'Exact raw current Source-contract-v1.json capsule','sources':sources,'author_identity':'/root/arithmetic_induction','reviewer_identity':'Distinct reviewer determines','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':'Only genuine distinct whole current Source/contract reviewer determines'}
contract={
 'schema':'unit-row-decision-context-engine-Source-contract-v1','scope':review['scope'],'status':'SOURCE_ONLY_UNMEASURED_NOT_ACTIVATED','source':cap(new_path),'sources':sources,'parent_engine':cap(old_path),'parent_source_contract':cap(PARENT/'Source-contract-v1.json'),'source_delta':delta,'author_static':static,'master_reference':cap(master),'design_proposal':cap(proposal),'Root_implementation_choice':cap(choice),'Root_qualification_choice':cap(qualification),
 'author_identity':'/root/arithmetic_induction','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'Review_ABI':review,
 'authorship':'Arithmetic authors engine13 and parent engine/router/adapter/c354 ancestry. Diagnosis authors the decision-context proposal and independent8f7a/9fd6 dependencies; controls authors4316/decorator and forthcoming caller. Root owns review/actual grants/execution/publication. Author static checks are not independent review or scientific acceptance.',
 'original_model_sources':oldcontract['original_model_sources'],'original_model_inputs':oldcontract['original_model_inputs'],'original_model_binding':oldcontract['original_model_binding'],
 'API':{
  'engine_VERSION':'lazy-unit-row-global-engine-v13-decision-local-checked-state',
  'constructor_and_public_methods':'Exact parent keyword/return ABIs, defaults and bodies except decision body. No additional parameter, callback, counter, context wire or checkpoint field. Snapshot version naturally reports current VERSION; logical snapshot/result/receipt schemas remain parent literals.',
  'semantics_VERSION':'unit-row-channel4-routed-nonimp-degree-semantics-v2',
  'fallback_VERSION':'unit-row-channel4-filtered-six-rule-fallback-v1',
  'transition_VERSION':'unit-row-channel4-routed-support-transition-v2',
  'private_helper':'_candidate_from_decision_context(self, raw, row, checked, current); only one callsite in immediate first-pass fresh checked-proposal witness loop. No producer, independent checker, fallback cursor, checkpoint or engine field receives checked/current.',
  'unchanged_fresh_candidate':'Parent _candidate raw exact. All place, advice, next_alternative, canonical cursor/replay and other candidate consumers still use it.',
  'runtime_map':'Module sources12 is parent sources12 with only engine replaced. Future Root caller14 retains original semantic17 separately; executable pin replacement does not rebase original epoch/keys.',
  'wire':'Exact parent native receipt union, full origin transfer wrapper, cursor/context/completion/poisoning, snapshot schema unit-row-channel4-routed-engine-snapshot-v1 and result schema unit-row-channel4-routed-lazy-global-search-result-v1.'},
 'context_lifetime':{
  'capture':'After unchanged full _check_authority and before the single full private_state call, capture owned state object/full canonical literal/revision; exact language, semantics, transition checker, tick and proposer identities; full original language.binding literal; marking_id; full owned authority literal and branch policy/tie. Initial full tuple is independently checked by unchanged semantics.private_state.',
  'guard':'Native tick first, then exact object/literal/revision/identity/binding/marking-id/owned-authority/policy comparisons and checked[0] full literal equality. Invoked around copy/delegation/rebuild/collision/legality/obligations/full packet checks and after exposed-candidate observation before first-pass results are used.',
  'full_marking':'Captured _authority is the complete already independently checked transition authority, including full original model, full frozen marking literal and routing policy. Guard compares that owned literal plus semantics.marking_id; it does not rerun check_marking/authority_snapshot. Existing fresh router/checker/rebuild continue independently checking full marking/membership as before.',
  'candidate_relation':'Reuse only checked t/m/selected/excluded/names from this one unchanged current state. Each offered candidate still undergoes original+decorated rebuild/full membership, dict(names) fresh ledger copy, whole t/m legality, occupancy/read-obligation reconstruction and full raw packet equality. Unchanged _observe enforces cross-candidate original/decorated ID/full-preimage equality globally.',
  'end':'try/finally sets active=False on every first-pass return/exception and before inherited fallback/scheduler suffix. Local references may live until decision returns but are inactive and never stored on engine/checkpoint or delegated as independent authority.',
  'exceptions':'No new catch/conversion. Timeout, authority, typing, collision, callback and other errors propagate normally. Existing search native-first restoration/UNKNOWN semantics are raw exact.',
  'scope':'Trusted synchronous pinned Sources only. No hostile frame/local mutation or arbitrary callback reentrancy protection claim. Exact owned rollback returning the same state object/revision/authority relation is semantically the same candidate relation; no extra persistent epoch or counter added.'},
 'implementation_seams':{'three_raw_regions':['own VERSION literal','insert private checked witness helper before unchanged _observe','replace only decision first-pass, keep fallback/scheduler suffix raw exact'],'changed_existing_callables':changed,'added_callables':added,'unchanged_existing_callables':unchanged,'preserved':'All other parent Source functions/class methods raw+AST exact, including _candidate/_observe/private support transition installation/receipt transfer/native validation/complete EOF certifier/checkpoint/rollback/place/exclusion/canonical fallback/replay/select_schedule/search/full target word check.'},
 'conformance_and_gaps':{
  'master':'No universe, point semantics, markings, dependency support, collision identity, global dead/UNKNOWN/forced/generation order, canonical fallback, branch policy, exact rollback or proof validation change. Earliest-generation named ROW/MARK tie variants retain parent scope; all24 roots remain0.',
  'degree_authority':'No independent proposer/checker work is reused or combined. The local tuple only replaces repeated engine private_state reconstruction after the same current independently checked proposal. Newnative origin/census, legacy safe route and full native schema remain unchanged.',
  'qualification':'Same six endpoint/twelve essential cases proposed under fresh Source-bound Root grants. Existing routed six qualified/twelve total result remains incomplete. Existing public transition/rollback/cursor/actual-child controls do not establish arbitrary adversarial context mutation/reentrancy coverage.',
  'runtime':'No measured speedup, fit, target discovery, activation or GCTS advantage is inferred. All setup/check/output costs and native20/512/55/60/90+1/16MiB bounds remain owned by unchanged caller. No proofword, donor or supplied route.',
  'framework':'No new custody, cache, controller, mutation counter or state epoch.'},
 'remaining_gates':['Distinct whole current Source/contract review and Root review.','Fresh separately granted Root qualification endpoints under unchanged original bounds, all12 essential; no inherited runtime pass or rerun of old failed actual.','Only Root may decide later target/ordinary comparison after full engine qualification.'],
 'flags':copy.deepcopy(oldcontract['flags'])}
contractcap=write('Source-contract-v1.json',contract)
review['source_contract']=contractcap
handoff={'schema':'unit-row-decision-context-engine-handoff-v1','scope':review['scope'],'source':cap(new_path),'source_contract':contractcap,'sources':sources,'source_delta':delta,'author_static':static,'actual_unified_patches':patches,'Review_ABI':review,'parent_engine':cap(old_path),'parent_source_contract':cap(PARENT/'Source-contract-v1.json'),'original_model_binding':oldcontract['original_model_binding'],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'author_identity':'/root/arithmetic_induction','status':'SOURCE_ONLY_UNMEASURED_NOT_ACTIVATED','authorship':contract['authorship'],'flags':contract['flags'],'changed_existing_callables':changed,'added_callables':added,'unchanged_existing_callable_count':len(unchanged),'runtime_fit':'UNMEASURED','remaining_gates':contract['remaining_gates']}
handoffcap=write('handoff-v1.json',handoff)
print(json.dumps({'source':cap(new_path),'contract':contractcap,'delta':delta,'static':static,'handoff':handoffcap,'unchanged_existing_callables':len(unchanged),'checks':len(checks)},sort_keys=True))
