"""Raw/AST-only plan preparation; no scientific imports or execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(path):
    p=Path(path);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(ref):
    p=Path(ref['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==ref
    return p
def read(path):return json.loads(Path(path).read_bytes())
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
def main(argv):
    assert len(argv)==2
    peerpath,peersha=argv
    hp=BASE/'unit-row-certified-marking-cold-source-20261016/handoff-v1.json'
    assert pin(hp)['sha256']=='cbcb941a8b4b3db0e8f4dae7b66b223b6937175a10a531e16766933d83f09142'
    h=read(hp);c=read(checked(h['source_contract']));s=c['sources'];i=c['inputs'];limits=c['limits']
    assert len(s)==9 and len(i)==8 and h['sources']==s
    for ref in [*s.values(),*i.values(),*c['original_model_sources'].values()]:checked(ref)
    for ref in s.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
    pp=Path(peerpath);assert pin(pp)['sha256']==peersha
    peer=read(pp)
    assert peer['source']==s['intake'] and peer['sources']==s and peer['source_contract']==h['source_contract']
    assert peer['scope']==c['scope'] and peer['author_identity']==c['author_identity']
    assert peer['reviewer_identity'] not in ('/root',c['author_identity'])
    assert peer['source_only'] is True and peer['source_review_passed'] is True
    assert peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
    review=dict(c['Review_ABI']);review.update(source_contract=h['source_contract'],reviewer_identity='/root',
        source_review_passed=True,concrete_blockers=[],
        authorship_disclosure='Root whole-read caller and both new modules. Advice_controls authored caller/decorator; diagnosis authored independent verifier and reviews caller; arithmetic peer-reviewed verifier. All review is raw/AST-only, no scientific execution.',
        checks=[
          'Whole current813-line caller and contract read. Seventeen inherited top-level helpers raw/AST-identical; complete transport/output/nativeexit/failure55 tail exact. Current executable9 is authenticated separately from original semantic17/input2; no epoch/key/source rebasing.',
          'Fixed prior Root disposition authenticates two accepted literal/certificate/check records via entire prior plan/contract/grant/review/raw files and expanded/response/output concordance. Old engine/intake never loaded. Independent current verifier rederives all six row0 exclusions and whole marking model from fresh original authority.',
          'Four exact original base prototypes are independently reconstructed and baselegal. Decorated full point data checked separately; pure actual point comparison saves all shared values, auxiliary union presence/value, full conflicts and capacity. Two row0 reads conflict at channel4; AX0 and same literal read1 remain allowed partial states. No graph/search/EOF/proof is inferred.',
          'Sixteen exact controls cover definition/root/point preservation/absence and scoped negatives. Builtin exact ValueError and case reason required; pre/post custody/resource faults propagate. Callback timeout explicitly injected after original tick, never promoted to native success.',
          'Same original native20/500MiB reserve,512MiB aggregate,60owned/90caller+1, failure-only55; once/meter2/CodeSeal/strong anchors/guard/complete wire closure retained. All current cold setup/auth/import/reconstruction/decorate/recheck/controls/output/exit/postprobe charged. Trusted synchronous pinned Source only.',
          'Both new modules independently Source-reviewed. Constructor qualification only; engine10, full graph, rollback, target search, proof/RL/advantage and reference conformance remain unqualified.'
        ])
    rr=save('ROOT-caller-Source-review-v1.json',review)
    dependencies={}
    for role,folder in [('decorator','unit-row-certified-mark-decorator'),('verifier','unit-row-channel4-state-verifier')]:
        root=pin(HERE/('ROOT-'+role+'-Source-review-v1.json'))
        peerref=pin(BASE/(folder+'-independent-source-20261016')/'typed-Source-review-v1.json')
        for ref in (root,peerref):
            v=read(checked(ref));assert v['source']==s['decorator' if role=='decorator' else 'marked_verifier']
            assert v['source_review_passed'] is True and v['scientific_calls']==0 and v['scientific_acceptance'] is False
        dependencies[role+'_ROOT']=root;dependencies[role+'_peer']=peerref
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
    assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    owned=HERE/'marking-owned-v1';external=HERE/'marking-external-v1'
    assert not owned.exists() and not external.exists()
    protocol=save('ROOT-marking-protocol-choice-v1.json',dict(
        schema='ROOT-certified-row0-marking-protocol-choice-v1',previous_goal_turn='progress',current_goal_turn='progress',
        sources=s,inputs=i,limits=limits,original_model_sources=c['original_model_sources'],
        original_model_inputs=c['original_model_inputs'],original_model_binding=c['original_model_binding'],
        expected_controls=16,expected_fixtures=4,scientific_execution=False,target_search=False,engine_activation=False,
        scope='Compile exactly two externally certified literals to actual channel4 point values; independent complete model/tile/state reconstruction plus four point comparisons. No graph/search or proof acceptance.',
        costs='All cold authentication/imports/reconstruction/decorating/checking/controls/point comparisons/output/nativeexit/postprobe charged.'))
    common=dict(invocation_id='certified-row0-marking-data-20261016-v1',purpose=c['API']['purpose'],
        output_directory=str(owned),sources=s,inputs=i,source_contract=h['source_contract'],
        reviews=dict(ROOT=rr,peer=pin(pp)),runtime=runtime,limits=limits,resource_rule=c['resource_rule'])
    grant=save('ROOT-marking-authorization-v1.json',dict(common,schema=c['API']['grant_schema'],author_identity='/root',
        actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dependencies))
    plan=save('ROOT-marking-plan-v1.json',dict(common,schema=c['API']['plan_schema'],ROOT_authorization=grant))
    save('ROOT-marking-preflight-v1.json',dict(schema='ROOT-certified-row0-marking-preflight-v1',plan=plan,handoff=pin(hp),
        scientific_calls=0,current_Source9_input8_original_Source17_verified=True,fresh_owned_and_external_outputs=True))
    print(json.dumps(dict(plan=plan,external_directory=str(external))))
if __name__=='__main__':main(sys.argv[1:])
