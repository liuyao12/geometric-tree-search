"""Root metadata/AST-only whole saved-helper review; no science."""
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
def inverse(d):
    raw=checked(d['source']).read_bytes();old=checked(d['parent']).read_bytes()
    forward,inverse=old,raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        forward=forward[:e['old_start']]+b+forward[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert forward==raw and inverse==old and len(d['edits'])==d['edit_count']
    assert patch_bytes(old,checked(d['patches'][0]).read_bytes())==raw
    assert patch_bytes(raw,checked(d['patches'][1]).read_bytes())==old
    compile(ast.parse(raw),d['source']['path'],'exec')
    return dict(parent=d['parent'],source=d['source'],edit_count=d['edit_count'],exact_region_and_actual_patch_inverses=True)
def main():
    folder=BASE/'unit-row-routed-engine-qualification-saved-source-20261016'
    cr=pin(folder/'Source-contract-v2.json');assert cr['sha256']=='042c356a7541e5ad1ce1c335c11600afc853a03fc0a3eee10ebb946fb423d6e2'
    c=read(checked(cr));v1=read(checked(c['preserved_v1_contract']));d1=read(checked(v1['source_delta']));d2=read(checked(c['source_delta']))
    ancestry=read(checked(c['parent_source_contract']));findings={}
    for role,count in(('decoder',6),('closer',40)):
        d=d1['helpers'][role];assert d['source']==v1['sources'][role] and d['parent']==ancestry['sources'][role] and d['edit_count']==count
        findings[role+'-v1']=inverse(d)
        old=checked(d['parent']).read_bytes();raw=checked(d['source']).read_bytes()
        of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
        for name in d['unchanged_top_definitions_raw_AST']:
            assert segment(old,of[name])==segment(raw,nf[name]) and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    assert c['sources']['decoder']==v1['sources']['decoder']==d2['decoder_raw_unchanged']
    assert d2['edit_count']==2 and d2['parent_closer']==v1['sources']['closer'] and d2['source']==c['sources']['closer']
    v2=dict(d2,parent=d2['parent_closer']);findings['closer-v2']=inverse(v2)
    old=checked(d2['parent_closer']).read_bytes();raw=checked(d2['source']).read_bytes()
    of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
    for name in d2['unchanged_named_functions_raw_AST']:
        assert segment(old,of[name])==segment(raw,nf[name]) and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    for name in('current_sources','inputs','limits','original_model_sources','original_model_inputs','original_model_binding','caller_source','caller_source_contract','literal_body'):
        assert c[name]==v1[name]
    cold=read(checked(c['caller_source_contract']))
    assert c['current_sources']==cold['sources'] and c['inputs']==cold['inputs']
    for refs in(c['current_sources'],c['inputs'],c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    peerpath=BASE/'unit-row-routed-engine-qualification-saved-independent-source-20261016/typed-Source-review-v2.json'
    peer=read(peerpath)
    assert peer['source_contract']==cr and peer['sources']==c['sources'] and peer['source_review_passed']is True
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_only=True,source_review_passed=True,scientific_calls=0,scientific_acceptance=False,helpers_executed=False,concrete_blockers=[],whole_two_helpers_and_contract_read=True,raw_inverse_findings=findings,peer_review=pin(peerpath),
        authorship_disclosure='Root read whole decoder/current closer through complete V1 and exact two-guard V2 delta, current contract and all record joins. Root found V1 same-session false negative. Arithmetic authors helpers; controls separately reviews while disclosing caller authorship. No mathematical model/checker or helper executed by this review.',
        checks=['Strict 4/16MiB canonical JSON/LF/duplicate/nonfinite/base64/single-zlib/notails/fullhash and complete wire unchanged.',
            'Native20/512/wait4/PID/reaped/once/Date/caller/runtime14/input8/original17 guards preserved. Only truthful same-positive-integer tool handle continuity additionally recognized; no bracket relabeling or actual rerun.',
            'Whole native receipts/proposals/state/origin/census/current packet/actual cursor/fresh cover and search snapshot/lineage joins are literal saved-data concordance only.',
            'MR04 demands actual depth/key/status lineage and no exclusion; no expected path replaces an observed trace.',
            'Three no-return modes get countsNone, qualified0/unqualified2, no decoder/move/transfer/rollback inference. All12 across6 required; aggregate stays false for current failures.',
            'No full GCTS, target theorem, learned constraint, RL or advantage from these controls.'])
    review=save('ROOT-qualification-saved-helper-Source-review-v2.json',rr)
    copied={}
    for role,ref in c['sources'].items():
        src=checked(ref);dest=HERE/src.name
        with dest.open('xb') as f:f.write(src.read_bytes())
        assert pin(dest)['sha256']==ref['sha256'] and pin(dest)['bytes']==ref['bytes'];copied[role]=pin(dest)
    print(json.dumps(dict(review=review,copied_helpers=copied,scientific_calls=0)))
if __name__=='__main__':main()
