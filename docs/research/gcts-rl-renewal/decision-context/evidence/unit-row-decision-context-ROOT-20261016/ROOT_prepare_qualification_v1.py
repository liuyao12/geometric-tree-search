"""Root metadata-only caller review and new-source prospective actual grants."""
import ast, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def read(p): return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(r):
    p=Path(r['path']); assert p.is_absolute() and p==p.resolve() and pin(p)==r
    return p
def save(name,v):
    p=HERE/name
    with p.open('x') as f: json.dump(v,f,indent=2,sort_keys=True); f.write('\n')
    return pin(p)
def literal(t,name):
    n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
    return ast.literal_eval(n.value)
def segment(b,n): return b''.join(b.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True); hunks=patch.splitlines(keepends=True); out=[]; pos=0; ix=2
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    while ix<len(hunks):
        m=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',hunks[ix]); assert m
        start=int(m[1]); count=int(m[2] or b'1'); newcount=int(m[4] or b'1'); ix+=1
        begin=start-1 if count else start; assert begin>=pos
        out.extend(lines[pos:begin]); pos=begin; used=made=0
        while ix<len(hunks) and not hunks[ix].startswith(b'@@ '):
            line=hunks[ix]; ix+=1; assert line[:1] in (b' ',b'-',b'+')
            if line[:1] in (b' ',b'-'): assert lines[pos]==line[1:]; pos+=1; used+=1
            if line[:1] in (b' ',b'+'): out.append(line[1:]); made+=1
        assert used==count and made==newcount
    out.extend(lines[pos:]); return b''.join(out)
def main():
    folder=BASE/'unit-row-decision-context-qualification-cold-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='105cc90ec4a8993410563dc1d6c9bd3fce62b5e5f0cd9696a13e229737fa26cd'
    c=read(checked(cr));s,i=c['sources'],c['inputs'];assert len(s)==14 and len(i)==8
    for refs in(s,i,c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    raw=checked(s['intake']).read_bytes();t=ast.parse(raw)
    for ref in s.values():compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    assert literal(t,'FIXED')=={k:v for k,v in s.items()if k!='intake'}
    assert literal(t,'VERSION')==c['version']=='unit-row-decision-context-qualification-cold-v1'and literal(t,'SCOPE')==c['scope']
    for name,want in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('QUALIFICATION_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases'])]:assert literal(t,name)==want
    d=read(checked(c['source_delta']));old=checked(d['parent']).read_bytes();ot=ast.parse(old)
    assert d['source']==s['intake'] and d['parent']==c['parent_source'] and d['edit_count']==len(d['edits'])==5
    rebuilt,inverse=old,raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode();assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:];inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old and patch_bytes(old,checked(d['patches'][0]).read_bytes())==raw and patch_bytes(raw,checked(d['patches'][1]).read_bytes())==old
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
    assert len(of)==18 and set(of)==set(nf)
    for name in set(of)-{'main'}:assert segment(old,of[name])==segment(raw,nf[name])and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    on={n.name:n for n in of['main'].body if isinstance(n,ast.FunctionDef)};nn={n.name:n for n in nf['main'].body if isinstance(n,ast.FunctionDef)}
    assert len(on)==34 and set(on)==set(nn)
    for name in on:assert segment(old,on[name])==segment(raw,nn[name])and ast.dump(on[name],include_attributes=False)==ast.dump(nn[name],include_attributes=False)
    oc={n.name:n for n in ot.body if isinstance(n,ast.ClassDef)};nc={n.name:n for n in t.body if isinstance(n,ast.ClassDef)};assert len(oc)==2 and set(oc)==set(nc)
    for name in oc:assert segment(old,oc[name])==segment(raw,nc[name])and ast.dump(oc[name],include_attributes=False)==ast.dump(nc[name],include_attributes=False)
    suffix=b'    boundary();offset=0\n';assert old[old.index(suffix):]==raw[raw.index(suffix):]
    parent=read(checked(c['parent_source_contract']))
    for k in('inputs','original_model_sources','original_model_inputs','original_model_binding','limits'):assert c[k]==parent[k]
    assert all(v==parent['sources'][k]for k,v in s.items()if k not in('intake','engine'))
    choice=pin(HERE/'ROOT-qualification-choice-v1.json');assert c['qualification_choice']==choice and choice['sha256']=='b62116fb90fb05266439c06ca15cf60ee186fe95196ec28c0c118625c5cb91b0'
    assert c['API']['purpose_modes_and_ordered_cases']==parent['API']['purpose_modes_and_ordered_cases']
    module_reviews=c['engine_reviews'];module_contract=read(checked(c['engine_source_contract']))
    assert all(s[k]==v for k,v in module_contract['sources'].items())
    for role,ref in module_reviews.items():
        r=read(checked(ref));assert r['sources']==module_contract['sources']and r['source_contract']==c['engine_source_contract']and r['scope']==module_contract['scope']
        assert r['source_review_passed']is r['source_only']is True and r['scientific_calls']==0 and r['scientific_acceptance']is False
    assert read(checked(module_reviews['ROOT']))['reviewer_identity']=='/root'and read(checked(module_reviews['peer']))['reviewer_identity']=='/root/hilbert_ordering_diagnosis'
    peerpath=BASE/'unit-row-decision-context-qualification-cold-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['reviewer_identity']=='/root/hilbert_ordering_diagnosis'and peer['author_identity']=='/root/hilbert_advice_controls'
    assert peer['source']==s['intake']and peer['sources']==s and peer['source_contract']==cr and peer['scope']==c['scope']
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    checks=save('ROOT-qualification-raw-inverse-review-v1.json',dict(schema='ROOT-decision-context-qualification-raw-inverse-review-v1',source=s['intake'],source_contract=cr,parent=d['parent'],exact5region_and_actualpatch_inverse=True,helpers17_nested34_classes2_raw_AST_exact=True,native_final_exit_and_failure_suffix_exact=True,current14_input8_original17_input2_verified=True,new_module_reviews=module_reviews,AST_compile_only=True,scientific_calls=0))
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=checks,whole_current_Source_and_contract_read=True,
        authorship_disclosure='Root read all5 literal edits and whole current contract; all unchanged cold functions/families/framework/output/native/failure regions join previously whole-read38f8 through independently verified full raw/AST and actual patch inverses. Engine13 full changed Source/contract independently reviewed by Root and diagnosis. Root owns metadata and all actuals.',
        checks=['Only caller VERSION/SCOPE, engine13 capsule, contract schema and engine VERSION gate differ;17 top helpers/all34 direct nested helpers and2 classes raw/AST exact.',
        'Current14/input8 separate from unchanged original17/input2 epoch/full marking. Both component currentSource reviews and all original costs/native limits charged.',
        'Same6 purposes/all12 original essentials and scientific family bodies, fixture seeds/assertions, ordinary global decisions and canonical fallback path preserved. No supplied proofword/branch route or altered universe.',
        'Whole origin/native receipts/current packet refresh, genuine EOF+fresh full survivor keySET, actual search lineage and checkpoint restoration still required by saved closure.',
        'Normal Source/lifecycle context scope only; no deliberate livecontext/hostile reentrancy/ABA or extra postrollback decision claimed.',
        'All6 separate20/512 windows; no inherited acceptance, unchangedfailedrerun, combined20, oldStageC promotion, target theorem, RL or advantage claim.'])
    rootreview=save('ROOT-qualification-caller-Source-review-v1.json',rr)
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9');assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    endpoints=[]
    for mode in('router-protocol','global-forced-dead','singleton-transfer','two-transfer','short-EOF','child-UNKNOWN'):
        purpose='unit-row-marked-aware-'+mode+'-controls';owned=HERE/('MR-'+mode+'-owned-v1');external=HERE/('MR-'+mode+'-external-v1')
        assert not owned.exists()and not external.exists()
        common=dict(invocation_id='decision-context-qualification-'+mode+'-20261016-v1',purpose=purpose,output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rootreview,peer=pin(peerpath)),runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
        grant=save('ROOT-MR-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,all_six_endpoints_required=True,combined20_suite_claim=False,target_budget_changed=False))
        plan=save('ROOT-MR-'+mode+'-plan-v1.json',dict(common,schema='ROOT-routed-engine-qualification-plan-v1',ROOT_authorization=grant))
        endpoints.append(dict(mode=mode,plan=plan,external_directory=str(external),ordered_cases=c['API']['purpose_modes_and_ordered_cases'][purpose]))
    save('ROOT-qualification-preflight-v1.json',dict(schema='ROOT-decision-context-qualification-preflight-v1',endpoints=endpoints,protocol_choice=choice,scientific_calls=0,new_module_reviews=module_reviews,no_combined20_claim=True,all12essential=True))
    print(json.dumps(endpoints))
if __name__=='__main__':main()
