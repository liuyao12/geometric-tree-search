"""Root metadata/AST-only engine13 review; no scientific execution."""
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
def definitions(t):
    found={}
    for n in t.body:
        if isinstance(n,ast.FunctionDef):found[n.name]=n
        elif isinstance(n,ast.ClassDef):
            for m in n.body:
                if isinstance(m,ast.FunctionDef):found[n.name+'.'+m.name]=m
    return found

def main():
    folder=BASE/'unit-row-decision-context-engine-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='7cd85361fb73f70154c7b738f65c17accaf7e2ad14deadcd41f0efb736cf4e83'
    c=read(checked(cr));d=read(checked(c['source_delta']));parent=read(checked(c['parent_source_contract']))
    assert d['parent']==c['parent_engine']==parent['sources']['engine']and d['source']==c['source']==c['sources']['engine']
    assert len(c['sources'])==12 and len(c['original_model_sources'])==17 and len(c['original_model_inputs'])==2
    for refs in(c['sources'],c['original_model_sources'],c['original_model_inputs']):
        for r in refs.values():checked(r)
    for k in('original_model_sources','original_model_inputs','original_model_binding'):assert c[k]==parent[k]
    assert all(r==parent['sources'][k]for k,r in c['sources'].items()if k!='engine')
    raw=checked(c['source']).read_bytes();old=checked(c['parent_engine']).read_bytes();rebuilt,inverse=old,raw
    assert len(d['edits'])==3
    for e in reversed(d['edits']):
        a,b=e['old'].encode(),e['new'].encode();assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:];inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['actual_unified_patches']['forward']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['actual_unified_patches']['inverse']).read_bytes())==old
    ot,nt=ast.parse(old),ast.parse(raw);compile(nt,c['source']['path'],'exec');of,nf=definitions(ot),definitions(nt)
    assert set(nf)-set(of)=={'LazyUnitRowEngine._candidate_from_decision_context'}and set(of)-set(nf)==set()
    unchanged=set(of)-{'LazyUnitRowEngine.decision'};assert len(unchanged)==37 and unchanged==set(d['unchanged_existing_callables'])
    for k in unchanged:assert segment(old,of[k])==segment(raw,nf[k])and ast.dump(of[k],include_attributes=False)==ast.dump(nf[k],include_attributes=False)
    assert literal(nt,'VERSION')==c['API']['engine_VERSION']=='lazy-unit-row-global-engine-v13-decision-local-checked-state'
    calls=[n for n in ast.walk(nt)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='_candidate_from_decision_context']
    assert len(calls)==1 and calls[0]in list(ast.walk(nf['LazyUnitRowEngine.decision']))
    helper=nf['LazyUnitRowEngine._candidate_from_decision_context'];assert not any(isinstance(n,ast.Attribute)and n.attr=='private_state'for n in ast.walk(helper))
    suffix=b'        for row in frontier:\n            if certificates[row][\'status\'] == \'UNKNOWN\':'
    od=segment(old,of['LazyUnitRowEngine.decision']);nd=segment(raw,nf['LazyUnitRowEngine.decision']);assert od[od.index(suffix):]==nd[nd.index(suffix):]
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],distinct_peer_review_required_before_actual=True,whole_affected_Source_and_contract_read=True,
        authorship_disclosure='Root read full old/new changed decision and candidate helper, full contract and all3 edit regions; whole raw forward/inverse and actual patches plus37 unchanged callable comparisons join the whole-read engine12 ancestry. Root authored metadata only, no scientific module or model execution. Diagnosis authors proposal and independent checker dependencies, disclosed in peer review.',
        findings=['One checked tuple from unchanged independent private_state, stack-only active closure. Full state object/literal/revision/current identity/binding/marking and captured owned authority/policy guards, native tick before checks.',
        'Every candidate retains raw shape/incident full key, unchanged independent rebuild, original+decorated collision against a copied baseline names ledger, whole t/m/selected/excluded legality, read occupancy obligations and entire packet equality. Unchanged _observe preserves both cross-candidate collision ledgers.',
        'Fresh proposer/checker gets only its own copied state, never checked tuple/context. Existing native receipt validation remains independently fresh and raw exact. Context inactive in finally before inherited fallback/scheduler suffix; every other old callable including _candidate/place/cursor/rollback/search raw+AST exact.',
        'All original17/input2/binding and11 other module Sources remain exact. No new marking/grammar/epoch/budget, donor/route/proofword, cache/custody framework or hidden cluster restriction.',
        'This is conditional synchronous pinned-Source reasoning, not hostile callback/frame robustness. Guard compares captured full authority, not fresh authority_snapshot every time; fresh independent math and marking checks remain as before. Existing12 do not test deliberate guard mismatch or postrollback requery.',
        'Specialized24-row model; no full GCTS, universal finite Wang palette, RL, learned pruning, target theorem, measured fit or speed benefit accepted here.'],
        raw_inverse=dict(three_complete_regions=True,actual_forward_and_inverse_patches=True,whole_AST_inverse=True,unchanged_callables=37,single_private_callsite=True,fallback_scheduler_suffix_raw_exact=True))
    out=save('ROOT-engine-Source-review-v1.json',rr);print(json.dumps(dict(review=out,scientific_calls=0)))
if __name__=='__main__':main()
