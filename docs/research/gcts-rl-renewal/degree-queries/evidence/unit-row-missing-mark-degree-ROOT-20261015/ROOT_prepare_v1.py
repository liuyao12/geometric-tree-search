"""Raw Source/AST/review/plan metadata only. No scientific functions execute."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(ref):
    p=Path(ref['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==ref;return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
assert len(sys.argv)==3
peer_path=Path(sys.argv[1]);assert pin(peer_path)['sha256']==sys.argv[2]
hpath=BASE/'unit-row-missing-mark-cold-ROOT-source-20261015/handoff-v1.json'
assert pin(hpath)['sha256']=='ba88c71d73efaf3c7b9014ae549ac0fe020ba232f16a67ae24ef466855533e89'
h=read(hpath);sources=h['sources'];inputs=h['inputs'];cr=h['source_contract'];contract=read(check(cr))
assert sources['intake']['sha256']=='cbf39e7381dda8e637e6ad1bac85a94c217937415116151d988546563a5458c3'
assert cr['sha256']=='827f85dd6a45f82fef698deb10c8c41543a555475fc0971ae5707c7a36a73f0c'
assert contract['sources']==sources and contract['inputs']==inputs and len(sources)==7 and len(inputs)==2
for ref in [*sources.values(),*inputs.values()]:check(ref)
for ref in sources.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==cr
assert peer['scope']==contract['scope'] and peer['author_identity']=='/root' and peer['reviewer_identity']=='/root/hilbert_advice_controls'
assert peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
prpath=BASE/'unit-row-missing-mark-degree-independent-source-20261015/typed-Source-review-v1.json'
assert pin(prpath)['sha256']=='a5a98a012ae74621ec6d8cd251684b5a2c8768aac22eee777f24f11eae0256d3'
pr=read(prpath);assert pr['source']==sources['proposer'] and pr['source_review_passed'] is True
checker_h=read(BASE/'unit-row-missing-mark-checker-source-20261015/handoff-v2.json')
ccref=checker_h['source_contract'];cc=read(check(ccref))
assert ccref['sha256']=='342cb0662f66262fa3ceb891f407a70128e299f8cdcc81bf95625902f6081cb9' and cc['source']==sources['degree_checker']
creview=dict(cc['Review_ABI']);creview.update(source_contract=ccref,reviewer_identity='/root',source_review_passed=True,
    scientific_calls=0,scientific_acceptance=False,source_only=True,
    authorship_disclosure='Root read whole27,553B checker and11,994B contract. Root did not author checker/proposer/membership/kernel/harness; authored policy/old converter/current caller. This distinct checker review is separate from caller author check.',
    checks=['Twelve original state/tile/legality helpers preserve exact full point data, ordered repeated ports, selected multiplicity/exclusions and current original binding.',
      'Independent carrier uses finite odometer positive compositions and explicit-stack products; complete all constructor/name/scope cases, arity0, term12 and whole44 filters. No proposer import/call.',
      'Complete missing covers independently rebuild every AX/Gamma/UG/orderedMP fibre, including same-row finite-AST empty cases; derived43-|C| bound unchanged.',
      'Every primitive/member/full remote legality decision re-enumerated, entire survivors/root rejections/fibre census counts and both rolling hashes compared; hash claims alone have no authority.',
      'A second survivor rejects a claimed completed missing cover because protocol must return TWO early. Partial fibre arrays remain unverified diagnostics for actual independently checked two keys only.',
      'UNKNOWN never zero/one. Only exact completed OutsideLanguage filters; all timeout/resource/callback/other failures propagate. No graph/proof/RL/resource acceptance.'],
    concrete_blockers=[])
creview_ref=save('ROOT-checker-Source-review-v1.json',creview)
hh=read(BASE/'unit-row-missing-mark-controls-source-20261015/handoff-v2.json');hcref=hh['source_contract'];hc=read(check(hcref))
assert hcref['sha256']=='8e0e33e64cb1e4c61f57c52d6cd4453e697dab3446a9813618eddf558c9859e1' and hc['source']==sources['controls']
hr=save('ROOT-controls-Source-review-v1.json',{'schema':'ROOT-missing-mark-controls-Source-review-v1',
    'source':sources['controls'],'source_contract':hcref,'author_identity':'/root/hilbert_ordering_diagnosis','reviewer_identity':'/root',
    'source_only':True,'source_review_passed':True,'scientific_calls':0,'scientific_acceptance':False,
    'scope':'Complete frozen harness20,072B and8,367B contract; all8 original fixture helpers unchanged, only current API/run/version successor.',
    'checks':['Fresh rerun of original controls, explicit nowZERO missing-prefix vs retained implicationUNKNOWN; original oldactual not relabeled.',
      'Tiny carrier1/2 full direct-reference comparison conditional on original empty predicates, every binder spelling preserved; no full44 registry count.',
      'Deepnot size42 leaves maxA1 actual bot-only ordered MP candidates; size43 leaves maxA0. Original membership/pointstate construction and collision checks required, unavailable fixtures remainSKIPPED.',
      'Exact exclusions are assumed branch contexts; complete missing0/1 requires current independent fibre receipt.',
      'Forged completion/omittedpair/occurscase/count/twohash/missingoutcome/bound controls require genuine current checker rejection, not callback failure.',
      'Original native tick retained under three injected callback controls; full evidence returned, no solver/proof/resource claim.'],
    'authorship_disclosure':'Root did not author harness/checker/proposer but authored policy and caller; all scientific calls0.'})
rr=dict(contract['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,
    source_only=True,scientific_calls=0,scientific_acceptance=False,
    authorship_disclosure='Root authored caller: this is an AUTHOR Source/AST check, not independent caller review. Distinct whole peer and Root distinct checker/harness reviews are separate.',
    checks=['All15 old helper ASTs exact; main inverseAST exact after removing carrier adapter and carrier argument.',
      'Same original Source7/input2, full original authority/fresh language per endpoint, native gates20/512/55/60/90+1, meter2/once driver and complete output2/twoLF/direct exit.',
      'Direct carrier wrapper literal1/2 and<=1000 entries only tests small EOF; full public/checker profile generator unchanged. Native tick precedes injected callback and all actual iteration is inside guarded harness delegation.',
      'No saved word/donor/library or new proof/GCTS/graph/rollback/RL/benefit acceptance. Known synchronous Source scope, no hostile Python/OS guarantee.'])
rrref=save('ROOT-caller-author-Source-review-v1.json',rr)
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
protocol=save('ROOT-protocol-choice-v1.json',{'schema':'ROOT-missing-mark-degree-protocol-choice-v1',
    'previous_goal_turn':'progress','endpoint':'Complete fresh old+missing-mark controls, including tiny generator and new complete inverse-fibre0/1 cases, or UNKNOWN.',
    'sources':sources,'inputs':inputs,'limits':limits,'old_actual_unchanged':True,
    'expected_original_theory_case_counts':{'total':36,'passed':35,'unreachable_skip':1},
    'cost_scope':'All cold setup, fixture creation, three fresh endpoint wrappers, generation/re-enumeration/all controls/output/exit/postterminal probe.',
    'complete_graph_or_proof_or_GCTS_or_RL_claim':False,'scientific_execution_occurred':False})
owned=HERE/'missing-owned-v1';external=HERE/'missing-external-v1';assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-missing-mark-degree-controls-20261015-v1','purpose':'unit-row-local-degree-controls',
    'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,'reviews':{'ROOT':rrref,'peer':pin(peer_path)},
    'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-authorization-v1.json',dict(common,schema='ROOT-unit-row-degree-controls-authorization-v1',author_identity='/root',
    actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,
    dependency_reviews={'proposer':pin(prpath),'checker':creview_ref,'controls':hr}))
plan=save('ROOT-plan-v1.json',dict(common,schema='ROOT-unit-row-degree-controls-plan-v1',ROOT_authorization=grant))
save('ROOT-preflight-v1.json',{'schema':'ROOT-missing-mark-degree-preflight-v1','plan':plan,'scientific_calls':0,'actual_execution_occurred':False,'fresh_output_and_external':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
