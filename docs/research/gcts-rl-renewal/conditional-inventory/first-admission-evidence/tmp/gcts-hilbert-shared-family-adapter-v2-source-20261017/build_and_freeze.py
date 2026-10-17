from pathlib import Path
import ast,json,hashlib,difflib,subprocess
A=Path('/private/tmp/gcts-hilbert-shared-family-adapter-source-20261017');D=Path('/private/tmp/gcts-hilbert-shared-family-adapter-v2-source-20261017')
oldpath=A/'hilbert_shared_family_admission_adapter_v1.py';old=oldpath.read_text();new=old.replace("VERSION = 'hilbert-shared-parametric-family-native-admission-adapter-v1'","VERSION = 'hilbert-shared-parametric-family-native-admission-adapter-v2-unknown-prefix'",1)
a="""    require(checked['schema'] == CHECK_SCHEMA and checked['version'] == CHECKER_VERSION
            and canonical(checked['request']) == canonical(expected_request), 'fresh whole independent conditional-check request')"""
b="""    require(checked['schema'] == CHECK_SCHEMA and checked['version'] == CHECKER_VERSION
            and type(checked['status']) is str and checked['status'] in ('UNKNOWN','CONDITIONAL_EXPANSION_CHECKED'),
            'fresh independent conditional-check schema/version/status')"""
assert new.count(a)==1;new=new.replace(a,b)
a="""    if checked['status'] == 'UNKNOWN':
        require(checked['conditional_expansion_checked'] is False and checked['expansion'] is None,"""
b="""    if checked['status'] == 'UNKNOWN':
        # Pinned checker4358 assigns its initial request only after the whole
        # five-field copy, then adds proposal only after that copy completes.
        # Own-limit UNKNOWN can therefore retain None, five or all six fields.
        prefix = checked['request']
        if prefix is not None:
            prefix_fields = set(expected_request) - {'proposal'}
            require(type(prefix) is dict and set(prefix) in (prefix_fields,set(expected_request))
                    and canonical(prefix) == canonical({key:expected_request[key]for key in prefix}),
                    'exact completed checker request prefix on unaccepted UNKNOWN')
        require(checked['conditional_expansion_checked'] is False and checked['expansion'] is None,"""
assert new.count(a)==1;new=new.replace(a,b)
a="""    require(checked['status'] == 'CONDITIONAL_EXPANSION_CHECKED' and checked['conditional_expansion_checked'] is True,
            'complete independent conditional expansion only')"""
b="""    require(checked['status'] == 'CONDITIONAL_EXPANSION_CHECKED' and checked['conditional_expansion_checked'] is True
            and canonical(checked['request']) == canonical(expected_request),
            'complete independent conditional expansion with the whole exact request')"""
assert new.count(a)==1;new=new.replace(a,b)
p=D/'hilbert_shared_family_admission_adapter_v2.py';p.write_text(new);ast.parse(new);compile(new,str(p),'exec')
def ref(p):
 p=Path(p);v=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)}
def put(n,v):
 p=D/n
 with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
edits=[]
for tag,i,j,k,l in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
 if tag!='equal':edits.append({'old_start':i,'old_end':j,'new_start':k,'new_end':l,'before':old[i:j],'after':new[k:l]})
f=old
for e in reversed(edits):f=f[:e['old_start']]+e['after']+f[e['old_end']:]
assert f==new
r=new
for e in reversed(edits):r=r[:e['new_start']]+e['before']+r[e['new_end']:]
assert r==old and ast.dump(ast.parse(r),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
patches={}
for direction,left,right in [('forward',old,new),('inverse',new,old)]:
 pp=D/('adapter-v1-to-v2-'+direction+'.patch');pp.write_text(''.join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile='target.py',tofile='target.py')))
 work=D/('patch-audit-'+direction);work.mkdir();(work/'target.py').write_text(left)
 x=subprocess.run(['patch','--batch','--fuzz=0','-p0','-i',str(pp)],cwd=work,capture_output=True,text=True)
 assert x.returncode==0 and (work/'target.py').read_text()==right
 patches[direction]=ref(pp)
def regions(text):
 lines=text.splitlines(keepends=True)
 return {n.name:(''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False))for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
o,n=regions(old),regions(new);same=[k for k in o if o[k]==n[k]]
assert set(same)==set(o)-{'adapt_expansion'}
source=ref(p)
delta=put('Source-delta-v2.json',{'schema':'Hilbert-shared-family-native-adapter-raw-delta-v2','source_only':True,'parent':ref(oldpath),'source':source,'edits':edits,'forward_patch':patches['forward'],'inverse_patch':patches['inverse'],'full_raw_forward_inverse':True,'whole_AST_inverse':True,'actual_patch_F0_directions':2,'raw_AST_exact_regions':same})
audit=put('static-audit-v2.json',{'schema':'Hilbert-shared-family-native-adapter-static-audit-v2','source_only':True,'scientific_calls':0,'module_evaluations':0,'compile_without_evaluation':True,'raw_AST_exact_regions':same,'describe_host_unchanged':True,'all_native_point_loops_unchanged':True,'current_scope':'Only own VERSION plus schema/status dispatch, exact UNKNOWN request prefixes and full success request join. No new catch, no modified native/checker function, no semantic/resource/census change.','raw_edit_count':len(edits),'actual_patch_F0_directions':2,'full_raw_AST_inverse':True})
api=json.loads((A/'API-wire-v1.json').read_text());api['VERSION']='hilbert-shared-parametric-family-native-admission-adapter-v2-unknown-prefix';api['schema']='Hilbert-shared-family-native-adapter-API-v2';api['result']['UNKNOWN']='Independent checker own-limit UNKNOWN only: request may be None, exact completed five-field initial copy without proposal, or exact complete six-field request. expansionNone/checkedFalse required; no partial expansion/member/union accepted. Callback/native errors still propagate.'
api['parent_API']=ref(A/'API-wire-v1.json');ar=put('API-wire-v2.json',api)
c=json.loads((A/'Source-contract-v2.json').read_text());c.update(schema='Hilbert-shared-family-native-adapter-Source-contract-v2',source=source,sources={'hilbert_native_adapter':source},API=ar,delta=delta,static_audit=audit,parent_source=ref(oldpath),parent_contract=ref(A/'Source-contract-v2.json'),preserved_negative=ref('/private/tmp/gcts-hilbert-shared-family-adapter-peer-20261017/typed-Source-review-v1.json'),correction='Exact pinned4358 own-limit UNKNOWN request-prefix compatibility; complete success still requires all six fields. Native/tick failures unchanged and not converted to UNKNOWN.')
c.pop('metadata_revision',None);c.pop('preserved_prior_contract',None);c.pop('metadata_correction',None)
c['Review_ABI'].update(schema='Hilbert-shared-family-native-adapter-typed-Source-review-v2',source=source,sources={'hilbert_native_adapter':source})
cr=put('Source-contract-v2.json',c)
h=put('handoff-v2.json',{'schema':'Hilbert-shared-family-native-adapter-handoff-v2','source_only':True,'scientific_calls':0,'module_evaluations':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':source,'source_contract':cr,'API':ar,'delta':delta,'static_audit':audit,'preserved_negative':c['preserved_negative'],'Review_ABI':c['Review_ABI']})
print(json.dumps({'handoff':h,'contract':cr,'source':source,'API':ar,'delta':delta,'audit':audit,'raw_edit_count':len(edits),'exact_regions':same},indent=2))
