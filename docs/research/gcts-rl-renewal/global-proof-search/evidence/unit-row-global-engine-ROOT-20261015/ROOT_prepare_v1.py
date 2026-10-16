"""Frozen Source/review/plan metadata only. No project or mathematical calls."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    return pin(p)
def common_save(name,value):
    p=HERE/name
    if p.exists():assert read(p)==value;return pin(p)
    return save(name,value)
assert len(sys.argv)==4
mode,peer_name,peer_sha=sys.argv[1:];assert mode in ('controls','search')
peer_path=Path(peer_name);assert pin(peer_path)['sha256']==peer_sha
hpath=BASE/'unit-row-global-cold-ROOT-source-20261015/handoff-v1.json'
assert pin(hpath)['sha256']=='d36ed12ca5503a6d52084aacc2e60f0e338b60e59c88c5b849d283340163b453'
h=read(hpath);sources,inputs,cr=h['sources'],h['inputs'],h['source_contract'];contract=read(check(cr))
assert sources['intake']['sha256']=='4e83784213ae01805648bac7ba8787842db846fabf037b8f3f6a56d5978d6ff2' and sources['intake']['bytes']==25792
assert cr['sha256']=='1dc66c42243725e0f27b3c6172bce11249835717f5749b86ed015d19f3843b7b'
assert contract['sources']==sources and contract['inputs']==inputs and len(sources)==9 and len(inputs)==2
assert sources['engine']['sha256']=='ebd4b3eb9ef708525c6ce629d7619d6c3241cc0046afe3852ec9423af9f5197e'
assert sources['fallback']['sha256']=='69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae'
assert sources['controls']['sha256']=='d7b0c0f6776e6b383e92e270f559e9b8978523a5ac5cfd91ec283996e214e4d7'
for ref in [*sources.values(),*inputs.values()]:check(ref)
for ref in sources.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==cr
assert peer['scope']==contract['scope'] and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
assert peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
dependency_reviews={}
for role,folder,checks in [
 ('fallback','unit-row-all-six-fallback-source-20261015',[
 'Whole24,227B Source and14,336B contract read. Exact lexical size grammar and all six literal rule families; necessary UI42/UG43/MP43 and atomic template bounds preserve entire declared inventory.',
 'Full keys include original epoch/witness/ordered repeated premises/offsets/translation. Whole primitive and t/m legality rechecked; pending marks are obligations.',
 'Real per-rule complete markers, permanent cursor poison, native callback failure not EOF. Generic complete lazy path retained; no arbitrary EOF authority or resource fit claim.']),
 ('engine','unit-row-lazy-global-engine-source-20261015',[
 'Whole27,865B Source and13,491B V1 contract read. Complete global cheap queries, certified ZERO before forced/branch, UNKNOWN blocks positive decision, ROW-TIE within earliest generation.',
 'New alternatives independently reconstructed by currentc354. Same-state cursor replay validates consumed full prefix; EOF zero/one/exhaustion requires a fresh independent completed cover with exact entire key agreement.',
 'Copy-on-write checkpoint contains point totals, m union/refcounts, selected/excluded keys, root generations, revision/versions, certificates, logical cursor prefixes, observed incidences and reverse dependencies. Live cursors discarded/replayed.',
 'Only proved childEXHAUSTED creates parent exclusion; UNKNOWN cannot prune, caps never exhaust. Deepest interrupted state captured before unwind, root and all stack contexts restored.',
 'Explicit gap: ALL24 invalidation does not retain unaffected domains (master4). Specialized unit-row ROW-TIE+ALL24-REBIND variant, not complete reference incremental conformance/acceleration. Public place needs caller checkpoint/finally after installation errors.']),
 ('controls','unit-row-lazy-engine-controls-source-20261015',[
 'Whole21,896B Source and13,405B contract read. Seventeen prospective cases; original AX/Gamma/parameter/target stay unchanged and all fixture memberships validated inside actual.',
 'Genuine late dead before earlier singleton, global forced before branching, remote mark invalidates unseen reverse MP key, exact whole cursor/dependency rollback and ordered alternatives.',
 'Exact completed current cover needed for one-key EOF; missing survivor rejects. Interruptions delegate real cursors and never fabricate EOF, unknown child restoration/no EXCLUDE challenged.',
 'Two pure synthetic scheduler controls explicitly NONLOGICAL; manual transaction cases not scheduled reference traces. Assumed branch exclusions not learned pruning. All actual admission remains pending.'])]:
    handoff_name='handoff-v2.json' if role=='engine' else 'handoff-v1.json'
    dep_h=read(BASE/folder/handoff_name);dep_cr=dep_h['source_contract'];dep_contract=read(check(dep_cr));assert dep_contract['source']==sources[role]
    if role=='engine':
        assert dep_cr['sha256']=='a7356f8f0f977fe8acaa514d2003991ba71f6db7960d5404846ad65fe09bedb0'
        checks[0]='Whole27,865B Source,13,491B V1 and16,287B currentV2 contracts read. Complete global cheap queries, certified ZERO before forced/branch, UNKNOWN blocks positive decision, ROW-TIE within earliest generation.'
    review=dict(dep_contract['Review_ABI']);review.update(source_contract=dep_cr,reviewer_identity='/root',source_only=True,
      source_review_passed=True,scientific_calls=0,scientific_acceptance=False,checks=checks,concrete_blockers=[],
      authorship_disclosure='Root did not author this dependency; Root authored the cold caller and policy. Distinct dependency Source review, not runtime/caller-independent admission.')
    dependency_reviews[role]=common_save('ROOT-'+role+'-Source-review-v1.json',review)
author=dict(contract['Review_ABI']);author.update(source_contract=cr,reviewer_identity='/root',source_only=True,
 source_review_passed=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],
 authorship_disclosure='Root authored caller. This is an AUTHOR check; genuine distinct whole caller review is separate.',
 checks=['All15 original helper ASTs unchanged; complete Source9/input2/native/output/exit lifecycle retained.',
 'Two exact grant purposes, no supplied word/library/donor or route in original-root search. Control seams remain scoped.',
 'Private original authority per proposer/cursor/completion and per-engine semantics. Native tick precedes every injected tick. Whole surrounding endpoint Source guards; no per-method/yield seal claimed.',
 'Original20/512MiB/55/60/90+1 and same native meter2/once driver. All strong admission flags false; complete output2/two-LF/native postprobe still required.'])
author_ref=common_save('ROOT-caller-author-Source-review-v1.json',author)
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
if mode=='search':
    admitted=read(HERE/'ROOT-controls-disposition-v1.json')
    assert admitted['controls_accepted'] is True and admitted['native_resources_qualified'] is True
    assert admitted['passed_cases']==17 and admitted['skipped_cases']==0
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{
 'schema':'ROOT-unit-row-global-engine-protocol-choice-v1','previous_goal_turn':'progress',
 'endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution_occurred':False,
 'expected_controls_original_counts':{'total':17,'passed':17,'skipped':0},
 'original_search':'Same right-two closed target, original axioms/emptyGamma/parameter,24unit obligations and all-six bounded inventory; fresh initial_stateNone, no route input.',
 'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},
 'conformance_gaps':['ALL24 rebind does not retain unaffected domains.','No general independent all-six EOF/exhaustion certifier.','Specialized fixed unit rows, no fractional/shared positive support/general growth.'],
 'independent_proof_or_trajectory_or_RL_or_advantage_claim':False,
 'cost_scope':'Complete cold setup/input/authentication, all generation and independent membership, re-enumeration, controls or search, cursor replay, trace and output/exit/native postprobe.'})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1');assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-global-engine-'+mode+'-20261015-v1','purpose':'unit-row-global-engine-'+mode,
 'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,
 'reviews':{'ROOT':author_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',
 author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dependency_reviews))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-global-engine-preflight-v1','plan':plan,'scientific_calls':0,'actual_execution_occurred':False,'fresh_output_and_external':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
