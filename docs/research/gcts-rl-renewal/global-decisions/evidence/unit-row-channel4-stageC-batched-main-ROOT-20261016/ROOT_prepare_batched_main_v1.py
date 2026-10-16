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
    folder=BASE/'unit-row-channel4-stageC-batched-main-source-20261016'
    cr=pin(folder/'Source-contract-v1.json')
    assert cr['sha256']=='a433608ca59165c5d470513098fb383ebd4b8408d55a0dc98fa222f6fb45c257'
    c=read(checked(cr)); s,i=c['sources'],c['inputs']
    assert len(s)==11 and len(i)==8
    for refs in (s,i,c['original_model_sources'],c['original_model_inputs']):
        for r in refs.values(): checked(r)
    raw=checked(s['intake']).read_bytes(); t=ast.parse(raw)
    for r in s.values(): compile(ast.parse(checked(r).read_bytes()),r['path'],'exec')
    assert literal(t,'FIXED')=={k:v for k,v in s.items() if k!='intake'}
    for name,want in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('STAGEC_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases'])]:
        assert literal(t,name)==want
    d=read(checked(c['source_delta'])); old=checked(d['parent']).read_bytes(); ot=ast.parse(old)
    assert d['source']==s['intake'] and d['edit_count']==len(d['edits'])==11
    rebuilt=old; inverse=raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['forward_patch']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['inverse_patch']).read_bytes())==old
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)}
    nf={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
    assert set(of)==set(nf)
    for name in d['all17_helpers_raw_AST_exact']:
        assert segment(old,of[name])==segment(raw,nf[name])
        assert ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    on={n.name:n for n in of['main'].body if isinstance(n,ast.FunctionDef)}
    nn={n.name:n for n in nf['main'].body if isinstance(n,ast.FunctionDef)}
    for name in d['all_other_parent_main_nested_raw_AST_exact']:
        assert segment(old,on[name])==segment(raw,nn[name])
        assert ast.dump(on[name],include_attributes=False)==ast.dump(nn[name],include_attributes=False)
    for name in d['both_whole_classes_raw_AST_exact']:
        oc=next(n for n in ot.body if isinstance(n,ast.ClassDef) and n.name==name)
        nc=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==name)
        assert segment(old,oc)==segment(raw,nc)
    assert segment(raw,nn['forced_transfer_child']).replace(b'seeds=main_seed_batch(d)',b'seeds=[ax(0),ax(4),ug(ax_formula,1,2),ug(d,3,6),ug(ax_formula,5,8)]')==segment(old,on['forced_transfer_child'])
    tail=b'    result_raw=call(encode_result_transport,(result_raw,))\n'
    assert old[old.index(tail):]==raw[raw.index(tail):]
    choice=pin(HERE/'ROOT-batched-main-choice-v1.json')
    assert choice['sha256']=='3a8b1c4bb473210300ffa859341e33cfd2f0bb80807ed4dd647e42f7b1b6b10c'
    pc=read(BASE/'unit-row-channel4-stageC-cold-source-20261016/Source-contract-v1.json')
    for k in ('original_model_sources','original_model_inputs','original_model_binding','inputs','limits'): assert c[k]==pc[k]
    assert all(v==pc['sources'][k] for k,v in s.items() if k!='intake')
    peerpath=BASE/'unit-row-channel4-stageC-batched-main-independent-source-20261016/typed-Source-review-v1.json'
    peer=read(peerpath)
    assert pin(peerpath)['sha256']=='e6408cc7bbccd80bcc42fc356727cdd97442ae8757f245ff95d261c74edfeb4f'
    assert peer['source']==s['intake'] and peer['sources']==s and peer['source_contract']==cr
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_review_passed'] is True and peer['source_only'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
    checked(peer['findings'])
    inverse_review=save('ROOT-batched-main-raw-inverse-review-v1.json',dict(
        schema='ROOT-channel4-batched-main-raw-inverse-review-v1',source=s['intake'],contract=cr,parent=d['parent'],
        all_current11_input8_original17_input2_pins_verified=True,exact11_region_forward_inverse=True,
        actual_unified_forward_inverse=True,helpers17_nested30_classes2_raw_AST_equal=True,
        complete_C5_C6_C7_body_after_only_seed_line_replacement=True,whole_native_output_failure_tail_equal=True,
        all_current_Source_AST_compile_only=True,no_scientific_imports_or_execution=True,scientific_calls=0,scientific_acceptance=False))
    rr=dict(c['Review_ABI']); rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,
        source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=inverse_review,
        authorship_disclosure='Root read current full delta/changed constructor and C5-C7 plus inherited whole-Source review ancestry. Root authors metadata preparation, not scientific controller. Distinct peer independently reviews whole current caller. No runtime-fit promise.',
        checks=[
            'Original semantic17/input2 and language epoch exact; current11/input8 unchanged except caller; six limits exact.',
            'All11 edits and both actual patches reconstruct entire old/new bytes;17helpers,30nested,bothclasses,native/output/failure suffix exact.',
            'One private language builds identical ordered five seed descriptors with cumulative budget; finally discarded before unchanged fresh independent state reconstruction. No parser or language bound reset.',
            'Every C5-C7 assertion and guarded operation after seed call raw exact. Same genuine all-frontier FORCED1/FORCED5/BRANCH3, full MANY/SINGLETON receipt transfers, archive and occupancy refresh.',
            'Same owning native-first callback in genuine actual grown child; require TRY/PLACE/exact deliberate UNKNOWN/noEXCLUDE/full state+stack restore and output within original20; real deadline cannot pass.',
            'Sole dispatch current3; historical other6 not rerun or requalified. Failed v1 immutable; no same-controller9/suite20/full-GCTS/target-proof/RL/advantage acceptance.'])
    root_review=save('ROOT-batched-main-caller-Source-review-v1.json',rr)
    limits=dict(aggregate_owned_bytes=536870912,caller_finish_reserve_seconds=1,caller_seconds=90,failure_only_seconds=55,joint_seconds=20,owned_seconds=60)
    assert c['limits']==limits
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
    assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    purpose='unit-row-channel4-stageC-batched-main-controls'
    assert list(c['API']['purpose_modes_and_ordered_cases'])==[purpose]
    owned=HERE/'batched-main-owned-v1'; external=HERE/'batched-main-external-v1'
    assert not owned.exists() and not external.exists()
    common=dict(invocation_id='channel4-stageC-batched-main-qualification-20261016-v1',purpose=purpose,
        output_directory=str(owned),sources=s,inputs=i,source_contract=cr,
        reviews=dict(ROOT=root_review,peer=pin(peerpath)),runtime=runtime,limits=limits,
        resource_rule='single-owned-process-native-terminal-v1')
    grant=save('ROOT-batched-main-authorization-v1.json',dict(common,schema='ROOT-channel4-stageC-batched-main-authorization-v1',
        author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,
        essential_case_count=3,original_v1_four_endpoint_suite_qualified=False,same_controller_all_nine_qualified=False,
        combined20_suite_claim=False,target_budget_changed=False))
    plan=save('ROOT-batched-main-plan-v1.json',dict(common,schema='ROOT-channel4-stageC-batched-main-plan-v1',ROOT_authorization=grant))
    output=dict(plan=plan,external_directory=str(external),ordered_cases=c['API']['purpose_modes_and_ordered_cases'][purpose])
    save('ROOT-batched-main-preflight-v1.json',dict(schema='ROOT-channel4-batched-main-preflight-v1',
        endpoint=output,protocol_choice=choice,scientific_calls=0,
        original_v1_suite_remains_incomplete=True,old_six_not_requalified=True,all_three_essential=True))
    print(json.dumps(output))
if __name__=='__main__': main()

