"""Root one-plan Source metadata only; no scientific import or evaluation."""
import hashlib
import json
from pathlib import Path
import sys

S=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-source-20261017')
R=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017')
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
h=load(S/'handoff-v2.json');c=load(S/'Source-contract-v2.json')
sources=h['Review_ABI']['sources'];inputs=c['inputs']
others={
    'marked_adapter':Path('/private/tmp/gcts-marked-prefix-census-peer-20261017/typed-Source-review-v1.json'),
    'composer':Path('/private/tmp/gcts-native-component-composer-work4m-peer-20261017/typed-Source-review-v3.json'),
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
assert c['allocation']['composer_own_work']==4000000 and c['allocation']['fragment_priority']=='OPEN_INPUT_OUTPUT_FIRST'
assert not R.exists(),'Fresh one-plan metadata directory only'
R.mkdir()
review=dict(h['Review_ABI'],reviewer_identity='/root',source_review_passed=True,
    review_type='Root current Source review with exact raw forward/inverse AST audits and substantive productive CASE/API review',
    findings=[],blockers=[],reviewed_source=['Current cold7c760 is parent978327 plus2 VERSION/currentcomposer+CASE pin edits only. Reader1f4ae is parent1ae263 plus2 currentcapsule/responseVERSION edits only. All caller named functions/classes including main raw/AST exact. Full forward/inverse/AST and patch directions verified; compile only, no project evaluation.', 'Composer4149 is parentb829 plus2 ownVERSION/defaultwork1mto4m edits. CASEd00b is parent11bb plus3 ownVERSION/composerVERSION/requestwork1mto4m edits. All named bodies raw/AST exact. Root full inverse audited both; distinct Diagnosis per-role reviews required. No old result/runtime/availability inherited.', 'Original full model/theory/target/Gamma/profile/marking/Source17/input2/epoch unchanged, current executable17/input8 tracked separately. CASE8m/depth128, root48/ext96/head1/quantum8/closed+open slots and miner3 OPEN_INPUT_OUTPUT_FIRST remain fixed. Only constructor own step allowance increases; original native20/internal500reserve/512/once/CodeSeal/failure55/owned60/caller90+1 unchanged.', 'Previously whole-read productive CASE and composer preserve separate alternative point unions, full examined original/decorated census including discarded/removed types, distinct checked slot port classes, collect-all/mine-all/qualify-all phases, per-occurrence source expansion/independent check/roundtrip/original-root rebind/direct-native union check and full preimage collision comparisons. No engine/BRANCH/receiver or fake facts introduced.', 'Source-ground inventory is not arbitrary parameter validity, current global viability, scheduler/rollback, target theorem, receiver transfer, universal family lemma, trainedRL or GCTS gain. Saved reader only reconciles complete current Source/native/wire bytes; no scientific replay. New changed-cap actual is distinct, not an unchanged restart.'])
root_review=save('ROOT-Source-review-v1.json',review)
runtime=dict(path='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',sha256='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e',bytes=102352)
assert pin(runtime['path'])==runtime
plan=dict(schema='ROOT-routed-engine-qualification-plan-v1',invocation_id='ROOT-native-productive-inventory-work4m-20261017-v1',
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
