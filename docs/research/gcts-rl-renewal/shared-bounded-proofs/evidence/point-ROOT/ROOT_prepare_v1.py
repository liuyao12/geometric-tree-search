"""Source/AST and small plan/review metadata only; no scientific imports/calls."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
HANDOFF=BASE/'shared-bounded-point-board-cold-source-20261015/handoff-v1.json'
RUNTIME=Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    path=Path(ref['path']);assert path.is_absolute() and path==path.resolve() and pin(path)==ref;return path
def write(name,value):
    path=ROOT/name
    with path.open('x') as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n')
    return pin(path)
assert len(sys.argv)==3
peer_path=Path(sys.argv[1]);assert pin(peer_path)['sha256']==sys.argv[2]
assert pin(HANDOFF)['sha256']=='6235deaff0b7f0168e697b0433f1c9484968e7061cd50cb84cc2da4d80d8618b'
handoff=read(HANDOFF);sources=handoff['sources'];inputs=handoff['inputs'];contract_ref=handoff['source_contract']
assert len(sources)==7 and len(inputs)==3
assert sources['intake']['sha256']=='dd7a1a13829c63d41935038327c063a7089b2c3e28d28c20f4743ebcd6ec7be2'
assert contract_ref['sha256']=='19944feb69ddf1f0080cc5b7d2dc90c2711eeb9ed96d667bd8ff915e798809c0'
for ref in [*sources.values(),*inputs.values(),contract_ref]:check(ref)
contract=read(check(contract_ref));limits=contract['limits']
assert contract['schema']=='shared-bounded-point-board-verification-cold-Source-contract-v1'
assert contract['sources']==sources and contract['inputs']==inputs
assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==contract_ref
assert peer['scope']==contract['scope'] and peer['reviewer_identity']=='/root/hilbert_advice_controls'
assert peer['author_identity']=='/root/hilbert_ordering_diagnosis' and peer['source_only'] is True
assert peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
tree=ast.parse(check(sources['intake']).read_bytes());compile(tree,sources['intake']['path'],'exec')
parent_tree=ast.parse(check(contract['provenance']['parent_intake']).read_bytes())
defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
parent_defs={n.name:n for n in parent_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
helpers=contract['provenance']['copied15_helpers'];assert len(helpers)==15
for name in helpers:assert ast.dump(defs[name],include_attributes=False)==ast.dump(parent_defs[name],include_attributes=False)
assigns={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('FIXED','FIXED_INPUTS','LIMITS')}
assert assigns['FIXED']=={k:v for k,v in sources.items() if k!='intake'} and assigns['FIXED_INPUTS']==inputs and assigns['LIMITS']==limits
dependency_reviews={
 'converter':BASE/'shared-bounded-point-board-independent-source-20261015/converter-typed-Source-review-v1.json',
 'point_checker':BASE/'shared-bounded-point-board-source-20261015/ROOT-point-checker-Source-review-v1.json',
 'membership':BASE/'shared-bounded-language-independent-source-20261015/membership-typed-Source-review-v3.json'}
expected={'converter':'d211db0126c0404cc67863289c248ca7703652e18106d99ad055243d4499b862',
          'point_checker':'31d056594e6d2ace64b915efb4c41bc575966718cd814596eb315809ac055e5c',
          'membership':'64ee4adb46ba82693685a802456e74d6186bdaa5722dafd19e641bdb5ccc74ca'}
for role,path in dependency_reviews.items():
    review=read(path);assert pin(path)['sha256']==expected[role]
    assert review['source']==sources[role] and review['source_review_passed'] is True and review['scientific_calls']==0 and review['scientific_acceptance'] is False
dependency_reviews={k:pin(v) for k,v in dependency_reviews.items()}
prior=BASE/'shared-bounded-ordinary-ROOT-20261015/ROOT-ordinary-disposition-v2.json'
assert pin(prior)['sha256']=='14cd600bfa4df80d52badcaa4423e320befe0d13f2cf8f6d3ca7a041be84c4dc' and read(prior)['target_proof_accepted'] is True
runtime=pin(RUNTIME);assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
review=dict(contract['Review_ABI'])
for key in ('required','reviewers'):review.pop(key,None)
review.update(reviewer_identity='/root',source_contract=contract_ref,source_only=True,source_review_passed=True,scientific_calls=0,scientific_acceptance=False)
review['authorship_disclosure']='Root authored policy and untrusted point converter, not this intake, independent point checker, membership, kernel or1717. Root read whole current55,225B intake and18,227B contract; formerly truncated435-525 lines reread. Distinct current module reviews and whole intake peer remain separate.'
review['checks']=[
 'Source7/input3/plan12, operative consumed schema, original fixed limits and all15 parent helpers match.',
 'Previously discovered full17-command word is untrusted data; historical Source6 binding never confers current authority.',
 'Private currentSource7 language epoch governs all point values and complete word membership.',
 'Whole original word checks before converter; no search rerun or supplied-word discovery claim.',
 'All three full raw inputs reauthenticated after untrusted converter; fresh private language and original target/context rebuilt.',
 'All14 negative packet calls use unchanged private originals and genuine independent checker. Only exact expected reconstruction ValueErrors accepted; native/source faults propagate.',
 'Positive independent checker reconstructs and compares whole packet then all actual unit totals/marking occurrences.',
 'Entire padded24-command word comes from independent reconstruction, receives fresh membership and unchanged1717 against original private target.',
 'All output4 files/raw EOF/two-line completion/full stdout and final Source/native cancellation/exit paths preserved.',
 'No complete candidate graph/scheduler/rollback/trajectory/native-Wang/learned-marking/RL/count or search-speed admission.' ]
root_review=write('ROOT-Source-review-v1.json',review)
protocol=write('ROOT-protocol-choice-v1.json',{
 'schema':'ROOT-shared-bounded-point-board-protocol-choice-v1','previous_goal_turn':'progress','sources':sources,'inputs':inputs,
 'prior_successful_search':pin(prior),'endpoint':'Complete positive24-row translated point board of the actual discovered17-command word, or UNKNOWN.',
 'controls':'All14 isolated packet mutations must reject at genuine exact reconstruction; positive packet must exercise whole unit and literal marking accumulation. No negative accumulator-branch coverage claimed.',
 'cost_scope':'Separate cold verification stage; all original/padded membership and1717, converter, point checks,14 controls, Source/input/output/exit costs inside same original20/512. Prior search and failed attempt remain separate, never joint20.',
 'scope':'Positive finite point-board verification only. No GCTS search, candidate counts, trajectory, new theorem discovery, universal palette, RL or contribution benefit.',
 'limits':limits,'scientific_execution_occurred':False})
invocation='shared-bounded-right-two-point-board-20261015-v1';owned=ROOT/'point-owned-v1';external=ROOT/'point-external-v1'
assert not owned.exists() and not external.exists()
common={'invocation_id':invocation,'purpose':'shared-bounded-point-board-verification','output_directory':str(owned),
 'sources':sources,'inputs':inputs,'source_contract':contract_ref,'reviews':{'ROOT':root_review,'peer':pin(peer_path)},
 'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=write('ROOT-authorization-v1.json',dict(common,schema='ROOT-shared-bounded-point-board-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dependency_reviews))
plan=write('ROOT-plan-v1.json',dict(common,schema='ROOT-shared-bounded-point-board-plan-v1',ROOT_authorization=grant))
write('ROOT-preflight-v1.json',{'schema':'ROOT-shared-bounded-point-board-preflight-v1','plan':plan,'scientific_calls':0,'actual_execution_occurred':False,'output_directory_absent':True,'external_directory_absent':True,'helpers_AST_exact':helpers})
print(json.dumps({'plan':plan,'external_directory':str(external),'invocation_id':invocation}))
