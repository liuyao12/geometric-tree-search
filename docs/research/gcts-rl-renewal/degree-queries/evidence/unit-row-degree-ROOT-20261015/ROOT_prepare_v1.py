"""Only Source/AST/raw hashes and small reviews/plans. No scientific execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    p=Path(ref['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==ref;return p
def write(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
assert len(sys.argv)==3
peer_path=Path(sys.argv[1]);assert pin(peer_path)['sha256']==sys.argv[2]
hpath=BASE/'unit-row-degree-cold-ROOT-source-20261015/handoff-v1.json'
assert pin(hpath)['sha256']=='285ac8bd808b2ebc0dbbcebc691f989b9dbd74f521d6b3e0fc5fc13e5a4ffa61'
h=read(hpath);sources=h['sources'];inputs=h['inputs'];contract_ref=h['source_contract']
contract=read(check(contract_ref));assert sources['intake']['sha256']=='212ea04d6ff212256f1b0195ead617a4e6b3eccdd775874387e0d1848a157c1d'
assert contract_ref['sha256']=='0ff823ef165bfbc2f3d78ae8a90a0ff3d181eeb72d30c188fa94d3cb8475dc4f'
assert contract['sources']==sources and contract['inputs']==inputs and len(sources)==7 and len(inputs)==2
for ref in [*sources.values(),*inputs.values()]:check(ref)
for ref in sources.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==contract_ref
assert peer['reviewer_identity']=='/root/hilbert_advice_controls' and peer['author_identity']=='/root'
assert peer['scope']==contract['scope'] and peer['source_only'] is True and peer['source_review_passed'] is True
assert peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
proposer_review=BASE/'unit-row-implicit-degree-independent-source-20261015/typed-Source-review-v2.json'
assert pin(proposer_review)['sha256']=='d595b0fadedb96fd2adad777c5b030904e3979fc3e6dd6ee70dc98bfdcda0bf9'
assert read(proposer_review)['source']==sources['proposer'] and read(proposer_review)['source_review_passed'] is True
checker_review=BASE/'unit-row-degree-checker-source-20261015/ROOT-typed-Source-review-v1.json'
assert pin(checker_review)['sha256']=='dde6273a8e38c3a3d781f7c20e98086b7db2f6bebaeb74ddf471427599906ec7'
assert read(checker_review)['source']==sources['degree_checker'] and read(checker_review)['source_review_passed'] is True
hcpath=BASE/'unit-row-degree-controls-source-20261015/Source-contract-v1.json'
hc=read(hcpath);assert pin(hcpath)['sha256']=='2a37f4253068752320f6dd5f72eefe2ec9afaca754ffb8c7d7c10273f73ae1c2'
assert hc['source']==sources['controls']
harness_review=write('ROOT-controls-Source-review-v1.json',{
    'schema':'ROOT-unit-row-degree-controls-Source-review-v1','scope':hc['scope'],
    'author_identity':'/root/hilbert_ordering_diagnosis','reviewer_identity':'/root',
    'source':sources['controls'],'source_contract':pin(hcpath),'source_only':True,
    'source_review_passed':True,'scientific_calls':0,'scientific_acceptance':False,
    'authorship_disclosure':'Root read whole frozen13,982B Source and7,568B contract; Root did not author this harness, proposer, checker or membership, but authored policy/earlier converter/current caller.',
    'checks':['Whole original-context AX/UG-derived state composition, no saved proof word/library.',
        'Exact ZERO/SINGLETON/MANY receipts conditional on completed restricted census; missing-prefix/imp fixtures UNKNOWN.',
        'Original names/occurrence multiplicities preserved; exclusions are explicit branch assumptions, not justified pruning.',
        'TWO remote conflicting member actually reaches whole candidate legality rejection.',
        'Malformed evidence/private state/flags/full key/missing survivor rejections retain exact failures.',
        'SKIPPED original-unavailable or unreachable fixture never counted as pass; no theory change.',
        'Injected17-call callback exhaustion calls original native tick and propagates exact declared exception; no internal-phase claim.',
        'Full state/proposals/receipts returned; no graph/solver/proof/RL/resource acceptance.']})
root_review=dict(contract['Review_ABI']);root_review.update(source_contract=contract_ref,reviewer_identity='/root',
    source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,
    authorship_disclosure='Root AUTHORED caller: this is an author Source/AST check, not independent caller review. Genuine distinct whole caller peer is retained separately. Root independently reviewed checker/harness.',
    checks=['All15 helper ASTs copied unchanged from reviewed point-cold Source; original external once/meter2/runtime retained.',
      'Original Source7/input2/plan12/schema/six caps. No saved word/donor/library input.',
      'Private full original inputs reauthenticated; distinct fresh language for each proposer/checker; full epoch fixed.',
      'Native tick always runs before optional injected callback, with resource query before native timestamp.',
      'Known synchronous Source/default/callback guards and full output2/two-line wire/final direct exit; no hostile Python/OS claim.',
      'Only local control evidence; no search/graph/trajectory/proof/RL/benefit acceptance.'])
root_ref=write('ROOT-caller-author-Source-review-v1.json',root_review)
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
protocol=write('ROOT-protocol-choice-v1.json',{'schema':'ROOT-unit-row-degree-protocol-choice-v1',
    'previous_goal_turn':'progress','endpoint':'Once-only complete original-theory local-degree controls, or UNKNOWN.',
    'original_model_unchanged':True,'sources':sources,'inputs':inputs,'limits':limits,
    'cost_scope':'Entire cold setup, all fixture/proposer/checker/callback controls, output, exit and fresh native postterminal probe.',
    'logical_proof_or_GCTS_search_claim':False,'scientific_execution_occurred':False})
owned=HERE/'degree-owned-v1';external=HERE/'degree-external-v1';assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-local-degree-controls-20261015-v1','purpose':'unit-row-local-degree-controls',
    'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':contract_ref,
    'reviews':{'ROOT':root_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=write('ROOT-authorization-v1.json',dict(common,schema='ROOT-unit-row-degree-controls-authorization-v1',
    author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,
    protocol_choice=protocol,dependency_reviews={'proposer':pin(proposer_review),'checker':pin(checker_review),'controls':harness_review}))
plan=write('ROOT-plan-v1.json',dict(common,schema='ROOT-unit-row-degree-controls-plan-v1',ROOT_authorization=grant))
write('ROOT-preflight-v1.json',{'schema':'ROOT-unit-row-degree-preflight-v1','plan':plan,'actual_execution_occurred':False,
    'scientific_calls':0,'fresh_owned_and_external':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
