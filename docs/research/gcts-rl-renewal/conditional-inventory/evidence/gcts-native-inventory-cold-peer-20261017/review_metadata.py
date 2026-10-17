"""Independent Source bytes/AST/literal metadata only; no project evaluation."""
import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-inventory-ROOT-source-20261017')
O=Path('/private/tmp/gcts-native-inventory-cold-peer-20261017')
R=Path('/private/tmp/gcts-native-inventory-readout-peer-20261017')
def raw(path):
 p=Path(path);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(path):
 b=raw(path);return {'path':str(path),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ref(ref):assert pin(ref['path'])==ref;return raw(ref['path'])
def save(folder,name,obj):
 p=folder/name
 with p.open('xb')as f:f.write((json.dumps(obj,sort_keys=True,indent=2)+'\n').encode())
 return pin(p)
def dump(b):return ast.dump(ast.parse(b),include_attributes=False)
def literals(b):
 out={}
 for n in ast.parse(b).body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:out[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 return out
def regions(b):
 out={};lines=b.decode().splitlines(True)
 def visit(ns,prefix=''):
  for n in ns:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)):
    key=prefix+n.name
    out[key]=( ''.join(lines[min([n.lineno]+[x.lineno for x in n.decorator_list])-1:n.end_lineno]),ast.dump(n,include_attributes=False),n.lineno,n.end_lineno)
    visit(n.body,key+'.')
 visit(ast.parse(b).body);return out
def delta(path):
 d=json.loads(raw(path));a=ref(d['parent_source']);b=ref(d['source']);s=a.decode()
 for e in d['edits']:
  i=e['start'];assert s[i:i+len(e['old'])]==e['old'];s=s[:i]+e['new']+s[i+len(e['old']):]
 assert s.encode()==b
 for e in reversed(d['edits']):
  i=e['start'];assert s[i:i+len(e['new'])]==e['new'];s=s[:i]+e['old']+s[i+len(e['new']):]
 assert s.encode()==a and dump(s)==dump(a)
 for label,x,y in [('forward',a,b),('full-inverse',b,a)]:
  p=d['patches'][label];ref(p)
  with tempfile.TemporaryDirectory(dir=str(O))as directory:
   target=Path(directory)/'before';target.write_bytes(x)
   r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=directory,capture_output=True)
   assert r.returncode==0 and (target.read_bytes()if target.exists()else b'')==y
 return d,a,b
C=json.loads(raw(H/'Source-contract-v1.json'));S=ref(C['source'])
assert pin(H/'Source-contract-v1.json')=={'path':str(H/'Source-contract-v1.json'),'sha256':'0454a81b0e5e37cfc549e170df58f4abdc7717d6b7328e5167aba05825466ca3','bytes':22413}
D,A,B=delta(H/'caller-Source-delta-v1.json');assert S==B
compile(S,C['source']['path'],'exec',dont_inherit=True)
old,new=regions(A),regions(B);constants=literals(B)
unchanged=[k for k in old.keys()&new.keys()if old[k][:2]==new[k][:2]]
changed=[k for k in old.keys()&new.keys()if old[k][:2]!=new[k][:2]]
assert [k for k in changed if '.'not in k]==['main']
assert len(D['edits'])==17
assert constants['FIXED_INPUTS']==C['inputs'] and dict(constants['FIXED'],intake=C['source'])==C['sources']
assert constants['ORIGINAL_SOURCES']==C['original_model_sources'] and len(constants['ORIGINAL_SOURCES'])==17
assert constants['ORIGINAL_INPUTS']==C['original_model_inputs'] and len(constants['ORIGINAL_INPUTS'])==2
assert constants['ORIGINAL_BINDING']==C['original_model_binding'] and len(C['sources'])==17 and len(C['inputs'])==8
for k in ('FIXED_INPUTS','ORIGINAL_SOURCES','ORIGINAL_INPUTS','ORIGINAL_BINDING','LIMITS'):
 assert constants[k]==literals(A)[k]
assert not any(k in constants['FIXED']for k in ('engine','provider','routed_semantics','family_consumer'))
assert B[B.index(b"if __name__ == '__main__':"):]==A[A.index(b"if __name__ == '__main__':"):]
assert all(old[k][:2]==new[k][:2]for k in ['invoke','save_failure_diagnostic','encode_result_transport','anchor','same','main.tick','main.guard','main.boundary','main.call','main.fresh_language'])
call_checks={
 'whole_current_and_contract_pins':True,'17_sequential_raw_forward_full_inverse_AST_and_actual_patch_directions':True,
 'all_top_helpers_and_classes_except_main_raw_AST_exact':True,
 'native_tick_fullguard_invoke_exceptional_finally_raw_exact':True,
 'failure55_builtin_writer_and_outer_exit2_tail_raw_exact':True,
 'fixed_current17_input8_original17_input2_maps_literal_exact':True,
 'oldStageB_authentication_and_original_epoch_retained':True,
 'no_engine_provider_decision_or_search_in_current_modules':True,
 'one_call_guarded_inventory_with_fixed_cumulative_native_tick':True,
 'six_phase_sites_native_only_original_writer_mechanism_retained':True,
 'no_qualification_inherited_no_proof_RL_GCTS_or_frontier_viability':True,
 'strict_result_encode_output_completion_final_guard_retained':True,
 'Source_AST_compile_without_evaluation':True}
findings=[
 {'id':'NI-CALLER-AUTH','disposition':'PASS','lines':[329,407], 'finding':'Current Source17/input8 is pinned before loading; original semantic Source17/input2 authority remains separately raw-pinned and epoch-equal. Current modules include composer/cases/collector/miner/expansion/native host, no engine/provider.'},
 {'id':'NI-CALLER-BOUNDARY','disposition':'PASS','lines':[104,153,329,448,571,591], 'finding':'Strong function/default/cell anchors plus CodeSeal surround delegated case entry and exceptional return; tick retains native20/internal500MiB reserve. Existing failure55 builtin writer only catches exact builtin TimeoutError escaping original call boundary; no late model/census call.'},
 {'id':'NI-CALLER-COMPOSITION','disposition':'PASS','lines':[545,559,589,615], 'finding':'Fresh original language, independent marking check, empty native root and documented public CASE kwargs share cumulative native tick. Scientific acceptance is deferred to current injected cases and distinct composer/CASE reviews; this peer does not independently recheck its own composer.'},
 {'id':'NI-CALLER-PHASE','disposition':'PASS','lines':[532,558,597], 'finding':'Six fixed literal group sites use captured builtin os.write and native tick before/through/after write. At most one reached write per site; absence is not a cause, exclusive timing, trajectory or case result.'},
 {'id':'NI-CALLER-WIRE','disposition':'PASS','lines':[592,657], 'finding':'Complete canonical lossless output, response completion, owned file inventory, stdout final observation and original final native/Source guard remain charged. UNKNOWN returned evidence is not promoted to completed conditional inventory.'},
 {'id':'NI-SCOPE','disposition':'LIMITATION','finding':'Only prospective conditional component/source-ground inventory. No engine activation, live frontier viability, generalized lemma or target theorem, scheduler/rollback/RL/GCTS gain or runtime fit is accepted by this Source review.'}
]
manual=save(O,'findings-v1.json',{'source':C['source'],'source_contract':pin(H/'Source-contract-v1.json'),'findings':findings,'checks':call_checks,'unchanged_named_regions':[{'name':k,'line':new[k][2],'end_line':new[k][3]}for k in sorted(unchanged)],'changed_existing_regions':changed,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
review=dict(C['Review_ABI']);review.update(source_contract=pin(H/'Source-contract-v1.json'),reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,findings=manual,checks=call_checks,authorship_disclosure='Distinct from Root caller author. Reviewer authored composer9fee, host adapter4bd6, prior point/native/provider/consumer/caller ancestry and bootstrap design. This is caller/authority/native/transport Source review; composer and CASE correctness require their distinct peers. No independent scientific replay or own-component self-peer claim.',source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,runtime_qualified=False)
rp=save(O,'typed-Source-review-v1.json',review)
ch=save(O,'handoff-v1.json',{'schema':'ROOT-native-inventory-caller-peer-handoff-v1','review':rp,'findings':manual,'source':C['source'],'source_contract':pin(H/'Source-contract-v1.json'),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
# Independent saved reader whole-source review plus inherited parent and immediate repair inverses.
RD,RA,RB=delta(H/'reader-Source-delta-v1.json')
RC=json.loads(raw(H/'reader-Source-contract-v2.json'));R2=ref(RC['source']);assert RB==ref(RC['parent_reader'])
old_text=RC['edits'][0]['old'];new_text=RC['edits'][0]['new'];assert RB.decode().count(old_text)==1
assert RB.decode().replace(old_text,new_text).encode()==R2
assert R2.decode().replace(new_text,old_text,1).encode()==RB
for label,x,y in [('v2-forward',RB,R2),('v2-inverse',R2,RB)]:
 p=RC['patches'][label];ref(p)
 with tempfile.TemporaryDirectory(dir=str(R))as directory:
  target=Path(directory)/'before';target.write_bytes(x)
  r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=directory,capture_output=True)
  assert r.returncode==0 and target.read_bytes()==y
compile(R2,RC['source']['path'],'exec',dont_inherit=True)
r0,r1,r2=regions(RA),regions(RB),regions(R2)
assert all(r1[k][:2]==r2[k][:2]for k in r1 if k!='main')
assert literals(R2)['CURRENT_CONTRACT']==pin(H/'Source-contract-v1.json')
assert b'collector_or_family_pipeline_executed'not in R2
assert b"conditional_inventory_record_complete=pipeline['status']=='CHECKED_CONDITIONAL_INVENTORY'"in R2
assert RC['current_operative_contract']==pin(H/'Source-contract-v1.json')
negative=save(R,'source-negative-v1.json',{'schema':'ROOT-native-inventory-saved-reader-Source-negative-v1','source':RC['parent_reader'],'source_contract':pin(H/'reader-Source-contract-v1.json'),'source_only':True,'source_review_passed':False,'scientific_calls':0,'scientific_acceptance':False,'finding':{'id':'NI-READER-STALE-PIPELINE-FLAG-1','finding':'V1 retains summary collector_or_family_pipeline_executed:false even on a successful inventory path that executes collector/miner/expansion/check/host. This is misleading metadata, not a mathematical result. Root discovered before execution. V2 removes the lone stale field and retains full pipeline evidence; no semantic replay added.','closed_by':RC['source']}})
reader_checks={
 'whole_current_reader_contract_and_operative_capsule_pinned':True,
 '18_parent_raw_AST_inverse_and_actual_patch_directions':True,
 'one_immediate_field_removal_raw_AST_inverse_and_actual_patch_directions':True,
 'all_other_reader_functions_raw_AST_exact_to_v1':True,
 'same_buffer_pin_to_parse_response_and_lossless_envelope':True,
 'strict_native20_positive_55failure_512MiB_Date91_and_same_sessionpair':True,
 'current_once_plan_source_grant_review_runtime_and_native_exit_joins':True,
 'full_canonical_output_envelope_zlibEOF_and_responsecompletion':True,
 'phase6_prefix_and_failure4slots_remain_diagnostic_not_cause':True,
 'complete_conditional_record_only_from_current_pinned_caller_fullpayload':True,
 'no_semantic_replay_or_engine_proof_RL_GCTS_gain':True,
 'Source_AST_compile_without_evaluation':True}
readerfindings=save(R,'findings-v2.json',{'source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v2.json'),'operative_contract':pin(H/'Source-contract-v1.json'),'negative_v1':negative,'checks':reader_checks,'findings':[
 {'id':'NI-SAVED-AUTH','disposition':'PASS','lines':[147,222],'finding':'Literal current capsule joins whole current sources/input8, grant/reviews/runtime, plan nonce and unchanged once/native meter/external observation. Exact integer sessions permit bothNone or equal positive IDs; exact exits/terminal/reap/Date bracket remain required.'},
 {'id':'NI-SAVED-WIRE','disposition':'PASS','lines':[236,287],'finding':'Positive branch requires launch→postprobe strictly less than20seconds and peak below512MiB; exact owned2/final line/response2 canonical bytes and same pinned buffers, compressed+expanded hashes/EOF/caps are retained.'},
 {'id':'NI-SAVED-DIAGNOSTIC','disposition':'PASS','lines':[65,144,223,326],'finding':'Six bounded fixed phases form ordered reached-site subsequence, clock joined to original caller window. Exit2 remains UNKNOWN with zero qualified count and case-countNone in complete optional failure pair. Last scalar observation is not active frame/cause/state/proof. Caller leaves all slotsNone.'},
 {'id':'NI-SAVED-SCOPE','disposition':'PASS','lines':[287,324],'finding':'Reader retains full current lossless inventory evidence and only reports its pinned caller status. No proof checker or replay. Completed conditional record is not target theorem, global viability, engine/scheduler/rollback, generalized lemma, RL/GCTS or speedup acceptance.'},
 {'id':'NI-READER-STALE-PIPELINE-FLAG-1','disposition':'CLOSED','finding':'The exact V1 stale pipeline-false summary field is absent inV2; all other helper regions/native/wire/authority/flags unchanged.'}],
 'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
rr=save(R,'typed-Source-review-v2.json',{'schema':'ROOT-native-inventory-saved-reader-typed-Source-review-v2','scope':'ROOT-native-inventory-saved-reader-Source','author_identity':'/root','reviewer_identity':'/root/hilbert_advice_controls','source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v2.json'),'current_operative_contract':pin(H/'Source-contract-v1.json'),'source_review_passed':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'findings':readerfindings,'checks':reader_checks,'authorship_disclosure':'Distinct from Root saved reader/caller author. Reviewer authored composer9fee, earlier host/native/caller/provider/consumer and predecessor readout ancestry; this is saved metadata/transport Source review only, not mathematical replay or independent composer acceptance.','actual_or_result_files_read':False,'runtime_qualified':False,'concrete_blockers':[]})
rh=save(R,'handoff-v2.json',{'schema':'ROOT-native-inventory-reader-peer-handoff-v2','source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v2.json'),'review':rr,'findings':readerfindings,'preserved_negative_v1':negative,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
print(json.dumps({'caller_review':rp,'caller_handoff':ch,'caller_findings':manual,'reader_review':rr,'reader_handoff':rh,'reader_findings':readerfindings,'negative_v1':negative,'unchanged_caller_regions':len(unchanged)},sort_keys=True))
