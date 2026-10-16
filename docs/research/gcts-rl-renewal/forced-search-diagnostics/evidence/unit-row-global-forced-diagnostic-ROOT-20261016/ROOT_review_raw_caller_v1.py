"""Root Source/AST/raw-byte audit only. No mathematical module is evaluated."""
import ast
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
FOLDER = BASE / 'unit-row-global-forced-diagnostic-cold-source-20261016'


def read(p):
    return json.loads(Path(p).read_bytes())


def pin(p):
    p = Path(p)
    b = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))


def checked(ref):
    p = Path(ref['path'])
    assert p.is_absolute() and p == p.resolve() and pin(p) == ref
    return p


def literal(tree, name):
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    return ast.literal_eval(node.value)


def segment(raw, node):
    return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])


def patch_bytes(old, patch):
    lines = old.splitlines(keepends=True)
    hunks = patch.splitlines(keepends=True)
    out = []
    pos = 0
    ix = 2
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    while ix < len(hunks):
        match = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', hunks[ix])
        assert match
        start = int(match[1])
        count = int(match[2] or b'1')
        newcount = int(match[4] or b'1')
        ix += 1
        begin = start-1 if count else start
        assert begin >= pos
        out.extend(lines[pos:begin])
        pos = begin
        used = made = 0
        while ix < len(hunks) and not hunks[ix].startswith(b'@@ '):
            line = hunks[ix]
            ix += 1
            assert line[:1] in (b' ', b'-', b'+')
            if line[:1] in (b' ', b'-'):
                assert lines[pos] == line[1:]
                pos += 1
                used += 1
            if line[:1] in (b' ', b'+'):
                out.append(line[1:])
                made += 1
        assert used == count and made == newcount
    out.extend(lines[pos:])
    return b''.join(out)


def main():
    delta_path = FOLDER / 'Source-delta-v1.json'
    delta = read(delta_path)
    raw = checked(delta['source']).read_bytes()
    old = checked(delta['parent']).read_bytes()
    assert delta['source']['sha256'] == '28953cad70c4d51c9e18be583c2a3d95356676763f73bb580d28e48603b75608'
    assert delta['parent']['sha256'] == 'dd4edc8a204b9407a27e8c2d09d0a795accd6d6028e509ed96cabd879621f325'
    assert len(delta['edits']) == delta['edit_count'] == 13
    forward, inverse = old, raw
    for edit in reversed(delta['edits']):
        a, b = edit['old_utf8'].encode(), edit['new_utf8'].encode()
        assert old[edit['old_start']:edit['old_end']] == a
        assert raw[edit['new_start']:edit['new_end']] == b
        forward = forward[:edit['old_start']] + b + forward[edit['old_end']:]
        inverse = inverse[:edit['new_start']] + a + inverse[edit['new_end']:]
    assert forward == raw and inverse == old
    assert patch_bytes(old, checked(delta['patches'][0]).read_bytes()) == raw
    assert patch_bytes(raw, checked(delta['patches'][1]).read_bytes()) == old
    ot, nt = ast.parse(old), ast.parse(raw)
    assert ast.dump(ast.parse(inverse), include_attributes=False) == ast.dump(ot, include_attributes=False)
    for name in ('FIXED', 'FIXED_INPUTS', 'ORIGINAL_SOURCES', 'ORIGINAL_INPUTS',
                 'ORIGINAL_BINDING', 'LIMITS', 'QUALIFICATION_CASES_BY_PURPOSE', 'CLOCK_DOMAIN'):
        assert literal(ot, name) == literal(nt, name), name
    for refs in (literal(nt, 'FIXED'), literal(nt, 'FIXED_INPUTS'),
                 literal(nt, 'ORIGINAL_SOURCES'), literal(nt, 'ORIGINAL_INPUTS')):
        for ref in refs.values():
            checked(ref)
    for ref in literal(nt, 'FIXED').values():
        compile(ast.parse(checked(ref).read_bytes()), ref['path'], 'exec')
    compile(nt, delta['source']['path'], 'exec')
    old_top = {n.name: n for n in ot.body if isinstance(n, ast.FunctionDef)}
    new_top = {n.name: n for n in nt.body if isinstance(n, ast.FunctionDef)}
    assert len(old_top) == 18 and set(old_top) == set(new_top)
    for name in set(old_top) - {'main'}:
        assert segment(old, old_top[name]) == segment(raw, new_top[name]), name
        assert ast.dump(old_top[name], include_attributes=False) == ast.dump(new_top[name], include_attributes=False)
    old_nested = {n.name: n for n in old_top['main'].body if isinstance(n, ast.FunctionDef)}
    new_nested = {n.name: n for n in new_top['main'].body if isinstance(n, ast.FunctionDef)}
    assert len(old_nested) == 34 and set(old_nested) == set(new_nested)
    for name in set(old_nested) - {'make_engine', 'global_family'}:
        assert segment(old, old_nested[name]) == segment(raw, new_nested[name]), name
        assert ast.dump(old_nested[name], include_attributes=False) == ast.dump(new_nested[name], include_attributes=False)
    def assertions(node):
        return [ast.dump(n, include_attributes=False) for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'need']
    assert assertions(old_nested['global_family']) == assertions(new_nested['global_family'])
    for old_class in (n for n in ot.body if isinstance(n, ast.ClassDef)):
        new_class = next(n for n in nt.body if isinstance(n, ast.ClassDef) and n.name == old_class.name)
        assert segment(old, old_class) == segment(raw, new_class)
    suffix = b'    boundary();offset=0\n'
    assert old[old.index(suffix):] == raw[raw.index(suffix):]
    prints = [n for n in ast.walk(nt) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name) and n.func.id == 'print'
              and n.args and isinstance(n.args[0], ast.Constant)
              and isinstance(n.args[0].value, str) and n.args[0].value.startswith('GF_')]
    assert len(prints) == len({n.args[0].value for n in prints}) == 7
    output = dict(schema='ROOT-global-forced-diagnostic-raw-Source-review-v1',
                  source=delta['source'], parent=delta['parent'], delta=pin(delta_path),
                  exact13region_full_raw_and_actual_patch_inverse=True,
                  top17_helpers_raw_AST_exact=True, direct_nested32_raw_AST_exact=True,
                  all_original_global_need_assertions_AST_exact=True, two_classes_raw_exact=True,
                  original_native_exit_and_top_level_failure_suffix_raw_exact=True,
                  existing_failure_writer_raw_exact=True, all_semantic_maps_inputs_limits_cases_exact=True,
                  current13_delegated_sources_original17_input2_verified=True,
                  seven_unique_fixed_marker_sites=True, compile_without_evaluation=True,
                  Root_read_all_added_regions_and_whole_parent_Source=True,
                  contract_review_or_actual_authorization_supplied=False,
                  source_only=True, scientific_calls=0, scientific_acceptance=False)
    with (HERE / 'ROOT-caller-raw-inverse-review-v1.json').open('x') as f:
        json.dump(output, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
