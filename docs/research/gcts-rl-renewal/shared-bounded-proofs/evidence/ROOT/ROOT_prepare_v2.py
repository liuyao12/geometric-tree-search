"""Root Source/AST and small metadata only; no scientific imports or calls."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
HANDOFF=BASE/'shared-bounded-ordinary-cold-source-20261015'/'handoff-v3.json'
MODULES=BASE/'shared-bounded-language-independent-source-20261015'/'handoff-v3.json'
RUNTIME=Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    path=Path(ref['path']);assert path.is_absolute() and path==path.resolve() and pin(path)==ref
    return path
def write(name,value):
    path=ROOT/name
    with path.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
    return pin(path)

assert len(sys.argv)==3
PEER=Path(sys.argv[1]);expected_peer=sys.argv[2]
assert pin(PEER)['sha256']==expected_peer
assert pin(HANDOFF)['sha256']=='01366cc20f9d2833ea46b6dffc0160168accc9860c1eb1f0dd9c17927e271e9f'
handoff=read(HANDOFF);sources=handoff['sources'];inputs=handoff['inputs'];contract_ref=handoff['source_contract']
assert sources['intake']['sha256']=='cd3fd500ccdcda59347e76ad06c3a7d1834076fd2759b066040529556148a389'
assert sources['proposer']['sha256']=='6cf0bf560d9426ef6e3acb5c7fd94981f8cdb4dbb8383b74747d01bb76158a8a'
assert contract_ref['sha256']=='4987f8074fa637d66c9ae1063aa9539da958b0debbc4fbea5a07def5d0bb6cdd'
for ref in [*sources.values(),*inputs.values(),contract_ref]:check(ref)
contract=read(check(contract_ref));limits=contract['limits']
assert contract['schema']=='shared-bounded-ordinary-positive-cold-Source-contract-v1'
assert contract['sources']==sources and contract['inputs']==inputs
assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,
               'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
peer=read(PEER)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==contract_ref
assert peer['scope']==contract['scope'] and peer['reviewer_identity']=='/root/hilbert_advice_controls'
assert peer['author_identity']=='/root/hilbert_ordering_diagnosis' and peer['source_only'] is True
assert peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
assert pin(MODULES)['sha256']=='3d7271bc2a7cab55bbd38f8208972168fd567dcec75b35c2213380b67ae2d839'
module_handoff=read(MODULES)
assert module_handoff['source_review_passed'] is True and module_handoff['concrete_soundness_blockers']==[]
assert module_handoff['advisories']==['V3-TERM-ONLY-QUIESCENCE-1']
dependency_reviews={}
for role,key in [('membership','membership_applicability'),('proposer','proposer_review')]:
    ref=module_handoff[key];review=read(check(ref))
    assert review['source']==sources[role] and review['source_review_passed'] is True
    assert review['reviewer_identity']=='/root/arithmetic_induction' and review['scientific_calls']==0 and review['scientific_acceptance'] is False
    dependency_reviews[role]=ref
oldpath=BASE/'shared-bounded-ordinary-cold-source-20261015'/'bounded_ordinary_intake_v2.py'
oldraw=oldpath.read_bytes();raw=check(sources['intake']).read_bytes()
assert hashlib.sha256(oldraw).hexdigest()=='f804bac13bf2b69f1d223a947ef8108298124f1350ab2e91f3cc06631a57d067'
oldtree=ast.parse(oldraw);tree=ast.parse(raw)
olddefs={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert len(defs)==16 and set(defs)==set(olddefs)
for name in defs:assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
oldassign={n.targets[0].id:ast.literal_eval(n.value) for n in oldtree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('FIXED','FIXED_INPUTS','LIMITS','VERSION')}
newassign={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in oldassign}
assert newassign['FIXED_INPUTS']==oldassign['FIXED_INPUTS']==inputs and newassign['LIMITS']==oldassign['LIMITS']==limits
assert newassign['FIXED']=={k:v for k,v in sources.items() if k!='intake'}
assert all(newassign['FIXED'][k]==oldassign['FIXED'][k] for k in oldassign['FIXED'] if k!='proposer')
compile(tree,sources['intake']['path'],'exec')
runtime=pin(RUNTIME)
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
review=dict(contract['Review_ABI'])
for key in ('reviewers','required'):review.pop(key,None)
review.update(reviewer_identity='/root',source_contract=contract_ref,source_only=True,
              source_review_passed=True,scientific_calls=0,scientific_acceptance=False)
review['authorship_disclosure']='Root authored policy and separate unexecuted point converter, not intake or membership/proposer/kernel/1717. Whole prior intake reviewed; exact current pin/VERSION delta, operative schema and whole producerV3 read. Distinct current producer and intake reviews retained.'
review['evidence']={'all16_definitions_AST_exact':sorted(defs),'original_inputs_and_limits_exact':True,
                    'genuine_current_dependency_reviews':dependency_reviews,'corrected_consumed_contract_schema_checked':True,
                    'checks':['Whole original private authority and fresh reauthentication/membership/unchanged1717 flow unchanged.',
                              'Full Source and direct caller guards, complete outputs/wire and native gates unchanged.',
                              'Producer V3 derives facts only from actual original premises and expanded checked primitives.',
                              'Literal target matching and pending transport watches are heuristic hints, never accepted facts.',
                              'Every extracted node ancestry remains acyclic, strict-prior and at most24 commands.',
                              'No target-specific symbol, intermediate word, donor or library is supplied.',
                              'Current code/metadata are Source only; no success, fit or search completeness is inferred.']}
review['explicit_heuristic_advisory']='V3-TERM-ONLY-QUIESCENCE-1: a new retained term without a fact change need not receive another wave. No every-new-term or exhaustion claim.'
root_review=write('ROOT-Source-review-v2.json',review)
protocol=write('ROOT-protocol-choice-v2.json',{
    'schema':'ROOT-shared-bounded-ordinary-positive-protocol-choice-v1','purpose':'shared-bounded-ordinary-positive-word',
    'previous_goal_turn':'progress','profile':inputs['profile'],'declaration':inputs['declaration'],
    'endpoint':'Fresh automatically proposed <=24-command word for the unchanged original closed right-two target, or UNKNOWN.',
    'comparison':'Same language, original logical inputs, all6 heuristic scalar limits, cold checker and native gates; different incomplete producer scheduling and generic goal closure hints.',
    'preserved_prior_actual':pin(ROOT/'ROOT-ordinary-disposition-v1.json'),
    'preserved_unexecuted_negative_contract':pin(BASE/'shared-bounded-ordinary-cold-source-20261015'/'Source-contract-v2.json'),
    'new_controls':'No supplied proof word or theorem route. Fresh complete membership and unchanged independently qualified1717 on any returned word. No new finite-count/GCTS/point controls inferred.',
    'advisory':review['explicit_heuristic_advisory'],
    'scope':'One ordinary search/check attempt only; no GCTS/RL, point/full24, legacy embedding, complete syntax enumeration or advantage claim.',
    'native_rule':'One owned process; no descendants; true terminal B=T; launch through fresh postprobe strictly below20s.',
    'limits':limits,'scientific_execution_occurred':False})
invocation='shared-bounded-right-two-ordinary-20261015-v2'
output=ROOT/'ordinary-owned-v2';external=ROOT/'ordinary-external-v2'
assert not output.exists() and not external.exists()
common={'invocation_id':invocation,'purpose':'shared-bounded-ordinary-positive-word','output_directory':str(output),
        'sources':sources,'inputs':inputs,'source_contract':contract_ref,'reviews':{'ROOT':root_review,'peer':pin(PEER)},
        'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=write('ROOT-authorization-v2.json',dict(common,schema='ROOT-shared-bounded-ordinary-positive-authorization-v1',
    author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,
    protocol_choice=protocol,dependency_reviews=dependency_reviews,
    authority_scope='Root authorizes this one frozen experiment only; no result or whole-profile admission is assumed.'))
plan=write('ROOT-plan-v2.json',dict(common,schema='ROOT-shared-bounded-ordinary-positive-plan-v1',ROOT_authorization=grant))
write('ROOT-preflight-v2.json',{'schema':'ROOT-shared-bounded-ordinary-positive-preflight-v1','plan':plan,
    'output_directory_absent':True,'external_directory_absent':True,'sources':sources,'inputs':inputs,
    'dependency_reviews':dependency_reviews,'scientific_calls':0,'actual_execution_occurred':False})
print(json.dumps({'plan':plan,'external_directory':str(external),'invocation_id':invocation}))
