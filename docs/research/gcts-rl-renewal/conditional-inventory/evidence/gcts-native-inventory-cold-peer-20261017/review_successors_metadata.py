"""Raw/AST/literal successor Source audit only; no project evaluation."""
import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-inventory-ROOT-source-20261017');O=Path('/private/tmp/gcts-native-inventory-cold-peer-20261017');R=Path('/private/tmp/gcts-native-inventory-readout-peer-20261017')
def raw(p):
 p=Path(p);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(p):
 b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ref(r):assert pin(r['path'])==r;return raw(r['path'])
def save(h,n,v):
 p=h/n
 with p.open('xb')as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
 return pin(p)
def lits(b):
 d={}
 for n in ast.parse(b).body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:d[n.targets[0].id]=ast.literal_eval(n.value)
   except(ValueError,TypeError):pass
 return d
def regions(b):
 ls=b.decode().splitlines(True)
 return {n.name:(''.join(ls[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False))for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def delta(p):
 d=json.loads(raw(p));a=ref(d['parent_source']);b=ref(d['source']);s=a.decode()
 assert len(d['edits'])==2
 for e in d['edits']:
  i=e['start'];assert s[i:i+len(e['old'])]==e['old'];s=s[:i]+e['new']+s[i+len(e['old']):]
 assert s.encode()==b
 for e in reversed(d['edits']):
  i=e['start'];assert s[i:i+len(e['new'])]==e['new'];s=s[:i]+e['old']+s[i+len(e['new']):]
 assert s.encode()==a and ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
 for label,x,y in [('forward',a,b),('full-inverse',b,a)]:
  patch=d['patches'][label];ref(patch)
  with tempfile.TemporaryDirectory(dir=str(O))as td:
   target=Path(td)/'before';target.write_bytes(x)
   out=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',patch['path']],cwd=td,capture_output=True)
   assert out.returncode==0 and target.read_bytes()==y
 compile(b,d['source']['path'],'exec',dont_inherit=True)
 return d,a,b
C=json.loads(raw(H/'Source-contract-v2.json'));oldC=json.loads(raw(H/'Source-contract-v1.json'))
D,A,B=delta(H/'caller-v2-Source-delta-v1.json');assert D['source']==C['source'];la,lb=lits(A),lits(B)
assert regions(A)==regions(B)
assert {k:la['FIXED'][k]for k in la['FIXED']if k!='inventory_cases'}=={k:lb['FIXED'][k]for k in lb['FIXED']if k!='inventory_cases'}
assert {k:v for k,v in la.items()if k not in('FIXED','VERSION')}=={k:v for k,v in lb.items()if k not in('FIXED','VERSION')}
assert lb['VERSION']==C['version']=='ROOT-native-connected-conditional-inventory-cold-v2-case-work8m'
assert dict(lb['FIXED'],intake=C['source'])==C['sources']
assert lb['FIXED']['inventory_cases']['sha256']=='c0d6552f984abb98040c97867486b3441f89c8e40248b38452582834baadbb4d'
for k in ('inputs','limits','allocation','original_model_sources','original_model_inputs','original_model_binding','purpose','scope','schema','failure_protocol','native_protocol','artifact_API','scientific_interpretation'):
 assert C[k]==oldC[k]
assert C['case_work_limit']==8000000 and C['qualification_inherited']is False
find=save(O,'findings-v2.json',{'source':C['source'],'source_contract':pin(H/'Source-contract-v2.json'),'parent_review':pin(O/'typed-Source-review-v1.json'),'checks':{'two_raw_forward_inverse_whole_AST_exact':True,'both_actual_patch_directions_exact':True,'all19_top_named_regions_including_main_raw_AST_exact':len(regions(A))==19,'only_CASE_changes_in_literal_FIXED_values':True,'all_other_constants_raw_literal_equal':True,'all_native_once_CodeSeal_failure_phase_wire_bodies_unchanged':True,'original17_input2_current17_input8_allocation_native_limits_preserved':True,'compile_without_evaluation':True},'findings':[{'id':'NI-CALLER-V2-CAPSULE','disposition':'PASS','finding':'Only ownVERSION and fullFIXED literal changed. All19 top function/class regions, including whole main, are raw/AST identical. Current CASE pin c0d655 and responseVERSION are exact. CASE own work allowance8m is not a larger native or model limit; its correctness is covered by distinct CASE review.'},{'id':'NI-CALLER-V2-ORDER','disposition':'DISCLOSURE','finding':'FIXED was rendered in sorted role order. Since existing module loading iterates FIXED, setup iteration order may differ. Full identical current module set except CASE, all setup charged; no runtime-cost/order-equivalence claim.'},{'id':'NI-CALLER-V2-SCOPE','disposition':'LIMITATION','finding':'No actual/result data read, no runtime fit or current qualification inherited. Original20/512, all full validation and conditional-only scope remain.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
rev=dict(C['Review_ABI']);rev.update(source_contract=pin(H/'Source-contract-v2.json'),reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,findings=find,source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,authorship_disclosure='Distinct from Root caller author. Reviewer authored composer9fee and earlier host/native/caller/provider dependencies. This narrow caller/authority review does not self-peer composer or CASE mathematics; no scientific replay.',concrete_blockers=[])
cr=save(O,'typed-Source-review-v2.json',rev)
ch=save(O,'handoff-v2.json',{'schema':'ROOT-native-inventory-caller-peer-handoff-v2','source':C['source'],'source_contract':pin(H/'Source-contract-v2.json'),'review':cr,'findings':find,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
RC=json.loads(raw(H/'reader-Source-contract-v3.json'));RD,RA,RB=delta(H/'reader-v3-Source-delta-v1.json');assert RD['source']==RC['source']
rra,rrb=regions(RA),regions(RB);assert set(rra)==set(rrb)
assert [k for k in rra if rra[k]!=rrb[k]]==['main']
assert lits(RB)['CURRENT_CONTRACT']==pin(H/'Source-contract-v2.json')==RC['current_operative_contract']
# Erasing the one response-version string from main restores its entire body.
a=rra['main'][0];b=rrb['main'][0]
assert b.replace(lb['VERSION'],la['VERSION'])==a
assert b'collector_or_family_pipeline_executed'not in RB
rf=save(R,'findings-v3.json',{'source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v3.json'),'current_operative_contract':pin(H/'Source-contract-v2.json'),'parent_review':pin(R/'typed-Source-review-v2.json'),'checks':{'two_raw_forward_inverse_whole_AST_exact':True,'both_actual_patch_directions_exact':True,'all_other_reader_helper_regions_raw_AST_exact':True,'whole_main_exact_after_response_VERSION_restoration':True,'all_native20_55_512_Date_session_once_currentauthority_wire_failure_phase_joins_unchanged':True,'current_literal_capsule_and_response_VERSION_match_caller':True,'prior_stale_pipelinefalse_field_stays_absent':True,'compile_without_evaluation':True},'findings':[{'id':'NI-READER-V3-AUTHORITY','disposition':'PASS','finding':'Literal current contract308d4bf8 and responseVERSION exactly bind current callerbc1786. All operative main logic restores byte-for-byte after soleVERSION substitution; other helpers raw/AST exact. Full native/Date/session/once/same-buffer canonical wire and diagnostic phase/failure checks inherited by exact raw preservation.'},{'id':'NI-READER-V3-SCOPE','disposition':'LIMITATION','finding':'No semantic replay, actual reads, historical qualification, theorem/frontier/engine/RL/GCTS gain or predicted fit. Conditional record status remains exclusively the freshly pinned full caller payload; failure remainsUNKNOWN, not inferred progress.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
rr=save(R,'typed-Source-review-v3.json',{'schema':'ROOT-native-inventory-saved-reader-typed-Source-review-v3','scope':'ROOT-native-inventory-saved-reader-Source','author_identity':'/root','reviewer_identity':'/root/hilbert_advice_controls','source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v3.json'),'current_operative_contract':pin(H/'Source-contract-v2.json'),'source_review_passed':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'findings':rf,'authorship_disclosure':'Distinct from Root reader/caller author; reviewer authored composer/host/native and predecessor caller/readout ancestry. Saved metadata/transport Source review, no own-component self-peer or independent mathematical replay.','actual_or_result_files_read':False,'concrete_blockers':[]})
rh=save(R,'handoff-v3.json',{'schema':'ROOT-native-inventory-reader-peer-handoff-v3','source':RC['source'],'source_contract':pin(H/'reader-Source-contract-v3.json'),'review':rr,'findings':rf,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
print(json.dumps({'caller_review':cr,'caller_handoff':ch,'caller_findings':find,'reader_review':rr,'reader_handoff':rh,'reader_findings':rf},sort_keys=True))
