"""Reviewed once-plan metadata only; no scientific module evaluation."""
import hashlib,json,sys
from pathlib import Path
S=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
def ref(p):
    p=Path(p)
    with p.open('rb')as f:
        b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(Path(p).read_bytes())
assert len(sys.argv)==3,'caller and reader peer paths'
cp,rp=map(Path,sys.argv[1:]);h=load(S/'handoff-v1.json');c=load(S/'Source-contract-v1.json')
sources,inputs=h['sources'],c['inputs'];peer,reader_peer=load(cp),load(rp)
assert peer['source']==h['source']and peer['sources']==sources and peer['source_contract']==h['source_contract']
assert peer['source_review_passed']is True and peer['scientific_calls']==0 and peer['source_only']is True and peer['scientific_acceptance']is False and peer['reviewer_identity']!='/root'
assert reader_peer['source']==h['reader']and reader_peer['source_contract']==h['reader_source_contract']and reader_peer['current_operative_contract']==h['source_contract']
assert reader_peer['source_review_passed']is True and reader_peer['scientific_calls']==0 and reader_peer['source_only']is True
components={'receiver_provider':Path('/private/tmp/gcts-head-gated-provider-peer-20261017/typed-Source-review-v8.json'),
    'family_engine':Path('/private/tmp/gcts-head-gated-family-engine-peer-20261017/typed-Source-review-v7.json'),
    'head_gate':Path('/private/tmp/gcts-coarse-head-plan-marks-peer-20261017/typed-Source-review-v1.json'),
    'residual_policy':Path('/private/tmp/gcts-residual-binding-prefix-peer-20261017/typed-Source-review-v2.json'),
    'producer':Path('/private/tmp/gcts-observed-subset-expander-peer-20261017/typed-Source-review-v2.json'),
    'receiver_cases':Path('/private/tmp/gcts-callback-stage-helper-peer-20261017/typed-Source-review-v1.json')}
for role,p in components.items():
    r=load(p);assert r['source']==sources[role],role
    assert r.get('source_review_passed',r.get('pass'))is True and r['source_only']is True and r['scientific_calls']==0,role
    assert not r.get('scientific_acceptance',False)and not r.get('runtime_qualified',False),role
for x in [*sources.values(),*inputs.values(),h['source_contract'],h['reader'],h['reader_source_contract']]:assert ref(x['path'])==x
assert len(sources)==22 and len(inputs)==10
au=load(S/'ROOT-raw-Source-audit-v1.json');assert au['scientific_calls']==0 and all(x['whole_forward_inverse_AST']and x['both_actual_patch_directions_byte_exact']for x in au['checks'])
R=Path('/private/tmp/gcts-callback-stage-inference-visible-ROOT-20261017');assert not R.exists();R.mkdir()
def save(n,v):
    p=R/n
    with p.open('xb')as f:f.write((json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
    return ref(p)
review=dict(h['Review_ABI'],reviewer_identity='/root',source_review_passed=True,
    review_type='Whole current composition and exact successor raw/AST seams; distinct whole caller/readout and component peers joined',
    raw_audit=ref(S/'ROOT-raw-Source-audit-v1.json'),blockers=[],findings=[],reviewed_source=[
    'Original17/input2/epoch/theory/emptyGamma/full24rows/B12N44/target/frozenmarking unchanged; current22executable/10inputs remain separate implementation metadata.',
    'Provider8, engine7, gate1 and every other scientific dependency remain raw-identical. Helper adds bounded provider/consumer/search diagnostics only. Science delegates remain unconditional beyond diagnostic caps.',
    'Root capture reads only exact builtin fixed fields and20 integer accounting counters before existing full-copy/hash work; it never changes provider value, admission or full scientific flow. Nonconforming diagnostic shape leaves null. Original20 native ticks guard capture; a slot is an unvalidated raw observation.',
    'Root failure writer remains captured-builtin failure55 only, no late scientific calls. Original legacy branch retained, V2 gets an explicit separate wire bound. New nested conditional phase parser allows caught callback unwinds; complete output counts come only from full returned records.',
    'The once wrapper, native runtime and meter, Source custody/CodeSeal/original endpoint closure, complete fallback/global scheduler and rollback are unchanged. All old raw function regions outside declared instrumentation/writer seams match; full raw forward/inverse actualpatch/AST checks completed.',
    'This one separately declared visible inference diagnostic uses same reused pool, 1m provider work,2records/64trials/1instance,2nodes/256events, original20/512external/500reserve/55failure/60owned/90+1caller. Earlier terminal attempts are never restarted.',
    'Reached phases and raw summary fields are not checked offers, native moves, valid proof, completed search/restoration or an exclusive failure cause. No usefultransfer/RL/GCTSgain/universalpalette or wholeconformance acceptance.'])
root_ref=save('ROOT-Source-review-v1.json',review)
runtime={'path':'/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9','sha256':'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e','bytes':102352};assert ref(runtime['path'])==runtime
plan=dict(schema='ROOT-routed-engine-qualification-plan-v1',invocation_id='ROOT-callback-stage-receiver-visible-20261017-v1',purpose='receptor-inference-visible-probe',output_directory=str(R/'RI-owned-v1'),sources=sources,inputs=inputs,source_contract=h['source_contract'],reviews={'ROOT':root_ref,'peer':ref(cp)},runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
grant=dict(plan,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,component_reviews={role:ref(p)for role,p in components.items()},saved_readout=dict(source=h['reader'],source_contract=h['reader_source_contract'],peer=ref(rp)),scope='One bounded callback-stage inference diagnostic, current reviewed instrumentation, same full original mathematical model/native limits. No restart or theorem/usefultransfer/pruning/RL/speed acceptance.',unchanged_actual_may_be_restarted=False,scientific_acceptance=False)
plan['ROOT_authorization']=save('ROOT-authorization-v1.json',grant)
print(json.dumps({'plan':save('ROOT-plan-v1.json',plan),'external_directory':str(R/'RI-external-v1'),'scientific_calls':0}))
