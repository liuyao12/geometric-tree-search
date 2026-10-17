"""Independent Source/AST/byte-patch review; no project Source evaluation."""
import ast
import difflib
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

H = Path('/private/tmp/gcts-family-census-engine-source-20261017')
O = Path('/private/tmp/gcts-family-census-engine-peer-20261017')

def raw(p):
    p = Path(p)
    assert not getattr(p.stat(), 'st_flags', 0) & 0x40000000
    return p.read_bytes()

def pin(p):
    b = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def check(ref):
    assert pin(ref['path']) == ref
    return raw(ref['path'])

def save(name, v):
    p = O / name
    with p.open('xb') as f:
        f.write((json.dumps(v, sort_keys=True, indent=2) + '\n').encode())
    return pin(p)

handoff = json.loads(raw(H / 'handoff-v5.json'))
contract_ref = handoff['source_contract']
contract = json.loads(check(contract_ref))
source_ref = handoff['source']
current = check(source_ref)
parent4 = check(handoff['parent_source'])
parent3 = check(handoff['base_parent_source'])
api_ref = handoff['API']
api = json.loads(check(api_ref))
delta_ref = handoff['source_delta']
delta = json.loads(check(delta_ref))
for ref in [handoff['actual_patch_evidence'], handoff['static_audit'],
            handoff['retained_v4_handoff'], contract['preserved_v4_contract']]:
    check(ref)
for ref in contract['unchanged_components'].values():
    check(ref)
for b in (parent3, parent4, current):
    ast.parse(b)
    compile(b, '<engine-Source-only>', 'exec', dont_inherit=True)

def edits_exact(before, after, edits):
    f = before.decode()
    for e in edits:
        i = e['start']
        assert f[i:i+len(e['before'])] == e['before']
        f = f[:i] + e['after'] + f[i+len(e['before']):]
    assert f.encode() == after
    for e in reversed(edits):
        i = e['start']
        assert f[i:i+len(e['after'])] == e['after']
        f = f[:i] + e['before'] + f[i+len(e['after']):]
    assert f.encode() == before
    assert ast.dump(ast.parse(f), include_attributes=False) == ast.dump(ast.parse(before), include_attributes=False)

edits_exact(parent4, current, delta['immediate_edits'])
edits_exact(parent3, current, delta['combined_edits'])
assert len(delta['immediate_edits']) == 2 and len(delta['combined_edits']) == 14
patch_results = []
for label, before, after in [('immediate_forward', parent4, current),
                             ('immediate_inverse', current, parent4),
                             ('combined_forward', parent3, current),
                             ('combined_inverse', current, parent3)]:
    ref = handoff['patches'][label]
    check(ref)
    with tempfile.TemporaryDirectory(dir=str(O)) as td:
        target = Path(td) / 'target.py'
        target.write_bytes(before)
        r = subprocess.run(['/usr/bin/patch', '--batch', '-F0', str(target), '-i', ref['path']],
                           cwd=td, capture_output=True)
        assert r.returncode == 0 and target.read_bytes() == after
    patch_results.append({'direction': label, 'patch': ref, 'actual_F0_result_exact': True})

def regions(b):
    lines = b.decode().splitlines(True)
    out = {}
    def walk(nodes, prefix=''):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                name = prefix + n.name
                out[name] = {'raw': ''.join(lines[n.lineno-1:n.end_lineno]),
                             'AST': ast.dump(n, include_attributes=False), 'line': n.lineno}
                walk(n.body, name + '.')
    walk(ast.parse(b).body)
    return out

r3, r4, r5 = regions(parent3), regions(parent4), regions(current)
assert set(r4) == set(r5)
assert all(r4[k]['raw'] == r5[k]['raw'] and r4[k]['AST'] == r5[k]['AST'] for k in r4)
exact3 = [k for k in r3 if k in r5 and r3[k]['raw'] == r5[k]['raw'] and r3[k]['AST'] == r5[k]['AST']]
changed3 = [k for k in r3 if k in r5 and k not in exact3]
added3 = sorted(set(r5) - set(r3))
assert len(r4) == 53 and len(exact3) == 37
assert added3 == ['LazyUnitRowEngine._join_family_cursor_census', 'LazyUnitRowEngine._join_family_degree_census',
                  'LazyUnitRowEngine._join_prototype_census', 'LazyUnitRowEngine._record_family_tile_census']
for name in ['select_schedule', 'validate_native_receipt', 'certify_by_current_cover',
             'LazyUnitRowEngine._install', 'LazyUnitRowEngine._observe', 'LazyUnitRowEngine.place',
             'LazyUnitRowEngine._exclude_exhausted', 'LazyUnitRowEngine._open',
             'LazyUnitRowEngine.next_alternative', 'LazyUnitRowEngine._fallback_degree',
             'LazyUnitRowEngine._transfer_receipt', 'LazyUnitRowEngine._select_family_branch',
             'LazyUnitRowEngine._adopt_family_branch', 'LazyUnitRowEngine.search']:
    assert name in exact3

def constants(b):
    return {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(b).body
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}

c4, c5 = constants(parent4), constants(current)
assert [k for k in c4 if c4[k] != c5[k]] == ['VERSION', 'FAMILY_PROVIDER_VERSION']
provider_handoff = json.loads(raw('/private/tmp/gcts-observed-receptor-provider-source-20261017/handoff-v6.json'))
provider = check(provider_handoff['source'])
pc = constants(provider)
assert pc['VERSION'] == c5['FAMILY_PROVIDER_VERSION']
assert pc['RESULT_SCHEMA'] == c5['FAMILY_PROVIDER_SCHEMA']
assert pc['PRODUCER_IMPLEMENTATION'] == c5['OBSERVED_PRODUCER_IMPLEMENTATION']
assert len(provider_handoff['report_fields']) == 26 and len(provider_handoff['request_fields']) == 6
assert set(api['family_proposer_return']['report']['exact_fields']) == set(provider_handoff['report_fields'])
assert set(api['family_proposer_return']['report']['request_fields']) == set(provider_handoff['request_fields'])
assert api['family_proposer_return']['report']['binding_policies'] == provider_handoff['binding_policies']
assert api['family_proposer_return']['report']['residual_policy_version'] == pc['RESIDUAL_POLICY_VERSION']
assert api['source'] == source_ref and api['VERSION'] == c5['VERSION']

checks = [
    {'id': 'EXACT-SOURCE-ANCESTRY', 'passed': True,
     'finding': 'Current5/parent4/parent3, contracts/API, retained author metadata, dependency Sources and all patches authenticated as bytes. Two immediate and fourteen combined raw forward/inverse edits plus whole AST inverses independently reconstructed.'},
    {'id': 'ACTUAL-PATCH-DIRECTIONS', 'passed': True,
     'finding': 'All four frozen unified patches independently applied with /usr/bin/patch --batch -F0 to Source scratch and compared to exact whole destination bytes.'},
    {'id': 'DECLARED-CORE-UNCHANGED', 'passed': True,
     'finding': 'All53 parent4 named regions raw+AST exact.37 parent3 named regions raw+AST exact, including global scheduler/native receipt validators/cover join/install/observe/place/exclude/open/cursor replay/fallback degree/retention/family selection+adoption/search. Declared ledger additions and enclosing current methods read in full.'},
    {'id': 'FULL-IDENTITY-NOT-FACT', 'passed': True,
     'finding': 'Canonical preimage parsing, original epoch/decorated marking and existing ID-definition gates precede same-ID FULL-preimage equality. Fresh copied seed and initial selected/excluded names only constrain identity consistency. No semantic membership authority, incidence, candidate, point union, exclusion, degree or EOF is created by ledger entries.'},
    {'id': 'PROVIDER-EVERY-STATUS', 'passed': True,
     'finding': 'Exact outer batch/report, report26/request6/current state/decision/binding/marking/schema/V6/producer implementation/policyV2/falseflags join precedes full sorted unique census merge on READY and UNKNOWN/no-offer. checked_state may be null only as nonauthoritative data. Audited pinned provider supplies whole census completeness; engine is not a second provider replay.'},
    {'id': 'TEMPORAL-CENSUS', 'passed': True,
     'finding': 'Candidate packets and checked-context candidates join both original/decorated IDs; public native degree candidate/rejected keys are joined after unchanged native validation, with unchanged native reconstruction for public rejected keys. Later exposures compare against provider-only entries retained across installs; no private never-yielded base69 coverage claim.'},
    {'id': 'PUBLIC-CURSOR-ONLY', 'passed': True,
     'finding': 'After successful event-context check, public adapter5 prefix export must match whole actual context, state, marking, implementation, raw=shown+removed counters, ordinal and EOF flag. Full prefix includes channel4-removed base-yielded types and merges before event use; no extra advance/private cursor access/late timeout export/EOF authority.'},
    {'id': 'LITERAL-CONSUMER-RECEIPT', 'passed': True,
     'finding': 'Bare seven-field batch delegated to unchanged fresh d680. Full literal fresh consumer receipt retained inside DISTINCT engine-owned census-check wrapper together with provider report and census. All READY adapted members and observed types merged, continuation identities checked against owned ledger, current candidate independently rebuilt. No old receipt relabel.'},
    {'id': 'EXACT-OWNED-RESTORATION', 'passed': True,
     'finding': 'Ledger and latest-public-export dictionaries are copy-on-write. Checkpoint stores both and rollback restores references without callback; _install leaves identity metadata intact. Snapshot copies them. Root search exact-before/after rollback remains unchanged; history events do not become cross-branch authority.'},
    {'id': 'GLOBAL-POLICY-AND-FALLBACK', 'passed': True,
     'finding': 'Family proposer remains after actual completed BRANCH only, after global DEAD/UNKNOWN/FORCED and earliest-generation tie. Exactly one primitive preference then fresh decision. Pending families freshly rechecked; canonical stream/order and fresh independent full keySET cover gating remain unchanged.'},
    {'id': 'COST-ERROR-AND-SCOPE', 'passed': True,
     'finding': 'New reconstruction/export/JSON/copy operations charged through existing tick; malformed/collision/native/callback errors propagate. No cache budget reset/new clock/bound easing, no equal nth-tick/error timing/performance claim. Current Source authentication and trusted synchronous pinned scope remain required; no hostile reentrancy guarantee.'},
    {'id': 'NO-RUNTIME-INHERITANCE', 'passed': True,
     'finding': 'Original Source17/input2 epoch/model/marking separate from executable map. Frozen provider6/policy2925 wire concordance checked as Source only. No engine/proof/trajectory/pruning/GCTS/RL/resource qualification, runtime fit or prior result transfer asserted.'}
]
audit = save('independent-raw-AST-audit-v5.json', {
    'schema': 'receptor-family-full-census-engine-independent-byte-audit-v5',
    'source': source_ref, 'source_contract': contract_ref, 'source_delta': delta_ref,
    'immediate_raw_regions': 2, 'combined_raw_regions': 14,
    'immediate_named_regions_raw_AST_exact': sorted(r4),
    'parent3_unchanged_named_regions': exact3, 'parent3_changed_named_regions': changed3,
    'parent3_added_named_regions': added3,
    'actual_patches': patch_results, 'provider_current_source': provider_handoff['source'],
    'line_anchors': {k: v['line'] for k, v in r5.items()},
    'source_only': True, 'scientific_calls': 0, 'project_module_evaluated': False,
    'scientific_acceptance': False})
findings = save('findings-v5.json', {
    'schema': 'receptor-family-full-census-engine-independent-findings-v5',
    'source': source_ref, 'source_contract': contract_ref, 'checks': checks,
    'blocking_findings': [], 'source_review_passed': True,
    'qualification_obligations': contract['future_qualification_obligations'],
    'source_only': True, 'scientific_calls': 0, 'scientific_acceptance': False})
abi = contract['Review_ABI']
review = save('typed-Source-review-v5.json', {
    'schema': abi['schema'], 'scope': abi['scope'], 'source': source_ref,
    'sources': abi['sources'], 'source_contract': contract_ref,
    'author_identity': contract['author_identity'], 'reviewer_identity': '/root/hilbert_advice_controls',
    'reviewer_distinct_from_author': True,
    'authorship_disclosure': ('Reviewer authored host4bd6, unchanged d680 consumer, parent family engine3 and provider6; '
        'also prior c960/fallback/membership and caller/native ancestry. Diagnosis authored current engine4/5 ledger work '
        'and independent4358/9fd/8f plus point-adapter ancestry. Wire coordination/shared primitives disclosed. '
        'This is distinct review of current engine additions, not an independent peer of own provider or own older helpers.'),
    'source_review_passed': True, 'disposition': 'CONDITIONAL_SOURCE_PASS',
    'whole_current_source_contract_API_and_parent_delta_read': True,
    'blocking_findings': [], 'checks_passed': len(checks), 'findings': findings, 'independent_raw_audit': audit,
    'conditions': ['Root fresh whole executable-map/original17/input2 authentication, CodeSeal and unchanged native once grant remain mandatory.',
                   'Runtime engine/provider/census/rollback controls not executed or inherited. Future qualification obligations remain open.',
                   'Ledger is full identity consistency evidence over specified public exposures, never candidate/point/degree/proof authority.'],
    'source_only': True, 'scientific_calls': 0, 'source_evaluated': False, 'tests_executed': False,
    'actual_result_proofword_donor_reads': False, 'scientific_acceptance': False,
    'runtime_qualified': False, 'engine_accepted': False, 'proof_accepted': False,
    'pruning_accepted': False, 'RL_accepted': False})
handoff_ref = save('handoff-v5.json', {
    'schema': 'receptor-family-full-census-engine-independent-handoff-v5',
    'source': source_ref, 'source_contract': contract_ref, 'typed_review': review,
    'findings': findings, 'independent_raw_audit': audit,
    'source_review_passed': True, 'source_only': True, 'scientific_calls': 0,
    'scientific_acceptance': False})
print(json.dumps({'typed_review': review, 'findings': findings, 'audit': audit, 'handoff': handoff_ref}, sort_keys=True))
