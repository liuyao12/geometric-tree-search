"""Root one-plan Source metadata only; no scientific import or evaluation."""
import hashlib
import json
from pathlib import Path
import sys

S=Path('/private/tmp/gcts-native-productive-inventory-ROOT-source-20261017')
R=Path('/private/tmp/gcts-native-productive-inventory-ROOT-20261017')
def pin(path):
    p=Path(path);assert not getattr(p.stat(),'st_flags',0)&0x40000000
    with p.open('rb')as f:
        b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(path):return json.loads(Path(path).read_bytes())
def save(name,value):
    p=R/name
    with p.open('xb')as f:f.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
    return pin(p)

assert len(sys.argv)==4,'Cold peer, saved-reader peer and productive CASE peer'
cold_peer,reader_peer,cases_peer=map(Path,sys.argv[1:])
h=load(S/'handoff-v1.json');c=load(S/'Source-contract-v1.json')
sources=h['Review_ABI']['sources'];inputs=c['inputs']
others={
    'marked_adapter':Path('/private/tmp/gcts-marked-prefix-census-peer-20261017/typed-Source-review-v1.json'),
    'composer':Path('/private/tmp/gcts-native-component-composer-productive-peer-20261017/typed-Source-review-v2.json'),
    'miner':Path('/private/tmp/gcts-interface-coupled-miner-peer-20261017/typed-Source-review-v3.json'),
    'inventory_cases':cases_peer}
for p in (cold_peer,reader_peer,*others.values()):
    v=load(p)
    assert v['source_review_passed']is True and v['source_only']is True
    assert v['scientific_calls']==0 and v['scientific_acceptance']is False
assert load(cold_peer)['source_contract']==h['source_contract'] and load(cold_peer)['sources']==sources
assert load(cold_peer)['reviewer_identity']!='/root'
for role,p in others.items():assert load(p)['source']==sources[role]
assert load(reader_peer)['source']==h['reader'] and load(reader_peer)['source_contract']==h['reader_source_contract']
assert load(reader_peer)['current_operative_contract']==h['source_contract']
for ref in [*sources.values(),*inputs.values(),h['source_contract'],h['reader'],h['reader_source_contract']]:assert pin(ref['path'])==ref
audit=load(S/'ROOT-raw-Source-audit-v1.json')
assert audit['scientific_calls']==0 and all(v['whole_forward_inverse_AST']is True for v in audit['checks'])
assert c['case_work_limit']==8000000 and c['allocation']['components']==2
assert c['allocation']['composer_own_work']==1000000 and c['allocation']['fragment_priority']=='OPEN_INPUT_OUTPUT_FIRST'
assert not R.exists(),'Fresh one-plan metadata directory only'
R.mkdir()
review=dict(h['Review_ABI'],reviewer_identity='/root',source_review_passed=True,
    review_type='Root current Source review with exact raw forward/inverse AST audits and substantive productive CASE/API review',
    findings=[],blockers=[],reviewed_source=[
        'Current caller978327 is whole-read parentc03a plus6 exact version/scope/purpose/current-three-helper-ref/contract/evidence-schema edits. Reader1ae263 is parent11c1 plus5 exact currentcapsule/schema/scope/responseversion/helper-schema edits. Full raw forward/inverse, whole AST inverse and compile-without-evaluation audited. Native guards/ticks/CodeSeal/once/limits/thirteen phase wire/canonical lossless output/failure tail unchanged.',
        'Productive CASE11bb whole Source/API read. Exact10 edits/full inverse against whole-read CASEc0d6. Both native slots validated against independent collector actual ordered read maps; closed/open classification retains absent occupancy and factFalse. Alternative component unions never combined. Collect-all/mine-all/qualify-all have unique five stage labels. All emitted physical occurrences get fresh expansion/independent/source roundtrip/original-root rebind/second check/direct native adaptation and exact union equality.',
        'Whole composerb829/contractaf6c and miner7873/API reviewed as narrow successors with Root raw/AST inverse audits and distinct Diagnosis reviews9046/185a. Composer retains one closed and one open slot under original root48/ext96/head1/quantum8/own1m/depth128, with honest missing-slot UNKNOWN. Miner new explicit OPEN_INPUT_OUTPUT_FIRST is human advisory catalogue order, default old order retained; full scoped keys, at-cap descendant probes and actual built parameter-location reports preserve free-bound and untrusted-occupancy distinctions. No availability or useful transfer is inferred.',
        'Current executable Source17/input8 remains separate from original mathematical Source17/input2/epoch382755; original model/theory/target/Gamma/profile/marking are fixed. Original CodeSeal/full native immediate pre/post callback boundaries and same20/internal500MiB reserve, failure55/owned60/caller90+1 remain operative. Every current/authority Source/input is reread in actual; resident-byte prep is no OS-cache-cold or saved-science qualification claim.',
        'Current marked7e508 public full examined original/decorated prefix census remains sole export; includes removed/discarded exposures, global full-ID/preimage equality joined before proposals. Never-yielded private types or prefixes confer no degree/exhaustion/global graph authority. Complete canonical fallback remains unmodified; no provider or fictitious BRANCH invocation.',
        'Ground source validity is not arbitrary parameter validity, receptor transfer, target theorem, global frontier, full GCTS, trained RL or practical advantage. Helper broad flags remain false. Root saved reader reconciles current whole native/wire bytes only and never replays the scientific helper.'
    ])
root_review=save('ROOT-Source-review-v1.json',review)
runtime=dict(path='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',sha256='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e',bytes=102352)
assert pin(runtime['path'])==runtime
plan=dict(schema='ROOT-routed-engine-qualification-plan-v1',invocation_id='ROOT-native-productive-inventory-20261017-v1',
    purpose='native-productive-conditional-inventory',output_directory=str(R/'NPI-owned-v1'),
    sources=sources,inputs=inputs,source_contract=h['source_contract'],reviews=dict(ROOT=root_review,peer=pin(cold_peer)),
    runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
grant=dict(plan,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',
    actual_execution_authorized=True,maximum_actual_invocations=1,
    scope='One changed productive two-slot source-ground inventory actual under original full mathematical model/native limits. No prior actual restarts, receiver/engine/BRANCH/theorem/generalized lemma/RL/GCTS advantage acceptance.',
    component_reviews={role:pin(p)for role,p in others.items()},
    saved_readout=dict(source=h['reader'],source_contract=h['reader_source_contract'],peer=pin(reader_peer)),
    unchanged_actual_may_be_restarted=False,scientific_acceptance=False)
plan['ROOT_authorization']=save('ROOT-authorization-v1.json',grant)
out=save('ROOT-plan-v1.json',plan)
print(json.dumps(dict(plan=out,external_directory=str(R/'NPI-external-v1')),sort_keys=True))
