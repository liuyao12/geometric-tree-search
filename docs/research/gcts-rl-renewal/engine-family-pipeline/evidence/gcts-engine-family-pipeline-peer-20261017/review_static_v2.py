"""Source bytes/AST/literal metadata only; no reviewed module execution."""
from pathlib import Path
import ast
import hashlib
import json
import re
A=Path('/private/tmp/gcts-engine-family-pipeline-source-20261017')
D=Path('/private/tmp/gcts-engine-family-pipeline-peer-20261017')
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
    p=D/n
    with p.open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
    return pin(p)
def literal(n):
    if isinstance(n,ast.Constant):return n.value
    if isinstance(n,(ast.List,ast.Tuple,ast.Set)):
        v=[literal(x) for x in n.elts]
        return v if isinstance(n,ast.List) else tuple(v) if isinstance(n,ast.Tuple) else set(v)
    if isinstance(n,ast.Dict):return {literal(k):literal(v) for k,v in zip(n.keys,n.values)}
    raise ValueError(type(n).__name__)
def constants(tr):
    return {n.targets[0].id:n for n in tr.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
def regions(raw):
    tr=ast.parse(raw);lines=raw.decode().splitlines(True);out={}
    def walk(n,prefix):
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch,(ast.FunctionDef,ast.ClassDef)):
                key=prefix+ch.name;out[key]=(''.join(lines[ch.lineno-1:ch.end_lineno]),ast.dump(ch,include_attributes=False));walk(ch,key+'.')
            else:walk(ch,prefix)
    walk(tr,'');return tr,out
def patch(raw,path):
    rows=raw.decode().splitlines(True);p=path.read_text().splitlines(True);out=[];cur=0;k=2
    assert p[0].startswith('--- ') and p[1].startswith('+++ ')
    while k<len(p):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',p[k]);assert m
        usedn=int(m[2] or '1');maden=int(m[4] or '1');start=int(m[1])-1+(usedn==0)
        assert start>=cur;out.extend(rows[cur:start]);cur=start;k+=1;used=made=0
        while k<len(p) and not p[k].startswith('@@'):
            line=p[k];assert line[0] in ' +-'
            if line[0] in ' -':assert rows[cur]==line[1:];cur+=1;used+=1
            if line[0] in ' +':out.append(line[1:]);made+=1
            k+=1
        assert used==usedn and made==maden
    out.extend(rows[cur:]);return ''.join(out).encode()
h=json.loads((A/'handoff-v2.json').read_bytes());c=json.loads((A/'Source-contract-v2.json').read_bytes());c1=json.loads((A/'Source-contract-v1.json').read_bytes());delta=json.loads((A/'Source-delta-v1.json').read_bytes())
assert pin(A/'Source-contract-v2.json')['sha256']=='e637176c9cf7ffd0ce7a71cc5e8bcdacd0536f694797547f8d9d1ad649a06370'
assert pin(A/'handoff-v2.json')['sha256']=='7693fd761c2e7eb41c38463ac53b67cf526088cb2d250308b01bb58d58c32cd2'
refs={}
def verify(p):
    assert pin(p['path'])==p;refs[p['path']]=p
for p in [h['source'],h['case_source'],h['source_contract'],h['source_delta'],h['parent_source'],c['preserved_negative_contract'],pin(A/'handoff-v1.json'),pin(A/'handoff-v2.json')]:verify(p)
for p in delta['actual_patches'].values():verify(p)
for p in c['current_component_contracts'].values():verify(p)
assert c['source']==h['source']==c['Review_ABI']['source'] and c['sources']==h['sources']==c['Review_ABI']['sources']
assert h['case_source']==c['sources']['pipeline_cases'] and c['parent_source']==delta['parent']==h['parent_source']
parent=Path(delta['parent']['path']).read_bytes();current=Path(c['source']['path']).read_bytes();case=Path(h['case_source']['path']).read_bytes()
assert delta['edit_count']==len(delta['edits'])==12
forward=parent.decode()
for e in delta['edits']:
    i=e['start'];assert forward[i:i+len(e['old'])]==e['old'];forward=forward[:i]+e['new']+forward[i+len(e['old']):]
assert forward.encode()==current
inverse=current.decode()
for e in reversed(delta['edits']):
    i=e['start'];assert inverse[i:i+len(e['new'])]==e['new'];inverse=inverse[:i]+e['old']+inverse[i+len(e['new']):]
assert inverse.encode()==parent
assert patch(parent,A/'caller-forward.patch')==current and patch(current,A/'caller-full-inverse.patch')==parent
ta,ra=regions(parent);tb,rb=regions(current);tc,rc=regions(case)
assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ta,include_attributes=False)
common=set(ra)&set(rb);exact=sorted(k for k in common if ra[k]==rb[k]);changed=sorted(k for k in common if ra[k]!=rb[k])
assert changed==['main'] and set(rb)-set(ra)=={'main.run_pipeline'} and set(ra)-set(rb)=={'main.run_component'}
assert current[current.index(b"if __name__ == '__main__':"):]==parent[parent.index(b"if __name__ == '__main__':"):]
ca,cb=constants(ta),constants(tb)
for k in ('LIMITS','ORIGINAL_SOURCES','ORIGINAL_INPUTS','ORIGINAL_BINDING'):
    assert ast.dump(ca[k],include_attributes=False)==ast.dump(cb[k],include_attributes=False)
for k,field in [('FIXED_INPUTS','inputs'),('LIMITS','limits'),('ORIGINAL_SOURCES','original_model_sources'),('ORIGINAL_INPUTS','original_model_inputs'),('ORIGINAL_BINDING','original_model_binding')]:assert literal(cb[k].value)==c[field]
old_inputs=dict(literal(ca['FIXED_INPUTS'].value));old_inputs.pop('family_descriptor');assert old_inputs==c['inputs'] and len(old_inputs)==8
fixed=literal(cb['FIXED'].value);expected=dict(fixed);expected['intake']=c['source'];assert expected==c['sources'] and len(expected)==22
assert 'family_descriptor' not in c['inputs'] and 'component_cases' not in fixed
assert fixed['engine']['sha256']=='40adc4fef7d5930ad49100149c1ca6390b1894f88c52f6fb38d97d914b00ce10' and fixed['marked_adapter']['sha256']=='a1971d01cc1291af4b5508c81e3ef06bec17ee794d0a5d95b102d730ce0a3f7c'
cases=literal(cb['QUALIFICATION_CASES_BY_PURPOSE'].value);assert cases=={c['purpose']:c['expected_cases']} and len(c['expected_cases'])==1
assert literal(cb['VERSION'].value)==c['version']
for field in ('result_schema','payload_schema','response_schema','final_schema'):
    assert c['artifact_API'][field] in current.decode()
assert "'"+c['artifact_API']['payload_field']+"':payload" in current.decode()
case_constants=constants(tc);assert literal(case_constants['CASE'].value)==c['expected_cases'][0]
assert "state['selected'] == [] and state['excluded'] == []" in case.decode()
assert "state=marked.initial_state(language,tick)" in current.decode()
assert all(x in case.decode() for x in ("'native_first_capture': True",'len(captured[\'selected\']) == 1',"canonical(selected_key) == canonical(placements[0]['key'])",'first.search()',"decision = fresh.decision()",'consumer.consume_preferences','collector.collect_derivation','miner.mine_families','provider.build_family_batch'))
assert '.place(' not in case.decode() and not re.search(r'\._(?:observed|certs)\b',case.decode())
assert all(x in case.decode() for x in ("limits={'cuts': 1, 'members': 1, 'families': 1}","if decision['kind'] != 'BRANCH':", "if consumed['status'] != 'READY':", "result['status'] = 'CHECKED_FRESH_BRANCH_PREFERENCE'"))
for key in ('state_collector','family_miner','family_provider','family_consumer'):
    verify(c['sources'][key])
collector=json.loads(Path(c['current_component_contracts']['collector']['path']).read_bytes());provider=json.loads(Path(c['current_component_contracts']['provider']['path']).read_bytes())
assert c['sources']['state_collector']==collector['source'] and c['sources']['family_provider']==provider['source']
checks=['whole_frozen_caller_case_and_corrected_contract_read','all12_sequential_forward_inverse_exact','both_actual_unified_patch_directions_exact','whole_AST_inverse_exact','all_unchanged_helpers_native_failure_transport_guard_suffix_exact','only_main_and_owned_pipeline_shim_changed','current22_input8_original17_input2_binding_limits_exact','no_human_descriptor_input_or_componentcase_import','actual_empty_initial_pointstate_and_excluded_arrays','nativefirst_actual_capture_fullstate_TRY_PLACE_key_rootrestore_join','collector2_miner_literal_source_provider_consumer_ABIs','one_language_cumulative_tick_unchanged20_512_cost','actual_fresh_global_BRANCHand_noneplacement_preference','allUNKNOWNpaths_no_negative_or_theorem_promotion','fullrecords_untrimmed_bounded_transport_response_stdout','currentcontract_artifact_purpose_cases_VERSION_ABI_matches_source','V1_stale_operative_contract_preserved_negative','no_scientific_eval_test_clock_result_or_actual_byreviewer']
print(json.dumps(put('independent-static-v2.json',{'schema':'ROOT-engine-family-pipeline-independent-static-v2','source':c['source'],'case_source':h['case_source'],'source_contract':h['source_contract'],'raw_refs':list(refs.values()),'checks':checks,'check_count':len(checks),'edit_count':12,'raw_forward_inverse_and_AST_inverse_exact':True,'both_actual_patch_directions_exact':True,'raw_AST_exact_regions':exact,'changed_common_regions':changed,'added_regions':['main.run_pipeline'],'removed_regions':['main.run_component'],'current22map_exact':True,'input8_original17_input2_binding_limits_exact':True,'case_count':1,'scientific_calls':0,'source_only':True,'scientific_acceptance':False,'models_evaluated':0,'tests_run':0,'clocks_called':0,'actual_or_result_reads':0})))
