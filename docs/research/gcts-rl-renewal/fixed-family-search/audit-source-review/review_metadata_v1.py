"""Bounded SOURCE/JSON-metadata/hash/AST/ZIP-only independent reconciliation.

No project modules are imported; no gzip payload is inflated and no scientific
model/result/tape JSON is decoded. ROOT retains every actual execution gate.
"""
import ast
import hashlib
import json
import resource
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PACKAGE = ROOT / '.gcts-active/fixed-family-pool-trace-independent-20261012'
EXPECTED_PLAN = '60efcf293e9c1163a846560dbb610bae030d240336ead10b0caf08c6063f469a'
EXPECTED_INTEGRATION = 'f0d7e73e234f2284ca3a718f2e2a24575b56768782be99362a75bab8c5d239d9'


def pin(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
            size += len(block)
    return dict(path=str(path), sha256=digest.hexdigest(), bytes=size)


def save(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    began = time.perf_counter()
    if any((HERE / name).exists() for name in ('bindings-v1.json', 'metadata-cost-v1.json')):
        raise ValueError('exclusive source review metadata outputs already exist')
    plan_pin = pin(PACKAGE / 'audit-plan-v1.json')
    integration_pin = pin(PACKAGE / 'integration-v1.json')
    if plan_pin['sha256'] != EXPECTED_PLAN or integration_pin['sha256'] != EXPECTED_INTEGRATION:
        raise ValueError('exact independently reviewed package identity changed')
    # These are source plans and package manifests, never scientific payloads.
    plan = json.loads(Path(plan_pin['path']).read_text())
    integration = json.loads(Path(integration_pin['path']).read_text())
    expected = {}
    occurrences = []
    for group in ('sources', 'libraries', 'inputs', 'preserved'):
        for row in plan[group]:
            record = {key: row[key] for key in ('path', 'sha256', 'bytes')}
            path = str(Path(record['path']).resolve())
            if path != record['path']:
                raise ValueError('declared absolute path is not canonical: ' + path)
            if path in expected and expected[path] != record:
                raise ValueError('conflicting exact source/input path')
            expected[path] = record
            occurrences.append(dict(group=group, role=row.get('role'), path=path))
    checked = []
    for path, record in sorted(expected.items()):
        actual = pin(path)
        if actual != record:
            raise ValueError('source/input byte mismatch: ' + path)
        checked.append(actual)
    if len(checked) != 817:
        raise ValueError('expected complete 817-path source closure')
    package_files = []
    for row in integration['files']:
        actual = pin(row['path'])
        if actual != {key: row[key] for key in ('path', 'sha256', 'bytes')}:
            raise ValueError('integration member mismatch')
        package_files.append(actual)
    parsed = []
    for row in plan['sources'] + plan['libraries']:
        source = Path(row['path']).read_text()
        tree = ast.parse(source, filename=row['path'], feature_version=(3, 9))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        parsed.append(dict(path=row['path'], AST_nodes=sum(1 for _ in ast.walk(tree)),
                           import_names=sorted(set(imports))))
    archive = PACKAGE / 'audit-source-v1.zip'
    archive_expected = {Path(row['path']).name: row for row in plan['sources']}
    for name in ('source-plan-v1.json', 'audit-plan-v1.json'):
        archive_expected[name] = pin(PACKAGE / name)
    archived = []
    with zipfile.ZipFile(archive) as source_zip:
        names = source_zip.namelist()
        if len(names) != len(set(names)) or set(names) != set(archive_expected):
            raise ValueError('exact source ZIP member set')
        for name in names:
            payload = source_zip.read(name)
            actual = dict(sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
            wanted = {key: archive_expected[name][key] for key in ('sha256', 'bytes')}
            if actual != wanted:
                raise ValueError('source ZIP member bytes: ' + name)
            archived.append(dict(name=name, **actual))
    runtime = plan['runtime']
    if pin(runtime['binary']['path']) != runtime['binary'] or pin('/bin/ps') != runtime['observer']:
        raise ValueError('runtime/observer binary pin')
    if Path(runtime['executable']).resolve() != Path(runtime['binary']['path']).resolve():
        raise ValueError('declared runtime alias resolution')
    outputs_absent = {key: not Path(path).exists() for key, path in plan['outputs'].items()}
    activation_absent = not Path(plan['activation_path']).exists()
    if not all(outputs_absent.values()) or not activation_absent:
        raise ValueError('source disposition must precede ROOT dispatch')
    if plan['limits'] != dict(whole_seconds=180, supervisor_seconds=175,
                              child_seconds=170, peak_bytes=536870912):
        raise ValueError('prospective audit resource gates')
    save('bindings-v1.json', dict(status='passed_exact_source_only_metadata_reconciliation',
        plan=plan_pin, integration=integration_pin, source_input_occurrences=len(occurrences),
        unique_bound_paths=len(checked), exact_bound_files=checked, occurrences=occurrences,
        exact_package_files=package_files, Python39_AST=parsed, source_zip=pin(archive),
        exact_zip_members=archived, runtime=runtime, outputs_absent=outputs_absent,
        activation_absent=activation_absent, no_scientific_payload_decoded=True,
        project_imports=0, model_loads=0, fixtures=0, replays=0, checkers=0,
        search_runs=0, training_runs=0, native_queries=0, owner_dispatches=0))
    elapsed = time.perf_counter() - began
    save('metadata-cost-v1.json', dict(status='completed_source_only_hash_AST_metadata_helper',
        helper=pin(__file__), seconds_before_cost_receipt_write=elapsed,
        kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
            (1 if sys.platform == 'darwin' else 1024),
        scope='Hashing all raw pinned files, source-plan/manifest JSON and five source-ZIP entries; 11 source ASTs. No project imports or scientific payload decoding. Helper cost ends before final cost receipt serialization; source authoring/manual inspection is unmeasured and additional.'))
    print(json.dumps(dict(status='passed_source_only_metadata', unique_paths=len(checked),
        ASTs=len(parsed), ZIP_members=len(archived), seconds=elapsed), allow_nan=False))


if __name__ == '__main__':
    main()
