"""Metadata/source only: raw hashes, AST and source-ZIP; no scientific imports."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import resource
import time
import zipfile

ROOT = Path.cwd()
PACKAGE = Path('.gcts-active/fixed-family-pool-search-source-20261012')
OUT = Path('.gcts-active/fixed-family-pool-search-arithmetic-source-review-20261012')


def pin(path):
    path = Path(path); sha = hashlib.sha256(); length = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            sha.update(block); length += len(block)
    return {'path': str(path), 'sha256': sha.hexdigest(), 'bytes': length}


def save(name, data):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    begin = time.perf_counter()
    plan_path = PACKAGE / 'search-plan-v1.json'
    plan_pin = pin(plan_path)
    assert plan_pin['sha256'] == 'f63c9e804e67848100c513048452e16a2e00e16b5b21864ebb457c6d39d8ea4f'
    plan = json.loads(plan_path.read_text())
    entries = plan['sources'] + plan['inputs'] + plan['preserved_files']
    assert (len(plan['sources']), len(plan['inputs']), len(plan['preserved_files'])) == (7, 22, 774)
    assert len(entries) == 803 and len({item['path'] for item in entries}) == 803
    verified = []
    for item in entries:
        actual = pin(item['path'])
        assert actual == {key: item[key] for key in ('path', 'sha256', 'bytes')}, item['path']
        verified.append(actual)
    integration = json.loads((PACKAGE / 'integration-v1.json').read_text())
    for item in integration['files']:
        assert pin(item['path']) == item
    role = {item['role']: Path(item['path']) for item in plan['inputs']}
    assert len(role) == 22
    body_plan = json.loads(role['passed_full_lifecycle_producer_plan'].read_text())
    assert len(body_plan['inputs']) == 56
    runtime = plan['runtime']
    actual_runtime = pin(runtime['binary']['path'])
    assert actual_runtime == runtime['binary']
    assert str(Path(runtime['executable']).resolve()) == runtime['binary']['path']
    assert pin(runtime['executable'])['sha256'] == actual_runtime['sha256']
    for item in plan['static_gate_pins'].values():
        assert pin(item['path']) == item

    source_asts = []
    extra_sources = [role['prior_search_worker'], role['prior_unchanged_sibling_import'],
                     role['prior_unchanged_decoder'], role['frozen_lifecycle_kernel'],
                     role['proposal_module'],
                     Path('.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py')]
    for path in [Path(item['path']) for item in plan['sources']] + extra_sources:
        ast.parse(path.read_text(), filename=str(path), feature_version=(3, 9))
        source_asts.append({'source': pin(path), 'Python39_AST_parse': True, 'imported': False})
    old_text = role['prior_search_worker'].read_text()
    new_text = (PACKAGE / 'fixed_family_pool_adapter_v1.py').read_text()
    old_function = next(node for node in ast.parse(old_text).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'automatic_search')
    new_function = next(node for node in ast.parse(new_text).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'fixed_pool_search')
    old_nodes = {node.name: node for node in old_function.body if isinstance(node, ast.FunctionDef)}
    new_nodes = {node.name: node for node in new_function.body if isinstance(node, ast.FunctionDef)}
    unchanged = []
    for name in ('event', 'rollback', 'step', 'walk'):
        assert ast.dump(old_nodes[name], include_attributes=False) == ast.dump(new_nodes[name], include_attributes=False)
        unchanged.append(name)
    expected_diff = ''.join(difflib.unified_diff(
        (ast.get_source_segment(old_text, old_function) + '\n').splitlines(True),
        (ast.get_source_segment(new_text, new_function) + '\n').splitlines(True),
        fromfile='prior automatic_search unchanged', tofile='fixed_pool_search source-only sibling'))
    assert expected_diff == (PACKAGE / 'search-function-source-diff-v1.txt').read_text()
    zipped = []
    archive = PACKAGE / 'source-only-v1.zip'
    expected_members = [Path(item['path']).name for item in plan['sources']] + [
        'search-function-source-diff-v1.txt', 'prospective-audit-protocol-v1.json', 'search-plan-v1.json']
    with zipfile.ZipFile(archive) as source_zip:
        assert source_zip.namelist() == expected_members
        for member in source_zip.infolist():
            sha = hashlib.sha256(); length = 0
            with source_zip.open(member) as stream:
                for block in iter(lambda: stream.read(65536), b''):
                    sha.update(block); length += len(block)
            actual = pin(PACKAGE / member.filename)
            assert (sha.hexdigest(), length) == (actual['sha256'], actual['bytes'])
            zipped.append({'member': member.filename, 'sha256': sha.hexdigest(), 'bytes': length})
    assert plan['observations'] == [{'id': 'fixed-whole-family-pool', 'mode': 'fixed-whole-family-pool',
                                   'attempts': 128, 'seconds': 20, 'event_ceiling': 2000}]
    assert plan['prospective_resources'] == {'whole_seconds': 180, 'supervisor_seconds': 175,
                                          'child_seconds': 170, 'peak_bytes': 536870912}
    save('bindings-v1.json', {'plan': plan_pin, 'verified_pin_count': 803, 'pins': verified,
                             'source_zip': pin(archive), 'exact_zip_members': zipped,
                             'source_ASTs': source_asts, 'unchanged_nested_DFS_ASTs': unchanged,
                             'saved_DFS_diff_exact': True, 'original_body_plan_inputs': 56,
                             'runtime': runtime, 'static_gate_pins': plan['static_gate_pins']})
    interval = time.perf_counter() - begin
    save('metadata-cost-v1.json', {
        'status': 'passed_source_hash_AST_ZIP_metadata_checks_only',
        'seconds_before_cost_receipt_write': interval,
        'kernel_helper_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'raw_pinned_bytes_hashed': sum(item['bytes'] for item in verified),
        'metadata_decoding_scope': 'Search/source plans and manifests only; no model, trace, pool descriptor/result, scientific fixture or checker data decoded.',
        'scientific_import_model_fixture_search_owner_activation_RNG_native_replay_calls': 0,
        'runtime_executed_for_science': False,
        'cost_scope': 'Raw byte hashes/13 ASTs/source ZIP/metadata serialization; excludes startup, human source review, final cost receipt writing.'})
    print(json.dumps({'verified_pins': len(verified), 'ZIP_members': len(zipped),
                      'source_ASTs': len(source_asts), 'seconds': interval,
                      'kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))


if __name__ == '__main__':
    main()
