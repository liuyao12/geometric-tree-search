"""Root metadata-only typed Source review. Does not grant or run an actual."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
FOLDER = BASE / 'unit-row-global-forced-diagnostic-cold-source-20261016'


def read(p):
    return json.loads(Path(p).read_bytes())


def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def checked(ref):
    p = Path(ref['path'])
    assert p == p.resolve() and p.is_absolute() and pin(p) == ref
    return p


def literal(tree, name):
    return ast.literal_eval(next(n for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)).value)


def main():
    contract_pin = pin(FOLDER / 'Source-contract-v1.json')
    assert contract_pin['sha256'] == '06e873d471df980c4c0f5591679090cf254cf94be02e992477a28c07f0652595'
    c = read(checked(contract_pin))
    parent = read(checked(c['parent_source_contract']))
    assert len(c['sources']) == 14 and len(c['inputs']) == 8
    assert len(c['original_model_sources']) == 17 and len(c['original_model_inputs']) == 2
    for key in ('inputs', 'original_model_sources', 'original_model_inputs', 'original_model_binding',
                'limits', 'fixture_scope', 'artifact_API', 'qualification', 'engine_source_contract',
                'engine_reviews', 'engine_handoff', 'endpoint_count', 'essential_case_count'):
        assert c[key] == parent[key], key
    assert all(ref == parent['sources'][role] for role, ref in c['sources'].items() if role != 'intake')
    assert c['sources']['intake'] == c['source']
    assert c['source']['sha256'] == '28953cad70c4d51c9e18be583c2a3d95356676763f73bb580d28e48603b75608'
    for refs in (c['sources'], c['inputs'], c['original_model_sources'], c['original_model_inputs']):
        for ref in refs.values():
            checked(ref)
    tree = ast.parse(checked(c['source']).read_bytes())
    for name, expected in (
        ('FIXED', {k: v for k, v in c['sources'].items() if k != 'intake'}),
        ('FIXED_INPUTS', c['inputs']), ('ORIGINAL_SOURCES', c['original_model_sources']),
        ('ORIGINAL_INPUTS', c['original_model_inputs']), ('ORIGINAL_BINDING', c['original_model_binding']),
        ('LIMITS', c['limits']), ('VERSION', c['version']), ('SCOPE', c['scope']),
        ('QUALIFICATION_CASES_BY_PURPOSE', c['API']['purpose_modes_and_ordered_cases'])):
        assert literal(tree, name) == expected, name
    assert c['API']['purpose_modes_and_ordered_cases'] == parent['API']['purpose_modes_and_ordered_cases']
    assert c['diagnostic_choice'] == pin(HERE / 'ROOT-diagnostic-choice-v1.json')
    checked(c['diagnostic_proposal'])
    checked(c['source_delta'])
    checked(c['author_static'])
    module_contract = read(checked(c['engine_source_contract']))
    assert all(c['sources'][k] == v for k, v in module_contract['sources'].items())
    for role, ref in c['engine_reviews'].items():
        review = read(checked(ref))
        assert review['source_contract'] == c['engine_source_contract']
        assert review['sources'] == module_contract['sources']
        assert review['source_review_passed'] is review['source_only'] is True
        assert review['scientific_calls'] == 0 and review['scientific_acceptance'] is False
    raw = read(HERE / 'ROOT-caller-raw-inverse-review-v1.json')
    assert raw['source'] == c['source'] and raw['delta'] == c['source_delta']
    phase = c['diagnostics']['phase_stderr']
    assert phase['maximum_sites'] == len(phase['labels_in_runtime_order']) == 7
    assert c['diagnostics']['latest_callback_scalars']['validator'] is None
    assert c['diagnostics']['failure_only']['positive_joint_gate_accepted'] is False
    review = dict(c['Review_ABI'])
    review.update(source_contract=contract_pin, reviewer_identity='/root', source_review_passed=True,
        source_only=True, scientific_calls=0, scientific_acceptance=False, concrete_blockers=[],
        whole_current_Source_and_contract_read=True,
        raw_inverse_review=pin(HERE / 'ROOT-caller-raw-inverse-review-v1.json'),
        distinct_whole_caller_peer_required_before_grant=True,
        authorship_disclosure='Root authored only protocol choice, static metadata audits, future grants and publication. Root hand-read the whole parent caller, all thirteen added regions, whole contract and its unchanged authenticated maps. No project mathematical function evaluated. Controls authored this caller; diagnosis independently reviews it.',
        checks=[
            'Only caller diagnostics and authority scope/version change. Current thirteen delegated modules, original seventeen mathematical Sources/two inputs/epoch, current eight inputs, all six family meanings/twelve assertions and limits remain exact.',
            'All seventeen top helpers including builtin-only failure writer, thirty-two other direct nested helpers, two classes, original global assertions and final native/error suffix remain raw/AST exact. Both actual patches and full byte/AST inverse independently verified.',
            'Seven fixed direct original native samples surround unchanged complete statement groups; proposer reuses existing native sample and fallback/certifier add charged entry checks. Fixed four scalar slots, validator unavailable, exact builtin optional values or minus one, no model work or growing diagnostic history.',
            'Timeout catch is outside unchanged call/invoke exceptional full guards. Predelegation context and captured writer identity anchors are checked inline using builtin operations; only exact builtin TimeoutError invokes the inherited failure-only writer. No late original20 tick/guard/anchor/same/canonical/Path or model callback; original error re-raised and exit2 preserved.',
            'Complete failure-only two-file diagnostic remains unqualified. Setup, subclass timeout or later tail can leave no diagnostic; partial files and missing markers supply no phase absence, active-frame, return, move, restore, exhaustion, case count, proof or exclusive-cost claim.',
            'One prospective Root-owned global-purpose diagnostic only; no other five reruns, no inherited10of12 or oldStageC promotion, no new proof sequence/donor/cache/semantic epoch/budget, no target theorem/RL/advantage claim.'
        ])
    with (HERE / 'ROOT-caller-Source-review-v1.json').open('x') as f:
        json.dump(review, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(pin(HERE / 'ROOT-caller-Source-review-v1.json')))


if __name__ == '__main__':
    main()
