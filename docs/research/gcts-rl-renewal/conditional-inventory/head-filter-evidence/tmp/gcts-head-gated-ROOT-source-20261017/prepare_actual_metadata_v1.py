"""Review joins and once-plan metadata only; no scientific module evaluation."""
import hashlib,json,sys
from pathlib import Path
S=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017')
def ref(p):
 p=Path(p)
 with p.open('rb')as f:
  b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(Path(p).read_bytes())
assert len(sys.argv)==6,'mode,caller peer,reader peer,provider peer,engine peer'
mode,cp,rp,pp,ep=sys.argv[1:];assert mode in ('visible','literal')
h=load(S/'handoff-v1.json');c=load(S/'Source-contract-v1.json');sources=h['sources'];inputs=c['inputs'];peer=load(cp);reader_peer=load(rp)
assert peer['source']==h['source']and peer['sources']==sources and peer['source_contract']==h['source_contract']
assert peer['source_review_passed']is True and peer['scientific_calls']==0 and peer['source_only']is True and peer['scientific_acceptance']is False and peer['reviewer_identity']!='/root'
assert reader_peer['source']==h['reader']and reader_peer['source_contract']==h['reader_source_contract']and reader_peer['current_operative_contract']==h['source_contract']
assert reader_peer['source_review_passed']is True and reader_peer['scientific_calls']==0 and reader_peer['source_only']is True
components={'receiver_provider':Path(pp),'family_engine':Path(ep),'head_gate':Path('/private/tmp/gcts-coarse-head-plan-marks-peer-20261017/typed-Source-review-v1.json'),'residual_policy':Path('/private/tmp/gcts-residual-binding-prefix-peer-20261017/typed-Source-review-v2.json'),'producer':Path('/private/tmp/gcts-observed-subset-expander-peer-20261017/typed-Source-review-v2.json')}
for role,p in components.items():
 r=load(p);assert r['source']==sources[role],role
 assert r.get('source_review_passed',r.get('pass'))is True and r['source_only']is True and r['scientific_calls']==0,role
 assert not r.get('scientific_acceptance',False)and not r.get('runtime_qualified',False),role
for x in [*sources.values(),*inputs.values(),h['source_contract'],h['reader'],h['reader_source_contract']]:assert ref(x['path'])==x
assert len(sources)==22 and len(inputs)==10
au=load(S/'ROOT-raw-Source-audit-v1.json');assert au['scientific_calls']==0 and all(x['whole_forward_inverse_AST']and x['both_actual_patch_directions_byte_exact']for x in au['checks'])
R=Path('/private/tmp/gcts-head-gated-inference-'+mode+'-ROOT-20261017');assert not R.exists();R.mkdir()
def save(n,v):
 p=R/n
 with p.open('xb')as f:f.write((json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
 return ref(p)
review=dict(h['Review_ABI'],reviewer_identity='/root',source_review_passed=True,review_type='Whole current composition and exact successor raw/AST seam review; component peers separately joined',raw_audit=ref(S/'ROOT-raw-Source-audit-v1.json'),blockers=[],findings=[],reviewed_source=[
 'Original semantic Source17/input2/epoch/theory/emptyGamma/full24rows/B12N44/target/frozenmarking unchanged; current22executable/10inputs is separate implementation metadata.',
 'Caller ownVERSION/FIXED only; every named function raw/AST identical to prior370c. Helper ownVERSION/explicit head_gate_module injection only. Reader currentcontract/responseVERSION only. Whole inverse/forward AST and actualpatch directions exact; native once/meter/runtime/20/512/500reserve/55/60/90+1/CodeSeal/strictclosure untouched.',
 'Gate7595/conditionalpeer7094 uses descriptor-only invariant heads, never sourceground FORMULA value or occupiedfact. Unknown heads remain absent; unknown/capped/nested unsupported checks pass through. No deep/native/proof admission from matching heads. Completed conflict rejects only current advisory layout.',
 'Provider successor applies gate after identical common full structural plan materialization and attempt accounting before binding, both matching modes. Literal receipt/fullrequest retained for every reached plan including UNKNOWN; callback/guard/errors propagate. Gate cost charged to existing1m allowance. Full preflight/source/current membership/4358/4bd6/census remain mandatory.',
 'Current engine successor changes own/provider VERSION metadata only; all53 named regions raw/AST unchanged, full provider report/census retained through fresh consumer/primitive selection. No domains, degrees, scheduler, fallback, legal-placement checks or rollback changed.',
 'Same reused frozen qualified open inventory,2records/32trialquota each/30plans, same provider caps/node2/event256 and assigned-output tie within earliest generation; real engine reaches its own BRANCH. No fabricated receiver, premisefact, supplied proof, source route or target change.',
 'An offer is conditional native point data, not a completed theorem or useful search continuation. Reader is full saved wire/native resource reconciliation only. Capped/UNKNOWN prefixes never supply learned negatives or original impossibility. No trainedRL/GCTSgain/fullconformance/universalpalette claim.'])
root_ref=save('ROOT-Source-review-v1.json',review)
runtime={'path':'/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9','sha256':'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e','bytes':102352};assert ref(runtime['path'])==runtime
plan=dict(schema='ROOT-routed-engine-qualification-plan-v1',invocation_id='ROOT-head-gated-receiver-'+mode+'-20261017-v1',purpose='receptor-inference-'+mode+'-probe',output_directory=str(R/'RI-owned-v1'),sources=sources,inputs=inputs,source_contract=h['source_contract'],reviews={'ROOT':root_ref,'peer':ref(cp)},runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
grant=dict(plan,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,component_reviews={role:ref(p)for role,p in components.items()},saved_readout=dict(source=h['reader'],source_contract=h['reader_source_contract'],peer=ref(rp)),scope='One head-gated matched reused-inventory receiver probe under unchanged full mathematical model/native bounds. No restart or theorem/usefultransfer/pruning/RL/speed acceptance.',unchanged_actual_may_be_restarted=False,scientific_acceptance=False)
plan['ROOT_authorization']=save('ROOT-authorization-v1.json',grant);pr=save('ROOT-plan-v1.json',plan);print(json.dumps({'plan':pr,'external_directory':str(R/'RI-external-v1'),'scientific_calls':0}))
