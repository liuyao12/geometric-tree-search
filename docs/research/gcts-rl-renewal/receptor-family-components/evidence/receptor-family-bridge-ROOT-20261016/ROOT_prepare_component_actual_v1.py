"""Metadata/AST only. Root Source closure and one prospective component grant.

No project module is imported, evaluated, tested or called by this helper.
"""
import ast
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def read(path):
    return json.loads(Path(path).read_bytes())

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def checked(ref):
    path = Path(ref['path'])
    assert path.is_absolute() and path == path.resolve() and pin(path) == ref
    return path

def save(name, value):
    path = HERE/name
    with path.open('x') as file:
        json.dump(value, file, sort_keys=True, indent=2)
        file.write('\n')
    return pin(path)

def literal(tree, name):
    node = next(node for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
    return ast.literal_eval(node.value)

def segment(raw, node):
    return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])

def patch_bytes(old, patch):
    lines = old.splitlines(keepends=True)
    hunks = patch.splitlines(keepends=True)
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    output, pos, index = [], 0, 2
    while index < len(hunks):
        match = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', hunks[index])
        assert match
        start, count, made_count = int(match[1]), int(match[2] or b'1'), int(match[4] or b'1')
        index += 1
        begin = start-1 if count else start
        assert begin >= pos
        output.extend(lines[pos:begin])
        pos, used, made = begin, 0, 0
        while index < len(hunks) and not hunks[index].startswith(b'@@ '):
            line = hunks[index]
            index += 1
            assert line[:1] in (b' ', b'-', b'+')
            if line[:1] in (b' ', b'-'):
                assert lines[pos] == line[1:]
                pos += 1
                used += 1
            if line[:1] in (b' ', b'+'):
                output.append(line[1:])
                made += 1
        assert used == count and made == made_count
    output.extend(lines[pos:])
    return b''.join(output)

def delta(ref):
    data = read(checked(ref))
    old, new = checked(data['parent']).read_bytes(), checked(data['source']).read_bytes()
    assert patch_bytes(old, checked(data['patches'][0]).read_bytes()) == new
    assert patch_bytes(new, checked(data['patches'][1]).read_bytes()) == old
    if 'edits' in data:
        forward, back = old, new
        for edit in reversed(data['edits']):
            a, b = edit['old_utf8'].encode(), edit['new_utf8'].encode()
            assert old[edit['old_start']:edit['old_end']] == a
            assert new[edit['new_start']:edit['new_end']] == b
            forward = forward[:edit['old_start']]+b+forward[edit['old_end']:]
            back = back[:edit['new_start']]+a+back[edit['new_end']:]
        assert forward == new and back == old
    if 'literal_replacements' in data:
        forward, back = old.decode(), new.decode()
        for edit in data['literal_replacements']:
            assert forward.count(edit['old']) == 1
            forward = forward.replace(edit['old'], edit['new'], 1)
        for edit in reversed(data['literal_replacements']):
            assert back.count(edit['new']) == 1
            back = back.replace(edit['new'], edit['old'], 1)
        assert forward.encode() == new and back.encode() == old
    return old, new

def main():
    folder = BASE/'receptor-family-bridge-cold-ROOT-source-20261016'
    cr = pin(folder/'Source-contract-v2.json')
    assert cr['sha256'] == '4d2387f7d343ebe4606ccf1a4aa897c0b2842f83a95ffb99e2e0b04f280d7c2e'
    contract = read(checked(cr))
    sources, inputs = contract['sources'], contract['inputs']
    assert len(sources) == 18 and len(inputs) == 9
    for refs in (sources, inputs, contract['original_model_sources'], contract['original_model_inputs']):
        for ref in refs.values():
            checked(ref)
    assert len(contract['original_model_sources']) == 17 and len(contract['original_model_inputs']) == 2
    raw = checked(sources['intake']).read_bytes()
    tree = ast.parse(raw)
    for ref in sources.values():
        compile(ast.parse(checked(ref).read_bytes()), ref['path'], 'exec')
    for name, wanted in [
        ('FIXED', {k:v for k,v in sources.items() if k != 'intake'}),
        ('FIXED_INPUTS', inputs), ('ORIGINAL_SOURCES', contract['original_model_sources']),
        ('ORIGINAL_INPUTS', contract['original_model_inputs']),
        ('ORIGINAL_BINDING', contract['original_model_binding']), ('LIMITS', contract['limits']),
        ('VERSION', contract['version']), ('SCOPE', contract['scope']),
        ('QUALIFICATION_CASES_BY_PURPOSE', {contract['purpose']:contract['expected_cases']})]:
        assert literal(tree, name) == wanted
    assert len(contract['expected_cases']) == len(set(contract['expected_cases'])) == 12
    parent1, current = delta(contract['source_delta'])
    assert current == raw
    original, child1 = delta(pin(folder/'Source-delta-v1.json'))
    assert child1 == parent1
    ot = ast.parse(original)
    old_funcs = {n.name:n for n in ot.body if isinstance(n, ast.FunctionDef)}
    new_funcs = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert len(old_funcs) == len(new_funcs) == 18 and set(old_funcs) == set(new_funcs)
    for name in set(old_funcs)-{'main'}:
        assert segment(original, old_funcs[name]) == segment(raw, new_funcs[name])
    old_classes = {n.name:n for n in ot.body if isinstance(n, ast.ClassDef)}
    new_classes = {n.name:n for n in tree.body if isinstance(n, ast.ClassDef)}
    assert len(old_classes) == 2 and set(old_classes) == set(new_classes)
    for name in old_classes:
        assert segment(original, old_classes[name]) == segment(raw, new_classes[name])
    suffix = b'    boundary();offset=0\n'
    assert original[original.index(suffix):] == raw[raw.index(suffix):]
    parent_contract = read(checked(read(folder/'Source-delta-v1.json')['parent_source_contract']))
    for key in ('original_model_sources', 'original_model_inputs', 'original_model_binding', 'limits'):
        assert contract[key] == parent_contract[key]
    assert all(sources[k] == value for k,value in parent_contract['sources'].items() if k != 'intake')
    assert {k:v for k,v in inputs.items() if k != 'family_descriptor'} == parent_contract['inputs']
    component_contracts = {role:read(checked(ref)) for role,ref in contract['component_contracts'].items()}
    for role, component_contract in component_contracts.items():
        assert component_contract['source'] == sources[role]
    cases_contract = component_contracts['component_cases']
    assert cases_contract['expected_cases'] == contract['expected_cases']
    delta(cases_contract['source_delta'])
    adapter_contract = component_contracts['family_adapter']
    for ref in adapter_contract['source_delta_chain']:
        delta(ref)
    assert adapter_contract['original_model_sources'] == contract['original_model_sources']
    assert adapter_contract['original_model_inputs'] == contract['original_model_inputs']
    for role, ref in adapter_contract['dependency_sources'].items():
        checked(ref)
    cycle_paths = {
        'family_expander':'receptor-family-expander-independent-source-20261016/typed-Source-review-v1.json',
        'family_checker':'receptor-family-expansion-checker-independent-source-20261016/typed-Source-review-v1.json',
        'family_adapter':'receptor-family-six-rule-adapter-independent-source-20261016/typed-Source-review-v3.json',
        'component_cases':'receptor-family-bridge-controls-independent-source-20261016/typed-Source-review-v2.json'}
    cycle = {}
    for role, path in cycle_paths.items():
        ref = pin(BASE/path)
        review = read(checked(ref))
        assert review['source'] == sources[role] and review['source_contract'] == contract['component_contracts'][role]
        assert review['scientific_calls'] == 0 and not review.get('blockers', review.get('concrete_blockers', []))
        assert (review['status'] == 'CONDITIONAL_SOURCE_PASS' if role == 'family_adapter'
                else review['source_review_passed'] is True and review['source_only'] is True)
        checked(review['findings'])
        cycle[role] = ref
    unchanged = read(checked(contract['unchanged_component_contract']))
    assert all(sources[k] == v for k,v in unchanged['sources'].items())
    for ref in contract['unchanged_component_reviews'].values():
        review = read(checked(ref))
        assert review['sources'] == unchanged['sources'] and review['source_contract'] == contract['unchanged_component_contract']
        assert review['source_review_passed'] is review['source_only'] is True and review['scientific_calls'] == 0
    peer_path = BASE/'receptor-family-bridge-cold-independent-source-20261016/typed-Source-review-v2.json'
    peer = read(peer_path)
    assert peer['source'] == sources['intake'] and peer['sources'] == sources and peer['source_contract'] == cr
    assert peer['scope'] == contract['scope'] and peer['author_identity'] == '/root'
    assert peer['reviewer_identity'] == '/root/hilbert_advice_controls'
    assert peer['source_review_passed'] is peer['source_only'] is True and peer['scientific_calls'] == 0
    assert peer['scientific_acceptance'] is False
    checks = save('ROOT-component-composition-audit-v1.json', dict(
        schema='ROOT-receptor-family-component-composition-audit-v1', source=sources['intake'], source_contract=cr,
        current_source18_input9_original17_input2_distinct=True,
        raw_forward_and_full_inverse_patch_directions=10,
        top_helpers17_classes2_native_suffix_raw_exact=True, cases_six_literal_replacements_exact=True,
        adapter_v1_v2_v3_four_and_six_regions_exact=True,
        component_review_cycle=cycle, whole_caller_peer=pin(peer_path),
        unchanged_component_reviews=contract['unchanged_component_reviews'],
        AST_compile_without_evaluation_only=True, scientific_calls=0,
        disclosure='Root read whole producer and operative API/contract, whole adapterV1 plus every currentV2/V3 delta and contract, whole cases/caller and contracts. Root checker read public/critical boundary, not whole checker; whole checker peer review is Controls f69. Shared wire/old native authorship is disclosed by each component peer. This audit binds their exact current caps and does not relabel metadata as a second mathematical implementation.',
        conformance='Proposal-only typed family/point bridge in specialized24row/sixrule model. No candidate graph, fallback, live scheduler/rollback, theorem, automatic lemma extraction, RL or gain acceptance.'))
    review = dict(contract['Review_ABI'])
    review.update(source_contract=cr, reviewer_identity='/root', source_review_passed=True,
        concrete_blockers=[], composition_audit=checks,
        whole_operative_caller_Source_and_contract_review=True,
        authorship_disclosure='Root author of caller/cases, separate genuine Controls caller review and Diagnosis cases review. Component producer/checker/adapter have disclosed cross-review cycle. Root owns actuals.',
        checks=['All native/source/authentication guards and final tail preserve previous framework; raw17helper/2class and actual inverse checked.',
                'Current18/input9 do not rebase original17/input2 semantic epoch, Gamma, six rules, height24 or profile.',
                'Fresh syntax checker, native member admission and marked union checks are charged in one actual and all full records retained.',
                'Twelve ordered component assertions are distinct from current engine8/12; five positive native rules plus genuine original-empty-Gamma assumption rejection.',
                'No advice install, GCTS degree/EOF/scheduler/rollback or theorem/RL/advantage acceptance. Unexpected runtime exceptions are re-raised unchanged.'])
    root_review = save('ROOT-caller-Source-review-v1.json', review)
    runtime = pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
    assert runtime['sha256'] == 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    owned, external = HERE/'RF-owned-v1', HERE/'RF-external-v1'
    assert not owned.exists() and not external.exists()
    common = dict(invocation_id='receptor-family-component-20261016-v1', purpose=contract['purpose'],
        output_directory=str(owned), sources=sources, inputs=inputs, source_contract=cr,
        reviews=dict(ROOT=root_review, peer=pin(peer_path)), runtime=runtime, limits=contract['limits'],
        resource_rule='single-owned-process-native-terminal-v1')
    grant = save('ROOT-RF-authorization-v1.json', dict(common,
        schema='ROOT-routed-engine-qualification-authorization-v1', author_identity='/root',
        actual_execution_authorized=True, maximum_actual_invocations=1,
        component_only=True, engine_promoted=False, scientific_acceptance=False, target_budget_changed=False))
    plan = save('ROOT-RF-plan-v1.json', dict(common, schema='ROOT-routed-engine-qualification-plan-v1', ROOT_authorization=grant))
    print(json.dumps(dict(plan=plan, external_directory=str(external), scientific_calls=0)))

if __name__ == '__main__':
    main()
