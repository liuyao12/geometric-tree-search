"""Root metadata/AST review only. No project imports or scientific calls."""
import ast
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
FOLDER = BASE / 'unit-row-marked-aware-router-engine-source-20261016'


def read(path):
    return json.loads(Path(path).read_bytes())


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def checked(ref):
    assert pin(ref['path']) == ref, ref['path']
    return Path(ref['path'])


def patch_bytes(old, patch):
    lines, hunks = old.splitlines(keepends=True), patch.splitlines(keepends=True)
    out, pos, ix = [], 0, 2
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    while ix < len(hunks):
        match = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', hunks[ix])
        assert match
        start, count, new_count = int(match[1]), int(match[2] or b'1'), int(match[4] or b'1')
        begin = start - 1 if count else start
        assert begin >= pos
        out.extend(lines[pos:begin]); pos = begin; used = made = 0; ix += 1
        while ix < len(hunks) and not hunks[ix].startswith(b'@@ '):
            line = hunks[ix]; ix += 1
            assert line[:1] in (b' ', b'-', b'+')
            if line[:1] in (b' ', b'-'):
                assert lines[pos] == line[1:]
                pos += 1; used += 1
            if line[:1] in (b' ', b'+'):
                out.append(line[1:]); made += 1
        assert used == count and made == new_count
    out.extend(lines[pos:])
    return b''.join(out)


def regions(tree, prefix=''):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = prefix + node.name
            result[name] = node
            if isinstance(node, ast.ClassDef):
                result.update(regions(node, name + '.'))
    return result


def segment(raw, node):
    return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])


contract_path = FOLDER / 'Source-contract-v1.json'
contract = read(contract_path)
assert pin(contract_path)['sha256'] == '221429b1197ba7489073260a06c882b2ca450dd97868a20a019e7ae3a7d3eade'
for refs in (contract['sources'], contract['original_model_sources'], contract['original_model_inputs']):
    for ref in refs.values():
        compile(ast.parse(checked(ref).read_bytes()), ref['path'], 'exec') if ref['path'].endswith('.py') else checked(ref)
parent = read(BASE / 'unit-row-marked-aware-calibration-report-ROOT-20261016/ROOT-progress-checkpoint-v1.json')
for name in ('original_model_sources', 'original_model_binding'):
    assert contract[name] == parent[name]
delta = read(checked(contract['source_delta']))
findings = {}
for role, info in delta['sources'].items():
    old = checked(info['parent']).read_bytes()
    new = checked(info['source']).read_bytes()
    forward, inverse = old, new
    for edit in reversed(info['edits']):
        before, after = edit['old_utf8'].encode(), edit['new_utf8'].encode()
        assert old[edit['old_start']:edit['old_end']] == before
        assert new[edit['new_start']:edit['new_end']] == after
        forward = forward[:edit['old_start']] + after + forward[edit['old_end']:]
        inverse = inverse[:edit['new_start']] + before + inverse[edit['new_end']:]
    assert forward == new and inverse == old
    assert len(info['edits']) == info['edit_count']
    patches = info['patches']
    assert patch_bytes(old, checked(patches[0]).read_bytes()) == new
    assert patch_bytes(new, checked(patches[1]).read_bytes()) == old
    findings[role] = dict(parent=info['parent'], source=info['source'], exact_edits=info['edit_count'],
                          raw_region_forward_inverse=True, actual_patch_forward_inverse=True)
old_engine = checked(contract['parent_engine']).read_bytes()
engine = checked(contract['source']).read_bytes()
old_adapter = checked(contract['parent_point_adapter']).read_bytes()
router = checked(contract['router_source']).read_bytes()
old_regions, current_regions = regions(ast.parse(old_engine)), regions(ast.parse(engine))
for name in delta['engine_core_raw_AST_exact']:
    assert segment(old_engine, old_regions[name]) == segment(engine, current_regions[name]), name
    assert ast.dump(old_regions[name], include_attributes=False) == ast.dump(current_regions[name], include_attributes=False)
assert segment(old_engine, old_regions['LazyUnitRowEngine.search']).replace(
    b"'unit-row-channel4-lazy-global-search-result-v1'",
    b"'unit-row-channel4-routed-lazy-global-search-result-v1'") == segment(engine, current_regions['LazyUnitRowEngine.search'])
adapter_regions, router_regions = regions(ast.parse(old_adapter)), regions(ast.parse(router))
for method in ('_projection', 'refresh_candidates'):
    assert segment(old_adapter, adapter_regions['MarkedTransition.'+method]) == segment(router, router_regions['RoutedMarkedTransition.'+method])
assert segment(old_adapter, adapter_regions['MarkedTransition.check_transition']).replace(
    b"'unit-row-channel4-checked-domain-transition-v1'",
    b"'unit-row-channel4-checked-domain-transition-v2'") == segment(router, router_regions['RoutedMarkedTransition.check_transition'])

review = dict(contract['Review_ABI'])
review.update(source_contract=pin(contract_path), reviewer_identity='/root', source_only=True,
    source_review_passed=True, scientific_calls=0, scientific_acceptance=False, concrete_blockers=[],
    whole_current_Source_and_contract_read=True, raw_inverse_findings=findings,
    inherited_engine_core_raw_AST_exact=delta['engine_core_raw_AST_exact'],
    support_projection_refresh_raw_exact=True, search_only_result_schema_changed=True,
    trusted_origin_scope='Native validator is a protocol/context cross-check after the exact routed independent checker. It is not an independent mathematical checker for arbitrary caller-supplied receipts; transfers and prefix records are engine-private.',
    authorship_disclosure='Arithmetic authors router/engine12 and old engine/adapter; diagnosis authors new independent fibre/state checking. Root read whole router/new regions/current contract and whole old engine/adapter; all unchanged regions independently joined by raw/AST inverses. No scientific module imported or called.',
    checks=[
        'Assigned nonimp route comes from fresh full checked state/output; immutable old point object passed to proposer/cursor. Raised errors propagate without fallback.',
        'Exact native legacy/new protocols retained; original17/input2/binding unchanged and separate from future current14 executable map.',
        'Fresh independent receipt checked before native context gate; ZERO/ONE completion separate from TWO lower bound; strong authority flags false.',
        'Typed transfer preserves whole historical native origin/census and correct origin-specific coverage flag; current sole/observations refresh under unchanged full-support/collision equality.',
        'Canonical fallback context/order/replay/EOF stream and global decision/owned rollback functions raw exact; fresh certifier joins entire actual survivor key set with fresh complete cover.',
        'Legacy implication/absent coverage remains safe, including UNKNOWN; no new target route, learned policy, budget easing or theorem result.',
    ],
    remaining_gates=['Root-owned fresh cold qualification and strict native/saved closure.',
                     'Target discovery and matched ordinary baseline only after engine qualification.'])
out = HERE / 'ROOT-router-engine-Source-review-v1.json'
with out.open('x') as stream:
    json.dump(review, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'review':pin(out), 'source_only':True, 'scientific_calls':0, 'raw_inverse':findings}))
