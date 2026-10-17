"""Root Source/literal/AST authoring only; never evaluates project code."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

S=Path('/private/tmp/gcts-native-productive-inventory-ROOT-source-20261017')
P=Path('/private/tmp/gcts-native-inventory-startup-diagnostic-source-20261017')
V='ROOT-native-productive-inventory-cold-v1'
SC='ROOT-native-productive-inventory-cold-Source'
CS='ROOT-native-productive-inventory-cold-Source-contract-v1'
EVIDENCE='ROOT-native-productive-conditional-inventory-evidence-v1'
def raw(path):
    p=Path(path)
    assert not getattr(p.stat(),'st_flags',0)&0x40000000
    with p.open('rb')as f:
        b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
    return b
def pin(path):
    b=raw(path);return {'path':str(path),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,value):
    p=S/name
    with p.open('xb')as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
    return pin(p)
def textfile(name,value):
    p=S/name
    with p.open('xb')as f:f.write(value.encode())
    return pin(p)
def mutate(text,edits,label,old,new):
    assert old and text.count(old)==1,(label,text.count(old))
    i=text.index(old);edits.append({'label':label,'start':i,'old':old,'new':new})
    return text[:i]+new+text[i+len(old):]
def delta(name,parent,current,edits):
    a=raw(parent);b=raw(current);t=a.decode()
    for e in edits:
        i=e['start'];assert t[i:i+len(e['old'])]==e['old']
        t=t[:i]+e['new']+t[i+len(e['old']):]
    assert t.encode()==b
    for e in reversed(edits):
        i=e['start'];assert t[i:i+len(e['new'])]==e['new']
        t=t[:i]+e['old']+t[i+len(e['new']):]
    assert t.encode()==a and ast.dump(ast.parse(t),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
    patches={}
    for direction,x,y in [('forward',a,b),('full-inverse',b,a)]:
        patches[direction]=textfile(name+'-'+direction+'.patch',''.join(difflib.unified_diff(x.decode().splitlines(True),y.decode().splitlines(True),fromfile='before',tofile='after')))
        with tempfile.TemporaryDirectory(dir=str(S))as tmp:
            target=Path(tmp)/'before';target.write_bytes(x)
            r=subprocess.run(['/usr/bin/patch','--batch','-F0',str(target),'-i',patches[direction]['path']],capture_output=True)
            assert r.returncode==0 and target.read_bytes()==y,(direction,r.stderr)
    return save(name+'-Source-delta-v1.json',{'schema':'ROOT-productive-inventory-Source-delta-v1','parent_source':pin(parent),'source':pin(current),'edits':edits,'patches':patches,'whole_raw_forward_exact':True,'whole_raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_both_directions_exact':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
def regions(data):
    lines=data.decode().splitlines(True);out={}
    def walk(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
                key=prefix+n.name;out[key]=(''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False));walk(n.body,key+'.')
    walk(ast.parse(data).body);return out

assert len(sys.argv)==3,'Frozen productive CASE Source and contract paths'
case_path,case_contract=map(Path,sys.argv[1:])
case=pin(case_path);cc=json.loads(raw(case_contract));assert cc['source']==case
parent=P/'native_inventory_startup_diagnostic_cold_v1.py'
a=raw(parent);assert hashlib.sha256(a).hexdigest()=='c03a8dfd6ae89f02e500fa90abb98e4c836b2d6bb9a03e48a60b9b439de04ce5'
oldC=json.loads(raw(P/'Source-contract-v2.json'))
current=dict(oldC['sources'])
current['composer']=pin(Path('/private/tmp/gcts-native-component-composer-productive-source-20261017/native_conditional_component_composer_v2.py'))
current['miner']=pin(Path('/private/tmp/gcts-interface-coupled-miner-source-20261017/receptor_family_miner_v3.py'))
assert current['composer']['sha256']=='b8293737f6a2d13554c6c0e774f4488c30c13c0dfc7f8e4e3cb63ddecd9d4a48'
assert current['miner']['sha256']=='7873c8a071079726151020191d574fcc3289a7e56b6ef91ccac244a1d003013c'
current['inventory_cases']=case
t=a.decode();edits=[]
t=mutate(t,edits,'own_VERSION',"VERSION='ROOT-native-inventory-startup-diagnostic-cold-v1'",'VERSION='+repr(V))
t=mutate(t,edits,'own_SCOPE',"SCOPE='ROOT-native-inventory-startup-diagnostic-cold-Source'",'SCOPE='+repr(SC))
t=mutate(t,edits,'purpose',"QUALIFICATION_CASES_BY_PURPOSE={'native-conditional-inventory': ['NI-01-automatic-connected-conditional-pair']}","QUALIFICATION_CASES_BY_PURPOSE={'native-productive-conditional-inventory': ['NPI-01-closed-and-open-conditional-inventory']}")
old_fixed=next(line for line in t.splitlines()if line.startswith('FIXED='))
t=mutate(t,edits,'current_three_helper_refs',old_fixed,'FIXED='+repr({k:v for k,v in current.items()if k!='intake'}))
t=mutate(t,edits,'current_contract_schema',"contract['schema']=='ROOT-native-inventory-startup-diagnostic-cold-Source-contract-v1'","contract['schema']=="+repr(CS))
t=mutate(t,edits,'productive_helper_evidence_schema',"inventory['schema']=='ROOT-native-conditional-inventory-evidence-v1'","inventory['schema']=="+repr(EVIDENCE))
source=textfile('native_productive_inventory_cold_v1.py',t);compile(t,source['path'],'exec',dont_inherit=True)
current['intake']=source
sd=delta('caller',parent,Path(source['path']),edits)
C={k:copy.deepcopy(oldC[k])for k in ('inputs','limits','artifact_API','original_model_sources','original_model_inputs','original_model_binding','failure_protocol','native_protocol','phase_protocol','case_work_limit')}
C.update(schema=CS,scope=SC,version=V,source=source,sources=current,author_identity='/root',source_only=True,scientific_calls=0,scientific_acceptance=False,qualification_inherited=False,instrumentation_diagnostic_only=True,parent_source=pin(parent),operative_parent_contract=pin(P/'Source-contract-v2.json'),source_delta=sd,purpose='native-productive-conditional-inventory')
C['allocation']={'root_advances':48,'extension_advances':96,'heads_per_rule':1,'quantum':8,'components':2,'component_slots':{'closed':1,'open':1},'composer_own_work':1000000,'composer_own_depth':128,'fragment_priority':'OPEN_INPUT_OUTPUT_FIRST'}
C['helper_contracts']={'composer':pin(Path('/private/tmp/gcts-native-component-composer-productive-source-20261017/Source-contract-v2.json')),'miner':pin(Path('/private/tmp/gcts-interface-coupled-miner-source-20261017/Source-contract-v3.json')),'inventory_cases':pin(case_contract)}
C['author_provenance']='Root authors cold integration and saved reader; Controls authors productive CASE/composer; Arithmetic authors miner V3. Distinct whole current Source peer reviews are required before one Root-owned measured actual.'
C['scientific_interpretation']='Conditional inventory only: two alternative automatically proposed two-member point unions, one closed and one with actual external inputs. Every emitted grounding needs its own fresh independent expansion, original-root rebind and native host-adapter union check. Descriptor catalogue identity is whole-preimage identity, with each physical occurrence retained; counts do not imply independent lemmas, transfer or proof.'
C['returned_record_scope']='Current source-ground conditional instances only, all broad flags false. A complete current authenticated native20/512-qualified helper record can support narrow qualification. UNKNOWN, phase writes and saved metadata do not supply scientific replay or infer missing results.'
C['scope_statement']='Original full Source17/input2/model epoch and current executable Source17/input8 remain distinct and unchanged mathematically. Only current composer/miner/CASE refs and explicit helper evidence schema change. Same native/once/CodeSeal/limits/guards/transport/failure tail. No global graph/degree/EOF/engine/scheduler/rollback/target theorem/receiver transfer/universal family lemma/trained RL/search-advantage authority.'
C['phase_protocol']['helper_stage_semantics']='One BEFORE_COMPOSER and AFTER_COMPOSER around composition; collect all separate component DAGs then one AFTER_DAG; mine all separate DAGs then one AFTER_MINER; qualify all physical extraction occurrences then one AFTER_QUALIFICATION. UNKNOWN may omit later reached sites.'
C['Review_ABI']={'schema':'ROOT-native-productive-inventory-typed-Source-review-v1','scope':SC,'author_identity':'/root','source':source,'sources':current,'source_contract':'current capsule','source_only':True,'scientific_calls':0,'scientific_acceptance':False}
cref=save('Source-contract-v1.json',C)
rparent=P/'ROOT_read_native_inventory_startup_diagnostic_saved_v2.py';ra=raw(rparent);rt=ra.decode();re=[]
oldline=next(line for line in rt.splitlines()if line.startswith('CURRENT_CONTRACT = '))
rt=mutate(rt,re,'operative_capsule',oldline,'CURRENT_CONTRACT = '+repr(cref))
rt=mutate(rt,re,'contract_schema',"contract['schema'] == 'ROOT-native-inventory-startup-diagnostic-cold-Source-contract-v1'","contract['schema'] == "+repr(CS))
rt=mutate(rt,re,'review_scope',"review['scope'] == 'ROOT-native-inventory-startup-diagnostic-cold-Source'","review['scope'] == "+repr(SC))
rt=mutate(rt,re,'response_VERSION',"body['version']=='ROOT-native-inventory-startup-diagnostic-cold-v1'","body['version']=="+repr(V))
rt=mutate(rt,re,'productive_helper_evidence_schema',"pipeline['schema']=='ROOT-native-conditional-inventory-evidence-v1'","pipeline['schema']=="+repr(EVIDENCE))
reader=textfile('ROOT_read_native_productive_inventory_saved_v1.py',rt);compile(rt,reader['path'],'exec',dont_inherit=True)
rd=delta('reader',rparent,Path(reader['path']),re)
rc=save('reader-Source-contract-v1.json',{'schema':'ROOT-native-productive-inventory-saved-reader-Source-contract-v1','author_identity':'/root','source':reader,'source_delta':rd,'current_operative_contract':cref,'operative_parent_contract':pin(P/'reader-Source-contract-v2.json'),'scope':'Same saved-only whole-byte/EOF/native20/512/once/Date/session/lossless/failure reconciliation; current productive Source capsule, response version and helper schema only. No scientific replay or semantic helper evaluation.','source_only':True,'scientific_calls':0,'scientific_acceptance':False})
ar,br=regions(a),regions(t.encode())
unchanged=[k for k in ar if k in br and ar[k]==br[k]]
assert all(ar[k]==br[k]for k in ar if k!='main')
assert a[a.index(b"if __name__ == '__main__':"):]==t.encode()[t.encode().index(b"if __name__ == '__main__':"):]
assert set(current)==set(oldC['sources']) and len(current)==17
assert {k for k in current if current[k]!=oldC['sources'][k]}=={'intake','composer','miner','inventory_cases'}
for k in ('original_model_sources','original_model_inputs','original_model_binding','inputs','limits','native_protocol','failure_protocol','case_work_limit'):assert C[k]==oldC[k]
audit=save('static-audit-v1.json',{'schema':'ROOT-native-productive-inventory-static-audit-v1','source':source,'reader':reader,'caller_edits':len(edits),'reader_edits':len(re),'unchanged_recursive_regions':unchanged,'all_existing_functions_except_main_raw_AST_exact':True,'unchanged_scientific_run_inventory':ar['main.run_inventory']==br['main.run_inventory'],'whole_forward_inverse_AST':True,'actual_patch_both_directions':True,'only_four_current_Source_roles_changed':True,'original_full_model_inputs_limits_native_and_failure_unchanged':True,'compile_without_evaluation':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
abi=dict(C['Review_ABI'],source_contract=cref)
h=save('handoff-v1.json',{'schema':'ROOT-native-productive-inventory-Source-handoff-v1','source':source,'source_contract':cref,'source_delta':sd,'reader':reader,'reader_source_contract':rc,'reader_delta':rd,'static_audit':audit,'Review_ABI':abi,'reader_Review_ABI':{'schema':'ROOT-native-productive-inventory-saved-reader-typed-Source-review-v1','scope':'ROOT-native-productive-inventory-saved-reader-Source','author_identity':'/root','source':reader,'source_contract':rc,'current_operative_contract':cref,'source_only':True,'scientific_calls':0,'scientific_acceptance':False},'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'source':source,'contract':cref,'reader':reader,'reader_contract':rc,'handoff':h,'caller_edits':len(edits),'reader_edits':len(re)},sort_keys=True))
