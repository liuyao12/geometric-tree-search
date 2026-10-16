"""Root metadata-only delta review and preservation of superseded saved dispositions."""
import ast, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p);b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(r):
    p=Path(r['path']);assert p==p.resolve() and pin(p)==r;return p
def save(p,v):
    with p.open('x')as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def patch(raw,delta):
    lines=raw.splitlines(keepends=True);chunks=delta.splitlines(keepends=True);out=[];pos=0;i=2
    assert chunks[0].startswith(b'--- ')and chunks[1].startswith(b'+++ ')
    while i<len(chunks):
        m=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',chunks[i]);assert m;i+=1
        used=made=0;n=int(m[2]or b'1');nn=int(m[4]or b'1');start=int(m[1])-1 if n else int(m[1]);assert start>=pos
        out.extend(lines[pos:start]);pos=start
        while i<len(chunks)and not chunks[i].startswith(b'@@ '):
            line=chunks[i];i+=1;assert line[:1]in(b' ',b'-',b'+')
            if line[:1]in(b' ',b'-'):assert lines[pos]==line[1:];pos+=1;used+=1
            if line[:1]in(b' ',b'+'):out.append(line[1:]);made+=1
        assert (used,made)==(n,nn)
    return b''.join(out+lines[pos:])
def segment(raw,node):return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def main():
    folder=BASE/'unit-row-routed-engine-qualification-saved-source-20261016'
    cr=pin(folder/'Source-contract-v3.json');assert cr['sha256']=='eab5c3988beb571b7e5e12024ef6a08a445fac4a140fb0680804c2da725252f3'
    c=read(checked(cr));prior=read(checked(c['preserved_v2_contract']));d=read(checked(c['source_delta']))
    assert d['edit_count']==6 and d['parent_closer']==prior['sources']['closer'] and d['source']==c['sources']['closer']
    old=checked(d['parent_closer']).read_bytes();raw=checked(d['source']).read_bytes();forward,inverse=old,raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        forward=forward[:e['old_start']]+b+forward[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert forward==raw and inverse==old
    assert patch(old,checked(d['patches'][0]).read_bytes())==raw and patch(raw,checked(d['patches'][1]).read_bytes())==old
    ot,nt=ast.parse(old),ast.parse(raw);compile(nt,str(checked(d['source'])),'exec')
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
    assert set(of)==set(nf)==set(d['all_top_functions_raw_AST_exact']) and len(of)==24
    for name in of:assert segment(old,of[name])==segment(raw,nf[name]) and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    stores=[n for n in ast.walk(nt)if isinstance(n,ast.Name)and isinstance(n.ctx,ast.Store)and n.id=='expected_cases']
    assert len(stores)==1
    binding=next(n for n in nt.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='expected_cases'for x in n.targets))
    assert isinstance(binding.value,ast.Call)and isinstance(binding.value.func,ast.Name)and binding.value.func.id=='tuple'
    assert c['sources']['decoder']==prior['sources']['decoder']==d['decoder_raw_unchanged']
    for k in('current_sources','inputs','limits','original_model_sources','original_model_inputs','original_model_binding','caller_source','caller_source_contract','literal_body'):
        assert c[k]==prior[k]
    for refs in(c['current_sources'],c['inputs'],c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    peerpath=BASE/'unit-row-routed-engine-qualification-saved-independent-source-20261016/typed-Source-review-v3.json'
    peer=read(peerpath);assert peer['sources']==c['sources']and peer['source_contract']==cr
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    previous=HERE/'ROOT-qualification-saved-helper-Source-review-v2.json'
    assert pin(previous)['sha256']=='bb0d3dc0e51b3e03bd820db8aeddad0959ac7884eff4331462533acd38422345'
    review=dict(c['Review_ABI']);review.update(source_contract=cr,reviewer_identity='/root',source_only=True,source_review_passed=True,scientific_calls=0,scientific_acceptance=False,helpers_executed=False,concrete_blockers=[],peer_review=pin(peerpath),preserved_review=pin(previous),
        review_scope='Root previously read whole decoder and closer V1/current V2 delta. Root now read whole six-edit V3 delta, whole V3 contract, entire affected top-level case-binding/negative-loop/result flow. All24 functions and remaining raw Source exactly preserved by independently applied edit and actual patch inverses.',
        findings=['One immutable expected_cases tuple binding; all reported/passed/qualified counts and case_names use this binding. Negative expected_proposal separate; remaining expected only function-local cursor set.',
        'Same literal native/authority/wire/receipt/context/move/restore joins, failure count nulls and aggregate required12 guard. No semantic replay or new actual. Decoder unchanged.',
        'V2 router count22 is invalid reporting, never aggregate acceptance. All6 V2 dispositions preserved separately; same saved records will be closed again, not rerun.',
        'No target theorem, engine qualification, RL, conformance or advantage conclusion.'])
    save(HERE/'ROOT-qualification-saved-helper-Source-review-v3.json',review)
    q=HERE/'superseded-saved-v2';q.mkdir();records=[]
    modes=('router-protocol','global-forced-dead','singleton-transfer','two-transfer','short-EOF','child-UNKNOWN')
    for mode in modes:
        p=HERE/('ROOT-MR-'+mode+'-disposition-v1.json');r=pin(p);v=read(p)
        assert v['closure_helper']['sha256']==d['parent_closer']['sha256']
        if mode=='router-protocol':assert v['qualified_case_count']==22 and isinstance(v['case_names'],dict)
        target=q/p.name;assert not target.exists();p.rename(target)
        assert pin(target)['sha256']==r['sha256'];records.append(dict(mode=mode,original=r,preserved=pin(target)))
    assert not(HERE/'ROOT-MR-qualification-disposition-v1.json').exists()
    save(q/'ROOT-quarantine-manifest-v1.json',dict(schema='ROOT-routed-saved-v2-quarantine-v1',reason='Router global expected variable shadowed by failing proposal: invalid final count22 and dict case_names. No aggregate run or accepted result. Preserve all6 V2 saved dispositions before V3 closure.',records=records,scientific_actuals_changed=False,scientific_rerun=False,decoder_rerun=False))
    dest=HERE/checked(c['sources']['closer']).name
    with dest.open('xb')as f:f.write(raw)
    assert pin(dest)['sha256']==c['sources']['closer']['sha256']
    print(json.dumps(dict(review=pin(HERE/'ROOT-qualification-saved-helper-Source-review-v3.json'),closer=pin(dest),quarantine_records=len(records),scientific_calls=0)))
if __name__=='__main__':main()
