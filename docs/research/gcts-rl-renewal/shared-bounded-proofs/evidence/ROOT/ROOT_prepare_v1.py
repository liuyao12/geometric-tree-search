"""Root small metadata/Source-AST preparation only; no scientific imports/calls."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
HANDOFF=BASE/'shared-bounded-ordinary-cold-source-20261015'/'handoff-v1.json'
PEER=BASE/'shared-bounded-ordinary-cold-independent-source-20261015'/'typed-Source-review-v1.json'
MODULES=BASE/'shared-bounded-language-independent-source-20261015'/'handoff-v2.json'
RUNTIME=Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(path):return json.loads(path.read_bytes())
def check(ref):
    path=Path(ref['path']);assert path.is_absolute() and path==path.resolve()
    assert pin(path)==ref
    return path
def write(name,value):
    path=ROOT/name
    with path.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
    return pin(path)

assert pin(HANDOFF)['sha256']=='bce6c9363878e407dab92a317400ebb6f10f2c70ea46f064656483ac31954d22'
handoff=read(HANDOFF)
sources=handoff['sources'];inputs=handoff['inputs'];contract_ref=handoff['source_contract']
assert sources['intake']['sha256']=='f804bac13bf2b69f1d223a947ef8108298124f1350ab2e91f3cc06631a57d067'
assert contract_ref['sha256']=='99ff0726969678a2576b24feea33cbb6d81c91598649d0b181d4a4837626df26'
for ref in [*sources.values(),*inputs.values(),contract_ref]:check(ref)
contract=read(check(contract_ref))
assert contract['sources']==sources and contract['inputs']==inputs
limits=contract['limits']
assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,
               'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
peer=read(PEER)
assert pin(PEER)['sha256']=='4155bfb336d372c3f17259e0b1f0acba02b45a760215ce08a22faf0199e59a57'
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==contract_ref
assert peer['scope']==contract['scope'] and peer['reviewer_identity']=='/root/hilbert_advice_controls'
assert peer['author_identity']=='/root/hilbert_ordering_diagnosis' and peer['source_only'] is True
assert peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
module_handoff=read(MODULES)
assert module_handoff['source_review_passed'] is True and module_handoff['concrete_blockers']==[]
assert all(module_handoff['sources'][role]==sources[role] for role in ('membership','proposer'))
dependency_reviews={}
for role in ('membership','proposer'):
    ref=module_handoff[role+'_review'];review=read(check(ref))
    assert review['source']==sources[role] and review['source_review_passed'] is True
    assert review['reviewer_identity']=='/root/arithmetic_induction' and review['scientific_calls']==0
    assert review['scientific_acceptance'] is False
    dependency_reviews[role]=ref
parent=check(contract['provenance']['parent_helpers'])
oldtree=ast.parse(parent.read_bytes());tree=ast.parse(check(sources['intake']).read_bytes())
olddefs={node.name:node for node in oldtree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
defs={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
helpers=contract['provenance']['copied_helpers']
assert len(helpers)==15 and set(defs)==set(helpers)|{'main'}
for name in helpers:assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
compile(tree,sources['intake']['path'],'exec')
runtime=pin(RUNTIME)
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
review=dict(contract['Review_ABI'])
for key in ('reviewers','required'):review.pop(key,None)
review.update(reviewer_identity='/root',source_contract=contract_ref,source_only=True,
              source_review_passed=True,scientific_calls=0,scientific_acceptance=False)
review['authorship_disclosure']='Root authored the policy and separate unexecuted point converter, not this intake or its membership/proposer/kernel/1717 Sources. Whole intakeV1 read with the formerly truncated middle reread, exact V2 pin/version delta read; both new module Sources read whole with exact narrow V2 exception repair.'
review['scope_limit']='Reviewed fixed synchronous Sources and exact current native Darwin caller only; no hostile Python/OS VM claim or actual/fit prediction.'
review['evidence']={'helpers_AST_exact':helpers,'all_Source_and_input_pins_revalidated':True,
                    'current_dependency_reviews':dependency_reviews,
                    'checks':['Exact Source6/input2/plan12 and original runtime.',
                              'No catalogue, donor, library, word or target-route input.',
                              'Private authenticated raw declaration/profile and independent original authority.',
                              'Full Source and original caller guards around delegates; native-only interior ticks.',
                              'Exported OutsideLanguage class reference is included in sealed membership class/module bindings.',
                              'Discard producer-held language and reauthenticate both whole raw inputs.',
                              'Fresh private language checks every expanded command and complete binding.',
                              'Unchanged1717 receives freshly decoded original theory/parameters/Gamma/target.',
                              'Negative heuristic return remains UNKNOWN; no ground count or full graph claim.',
                              'Complete exclusive output3 and two-line response with raw EOF/digests.',
                              'Original20/512/55/60/90+1 and final native cancellation/exit paths.']}
root_review=write('ROOT-Source-review-v1.json',review)
protocol=write('ROOT-protocol-choice-v1.json',{
    'schema':'ROOT-shared-bounded-ordinary-positive-protocol-choice-v1',
    'purpose':'shared-bounded-ordinary-positive-word','previous_goal_turn':'progress',
    'profile':inputs['profile'],'declaration':inputs['declaration'],
    'endpoint':'First fresh automatically proposed <=24-command word for the original closed right-two target, or UNKNOWN.',
    'new_controls':'No synthetic proof word or theorem route is supplied. This first production-same search is followed by full fresh membership and unchanged independently qualified1717 word checking. New palette/count/point controls are not inferred from it.',
    'unchanged_checker_control_scope':'Historical checker qualification belongs to unchanged1717 only; it is not new-language enumeration/count/legacy-embedding evidence.',
    'preserve':'V1 generic exception-boundary negative and every prior old-profile UNKNOWN/finite-negative remain distinct.',
    'native_rule':'One owned process, no descendants, true terminal B=T and native launch-to-fresh-postprobe strictly below20s.',
    'limits':limits,'scientific_execution_occurred':False,
    'no_GCTS_RL_fullboard_count_or_legacy_claim':True})
invocation='shared-bounded-right-two-ordinary-20261015-v1'
output=ROOT/'ordinary-owned-v1';external=ROOT/'ordinary-external-v1'
assert not output.exists() and not external.exists()
common={'invocation_id':invocation,'purpose':'shared-bounded-ordinary-positive-word',
        'output_directory':str(output),'sources':sources,'inputs':inputs,'source_contract':contract_ref,
        'reviews':{'ROOT':root_review,'peer':pin(PEER)},'runtime':runtime,'limits':limits,
        'resource_rule':'single-owned-process-native-terminal-v1'}
grant=write('ROOT-authorization-v1.json',dict(common,
    schema='ROOT-shared-bounded-ordinary-positive-authorization-v1',author_identity='/root',
    actual_execution_authorized=True,maximum_actual_invocations=1,
    protocol_choice=protocol,dependency_reviews=dependency_reviews,
    authority_scope='Root actual permission for this one frozen experiment only; no result is assumed.'))
plan=write('ROOT-plan-v1.json',dict(common,schema='ROOT-shared-bounded-ordinary-positive-plan-v1',ROOT_authorization=grant))
write('ROOT-preflight-v1.json',{'schema':'ROOT-shared-bounded-ordinary-positive-preflight-v1',
    'plan':plan,'output_directory_absent':True,'external_directory_absent':True,
    'sources':sources,'inputs':inputs,'dependency_reviews':dependency_reviews,
    'source_only_metadata_preparation':True,'scientific_calls':0,'actual_execution_occurred':False})
print(json.dumps({'plan':plan,'external_directory':str(external),'invocation_id':invocation}))
