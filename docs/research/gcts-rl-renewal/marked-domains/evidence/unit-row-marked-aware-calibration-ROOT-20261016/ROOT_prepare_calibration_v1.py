"""Root metadata/AST-only preparation for one batched MAIN actual."""
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
    folder=BASE/'unit-row-marked-aware-calibration-cold-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='d5a0467432caaf18cba837b1bd72c83eeefd80c2763b64641786af34b26fb773'
    c=read(checked(cr));s,i=c['sources'],c['inputs'];assert len(s)==13 and len(i)==8
    for refs in(s,i,c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    raw=checked(s['intake']).read_bytes();t=ast.parse(raw)
    for ref in s.values():compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    assert literal(t,'FIXED')=={k:v for k,v in s.items()if k!='intake'}
    for name,want in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('CALIBRATION_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases'])]:assert literal(t,name)==want
    d=read(checked(c['source_delta']));old=checked(d['parent']).read_bytes();ot=ast.parse(old)
    assert d['source']==s['intake'] and d['edit_count']==len(d['edits'])==19
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
    assert all(v==parentc['sources'][k]for k,v in s.items()if k not in('intake','marked_aware_proposer','marked_aware_checker'))
    choice=pin(HERE/'ROOT-calibration-choice-v1.json');assert choice['sha256']=='3bcef5ab2f0dd4e472dcf5e8a1955d47ddd62260a0d8dcef98c410b3f690cf8d'
    module_reviews={}
    for role,peerfolder,reviewer in[('proposer','unit-row-marked-aware-fibre-proposer-independent-source-20261016','/root/hilbert_ordering_diagnosis'),('checker','unit-row-marked-aware-fibre-checker-independent-source-20261016','/root/hilbert_advice_controls')]:
        rp=HERE/('ROOT-'+role+'-Source-review-v1.json');pp=BASE/peerfolder/'typed-Source-review-v1.json'
        for q in(rp,pp):
            r=read(q);assert r['source']==s['marked_aware_'+role] and r['source_review_passed']is True and r['scientific_calls']==0 and r['source_only']is True
        assert read(pp)['reviewer_identity']==reviewer
        module_reviews[role]=dict(ROOT=pin(rp),peer=pin(pp))
    peerpath=BASE/'unit-row-marked-aware-calibration-cold-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source']==s['intake']and peer['sources']==s and peer['source_contract']==cr
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    checks=save('ROOT-calibration-raw-inverse-review-v1.json',dict(schema='ROOT-marked-aware-calibration-raw-inverse-review-v1',source=s['intake'],source_contract=cr,parent=d['parent'],exact19region_and_actualpatch_inverse=True,helpers17_core20_classes2_raw_AST_exact=True,native_final_exit_and_failure_suffix_exact=True,current13_input8_original17_input2_verified=True,new_module_reviews=module_reviews,AST_compile_only=True,scientific_calls=0))
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=checks,whole_current_Source_and_contract_read=True,
        authorship_disclosure='Root read every new region and whole current contract; raw/AST identical framework retains previous whole-read ancestry. Root authors metadata and owns actuals, not this scientific caller. Both new module Source reviews are separately pinned; no unrelated second kernel claim.',
        checks=['All19 exactbyte edits and both patches reconstruct entire parent/new caller;17helpers/core20/classes2/native exit failure exact.','Source13/input8 separately from unchanged original17/input2 epoch and full marking; all setup and output charged.','ZERO oldC1, SINGLETON oldC4 and TWO separately ownedC42 state invoke new proposer and fresh independent checker, no old degree/cursor/engine querying or receipt substitution.','ZERO/ONE full independent census, TWO full distinct current packets and lower bound only; exact pending reads never installed facts.','Three mutated full proposals rejected only by exact invalid-dataValueError; timeouts/guard/resource errors cannot pass.','Four fresh grants/endpoints, original sixlimits, all6 essential; no combined20, oldStageC promotion, target/RL/fullGCTS/speedup claim.'])
    rootreview=save('ROOT-calibration-caller-Source-review-v1.json',rr)
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9');assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    endpoints=[]
    for mode in('zero','singleton','two','negative-protocol'):
        purpose='unit-row-marked-aware-calibration-'+mode;owned=HERE/('MA-'+mode+'-owned-v1');external=HERE/('MA-'+mode+'-external-v1')
        assert not owned.exists()and not external.exists()
        common=dict(invocation_id='marked-aware-calibration-'+mode+'-20261016-v1',purpose=purpose,output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rootreview,peer=pin(peerpath)),runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
        grant=save('ROOT-MA-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-marked-aware-calibration-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,all_four_endpoints_required=True,combined20_suite_claim=False,target_budget_changed=False))
        plan=save('ROOT-MA-'+mode+'-plan-v1.json',dict(common,schema='ROOT-marked-aware-calibration-plan-v1',ROOT_authorization=grant))
        endpoints.append(dict(mode=mode,plan=plan,external_directory=str(external),ordered_cases=c['API']['purpose_modes_and_ordered_cases'][purpose]))
    save('ROOT-calibration-preflight-v1.json',dict(schema='ROOT-marked-aware-calibration-preflight-v1',endpoints=endpoints,protocol_choice=choice,scientific_calls=0,new_module_reviews=module_reviews,no_combined20_claim=True,all6essential=True))
    print(json.dumps(endpoints))
if __name__=='__main__':main()
