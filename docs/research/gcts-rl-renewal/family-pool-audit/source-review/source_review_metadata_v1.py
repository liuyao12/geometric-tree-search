"""Source-review metadata only; no scientific module imports or calls.

Hashes frozen bytes, checks the source ZIP, parses ASTs and writes the separate
review receipt. Does not decode model, certificate or preparation evidence.
"""
import ast
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
AUDIT = ROOT / '.gcts-active/family-pool-independent-audit-20261012'


def pin(path):
    path = Path(path).resolve()
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return dict(path=str(path), sha256=h.hexdigest(), bytes=size)


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    began = time.perf_counter()
    intent_path = HERE / 'metadata-review-plan-v1.json'
    intent = json.loads(intent_path.read_text())
    plan_path = Path(intent['audit_plan']['path'])
    if pin(plan_path) != intent['audit_plan']:
        raise ValueError('reviewed audit plan changed')
    plan = json.loads(plan_path.read_text())
    all_pins = plan['sources'] + plan['libraries'] + plan['inputs'] + plan['preserved']
    checked, mismatches, duplicates = {}, [], []
    for declaration in all_pins:
        expected = {k: declaration[k] for k in ('path', 'sha256', 'bytes')}
        actual = pin(expected['path'])
        if actual != expected:
            mismatches.append(dict(expected=expected, actual=actual))
        if expected['path'] in checked:
            duplicates.append(expected['path'])
            if checked[expected['path']] != expected:
                raise ValueError('one path has inconsistent frozen declarations')
        checked[expected['path']] = expected
    archive = pin(plan['source_archive']['path'])
    if archive != plan['source_archive']:
        mismatches.append(dict(expected=plan['source_archive'], actual=archive))
    archive_members = []
    with zipfile.ZipFile(archive['path']) as z:
        expected_names = [str(Path(item['path']).relative_to(ROOT))
                          for item in plan['sources'] + plan['libraries']]
        if z.namelist() != expected_names or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('archive names/order differ from frozen source closure')
        for item, name in zip(plan['sources'] + plan['libraries'], expected_names):
            data = z.read(name)
            actual = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            if actual != {k: item[k] for k in ('sha256', 'bytes')}:
                raise ValueError('archive member differs from frozen source bytes')
            archive_members.append(dict(member=name, **actual))
    runtime = pin(Path(plan['runtime']['executable']).resolve())
    if runtime != plan['runtime']['binary']:
        raise ValueError('runtime binary pin differs')
    if plan['limits'] != dict(whole_seconds=180, supervisor_seconds=175,
                             child_seconds=170, peak_bytes=536870912):
        raise ValueError('unexpected prospective resource limits')
    ast_sources = []
    for item in plan['sources'] + plan['libraries']:
        source = Path(item['path']).read_text()
        tree = ast.parse(source)
        imports, definitions = [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                definitions.append(dict(name=node.name, start=node.lineno, end=node.end_lineno))
        ast_sources.append(dict(pin={k: item[k] for k in ('path', 'sha256', 'bytes')},
            lines=len(source.splitlines()), imports=sorted(imports), definitions=definitions,
            AST_only=True, imported_or_executed=False))
    output_presence = {name: Path(path).exists() for name, path in plan['outputs'].items()}
    activation_present = Path(plan['activation_path']).exists()
    if mismatches:
        raise ValueError('frozen pin mismatches: ' + str(mismatches))
    result = dict(schema='independent_source_only_family_pool_review-v1',
        status='PASS_prospective_source_review_no_actual_acceptance',
        audit_plan=pin(plan_path), review_intent=pin(intent_path), review_tool=pin(__file__),
        reviewed_by='hilbert_incidence; producer author, not independent auditor author',
        independence='Reviewer uses only stdlib metadata operations; future audited worker imports independently authored point/body/symbolic libraries, never producer/core/lifecycle/controller/search/native code.',
        source_coverage=dict(new_sources='All three new sources read completely.',
            point_body_libraries='Full point and family registry sources read; source registry expansion, descriptor transports, identity reconstruction and initial-state semantics reviewed.',
            symbolic_library='All called helpers and SymbolicChecker methods through compile_primitive; point_union; imports and guarded CLI reviewed. Unused historic fixture/forest/CLI algorithms are outside this review.',
            expansion_library='All called symbolic_source_gate, transported_body, mapped_expression, literal_expansion, recipe_key, canonical_embedding, placed_identity, receptor_ports, checked_aggregate; associated helpers/imports and guarded CLI reviewed. Uncalled historical complete-file parser/audit/fixture routes are outside this review.'),
        checked_pin_counts=dict(sources=len(plan['sources']), libraries=len(plan['libraries']),
            inputs=len(plan['inputs']), preserved=len(plan['preserved']), total=len(all_pins),
            unique_paths=len(checked), duplicate_paths=duplicates, mismatches=0),
        all_exact_source_input_preservation_pins=list(checked.values()),
        archive=archive, archive_members=archive_members, runtime=plan['runtime'],
        AST_source_metadata=ast_sources,
        findings=intent['manual_findings'], blockers=[],
        owner_review=dict(limits=plan['limits'], exclusive_outputs=True,
            exact_ROOT_activation_required=True, fresh_runtime_and_byte_verification=True,
            direct_child_only=True, scientific_child_alarm_seconds=170,
            permitted_metadata_sampling='Owned child and owner RSS via /bin/ps; deadline and memory failures terminate owned process group and wait4/reap child.',
            terminal_resource_test='Maximum of sampled combined peak and conservative child+owner+metadata-child kernel peaks; no hard OS soft-limit assertion.',
            failure_semantics='Infrastructure/resource/worker failure is UNKNOWN, not pool or theorem rejection.',
            cost_scope='Owner timer starts before input/runtime/activation verification; worker serialization/postverification inside owned phase; final owner receipt write explicitly outside pre-write timer.',
            outside_process_observation='No child was launched, observed, imported or replayed by this reviewer.'),
        caveats=intent['caveats'],
        outputs_present_at_metadata_check=output_presence,
        activation_present_at_metadata_check=activation_present,
        actual_execution_authorized_by_this_review=False,
        scientific_imports=0, model_constructions=0, scientific_fixture_runs=0,
        audit_worker_runs=0, engine_runs=0, search_runs=0, native_queries=0,
        source_review_authoring_cost='Unmeasured human/model source inspection and writing; not zero.',
        metadata_validation_seconds_before_receipt_write=time.perf_counter()-began,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    save(HERE / 'source-review-v1.json', result)
    manifest = dict(status='immutable_source_only_review', files=[pin(HERE/name) for name in
        ('source_review_metadata_v1.py', 'metadata-review-plan-v1.json', 'source-review-v1.json')],
        authority='Prospective source disposition only; ROOT dispatch and actual independent audit remain separate.')
    save(HERE / 'integration-v1.json', manifest)
    print(json.dumps(dict(status=result['status'], counts=result['checked_pin_counts'],
        seconds=result['metadata_validation_seconds_before_receipt_write'],
        bytes=result['metadata_kernel_peak_bytes'], review=pin(HERE/'source-review-v1.json'),
        integration=pin(HERE/'integration-v1.json'), output_presence=output_presence,
        activation_present=activation_present)))


if __name__ == '__main__':
    main()
