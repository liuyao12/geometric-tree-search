"""Independent Root integration Source bytes/AST/literal metadata review only."""
import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-productive-inventory-ROOT-source-20261017');O=Path('/private/tmp/gcts-native-productive-inventory-cold-peer-20261017');R=Path('/private/tmp/gcts-native-productive-inventory-readout-peer-20261017')
def raw(p):
 p=Path(p);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(p):
 b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ref(r):assert pin(r['path'])==r;return raw(r['path'])
def save(folder,n,v):
 p=folder/n
 with p.open('xb')as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
 return pin(p)
def literals(b):
 out={}
 for n in ast.parse(b).body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:out[n.targets[0].id]=ast.literal_eval(n.value)
   except(ValueError,TypeError):pass
 return out
def regions(data):
 ls=data.decode().splitlines(True);out={}
 def walk(ns,prefix=''):
  for n in ns:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    key=prefix+n.name;out[key]=(''.join(ls[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False));walk(n.body,key+'.')
 walk(ast.parse(data).body);return out
def delta(path,count):
 d=json.loads(raw(path));a=ref(d['parent_source']);b=ref(d['source']);s=a.decode();assert len(d['edits'])==count
 for e in d['edits']:
  i=e['start'];assert s[i:i+len(e['old'])]==e['old'];s=s[:i]+e['new']+s[i+len(e['old']):]
 assert s.encode()==b
 for e in reversed(d['edits']):
  i=e['start'];assert s[i:i+len(e['new'])]==e['new'];s=s[:i]+e['old']+s[i+len(e['new']):]
 assert s.encode()==a and ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
 for label,x,y in [('forward',a,b),('full-inverse',b,a)]:
  p=d['patches'][label];ref(p)
  with tempfile.TemporaryDirectory(dir=str(O))as td:
   target=Path(td)/'before';target.write_bytes(x)
   r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=td,capture_output=True)
   assert r.returncode==0 and target.read_bytes()==y
 compile(b,d['source']['path'],'exec',dont_inherit=True)
 return d,a,b
F=json.loads(raw(H/'handoff-v1.json'));C=json.loads(ref(F['source_contract']));oldC=json.loads(ref(C['operative_parent_contract']))
D,A,B=delta(H/'caller-Source-delta-v1.json',6);assert D['source']==C['source']==F['source']
la,lb=literals(A),literals(B);ra,rb=regions(A),regions(B)
same=[k for k in ra if ra[k]==rb[k]];changed=[k for k in ra if ra[k]!=rb[k]]
assert changed==['main']
assert all(ra[k]==rb[k]for k in ra if k!='main')
assert {k:v for k,v in la.items()if k not in('FIXED','VERSION','SCOPE','QUALIFICATION_CASES_BY_PURPOSE')}=={k:v for k,v in lb.items()if k not in('FIXED','VERSION','SCOPE','QUALIFICATION_CASES_BY_PURPOSE')}
assert {k:la['FIXED'][k]for k in la['FIXED']if k not in('composer','miner','inventory_cases')}=={k:lb['FIXED'][k]for k in lb['FIXED']if k not in('composer','miner','inventory_cases')}
assert dict(lb['FIXED'],intake=C['source'])==C['sources'] and len(C['sources'])==17
assert lb['FIXED_INPUTS']==C['inputs']==oldC['inputs'] and len(C['inputs'])==8
assert lb['ORIGINAL_SOURCES']==C['original_model_sources']==oldC['original_model_sources'] and len(C['original_model_sources'])==17
assert lb['ORIGINAL_INPUTS']==C['original_model_inputs']==oldC['original_model_inputs'] and len(C['original_model_inputs'])==2
assert lb['ORIGINAL_BINDING']==C['original_model_binding']==oldC['original_model_binding']
assert C['limits']==oldC['limits']==lb['LIMITS']
assert lb['VERSION']==C['version'] and lb['SCOPE']==C['scope'] and list(lb['QUALIFICATION_CASES_BY_PURPOSE'])==[C['purpose']]
for role in ('composer','miner','inventory_cases'):
 ref(C['sources'][role]);hc=json.loads(ref(C['helper_contracts'][role]));assert hc['source']==C['sources'][role]
assert C['case_work_limit']==8000000 and C['allocation']=={'component_slots':{'closed':1,'open':1},'components':2,'composer_own_depth':128,'composer_own_work':1000000,'extension_advances':96,'fragment_priority':'OPEN_INPUT_OUTPUT_FIRST','heads_per_rule':1,'quantum':8,'root_advances':48}
assert C['qualification_inherited']is False and C['instrumentation_diagnostic_only']is True
assert A[A.index(b"if __name__ == '__main__':"):]==B[B.index(b"if __name__ == '__main__':"):]
caller_checks={'whole_current_source_and_contract_pins':True,'six_exact_raw_AST_forward_fullinverse':True,'both_actual_patch_directions_exact':True,'36_inherited_recursive_regions_raw_AST_exact':len(same)==36,'only_containing_main_changed_two_schema_literals':changed==['main'],'current17_input8_vs_original17_input2_epoch_exact':True,'only_three_helper_refs_change_math_dependencies':True,'exact_productive_helper_API_and_evidence_schema':True,'native20_512_internal500_once_CodeSeal_exceptional_finalguards_failure55_tail_exact':True,'same13_phase_protocol_75line850total':C['phase_protocol']['max_line_bytes']==75 and C['phase_protocol']['max_total_complete_phase_bytes']==850,'same_lossless_JSON_zlib_base64_responsecompletion_final_wire':True,'compile_without_evaluation':True}
assert all(caller_checks.values())
find=save(O,'findings-v1.json',{'source':C['source'],'source_contract':F['source_contract'],'parent_source':D['parent_source'],'checks':caller_checks,'findings':[{'id':'NPI-CALLER-COMPOSITION','disposition':'PASS','finding':'Six exact edits update VERSION/SCOPE/purpose, current composer2/miner3/CASE3 refs, contract schema and helper evidence gate only. Every other recursive region is raw/AST exact; current17/input8 remains separate from immutable original17/input2/epoch.'},{'id':'NPI-CALLER-NATIVE','disposition':'PASS','finding':'Whole immediate call/invoke exceptional guards, CodeSeal/strong anchors/native20/internal500MiB reserve and original limits remain exact. Same fixed13 charged phase sites and signed64/builtin writer guard,75Bmaxline/850Btotal; no history or cause inference.'},{'id':'NPI-CALLER-WIRE','disposition':'PASS','finding':'Current productive result schema accepted without changing full canonical lossless output/response/completion/final native gates. Original optional failure55 builtin4slot path and exit2 tail are exact; no late census/model callback is added.'},{'id':'NPI-CALLER-SCOPE','disposition':'LIMITATION','finding':'Reviewer authored composer2/CASE3 and prior host/native/instrumentation ancestry, so this is distinct Root integration/authority/native/wire review only. Diagnosis separate whole CASE peer is required; no own-component self-review or current runtime/native inventory/engine/theorem/transfer/RL/GCTS benefit acceptance.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_or_result_files_read':False})
review=dict(F['Review_ABI']);review.update(reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,status='CONDITIONAL_SOURCE_PASS',findings=find,checks=caller_checks,authorship_disclosure='Root authored current cold integration; reviewer authored delegated composer2, CASE3, prior host/native and startup instrumentation. This reviews the integration boundary, not own components as independent mathematical peer; Diagnosis CASE review separately required.',source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,concrete_blockers=[])
cr=save(O,'typed-Source-review-v1.json',review)
ch=save(O,'handoff-v1.json',{'schema':'native-productive-inventory-cold-peer-handoff-v1','source':C['source'],'source_contract':F['source_contract'],'review':cr,'findings':find,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
RC=json.loads(ref(F['reader_source_contract']));RD,AA,BB=delta(H/'reader-Source-delta-v1.json',5);assert RD['source']==F['reader']==RC['source'];r0,r1=regions(AA),regions(BB)
assert [k for k in r0 if r0[k]!=r1[k]]==['main']
assert literals(BB)['CURRENT_CONTRACT']==F['source_contract']==RC['current_operative_contract']
restored=r1['main'][0]
for e in RD['edits']:
 if e['label']!='operative_capsule':
  assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==r0['main'][0]
assert r0['read_phases']==r1['read_phases'] and r0['read_failure_diagnostic']==r1['read_failure_diagnostic']
reader_checks={'current_literal_contract_and_response_VERSION_match':True,'five_exact_raw_AST_forward_fullinverse':True,'both_actual_patch_directions_exact':True,'all_other_reader_functions_raw_AST_exact':True,'whole_main_exact_after_four_literal_restorations':True,'native20_positive55failure512_Date_session_once_exit_concordance_exact':True,'same_buffer_pin_parse_and_complete_canonical_lossless_EOF_wire_exact':True,'same13_phase_and_optional4slots_failure_no_cause_inference':True,'productive_fullpayload_opaque_no_semantic_replay':True,'compile_without_evaluation':True}
rf=save(R,'findings-v1.json',{'source':RC['source'],'source_contract':F['reader_source_contract'],'current_operative_contract':F['source_contract'],'checks':reader_checks,'findings':[{'id':'NPI-READER-AUTH','disposition':'PASS','finding':'Exact five changes bind current productive contract/reviewScope/responseVersion/helperSchema. Parent full main restores after four in-function literal substitutions; all other helpers raw/AST exact.'},{'id':'NPI-READER-NATIVE-WIRE','disposition':'PASS','finding':'Unchanged same-buffer wholepin/response2/final1/canonical envelope/decompressionEOF/caps, nativeonce/meter2/postprobe20/512 positive and55 failure, exact same sessionpair/Date/exit/reap joins remain.'},{'id':'NPI-READER-INTERPRETATION','disposition':'PASS','finding':'Status and narrow conditional_inventory_record_complete are literal CURRENT pinned helper record observations. No arrays flattened, joined into aggregate placements or semantically replayed. Complete current checked record can support narrow inventory status under separate Root acceptance; phases/failure/UNKNOWN cannot supply missing scientific evidence or broad authority.'},{'id':'NPI-READER-OVERLAP','disposition':'LIMITATION','finding':'Root reader author differs from reviewer. Reviewer owns composer/CASE/instrumentation and prior native/readout ancestry; no own-component independent checker claim. Diagnosis CASE peer and Root measured acceptance remain separate; no actual data read.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_or_result_files_read':False})
rr=dict(F['reader_Review_ABI']);rr.update(reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,status='CONDITIONAL_SOURCE_PASS',findings=rf,checks=reader_checks,authorship_disclosure=review['authorship_disclosure'],source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,concrete_blockers=[])
rref=save(R,'typed-Source-review-v1.json',rr)
rh=save(R,'handoff-v1.json',{'schema':'native-productive-inventory-readout-peer-handoff-v1','source':RC['source'],'source_contract':F['reader_source_contract'],'review':rref,'findings':rf,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
print(json.dumps({'caller_review':cr,'caller_handoff':ch,'caller_findings':find,'reader_review':rref,'reader_handoff':rh,'reader_findings':rf,'unchanged_caller_regions':len(same)},sort_keys=True))
