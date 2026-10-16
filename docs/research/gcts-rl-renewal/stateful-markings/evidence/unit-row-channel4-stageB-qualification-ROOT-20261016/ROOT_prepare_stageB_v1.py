"""Root raw/AST review concordance and once-plan preparation; no science."""
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
    n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(n.value)
def segment(raw,node):
    return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True); hunks=patch.splitlines(keepends=True)
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    output=[]; pos=0; index=2
    while index<len(hunks):
        h=hunks[index]; match=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',h)
        assert match, h
        start=int(match[1]); count=int(match[2] or b'1')
        newcount=int(match[4] or b'1'); index+=1
        begin=start-1 if count else start
        assert begin>=pos; output.extend(lines[pos:begin]); pos=begin
        consumed=produced=0
        while index<len(hunks) and not hunks[index].startswith(b'@@ '):
            line=hunks[index]; index+=1
            assert line[:1] in (b' ',b'-',b'+'), line
            if line[:1] in (b' ',b'-'):
                assert lines[pos]==line[1:]; pos+=1; consumed+=1
            if line[:1] in (b' ',b'+'): output.append(line[1:]); produced+=1
        assert consumed==count and produced==newcount
    output.extend(lines[pos:]); return b''.join(output)

def main():
    folder=BASE/'unit-row-channel4-stageB-cold-source-20261016'
    hp=folder/'handoff-v1.json'
    assert pin(hp)['sha256']=='67877c65f4403baf0dce9244b49325c8f6137dcc264b2ca93f7ce16ac7bfb2d3'
    h=read(hp); cr=h['source_contract']; c=read(checked(cr))
    assert cr['sha256']=='b621e8776b81228510615ed7c36de103162e6460be3ac410aaad323ea6f1c851'
    s,i=c['sources'],c['inputs']; assert len(s)==11 and len(i)==8
    for refs in (s,i,c['original_model_sources'],c['original_model_inputs'],c['references']):
        for ref in refs.values(): checked(ref)
    for name in ('source','source_contract','source_delta','author_static'):
        checked(h[name])
    oldc=read(checked(c['references']['parent_contract']))
    assert c['original_model_sources']==oldc['original_model_sources']
    assert c['original_model_inputs']==oldc['original_model_inputs'] and c['original_model_binding']==oldc['original_model_binding']
    assert all(v==oldc['sources'][k] for k,v in s.items() if k!='intake')
    raw=checked(s['intake']).read_bytes(); tree=ast.parse(raw)
    compile(tree,s['intake']['path'],'exec')
    for ref in s.values(): compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    assert literal(tree,'FIXED')=={k:v for k,v in s.items() if k!='intake'}
    for name,wanted in [('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits'])]:
        assert literal(tree,name)==wanted
    d=read(checked(c['source_delta'])); old=checked(d['parent']).read_bytes()
    assert d['source']==s['intake'] and d['edit_count']==len(d['edits'])==31
    rebuilt=old; inverse=raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['forward_patch']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['inverse_patch']).read_bytes())==old
    oldtree=ast.parse(old)
    oldfunc={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
    newfunc={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert set(newfunc)==set(oldfunc) and len(d['unchanged_top_helpers'])==17
    for name in d['unchanged_top_helpers']:
        assert segment(old,oldfunc[name])==segment(raw,newfunc[name])
        assert ast.dump(oldfunc[name],include_attributes=False)==ast.dump(newfunc[name],include_attributes=False)
    tail=b'    result_raw=call(encode_result_transport,(result_raw,))\n'
    assert old[old.index(tail):]==raw[raw.index(tail):]
    assert [n.name for n in tree.body if isinstance(n,ast.ClassDef)]==['ObservedCursor']
    assert len(c['expected_cases'])==c['expected_case_count']==9
    peerpath=BASE/'unit-row-channel4-stageB-cold-independent-source-20261016/typed-Source-review-v1.json'
    peer=read(peerpath)
    assert pin(peerpath)['sha256']=='3eff4bd0cb8534e47c18b7587324d6f08d94040893d70ab01790cbfac1e764c9'
    assert peer['source']==s['intake'] and peer['sources']==s and peer['source_contract']==cr
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_review_passed'] is True and peer['source_only'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
    reviewdata=dict(schema='ROOT-channel4-stageB-raw-inverse-review-v1',source=s['intake'],contract=cr,parent=d['parent'],
        whole_current_Source_and_contract_read=True,all_current11_input8_original17_input2_pins_verified=True,
        exact31_region_forward_inverse=True,actual_unified_forward_inverse=True,helpers17_raw_AST_equal=True,
        whole_native_output_failure_tail_equal=True,all_current_Source_AST_compile_only=True,
        no_scientific_imports_or_execution=True,scientific_calls=0,scientific_acceptance=False)
    inverse_review=save('ROOT-stageB-raw-inverse-review-v1.json',reviewdata)
    choice=save('ROOT-stageB-choice-v1.json',dict(schema='ROOT-channel4-stageB-choice-v1',previous_goal_turn='progress',current_goal_turn='progress',
        previous_checkpoint=pin(BASE/'unit-row-channel4-stageA-report-ROOT-20261016/ROOT-progress-checkpoint-v1.json'),
        purpose=c['API']['purpose'],expected_cases=c['expected_cases'],
        scope='Fresh valid local marked states, public next_alternative/place/checkpoint/rollback/state_snapshot only. No global decision/search, supplied proof word, donor or route.',
        essential_families=c['families'],limits=c['limits'],maximum_planned_actual_invocations=1,
        actual_execution_authorized=False,native_fit='UNMEASURED',scientific_calls=0,scientific_acceptance=False,
        remaining_gaps=c['remaining_gates']))
    root=dict(c['Review_ABI']); root.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,
        source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],raw_inverse_review=inverse_review,
        authorship_disclosure='Root read the whole new caller and current contract; Root authored no current scientific engine/controller logic. Current dependencies reuse prior whole Root/peer reviews with raw-identical pins. Source pass is conditional, not runtime acceptance.',
        checks=[
          'Current11/input8 remains distinct from original semantic17/input2. Fixed acceptedStageA23/0 data is whole-authenticated; marking is freshly reconstructed by independent9fd6. No old receipt supplies a new engine cache or proof.',
          'All31 byte regions and actual unified patches independently reconstruct both full parent/new bytes. Seventeen helpers and whole transport/output/nativeexit/failure suffix remain exact. Same native20/512 aggregate/internal500 reserve, once/meter2 and CodeSeal boundaries.',
          'Whole family_A/B/C FunctionType transactions use original guarded call/invoke. Public placements rebuild and check full current point legality. ObservedCursor records genuine wrapped current events; its class methods are captured by unchanged CodeSeal/function anchors. No private state, slot, cert or ledger mutation.',
          'FamilyA tests real unseen remote support and same prototype ledger plus genuinely new prototype outside query support; both base1 and added4 change, so no isolated4 causal claim. Full before/after current packets and transitions are saved, with exact outer restoration.',
          'FamilyB repeats retention before replay (AX1 then sameAX22), keeps literal original context/keys/full candidate/EOF archive exactly once, refreshes only current obligations, checkpoints the nonempty archive, replays genuine two-key current prefix/EOF twice across exact inner restoration, and restores outer snapshot.',
          'FamilyC uses real two selected consumers for shared4,1 refs2, removes one then last assignment with nested rollback while fixed4,0 ref1 remains. Absence stays distinct from assigned zero.',
          'All9 essential assertions and exact complete snapshots must finish; no skip/partial-pass/exception-as-negative. Work counters and cumulative external event log are intentionally outside semantic checkpoint. No cached degree transfer/global scheduling/UNKNOWN-child restoration/search/proof/RL/gain qualification.'
        ])
    rr=save('ROOT-stageB-caller-Source-review-v1.json',root)
    engine_root=c['references']['engine_ROOT_review']; engine_peer=c['references']['engine_peer']
    for ref in (engine_root,engine_peer):
        v=read(checked(ref)); assert v['source']==s['engine'] and v['adapter_source']==s['marked_adapter'] and v['source_review_passed'] is True
    limits=dict(aggregate_owned_bytes=536870912,caller_finish_reserve_seconds=1,caller_seconds=90,failure_only_seconds=55,joint_seconds=20,owned_seconds=60)
    assert c['limits']==limits
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
    assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    owned=HERE/'stageB-owned-v1'; external=HERE/'stageB-external-v1'
    assert not owned.exists() and not external.exists()
    common=dict(invocation_id='channel4-retention-archive-refs-qualification-20261016-v1',purpose=c['API']['purpose'],
        output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rr,peer=pin(peerpath)),runtime=runtime,limits=limits,resource_rule='single-owned-process-native-terminal-v1')
    grant=save('ROOT-stageB-authorization-v1.json',dict(common,schema='ROOT-channel4-stageB-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,
        protocol_choice=choice,dependency_reviews=dict(engine_ROOT=engine_root,engine_peer=engine_peer)))
    plan=save('ROOT-stageB-plan-v1.json',dict(common,schema='ROOT-channel4-stageB-plan-v1',ROOT_authorization=grant))
    save('ROOT-stageB-preflight-v1.json',dict(schema='ROOT-channel4-stageB-preflight-v1',handoff=pin(hp),plan=plan,scientific_calls=0,
        current_Source11_input8_original_Source17_verified=True,fresh_owned_and_external_outputs=True))
    print(json.dumps(dict(plan=plan,external_directory=str(external))))

if __name__=='__main__': main()
