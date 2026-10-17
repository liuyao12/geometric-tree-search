"""Current Root integration Source/AST/metadata only, no project evaluation."""
import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-source-20261017');O=Path('/private/tmp/gcts-native-productive-inventory-work4m-cold-peer-20261017');R=Path('/private/tmp/gcts-native-productive-inventory-work4m-readout-peer-20261017')
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
def delta(path):
 d=json.loads(raw(path));a=ref(d['parent_source']);b=ref(d['source']);s=a.decode();assert len(d['edits'])==2
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
F=json.loads(raw(H/'handoff-v2.json'));C=json.loads(ref(F['source_contract']));P=json.loads(ref(C['operative_parent_contract']))
D,A,B=delta(H/'caller-Source-delta-v1.json');assert D['source']==F['source']==C['source'];la,lb=literals(A),literals(B)
assert regions(A)==regions(B)
assert {k:v for k,v in la.items()if k not in('FIXED','VERSION')}=={k:v for k,v in lb.items()if k not in('FIXED','VERSION')}
assert {k:v for k,v in la['FIXED'].items()if k not in('composer','inventory_cases')}=={k:v for k,v in lb['FIXED'].items()if k not in('composer','inventory_cases')}
assert dict(lb['FIXED'],intake=C['source'])==C['sources'] and len(C['sources'])==17
assert lb['FIXED_INPUTS']==C['inputs']==P['inputs'] and len(C['inputs'])==8
for k in ('original_model_sources','original_model_inputs','original_model_binding','limits','phase_protocol','purpose','schema','scope','artifact_API','case_work_limit','returned_record_scope','scientific_interpretation'):
 assert C[k]==P[k]
assert C['allocation']==dict(P['allocation'],composer_own_work=4000000)
for role in ('composer','inventory_cases'):
 ref(C['sources'][role]);h=json.loads(ref(C['helper_contracts'][role]));assert h['source']==C['sources'][role]
assert C['case_work_limit']==8000000 and C['budget_ablation']=={'case_own_work':8000000,'composer_own_work':4000000,'native_positive_seconds':20,'other_allocations_unchanged':True,'parent_composer_own_work':1000000,'scientific_qualification_inherited':False}
comp_peer=pin('/private/tmp/gcts-native-component-composer-work4m-peer-20261017/typed-Source-review-v3.json')
case_peer=pin('/private/tmp/gcts-native-productive-inventory-cases-work4m-peer-20261017/typed-Source-review-v4.json')
checks={'two_exact_literal_edits_raw_AST_fullinverse':True,'both_actualpatch_directions_apply_exact':True,'ALL37recursive_function_class_regions_including_main_raw_AST_exact':len(regions(B))==37,'only_composer_and_CASE_capsules_change_currentmap_values':True,'current17_input8_vs_original17_input2_epoch_model_unchanged':True,'native20_512_internal500_once_CodeSeal_allguards_phases_transport_failure_tail_exact':True,'composer_work4m_CASE8m_other_allocation_unchanged':True,'separate_helper_peers_present_no_self_peer':True,'AST_compile_without_evaluation':True}
assert all(checks.values())
find=save(O,'findings-v2.json',{'source':C['source'],'source_contract':F['source_contract'],'parent_review':pin('/private/tmp/gcts-native-productive-inventory-cold-peer-20261017/typed-Source-review-v1.json'),'checks':checks,'unchanged_regions':list(regions(B)),'helper_peers':{'composer':comp_peer,'cases':case_peer},'findings':[{'id':'NPI4-CALLER-DELTA','disposition':'PASS','finding':'Exactly VERSION and wholeFIXED replacement; literalmap differs only composer/CASE capsules. All37 recursive regions including fullmain are rawASTexact, all other literals unchanged. No root/allocation/model/native/guard/phase/failure/output behavior changed in caller.'},{'id':'NPI4-CALLER-COST','disposition':'PASS','finding':'Current source contracts explicitly request composer ownwork4m withCASE8m, same depth128/root48/ext96/head1/quantum8/two slots and native20/512 limits. Extra own-work allowance is not runtime fit, success, availability, transfer or advantage evidence.'},{'id':'NPI4-CALLER-OVERLAP','disposition':'LIMITATION','finding':'Root authors current integration; reviewer authors delegated helper literal ablation/composer/CASE and prior host/native/instrumentation. This is integration Source review only; distinct Diagnosis helper peers separately bound. No own-helper self-review or scientific replay/acceptance.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_or_result_files_read':False})
review=dict(F['Review_ABI']);review.update(reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,status='CONDITIONAL_SOURCE_PASS',findings=find,checks=checks,authorship_disclosure='Root current integration author; Controls reviewer authored delegated composer/CASE budget edits and prior host/native/instrumentation. Separate Diagnosis helper peers required and retained; no mathematical own-helper peer or runtime qualification claim.',source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,concrete_blockers=[])
cr=save(O,'typed-Source-review-v2.json',review)
ch=save(O,'handoff-v2.json',{'schema':'native-productive-inventory-work4m-cold-peer-handoff-v2','source':C['source'],'source_contract':F['source_contract'],'review':cr,'findings':find,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
RC=json.loads(ref(F['reader_source_contract']));RD,RA,RB=delta(H/'reader-Source-delta-v1.json');assert RD['source']==RC['source']==F['reader']
r0,r1=regions(RA),regions(RB);assert [k for k in r0 if r0[k]!=r1[k]]==['main']
assert r1['main'][0].replace(lb['VERSION'],la['VERSION'])==r0['main'][0]
assert literals(RB)['CURRENT_CONTRACT']==F['source_contract']==RC['current_operative_contract']
rchecks={'two_exact_literal_edits_raw_AST_fullinverse':True,'both_actualpatch_directions_apply_exact':True,'all_helpers_raw_AST_exact_except_main_responseVERSION_only':True,'wholemain_exact_after_single_responseVERSION_restore':True,'current_literal_contract_and_response_VERSION_join':True,'all_native_once_Date_session_samebuffer_fullcanonical_lossless_EOF_wire_joins_unchanged':True,'failure55_countsNone_qualified0_phase13_no_cause_scope_unchanged':True,'same_currentproducer_status_narrowinventory_no_semantic_replay':True,'AST_compile_without_evaluation':True}
rf=save(R,'findings-v2.json',{'source':RC['source'],'source_contract':F['reader_source_contract'],'current_operative_contract':F['source_contract'],'parent_review':pin('/private/tmp/gcts-native-productive-inventory-readout-peer-20261017/typed-Source-review-v1.json'),'checks':rchecks,'findings':[{'id':'NPI4-READER-DELTA','disposition':'PASS','finding':'Only frozenCURRENT_CONTRACT capsule and responseVERSION change. All helper functions exact, wholemain raw restored by singleVERSION substitution. Current producer/full wire/resource observations keep prior narrow interpretation; no science replay or altered failure handling.'},{'id':'NPI4-READER-NATIVE','disposition':'PASS','finding':'Same strict native20/512 positive,55 failure, once/meter2/reap/postprobe/Date/session/exit joins; retained samebuffer canonical two-file/response/final/envelope/compressed+expandedEOF hashes;13 phases only reached-sites, optional4slots failure never cause or missing result.'},{'id':'NPI4-READER-OVERLAP','disposition':'LIMITATION','finding':'Root reader integration author distinct from reviewer, whose own helper and prior instrumentation/readout ancestry is disclosed. No actual/output/model/clock/helper execution or scientific data read.'}],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_or_result_files_read':False})
rr=dict(F['reader_Review_ABI']);rr.update(reviewer_identity='/root/hilbert_advice_controls',source_review_passed=True,status='CONDITIONAL_SOURCE_PASS',findings=rf,checks=rchecks,authorship_disclosure=review['authorship_disclosure'],source_only=True,scientific_calls=0,scientific_acceptance=False,actual_or_result_files_read=False,concrete_blockers=[])
rref=save(R,'typed-Source-review-v2.json',rr)
rh=save(R,'handoff-v2.json',{'schema':'native-productive-inventory-work4m-readout-peer-handoff-v2','source':RC['source'],'source_contract':F['reader_source_contract'],'review':rref,'findings':rf,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'concrete_blockers':[]})
print(json.dumps({'caller_review':cr,'caller_handoff':ch,'caller_findings':find,'reader_review':rref,'reader_handoff':rh,'reader_findings':rf},sort_keys=True))
