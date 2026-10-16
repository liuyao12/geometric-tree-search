"""Root metadata-only saved helper successor review; no semantic replay."""
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
    folder=BASE/'unit-row-decision-context-qualification-saved-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='81f6353a6c9aa6b931516d4f6c9faf8698e942d55737b8c294944a7af78faac6'
    c=read(checked(cr));parent=read(checked(c['parent_source_contract']));d=read(checked(c['source_delta']))
    assert c['parent_helpers']==parent['sources']
    findings={}
    for role,count in(('decoder',1),('closer',7)):
        v=d['helpers'][role];assert v['parent']==c['parent_helpers'][role]and v['source']==c['sources'][role]and len(v['edits'])==count
        old=checked(v['parent']).read_bytes();raw=checked(v['source']).read_bytes();forward,inverse=old,raw
        for e in reversed(v['edits']):
            a,b=e['old'].encode(),e['new'].encode();assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
            forward=forward[:e['old_start']]+b+forward[e['old_end']:];inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
        assert forward==raw and inverse==old
        assert patch_bytes(old,checked(v['actual_unified_patches']['forward']).read_bytes())==raw
        assert patch_bytes(raw,checked(v['actual_unified_patches']['inverse']).read_bytes())==old
        ot,nt=ast.parse(old),ast.parse(raw);compile(nt,v['source']['path'],'exec')
        assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ot,include_attributes=False)
        of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
        assert set(of)==set(nf)and len(of)==(9 if role=='decoder'else 24)
        for name in d['function_preservation'][role]['unchanged_raw_AST']:
            assert segment(old,of[name])==segment(raw,nf[name])and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
        if role=='closer':
            assert literal(nt,'EXPECTED_CONTRACT')==c['caller_source_contract']and literal(nt,'ENGINE_VERSION')=='lazy-unit-row-global-engine-v13-decision-local-checked-state'
            stores=[n for n in ast.walk(nt)if isinstance(n,ast.Name)and isinstance(n.ctx,ast.Store)and n.id=='expected_cases'];assert len(stores)==1
            assert 'expected_proposal' in raw.decode()and c['API']['purpose_modes_and_ordered_cases']==parent['API']['purpose_modes_and_ordered_cases']
        findings[role]=dict(source=v['source'],parent=v['parent'],exact_raw_and_AST_inverse=True,actual_forward_and_inverse_patches=True,edit_count=count)
    cold=read(checked(c['caller_source_contract']));assert c['current_sources']==cold['sources']and c['inputs']==cold['inputs']and c['caller_source']==cold['source']
    for k in('inputs','original_model_sources','original_model_inputs','original_model_binding','limits'):assert c[k]==parent[k]==cold[k]
    assert all(v==parent['current_sources'][k]for k,v in c['current_sources'].items()if k not in('engine','intake'))
    for refs in(c['current_sources'],c['inputs'],c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    peerpath=BASE/'unit-row-decision-context-qualification-saved-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['source_contract']==cr and peer['sources']==c['sources']and peer['scope']==c['scope']
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls'and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_only=True,source_review_passed=True,scientific_calls=0,scientific_acceptance=False,helpers_executed=False,concrete_blockers=[],peer_review=pin(peerpath),raw_inverse_findings=findings,
        review_scope='Root read whole current contract and entire1+7 changed helper regions; raw+AST and actual patch inverses join the whole-read corrected V3 helper ancestry. Root separately rechecked declared-case/negative-proposal/final count flow, route/version and current Source authority. No model/proof replay.',
        findings=['Only fixed current cold contract/source/SCOPE/VERSION and engine13 VERSION authorities change. All native20/512/once/wait4/reaped/Date/session/full wire/canonical zlib flags and case-record joins preserved.',
        'One immutable expected_cases tuple binding; final list/count lineage preserved. Negative expected_proposal remains isolated; aggregate still requires all12 across six distinct current plans. No inherited acceptance.',
        'Complete native origin/state/census/transfers/current read occupancy/whole packet/cursor+fresh-keySET/search trace/owned restoration joins remain literal saved concordance. None is a fresh mathematical check outside measured actual.',
        'Failure mode is opaque native-only administrative closure, null reported/passed/skipped counts,0qualified,2unqualified, no failed output decode or inferred moves. Full engine remains false on any required failure.',
        'Current14/input8 distinct from exact original17/input2 binding. No target proof, learned marking/RL, universal palette, fullGCTS, speedup or hostile context robustness accepted.'])
    review=save('ROOT-saved-helper-Source-review-v1.json',rr);copies={}
    for role,ref in c['sources'].items():
        src=checked(ref);dest=HERE/src.name
        with dest.open('xb')as f:f.write(src.read_bytes())
        assert pin(dest)['sha256']==ref['sha256']and pin(dest)['bytes']==ref['bytes'];copies[role]=pin(dest)
    print(json.dumps(dict(review=review,copied_helpers=copies,scientific_calls=0)))
if __name__=='__main__':main()
