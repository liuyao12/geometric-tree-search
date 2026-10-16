"""Root Source-only concordance and four distinct once-plan grants; no science."""
import ast
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def read(p): return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(r):
    p=Path(r['path']); assert p.is_absolute() and p==p.resolve() and pin(p)==r
    return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f: json.dump(value,f,indent=2,sort_keys=True); f.write('\n')
    return pin(p)
def literal(tree,name):
    node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(node.value)
def segment(raw,node): return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True); hunks=patch.splitlines(keepends=True)
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    output=[]; pos=0; index=2
    while index<len(hunks):
        match=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',hunks[index]); assert match
        start=int(match[1]); count=int(match[2] or b'1'); newcount=int(match[4] or b'1'); index+=1
        begin=start-1 if count else start
        assert begin>=pos; output.extend(lines[pos:begin]); pos=begin; consumed=produced=0
        while index<len(hunks) and not hunks[index].startswith(b'@@ '):
            line=hunks[index]; index+=1; assert line[:1] in (b' ',b'-',b'+')
            if line[:1] in (b' ',b'-'): assert lines[pos]==line[1:]; pos+=1; consumed+=1
            if line[:1] in (b' ',b'+'): output.append(line[1:]); produced+=1
        assert consumed==count and produced==newcount
    output.extend(lines[pos:]); return b''.join(output)

def main():
    folder=BASE/'unit-row-channel4-stageC-cold-source-20261016'
    cr=pin(folder/'Source-contract-v1.json'); c=read(checked(cr))
    assert cr['sha256']=='b6e97354241cb1f367575080011136344fa93311d9a55b089794d1754fbdecba'
    s,i=c['sources'],c['inputs']; assert len(s)==11 and len(i)==8
    for refs in (s,i,c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values(): checked(ref)
    raw=checked(s['intake']).read_bytes(); tree=ast.parse(raw)
    for ref in s.values(): compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    assert literal(tree,'FIXED')=={k:v for k,v in s.items() if k!='intake'}
    for name,wanted in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('STAGEC_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases'])]:
        assert literal(tree,name)==wanted
    d=read(checked(c['source_delta'])); old=checked(d['parent']).read_bytes(); oldtree=ast.parse(old)
    assert d['source']==s['intake'] and d['edit_count']==len(d['edits'])==26
    rebuilt=old; inverse=raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['forward_patch']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['inverse_patch']).read_bytes())==old
    of={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
    nf={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert set(of)==set(nf) and len(d['all17_helpers'])==17
    for e in d['all17_helpers']:
        name=e['name']; assert segment(old,of[name])==segment(raw,nf[name])
        assert ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    on={n.name:n for n in of['main'].body if isinstance(n,ast.FunctionDef)}
    nn={n.name:n for n in nf['main'].body if isinstance(n,ast.FunctionDef)}
    assert len(d['nested_raw_AST_preserved'])==20
    for name in d['nested_raw_AST_preserved']:
        assert segment(old,on[name])==segment(raw,nn[name])
        assert ast.dump(on[name],include_attributes=False)==ast.dump(nn[name],include_attributes=False)
    oc=next(n for n in oldtree.body if isinstance(n,ast.ClassDef) and n.name=='ObservedCursor')
    nc=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ObservedCursor')
    assert segment(old,oc)==segment(raw,nc) and ast.dump(oc,include_attributes=False)==ast.dump(nc,include_attributes=False)
    tail=b'    result_raw=call(encode_result_transport,(result_raw,))\n'
    assert old[old.index(tail):]==raw[raw.index(tail):]
    choice=pin(HERE/'ROOT-stageC-choice-v1.json')
    assert choice['sha256']=='8c5025b61390af533f23b6dac972b639bb04a4313bb5e0a759192d09346dc194'
    prior=read(checked(i['stageB_plan'])); priorc=read(checked(prior['source_contract']))
    assert c['original_model_sources']==priorc['original_model_sources']
    assert c['original_model_inputs']==priorc['original_model_inputs'] and c['original_model_binding']==priorc['original_model_binding']
    assert all(v==prior['sources'][k] for k,v in s.items() if k!='intake')
    peerpath=BASE/'unit-row-channel4-stageC-cold-independent-source-20261016/typed-Source-review-v1.json'; peer=read(peerpath)
    assert pin(peerpath)['sha256']=='46e24f7f82fe18d1088b31d4a872e3cd63b9acccdf9b20d9a4367f37b1e710e7'
    assert peer['source']==s['intake'] and peer['sources']==s and peer['source_contract']==cr
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_review_passed'] is True and peer['source_only'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
    checked(peer['findings'])
    inverse_review=save('ROOT-stageC-raw-inverse-review-v1.json',dict(schema='ROOT-channel4-stageC-raw-inverse-review-v1',
        source=s['intake'],contract=cr,parent=d['parent'],whole_current_Source_and_contract_read=True,
        all_current11_input8_original17_input2_pins_verified=True,exact26_region_forward_inverse=True,
        actual_unified_forward_inverse=True,helpers17_nested20_observer_raw_AST_equal=True,
        whole_native_output_failure_tail_equal=True,all_current_Source_AST_compile_only=True,
        no_scientific_imports_or_execution=True,scientific_calls=0,scientific_acceptance=False))
    rr=dict(c['Review_ABI']); rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,
        source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=inverse_review,
        authorship_disclosure='Root read whole current caller/contract; authored no current scientific controller or engine. Existing raw-identical dependency reviews remain distinct from new caller review. Conditional Source pass; no runtime prediction.',
        checks=[
          'Full original17/input2 semantic authority preserved separately from executable11/input8; accepted StageB9 data fully authenticated, marking independently checked fresh. All cold setup/guards/costs remain charged.',
          'All26 regions and actual unified patches independently reconstruct whole parent and new bytes. Seventeen helpers, twenty nested helpers, whole ObservedCursor and native/output/failure suffix exact. No new custody framework or clock seam.',
          'C1/C3 genuine checked original-singleton-to-marked-zero and policy-independent post-DEAD public transaction preserve full original receipt/current wrapper chain, full matching states/transitions, then actual second DEAD; outer restore exact.',
          'C2 actual later complete ZERO outranks earlier complete SINGLETON without placement. C4 natural original partial2-to-marked1 plus real cursor2/1 EOF and same normal fresh certifier None must remain UNKNOWN and block a checked singleton. No suppression/relabel.',
          'C5/C6 real all-frontier resolved FORCED1 then FORCED5 then ROW BRANCH3; public actual candidates, both MANY/SINGLETON complete transfer chains, whole current packets/read occupancy and original full cursor archive, populated parent preserved.',
          'C7 fixed constructor callback invokes owning tick first, only interrupts actual grown child; require TRY and PLACE, exact dedicated UNKNOWN reason/noEXCLUDE/no found, full last-state/native record, exact complete root+stack and outer restore. No first-child key/count assumed.',
          'C8/C9 synthetic scheduler dictionaries explicitly NONLOGICAL. Production roots remain0; no broad completeness/GCTS/proof/RL/advantage claim. All9 across four distinct original20 endpoints essential; no combined20 suite or budget change.'
        ])
    root_review=save('ROOT-stageC-caller-Source-review-v1.json',rr)
    limits=dict(aggregate_owned_bytes=536870912,caller_finish_reserve_seconds=1,caller_seconds=90,failure_only_seconds=55,joint_seconds=20,owned_seconds=60)
    assert c['limits']==limits
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
    assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    endpoints=[]
    for mode in ('stageC-dead-transfer','stageC-natural-unknown','stageC-forced-transfer-child','stageC-scheduler'):
        purpose='unit-row-channel4-'+mode+'-controls'
        assert purpose in c['API']['purpose_modes_and_ordered_cases']
        owned=HERE/(mode+'-owned-v1'); external=HERE/(mode+'-external-v1')
        assert not owned.exists() and not external.exists()
        common=dict(invocation_id='channel4-'+mode+'-qualification-20261016-v1',purpose=purpose,
            output_directory=str(owned),sources=s,inputs=i,source_contract=cr,
            reviews=dict(ROOT=root_review,peer=pin(peerpath)),runtime=runtime,limits=limits,
            resource_rule='single-owned-process-native-terminal-v1')
        grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-channel4-stageC-authorization-v1',
            author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,
            all_four_endpoints_required=True,combined20_suite_claim=False,target_budget_changed=False))
        plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-channel4-stageC-plan-v1',ROOT_authorization=grant))
        endpoints.append(dict(mode=mode,plan=plan,external_directory=str(external),ordered_cases=c['API']['purpose_modes_and_ordered_cases'][purpose]))
    save('ROOT-stageC-preflight-v1.json',dict(schema='ROOT-channel4-stageC-preflight-v1',endpoints=endpoints,
        protocol_choice=choice,scientific_calls=0,current_Source11_input8_original_Source17_verified=True,
        fresh_distinct_owned_and_external_outputs=True,no_combined20_claim=True,all9_required=True))
    print(json.dumps(endpoints))

if __name__=='__main__': main()
