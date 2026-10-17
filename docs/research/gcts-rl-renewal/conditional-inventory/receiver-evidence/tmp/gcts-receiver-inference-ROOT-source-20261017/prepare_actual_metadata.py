"""Root actual metadata preparation only; no project/scientific evaluation."""
import hashlib
import json
from pathlib import Path
import sys

S=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')


def ref(p):
    p=Path(p)
    with p.open('rb') as f:
        b=f.read(16777217)
        assert len(b)<=16777216 and f.read(1)==b''
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))


def load(p):return json.loads(Path(p).read_bytes())


assert len(sys.argv)==6,'mode, cold peer, reader peer, provider peer, engine peer'
mode,cold_path,reader_path,provider_path,engine_path=sys.argv[1:]
assert mode in ('visible','literal')
h=load(S/'handoff-v1.json');c=load(S/'Source-contract-v1.json')
sources=h['sources'];inputs=c['inputs']
peer=load(cold_path);rp=load(reader_path)
assert peer['source']==h['source'] and peer['sources']==sources and peer['source_contract']==h['source_contract']
assert peer['source_review_passed'] is True and peer['scientific_calls']==0
assert peer['source_only'] is True and peer['scientific_acceptance'] is False
assert peer['reviewer_identity']!='/root'
assert rp['source']==h['reader'] and rp['source_contract']==h['reader_source_contract']
assert rp['current_operative_contract']==h['source_contract'] and rp['source_review_passed'] is True
assert rp['source_only'] is True and rp['scientific_calls']==0
components={'receiver_provider':Path(provider_path),'family_engine':Path(engine_path),
 'residual_policy':Path('/private/tmp/gcts-residual-binding-prefix-peer-20261017/typed-Source-review-v2.json'),
 'producer':Path('/private/tmp/gcts-observed-subset-expander-peer-20261017/typed-Source-review-v2.json')}
for role,p in components.items():
    r=load(p)
    assert r['source']==sources[role],role
    assert r.get('source_review_passed',r.get('pass')) is True,role
    assert r['source_only'] is True and r['scientific_calls']==0,role
    assert not r.get('scientific_acceptance',False) and not r.get('runtime_qualified',False),role
for x in [*sources.values(),*inputs.values(),h['source_contract'],h['reader'],h['reader_source_contract']]:
    assert ref(x['path'])==x
audit=load(S/'ROOT-raw-Source-audit-v1.json')
assert audit['scientific_calls']==0 and all(x['whole_forward_inverse_AST'] and x['both_actual_patch_directions_byte_exact'] for x in audit['checks'])
R=Path('/private/tmp/gcts-receiver-inference-'+mode+'-ROOT-20261017')
assert not R.exists();R.mkdir()
def save(name,value):
    p=R/name
    with p.open('xb')as f:f.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
    return ref(p)
root_review=dict(h['Review_ABI'],reviewer_identity='/root',source_review_passed=True,
    review_type='Root whole new receiver seam and current source composition review; raw/AST inverses and peer component joins',
    raw_audit=ref(S/'ROOT-raw-Source-audit-v1.json'),blockers=[],findings=[],
    reviewed_source=[
     f'Original Source17/input2/theory/emptyGamma/24row/B12N44/epoch and frozen pointmarking preserved. Current{len(sources)} executable Sources and{len(inputs)} inputs are separate metadata, not a mathematical rebasing.',
     'Caller inherited35 namedregions rawAST unchanged; only main composition changes. Reader9 inherited regions unchanged; exact15 raw edits each and full forward/inverse AST and -F0 patch directions verified. Native once/meter/runtime and strict20/512/500reserve/55/60/90+1/CodeSeal unchanged.',
     'Prior qualified inventory is frozen data, raw-hash/whole original-model+marking/provenance/qualified-occurrence joins checked; fresh source/current native checks remain in provider. First open pool is a declared advisory policy, not a base-domain exclusion. Prior construction cost separate; no cold or speedup claim.',
     'Root helper real engine.search with maximum_nodes2 retains entire24row mathematical model, original complete fallback, named assigned-output within earliest-generation tie, ordinary primitive selection, next global scan and exact snapshot/stack rollback. No fake BRANCH, assumed premise truth or supplied proof route.',
     'Provider6 reviewed relative to23da, with full observed inference from fd3e, explicit current typed environments and actual source/occupancy bindings. Exact original OutsideLanguage from current-transfer proposal is completed nonmembership only; time/callback/guard/unexpected failures propagate. Every native point instance freshly expanded, independently4358 checked and4bd6 admitted.',
     'Residual2 uses theory-name-prioritized max-index shells over all declared hostnames, not original sourceenv/target examples. Internal-only variables/eigenvalues remain explicit candidate parameters; unbound FORMULA/TERM and caps are UNKNOWN, not guesses or pruning. Equal perrecord32 trial quotas prevent literal-first starvation, same both arms.',
     'Engine5 full public original/decorated census seeded explicitly from frozen inventory, current degree removals/preflight/rejections/nooffers/cursor prefixes joined before preferences; COW ledger/current cursor exports checkpointed/restored. Bare d680 consumer receipt remains literal nested in new engine wrapper. No sampled family replaces degree/exhaustion authority.',
     'Source review and narrow actual probe do not establish full engine conformance, universal-family validity, completed theorem, useful proof transfer, trained RL or GCTS/search gain. Saved reader reconciles bytes/resources only; no scientific replay.'])
rootref=save('ROOT-Source-review-v1.json',root_review)
runtime=dict(path='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',sha256='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e',bytes=102352)
assert ref(runtime['path'])==runtime
plan=dict(schema='ROOT-routed-engine-qualification-plan-v1',
 invocation_id='ROOT-receiver-inference-'+mode+'-20261017-v1',
 purpose='receptor-inference-'+mode+'-probe',output_directory=str(R/'RI-owned-v1'),
 sources=sources,inputs=inputs,source_contract=h['source_contract'],
 reviews=dict(ROOT=rootref,peer=ref(cold_path)),runtime=runtime,
 limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
grant=dict(plan,schema='ROOT-routed-engine-qualification-authorization-v1',
 author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,
 component_reviews={role:ref(p)for role,p in components.items()},
 saved_readout=dict(source=h['reader'],source_contract=h['reader_source_contract'],peer=ref(reader_path)),
 scope='One matched reused-inventory actual receiver probe under original full model and native bounds; no unchanged restart, supplied receiver, theorem/pruning/RL/search-gain acceptance.',
 unchanged_actual_may_be_restarted=False,scientific_acceptance=False)
plan['ROOT_authorization']=save('ROOT-authorization-v1.json',grant)
planref=save('ROOT-plan-v1.json',plan)
print(json.dumps(dict(plan=planref,external_directory=str(R/'RI-external-v1'),scientific_calls=0)))
