"""Root metadata/AST-only review and preparation for six routed engine actuals."""
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
    folder=BASE/'unit-row-routed-engine-qualification-cold-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='dbe07d4eff585af988f052d7ed08ff164c3dc65ed8cdda2bac16be981db54941'
    c=read(checked(cr));s,i=c['sources'],c['inputs'];assert len(s)==14 and len(i)==8
    for refs in(s,i,c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    raw=checked(s['intake']).read_bytes();t=ast.parse(raw)
    for ref in s.values():compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    assert literal(t,'FIXED')=={k:v for k,v in s.items()if k!='intake'}
    for name,want in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('QUALIFICATION_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases'])]:assert literal(t,name)==want
    d=read(checked(c['source_delta']));old=checked(d['parent']).read_bytes();ot=ast.parse(old)
    assert d['source']==s['intake'] and d['edit_count']==len(d['edits'])==25
    rebuilt=old;inverse=raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['patches'][0]).read_bytes())==raw
    assert patch_bytes(raw,checked(d['patches'][1]).read_bytes())==old
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
    for name in d['all17_helpers_raw_AST_exact']:
        assert segment(old,of[name])==segment(raw,nf[name])and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    on={n.name:n for n in of['main'].body if isinstance(n,ast.FunctionDef)};nn={n.name:n for n in nf['main'].body if isinstance(n,ast.FunctionDef)}
    for name in d['all20_core_nested_helpers_raw_AST_exact']:
        assert segment(old,on[name])==segment(raw,nn[name])and ast.dump(on[name],include_attributes=False)==ast.dump(nn[name],include_attributes=False)
    for name in d['whole_classes_raw_AST_exact']:
        oc=next(n for n in ot.body if isinstance(n,ast.ClassDef)and n.name==name);nc=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name==name)
        assert segment(old,oc)==segment(raw,nc)
    suffix=b'    boundary();offset=0\n';assert old[old.index(suffix):]==raw[raw.index(suffix):]
    parentc=read(checked(c['parent_source_contract']))
    for k in('inputs','original_model_sources','original_model_inputs','original_model_binding','limits'):assert c[k]==parentc[k]
    assert all(v==parentc['sources'][k]for k,v in s.items()if k not in('intake','engine','degree_router'))
    choice=pin(HERE/'ROOT-qualification-choice-v1.json');assert choice['sha256']=='0e6e7ec255a054ee72cf8d7ecde22e82e9a1384ccd4161a8b675fa92a6029950'
    module_reviews=c['engine_router_reviews']
    module_contract=read(checked(c['engine_router_contract']))
    assert all(s[k]==v for k,v in module_contract['sources'].items())
    for role,ref in module_reviews.items():
        r=read(checked(ref));assert r['sources']==module_contract['sources'] and r['source_contract']==c['engine_router_contract']
        assert r['source_review_passed'] is True and r['scientific_calls']==0 and r['source_only'] is True
    assert read(checked(module_reviews['ROOT']))['reviewer_identity']=='/root'
    assert read(checked(module_reviews['peer']))['reviewer_identity']=='/root/hilbert_ordering_diagnosis'
    peerpath=BASE/'unit-row-routed-engine-qualification-cold-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['reviewer_identity']=='/root/hilbert_ordering_diagnosis' and peer['author_identity']=='/root/hilbert_advice_controls'
    assert peer['source']==s['intake']and peer['sources']==s and peer['source_contract']==cr
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    checks=save('ROOT-qualification-raw-inverse-review-v1.json',dict(schema='ROOT-routed-engine-qualification-raw-inverse-review-v1',source=s['intake'],source_contract=cr,parent=d['parent'],exact25region_and_actualpatch_inverse=True,helpers17_core20_classes2_raw_AST_exact=True,native_final_exit_and_failure_suffix_exact=True,current14_input8_original17_input2_verified=True,new_module_reviews=module_reviews,AST_compile_only=True,scientific_calls=0))
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=checks,whole_current_Source_and_contract_read=True,
        authorship_disclosure='Root read all new family/controller regions and the whole current contract; unchanged framework joins whole-read parent ancestry through raw/AST and actual patch inverses. Controls authors this caller, arithmetic authors router/engine and diagnosis authors new independent checkers. Root owns metadata and all actuals.',
        checks=['All25 exact edits and both actual patches reconstruct whole parent/new Source;17helpers/core20/classes2/native exit/failure exact.',
            'Runtime14/input8 separate from unchanged original17/input2 epoch/full marking; both component Source reviews current and all costs charged.',
            'Exact native new/legacy routing, fresh mathematical checker then context gate; malformed proposals rejected only for expected builtin ValueError.',
            'Normal conditional search must actually show forced1/forced3/dead2 with requery after changed prototype ledger and exact owned restoration. Full saved lineage joins mandatory before MR04 qualification.',
            'Independent SINGLE/TWO genuine forced placements retain whole typed origins and refresh current occupancy; subsequent actual decisions and populated/outer restore required.',
            'Actual public cursor EOF0/1 then fresh full-keySET cover; malformed key/context inputs cannot pass. Legacy implication EOF0 remains component-only None.',
            'Empty-root actual canonical BRANCH child native-first declared interruption must return UNKNOWN with no exhausted exclusion and full root restoration.',
            'Six separate once windows/all12 essential, unchanged20/512 and no combined20, oldStageC promotion, target theorem, RL or advantage claim.'])
    rootreview=save('ROOT-qualification-caller-Source-review-v1.json',rr)
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9');assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    endpoints=[]
    for mode in('router-protocol','global-forced-dead','singleton-transfer','two-transfer','short-EOF','child-UNKNOWN'):
        purpose='unit-row-marked-aware-'+mode+'-controls';owned=HERE/('MR-'+mode+'-owned-v1');external=HERE/('MR-'+mode+'-external-v1')
        assert not owned.exists()and not external.exists()
        common=dict(invocation_id='routed-engine-qualification-'+mode+'-20261016-v1',purpose=purpose,output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rootreview,peer=pin(peerpath)),runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
        grant=save('ROOT-MR-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,all_six_endpoints_required=True,combined20_suite_claim=False,target_budget_changed=False))
        plan=save('ROOT-MR-'+mode+'-plan-v1.json',dict(common,schema='ROOT-routed-engine-qualification-plan-v1',ROOT_authorization=grant))
        endpoints.append(dict(mode=mode,plan=plan,external_directory=str(external),ordered_cases=c['API']['purpose_modes_and_ordered_cases'][purpose]))
    save('ROOT-qualification-preflight-v1.json',dict(schema='ROOT-routed-engine-qualification-preflight-v1',endpoints=endpoints,protocol_choice=choice,scientific_calls=0,new_module_reviews=module_reviews,no_combined20_claim=True,all12essential=True))
    print(json.dumps(endpoints))
if __name__=='__main__':main()
