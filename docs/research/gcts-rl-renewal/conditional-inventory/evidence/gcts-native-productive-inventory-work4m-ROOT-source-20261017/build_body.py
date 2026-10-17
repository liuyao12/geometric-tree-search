composer_packet=Path('/private/tmp/gcts-native-component-composer-work4m-source-20261017/handoff-v3.json')
case_packet=Path('/private/tmp/gcts-native-productive-inventory-cases-work4m-source-20261017/handoff-v4.json')
ch=json.loads(raw(composer_packet));kh=json.loads(raw(case_packet))
for h in (ch,kh):
    assert pin(Path(h['source']['path']))==h['source']
    assert json.loads(raw(h['source_contract']['path']))['source']==h['source']
parent=P/'native_productive_inventory_cold_v1.py';a=raw(parent)
assert hashlib.sha256(a).hexdigest()=='978327235f539b4749ecb2ffbd9c376e7ae178576ccae02da8034c696fac95f9'
oldC=json.loads(raw(P/'Source-contract-v1.json'));current=dict(oldC['sources'])
current['composer']=ch['source'];current['inventory_cases']=kh['source']
t=a.decode();edits=[]
t=mutate(t,edits,'own_VERSION',"VERSION='ROOT-native-productive-inventory-cold-v1'",'VERSION='+repr(V))
old_fixed=next(line for line in t.splitlines()if line.startswith('FIXED='))
t=mutate(t,edits,'current_two_helper_refs',old_fixed,'FIXED='+repr({k:v for k,v in current.items()if k!='intake'}))
source=textfile('native_productive_inventory_cold_v2.py',t);compile(t,source['path'],'exec',dont_inherit=True)
current['intake']=source;sd=delta('caller',parent,Path(source['path']),edits)
C=copy.deepcopy(oldC)
C.update(version=V,source=source,sources=current,parent_source=pin(parent),operative_parent_contract=pin(P/'Source-contract-v1.json'),source_delta=sd)
C['allocation']['composer_own_work']=4000000
C['helper_contracts']['composer']=ch['source_contract'];C['helper_contracts']['inventory_cases']=kh['source_contract']
C['author_provenance']='Root authors work4m cold/saved-reader rebinding. Controls authors two literal composer and three literal CASE budget/version edits. Distinct whole current Source reviews required. No previous actual qualification inherited.'
C['scope_statement']='Own construction work allowance changes1m to4m only; CASE8m/depth128, original root48/ext96/head1/quantum8/two-slot proposal allocation, miner3 interface catalogue, original Source17/input2 model epoch and current17/input8 authority, native20/512/once/CodeSeal/guards/phase/transport/failure remain fixed. Longer prefix is not availability, useful transfer, proof, global graph, RL or speedup evidence.'
C['budget_ablation']={'parent_composer_own_work':1000000,'composer_own_work':4000000,'case_own_work':8000000,'native_positive_seconds':20,'other_allocations_unchanged':True,'scientific_qualification_inherited':False}
C['Review_ABI']=dict(oldC['Review_ABI'],source=source,sources=current,source_contract='current capsule')
cref=save('Source-contract-v2.json',C)
rparent=P/'ROOT_read_native_productive_inventory_saved_v1.py';ra=raw(rparent);rt=ra.decode();re=[]
oldline=next(line for line in rt.splitlines()if line.startswith('CURRENT_CONTRACT = '))
rt=mutate(rt,re,'operative_capsule',oldline,'CURRENT_CONTRACT = '+repr(cref))
rt=mutate(rt,re,'response_VERSION',"body['version']=='ROOT-native-productive-inventory-cold-v1'","body['version']=="+repr(V))
reader=textfile('ROOT_read_native_productive_inventory_saved_v2.py',rt);compile(rt,reader['path'],'exec',dont_inherit=True)
rd=delta('reader',rparent,Path(reader['path']),re)
rc=save('reader-Source-contract-v2.json',{'schema':'ROOT-native-productive-inventory-saved-reader-Source-contract-v1','author_identity':'/root','source':reader,'source_delta':rd,'current_operative_contract':cref,'operative_parent_contract':pin(P/'reader-Source-contract-v1.json'),'scope':'Same complete saved-only native/wire/phase/failure reconciliation, with current own-work4m Source capsule/responseVERSION. No scientific replay or inherited qualification.','source_only':True,'scientific_calls':0,'scientific_acceptance':False})
ar,br=regions(a),regions(t.encode());assert ar==br
assert set(current)==set(oldC['sources']) and len(current)==17
assert {k for k in current if current[k]!=oldC['sources'][k]}=={'intake','composer','inventory_cases'}
for k in ('original_model_sources','original_model_inputs','original_model_binding','inputs','limits','native_protocol','failure_protocol','case_work_limit','phase_protocol','purpose','artifact_API'):assert C[k]==oldC[k]
audit=save('static-audit-v2.json',{'schema':'ROOT-native-productive-inventory-work4m-static-audit-v2','source':source,'reader':reader,'caller_edits':len(edits),'reader_edits':len(re),'all_caller_function_class_regions_raw_AST_exact':True,'whole_forward_inverse_AST':True,'actual_patch_both_directions':True,'only_three_current_Source_roles_changed':True,'original_full_model_inputs_native_limits_and_case_limit_unchanged':True,'compile_without_evaluation':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
h=save('handoff-v2.json',{'schema':'ROOT-native-productive-inventory-Source-handoff-v2','source':source,'source_contract':cref,'source_delta':sd,'reader':reader,'reader_source_contract':rc,'reader_delta':rd,'static_audit':audit,'Review_ABI':dict(C['Review_ABI'],source_contract=cref),'reader_Review_ABI':{'schema':'ROOT-native-productive-inventory-saved-reader-typed-Source-review-v1','scope':'ROOT-native-productive-inventory-saved-reader-Source','author_identity':'/root','source':reader,'source_contract':rc,'current_operative_contract':cref,'source_only':True,'scientific_calls':0,'scientific_acceptance':False},'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'source':source,'contract':cref,'reader':reader,'reader_contract':rc,'handoff':h,'caller_edits':len(edits),'reader_edits':len(re)},sort_keys=True))
