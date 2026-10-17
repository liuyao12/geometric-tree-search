"""Source literal/AST/patch metadata authoring. Never imports project code."""
import ast,copy,difflib,hashlib,json,subprocess,tempfile
from pathlib import Path
CP=Path('/private/tmp/gcts-native-component-composer-productive-source-20261017');CO=Path('/private/tmp/gcts-native-component-composer-work4m-source-20261017')
KP=Path('/private/tmp/gcts-native-productive-inventory-cases-source-20261017');KO=Path('/private/tmp/gcts-native-productive-inventory-cases-work4m-source-20261017')
def raw(p):
 p=Path(p);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(p):
 b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def text(folder,n,s):
 p=folder/n
 with p.open('xb')as f:f.write(s.encode())
 return pin(p)
def save(folder,n,v):return text(folder,n,json.dumps(v,sort_keys=True,indent=2)+'\n')
def regions(data):
 lines=data.decode().splitlines(True);out={}
 def walk(ns,prefix=''):
  for n in ns:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    key=prefix+n.name;out[key]=(''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False));walk(n.body,key+'.')
 walk(ast.parse(data).body);return out
def make(folder,parent,name,replacements,label):
 a=raw(parent);s=a.decode();edits=[]
 for key,old,new in replacements:
  assert s.count(old)==1,(key,s.count(old));i=s.index(old);edits.append({'label':key,'start':i,'old':old,'new':new});s=s[:i]+new+s[i+len(old):]
 b=s.encode();compile(b,str(folder/name),'exec',dont_inherit=True)
 back=s
 for e in reversed(edits):
  i=e['start'];assert back[i:i+len(e['new'])]==e['new'];back=back[:i]+e['old']+back[i+len(e['new']):]
 assert back.encode()==a and ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
 assert regions(a)==regions(b)
 src=text(folder,name,s);patches={}
 for direction,x,y in [('forward',a,b),('full-inverse',b,a)]:
  p=text(folder,direction+'.patch',''.join(difflib.unified_diff(x.decode().splitlines(True),y.decode().splitlines(True),fromfile='before',tofile='after')));patches[direction]=p
  with tempfile.TemporaryDirectory(dir=str(folder))as td:
   target=Path(td)/'before';target.write_bytes(x)
   r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=td,capture_output=True)
   assert r.returncode==0 and target.read_bytes()==y
 delta=save(folder,'Source-delta-'+label+'.json',{'schema':'native-productive-work-ablation-Source-delta-'+label,'parent_source':pin(parent),'source':src,'edits':edits,'patches':patches,'whole_raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_both_directions_exact':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
 audit=save(folder,'static-audit-'+label+'.json',{'schema':'native-productive-work-ablation-static-'+label,'source':src,'source_delta':delta,'checks':{'exact_declared_literal_edit_count':len(edits),'whole_raw_AST_inverse':True,'both_actualpatch_directions_exact':True,'ALL_existing_named_regions_raw_AST_exact':True,'all_scientific_native_census_slot_UNKNOWN_or_stage_validation_bodies_unchanged':True,'AST_compile_without_evaluation':True},'unchanged_named_regions':list(regions(b)),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'project_module_imported_or_evaluated':False})
 return src,delta,audit,patches
cv='receptor-family-native-conditional-component-composer-v3-closed-open-slots-work4m';kv='ROOT-native-productive-conditional-inventory-cases-v4-composer-work4m'
cs,cd,ca,cp=make(CO,CP/'native_conditional_component_composer_v2.py','native_conditional_component_composer_v3.py',[
 ('own_VERSION',"VERSION = 'receptor-family-native-conditional-component-composer-v2-closed-open-slots'",'VERSION = '+repr(cv)),
 ('DEFAULT_LIMITS_own_work_only',"DEFAULT_LIMITS = {'work': 1000000,", "DEFAULT_LIMITS = {'work': 4000000,")],'v3')
oldC=json.loads(raw(CP/'Source-contract-v2.json'));api=json.loads(raw(CP/'API-wire-v2.json'))
api.update(schema='receptor-family-native-component-composer-API-v3',version=cv);api['limits']['work']=4000000
api['stop']=api['stop'].replace('work1m','work4m')
api['ablation']='Only default own-composer work comparison changes1m→4m; same shared native tick and literal finite proposal allocation. No runtime/availability/success/benefit inherited or predicted.'
capi=save(CO,'API-wire-v3.json',api)
C=copy.deepcopy(oldC);C.update(schema='receptor-family-native-component-composer-work4m-Source-contract-v3',source=cs,sources={'composer':cs},version=cv,API_wire=capi,source_delta=cd,static_audit=ca,operative_parent_contract=pin(CP/'Source-contract-v2.json'),parent_source=pin(CP/'native_conditional_component_composer_v2.py'),parent_handoff=pin(CP/'handoff-v2.json'),parent_distinct_review=pin('/private/tmp/gcts-native-component-composer-productive-peer-20261017/typed-Source-review-v2.json'),author_identity='/root/hilbert_advice_controls')
C['limits']['work']=4000000
C['operative_override']='Predeclared computational-budget ablation ONLY: DEFAULT_LIMITS.work1m→4m and ownVERSION. All parent body/protocol/slot/census/UNKNOWN/queue/validation semantics exact. Parent prose own1m now means4m in this current role only; no larger native20/512 Root allowance or changed case8m.'
C['qualification_inherited']=False;C['runtime_qualified']=False;C['runtime_fit']='UNMEASURED'
C['Review_ABI'].update(schema='receptor-family-native-component-composer-productive-slots-typed-Source-review-v3',source=cs,sources={'composer':cs},source_contract='current capsule')
cc=save(CO,'Source-contract-v3.json',C)
ch=save(CO,'handoff-v3.json',{'schema':'receptor-native-component-work4m-handoff-v3','source':cs,'source_contract':cc,'API_wire':capi,'source_delta':cd,'static_audit':ca,'actual_patches':cp,'Review_ABI':dict(C['Review_ABI'],source_contract=cc),'exact_change_count':2,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
ks,kd,ka,kp=make(KO,KP/'native_productive_inventory_cases_v3.py','native_productive_inventory_cases_v4.py',[
 ('own_VERSION',"VERSION = 'ROOT-native-productive-conditional-inventory-cases-v3'",'VERSION = '+repr(kv)),
 ('COMPOSER_VERSION',"COMPOSER_VERSION = 'receptor-family-native-conditional-component-composer-v2-closed-open-slots'",'COMPOSER_VERSION = '+repr(cv)),
 ('COMPOSER_LIMITS_own_work_only',"COMPOSER_LIMITS = {'work': 1000000,", "COMPOSER_LIMITS = {'work': 4000000,")],'v4')
oldK=json.loads(raw(KP/'Source-contract-v3.json'));kapi=json.loads(raw(KP/'API-wire-v3.json'))
kapi.update(schema='ROOT-native-productive-inventory-cases-API-v4',version=kv);kapi['allocation']['composer']['work']=4000000
kapi['ablation']='Only ownVERSION/composerVERSION/COMPOSER_LIMITS.work1m→4m change. Same CASE8m/depth128, miner3 OPEN_INPUT_OUTPUT_FIRST, all staged arrays/all emitted fresh checks/native tick/UNKNOWN semantics. Native20/512 unchanged outside this module.'
kr=save(KO,'API-wire-v4.json',kapi)
K=copy.deepcopy(oldK);K.update(schema='ROOT-native-productive-inventory-cases-work4m-Source-contract-v4',source=ks,sources={'cases':ks},version=kv,API=kr,source_delta=kd,static_audit=ka,operative_parent_contract=pin(KP/'Source-contract-v3.json'),parent_source=pin(KP/'native_productive_inventory_cases_v3.py'),composer=cs,composer_contract=cc,parent_distinct_review=pin('/private/tmp/gcts-native-productive-inventory-cases-peer-20261017/typed-Source-review-v3.json'))
K['allocation']['composer']['work']=4000000
K['operative_override']='Predeclared computational-budget ablation ONLY: composer requested work1m→4m, matching composerVERSION and ownVERSION. All parent CASE functions/classes including8m/depth128, phase stage order/all arrays/current unions/census/independent/native validation bodies are rawAST exact. No other proposal/allocation/model/native/receipt/UNKNOWN change, no success/availability/time/benefit inheritance.'
K['Review_ABI'].update(schema='ROOT-native-productive-inventory-cases-typed-Source-review-v4',source=ks,sources={'cases':ks},source_contract='current capsule')
kref=save(KO,'Source-contract-v4.json',K)
kh=save(KO,'handoff-v4.json',{'schema':'ROOT-native-productive-inventory-cases-work4m-handoff-v4','source':ks,'source_contract':kref,'API':kr,'source_delta':kd,'static_audit':ka,'actual_patches':kp,'Review_ABI':dict(K['Review_ABI'],source_contract=kref),'exact_change_count':3,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'composer':{'source':cs,'contract':cc,'API':capi,'delta':cd,'handoff':ch},'cases':{'source':ks,'contract':kref,'API':kr,'delta':kd,'handoff':kh}},sort_keys=True))
