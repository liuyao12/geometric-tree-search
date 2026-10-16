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
    folder=BASE/'unit-row-marked-aware-calibration-saved-source-20261016';cr=pin(folder/'Source-contract-v1.json')
    assert cr['sha256']=='110a18805d04695fa1ee26981e797db80eb856ede64e7f9c6cda6378a578c5d3'
    c=read(checked(cr));delta=read(checked(c['source_delta']));findings={}
    ancestry=read(checked(c['source_contract_ancestry']))
    for role,count in(('decoder',5),('closer',40)):
        d=delta['helpers'][role];raw=checked(d['source']).read_bytes();old=checked(d['parent']).read_bytes()
        assert d['source']==c['sources'][role]and d['parent']==ancestry['sources'][role]
        assert d['edit_count']==len(d['edits'])==count
        a=old;b=raw
        for e in reversed(d['edits']):
            x,y=e['old_utf8'].encode(),e['new_utf8'].encode()
            assert old[e['old_start']:e['old_end']]==x and raw[e['new_start']:e['new_end']]==y
            a=a[:e['old_start']]+y+a[e['old_end']:];b=b[:e['new_start']]+x+b[e['new_end']:]
        assert a==raw and b==old
        assert patch_bytes(old,checked(d['patches'][0]).read_bytes())==raw
        assert patch_bytes(raw,checked(d['patches'][1]).read_bytes())==old
        t=ast.parse(raw);ot=ast.parse(old);compile(t,d['source']['path'],'exec')
        of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
        for name in d['unchanged_top_definitions_raw_AST']:
            assert segment(old,of[name])==segment(raw,nf[name])and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
        findings[role]=dict(source=d['source'],parent=d['parent'],exact_forward_inverse=True,actual_patch_inverse=True,edit_count=count,unchanged_definitions=d['unchanged_top_definitions_raw_AST'],AST_compile_only=True,whole_Source_read=True)
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_only=True,source_review_passed=True,scientific_calls=0,scientific_acceptance=False,helpers_executed=False,concrete_blockers=[],whole_two_helpers_and_contract_read=True,raw_inverse_findings=findings,
        authorship_disclosure='Root read whole current two helpers/contract and independently checks exact5+40 edits and four actualpatches. Root authors metadata and ownsactuals; arithmetic authors helpers. Separate Source peer also required before use.',
        checks=['Strict4/16MiB/canonicalJSON LF/duplicate andnonfinite rejection/base64reencode/singlecompletezlib/notails/wholehash preserved.','CurrentSource13/input8/original17/input2/plan/reviews/grant/once/nativewait4/20/512/Date/output2/response2LF preserved; whole current binding separate from runtimeSources.','Full new local state/proposal/receipt/original state/keylist/marking/census/negativebadproposal literal joins only; no scientific reenumeration/membership/replay.','Zero/one complete versusTWOlowerbound flags unambiguous; actual strict expected failures never infer proof/engine/benefit/RL acceptance.','Genericclean nonzero rawadminclosure preserves countsNone/zeroqualified; confirmed deadline uses exactTimeout and actualnative>=20. No prefixprogress inferred.','Aggregate requires four distinct closed endpoints/sharedfullauthority/marking/all6; no combined20/oldStageCpromotion/engineintegration.'])
    print(json.dumps(save('ROOT-calibration-saved-helper-Source-review-v1.json',rr)))
if __name__=='__main__':main()
