"""Root Source-only fresh projection audit. No project Source evaluation."""
import ast, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
    p=Path(p); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p): return json.loads(Path(p).read_bytes())
def checked(r):
    p=Path(r['path']); assert p.is_absolute() and p==p.resolve() and pin(p)==r
    return p
def save(name,v):
    p=HERE/name
    with p.open('x') as f: json.dump(v,f,indent=2,sort_keys=True); f.write('\n')
    return pin(p)
def seg(b,n): return b''.join(b.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True); hunks=patch.splitlines(keepends=True); out=[]; pos=0; ix=2
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    while ix<len(hunks):
        m=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',hunks[ix]); assert m
        start=int(m[1]); count=int(m[2] or b'1'); made_count=int(m[4] or b'1'); ix+=1
        begin=start-1 if count else start; assert begin>=pos
        out.extend(lines[pos:begin]);pos=begin;used=made=0
        while ix<len(hunks) and not hunks[ix].startswith(b'@@ '):
            line=hunks[ix];ix+=1;assert line[:1] in (b' ',b'-',b'+')
            if line[:1] in (b' ',b'-'): assert lines[pos]==line[1:];pos+=1;used+=1
            if line[:1] in (b' ',b'+'): out.append(line[1:]);made+=1
        assert used==count and made==made_count
    out.extend(lines[pos:]);return b''.join(out)
def funcs(t):
    r={}
    for n in t.body:
        if isinstance(n,ast.FunctionDef): r[n.name]=n
        if isinstance(n,ast.ClassDef):
            for x in n.body:
                if isinstance(x,ast.FunctionDef): r[n.name+'.'+x.name]=x
    return r
def main():
    folder=BASE/'unit-row-fresh-projection-qualification-saved-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');c=read(checked(cr));d=read(checked(c['source_delta']))
    assert cr['sha256']=='06f1d21b333ae48505430b7c0be0349d260598fde33cbb9658a4125763b73d5e'
    caller=read(checked(c['caller_source_contract']))
    assert c['current_sources']==caller['sources'] and c['caller_source']==caller['source']
    reviewed=[];copies=[]
    for role,entry in d['helpers'].items():
        raw=checked(entry['source']).read_bytes();old=checked(entry['parent']).read_bytes();rebuilt,inverse=old,raw
        assert entry['edit_count']==len(entry['edits'])==(1 if role=='decoder'else 10)
        for e in reversed(entry['edits']):
            a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
            assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
            rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
            inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
        assert rebuilt==raw and inverse==old
        assert patch_bytes(old,checked(entry['patches'][0]).read_bytes())==raw
        assert patch_bytes(raw,checked(entry['patches'][1]).read_bytes())==old
        assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
        compile(ast.parse(raw),entry['source']['path'],'exec')
        of,nf=funcs(ast.parse(old)),funcs(ast.parse(raw));assert set(of)==set(nf)
        assert len(nf)==(9 if role=='decoder'else 24)
        changed=[]
        for name in of:
            if seg(old,of[name])!=seg(raw,nf[name]):changed.append(name)
        assert set(changed)==(set() if role=='decoder'else{'auth_plan','failure_only'})
        reviewed.append(dict(role=role,source=entry['source'],parent=entry['parent'],exact_raw_AST_patch_inverse=True,changed_functions=changed))
        target=HERE/Path(entry['source']['path']).name
        assert not target.exists();copies.append((target,raw))
    closer=checked(d['helpers']['closer']['source']).read_bytes()
    assert b'native_deadline_confirmed'not in closer and b'NATIVE20_DEADLINE_NO_RETURNED_CASE_RECORD'not in closer
    assert closer.count(b'failure_cause_established=False')==2
    assert b"failure_kind='NONZERO_NO_RETURNED_CASE_RECORD'"in closer
    assert b'reported_case_count=None,passed_cases=None,skipped_cases=None,qualified_case_count=0'in closer
    peerpath=BASE/'unit-row-fresh-projection-qualification-saved-independent-source-20261016/typed-Source-review-v1.json'
    peer=read(peerpath)
    assert peer['source_contract']==cr and peer['source_only']is peer['source_review_passed']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    assert peer['reviewer_identity']=='/root/hilbert_ordering_diagnosis'and peer['author_identity']=='/root/hilbert_advice_controls'
    assert peer['sources']==c['sources'] and peer['source']==c['source']
    for target,raw in copies:
        target.write_bytes(raw);assert target.read_bytes()==raw
    audit=save('ROOT-saved-helper-raw-inverse-review-v1.json',dict(schema='ROOT-fresh-projection-saved-helper-raw-inverse-review-v1',source_contract=cr,helpers=reviewed,Source_only=True,AST_compile_only=True,scientific_calls=0))
    r=dict(c['Review_ABI']);r.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=audit,whole_current_Source_and_contract_read=True,
      checks=['Whole old decoder/closer read and exact1+10 raw region/full AST and actualpatch inverses independently checked; current body differs only authority and failure attribution observations.',
      'All9 decoder/24 closer callable names stable; all12 expectedcases/single assignment and independent proposal name preserved. Source review does not execute metadata helper or replay any science.',
      'Canonical whole JSON/base64/zlib envelope, caps and all native/once/session/toolDate20/512/55/60/90+1 gates unchanged. Full original/currentauthority/marking/receipts/origin transfers/read occupancy/keySET/cursor/trace/checkpoint joins remain exact.',
      'Nonzero/no-record retains null reported/passed/skipped and zeroqualified/twounqualified; exact sharedtick line observed and lifetime>=20 separate, failurecauseFalse, no DEADLINE-specific kind or inferred semantic progress.',
      'Helpers copied byte-exact into Root actualfolder only, ready for Root saved closure after all actuals. Scientificcalls0 and strong success flags false. No scope widening, rerun or inherited10of12.'])
    print(json.dumps(save('ROOT-saved-helper-Source-review-v1.json',r)))
if __name__=='__main__':main()
