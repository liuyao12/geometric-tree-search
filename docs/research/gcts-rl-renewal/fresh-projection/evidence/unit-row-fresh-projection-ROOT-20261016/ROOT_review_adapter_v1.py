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
    folder=BASE/'unit-row-fresh-projection-adapter-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='8db81c755e0ade5eae2aa5d04ec68eb012be05a89b4ef092616a4343340fc040'
    c=read(checked(cr));d=read(checked(c['source_delta']))
    raw=checked(c['source']).read_bytes();old=checked(d['parent']).read_bytes()
    assert c['source']['sha256']=='a1971d01cc1291af4b5508c81e3ef06bec17ee794d0a5d95b102d730ce0a3f7c'
    rebuilt,inverse=old,raw
    assert len(d['edits'])==3
    for e in reversed(d['edits']):
        a,b=e['old'].encode(),e['new'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['actual_unified_patches']['forward']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['actual_unified_patches']['full_inverse']).read_bytes())==old
    t,ot=ast.parse(raw),ast.parse(old);nf,of=funcs(t),funcs(ot)
    assert set(nf)-set(of)=={'MarkedSemantics._fresh_base_projection'}
    untouched=set(of)-{'MarkedSemantics.base_state','MarkedSemantics.private_state'}
    assert len(untouched)==26
    for k in untouched:
        assert seg(raw,nf[k])==seg(old,of[k]) and ast.dump(nf[k],include_attributes=False)==ast.dump(of[k],include_attributes=False)
    body=seg(old,of['MarkedSemantics.base_state']).replace(b'def base_state(',b'def _fresh_base_projection(',1)
    body=body.replace(b'return self.base.private_state(language, base, tick)[0]',b'return self.base.private_state(language, base, tick)',1)
    assert body==seg(raw,nf['MarkedSemantics._fresh_base_projection'])
    assert seg(raw,nf['MarkedSemantics.base_state'])==b'    def base_state(self, language, state, tick):\n        return self._fresh_base_projection(language, state, tick)[0]\n'
    e=d['edits'][2];assert seg(old,of['MarkedSemantics.private_state']).replace(e['old'].encode(),e['new'].encode(),1)==seg(raw,nf['MarkedSemantics.private_state'])
    assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ot,include_attributes=False)
    p=read(checked(c['parent_caller_source_contract']));s=c['sources'];assert len(s)==13
    assert s==c['current_component_sources'] and s['marked_adapter']==c['source']
    assert all(v==p['sources'][k] for k,v in s.items() if k!='marked_adapter')
    for k in ('inputs','original_model_sources','original_model_inputs','original_model_binding','limits'):
        assert c[k]==p[k]
    assert c['Root_choice']==pin(HERE/'ROOT-implementation-choice-v1.json')
    for r in s.values():
        b=checked(r).read_bytes();compile(ast.parse(b),r['path'],'exec')
    audit=save('ROOT-adapter-raw-inverse-review-v1.json',dict(schema='ROOT-fresh-projection-adapter-raw-inverse-review-v1',source=c['source'],source_contract=cr,exact3region_and_actualpatch_inverse=True,unchanged26_callables_raw_AST_exact=True,helper_original_body_exact_except_return_index=True,private_state_exact_two_statement_replacement=True,current13_raw_capsules_verified=True,unchanged_original17_input2_input8_authority_compared_to_parent=True,AST_compile_only=True,scientific_calls=0))
    r=dict(c['Review_ABI']);r.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=audit,whole_current_Source_and_contract_read=True,
      authorship_disclosure='Root independently read whole adapter2 and composite contract; reviewed c354 tree/private_state and its literal idempotence, raw changed regions and all unchanged26 callable joins. Fresh current13 composition is reviewed here; old engine13 component reviews are historical ancestry, not relabelled current. No project Source evaluated.',
      checks=[
        'One synchronous local fresh checked tuple replaces only an immediate duplicate c354 private_state traversal. Returned s preserves literal ordered arrays/keys; returned t and names reconstruct equal values under unchanged authority.',
        'Public base_state still fresh[0]; tuple0/1/5 stay local. t values are immutable integers; dict(base_names) owns later collision-ledger writes. Tree copies, independent9fd whole marked reconstruction, c354/8f census, membership, full t/m/collision/read obligations outside that duplicate remain exact.',
        'No self/cursor/cache/checkpoint or crosscall/proposer-checker context added. Trusted synchronous pinned authority/tick scope; no hostile reentrancy/ABA guarantee or equivalent exception/tick timing assertion.',
        'Public wire/data/semantics/transition/fallback versions unchanged; explicit implementation tag plus Source filename/hash identifies this revision. New current14 caller must check tag and fresh composite reviews.',
        'Same unit-row specialized finite model, all six cases/twelve essentials, original17/input2/epoch/input8/native limits. No current qualification, target proof, full GCTS, RL or performance claim.'])
    print(json.dumps(save('ROOT-adapter-composite-Source-review-v1.json',r)))
if __name__=='__main__':main()
