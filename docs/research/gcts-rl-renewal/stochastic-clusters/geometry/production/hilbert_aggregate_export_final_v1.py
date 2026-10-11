"""Export immutable static aggregate evidence and compact read-only view."""
import hashlib
import json
import resource
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
EXTERNAL = ROOT / '.gcts-active/hilbert-aggregate-independent-audit-20261011'


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def validate(p):
    assert pin(ROOT / p['path']) == {k: p[k] for k in ('path', 'sha256', 'bytes')}, p['path']


def save(path, value):
    if path.exists():
        raise ValueError('immutable final export path exists')
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    started = time.perf_counter()
    manifest_path = HERE / 'export-final-v1.json'
    archive_path = HERE / 'evidence-final-v1.zip'
    if manifest_path.exists() or archive_path.exists():
        raise ValueError('final export already frozen')
    pending = json.loads((HERE / 'export-pending-v1.json').read_text())
    original = json.loads((HERE / 'plan-v1.json').read_text())
    for p in pending['files'] + original['preserved_files'] + original['argument_source_closure']:
        validate(p)
    for p in original['inputs'] + original['sources']:
        validate(p)
    repair = json.loads((HERE / 'plan-v2.json').read_text())
    for p in repair['sources'] + repair['v1_evidence_pins'] + repair['input_pins']:
        validate(p)
    reader_plan = json.loads((HERE / 'reader-extraction-plan-v2.json').read_text())
    for p in reader_plan['sources'] + reader_plan['inputs']:
        validate(p)
    external_manifest = EXTERNAL / 'integration-v2.json'
    external = json.loads(external_manifest.read_text())
    for p in external['files']:
        validate(p)
    audit = json.loads((EXTERNAL / 'audit-full-v2.json').read_text())
    audit_lifetime = json.loads((EXTERNAL / 'audit-lifetime-v2.json').read_text())
    assert audit['status'] == 'passed_independent_finite_static_symbolic_and_aggregate_audit'
    assert audit_lifetime['status'] == 'passed_full_lifetime_static_audit_gate'
    production = json.loads((HERE / 'outer-lifetime-v2.json').read_text())
    extraction = json.loads((HERE / 'reader-extraction-lifetime-v2.json').read_text())
    assert production['status'] == 'passed_outer_static_production_lifetime'
    assert extraction['status'] == 'passed_bounded_reader_preparation'
    completion = json.loads((EXTERNAL / 'completion-receipt-v2.json').read_text())
    files = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]
    members = {p['path']: p for p in files + original['argument_source_closure'] + external['files']}
    for p in original['inputs'] + reader_plan['inputs']:
        members[p['path']] = {k: p[k] for k in ('path', 'sha256', 'bytes')}
    members[str(external_manifest.relative_to(ROOT))] = pin(external_manifest)
    archive_contents = HERE / 'archive-contents-final-v1.json'
    save(archive_contents, {'status': 'exact_repository_relative_source_data_receipts',
                           'members': [members[k] for k in sorted(members)],
                           'member_count_excluding_this_receipt': len(members),
                           'scope': 'Own static phase, exact authoritative inputs, reviewed argument closure, independent finite audit, compact reader sources/data, and both preserved failure histories. No generic compiler/native authority claim.'})
    members[str(archive_contents.relative_to(ROOT))] = pin(archive_contents)
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with (ROOT / name).open('rb') as source, archive.open(info, 'w') as target:
                while True:
                    chunk = source.read(65536)
                    if not chunk:
                        break
                    target.write(chunk)
    # Full archive member byte/hash reconciliation, without loading scientific JSON.
    with zipfile.ZipFile(archive_path) as archive:
        assert sorted(archive.namelist()) == sorted(members)
        for name, expected in members.items():
            hasher, size = hashlib.sha256(), 0
            with archive.open(name) as stream:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    size += len(chunk)
            assert hasher.hexdigest() == expected['sha256'] and size == expected['bytes']
    all_files = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]
    for p in pending['files'] + original['preserved_files']:
        validate(p)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    final = {'version': 'hilbert-primitive-aggregate-static-export-v1',
             'status': 'immutable_finite_static_source_aggregate_audit_and_compact_view_complete',
             'files': all_files, 'file_count': len(all_files), 'total_bytes': sum(p['bytes'] for p in all_files),
             'archive_pin': pin(archive_path), 'archive_member_count': len(members),
             'archive_contents_pin': pin(archive_contents),
             'producer_checkpoint_pin': pin(HERE / 'production-checkpoint-v2.json'),
             'independent_integration_pin': pin(external_manifest),
             'independent_audit_pin': pin(EXTERNAL / 'audit-full-v2.json'),
             'independent_lifetime_pin': pin(EXTERNAL / 'audit-lifetime-v2.json'),
             'independent_parser_scope_pin': pin(EXTERNAL / 'parser-scope-v2.json'),
             'independent_completion_pin': pin(EXTERNAL / 'completion-receipt-v2.json'),
             'reader_data_pin': pin(HERE / 'reader-data-v2.json'),
             'reader_projection_receipt_pin': pin(HERE / 'reader-extraction-receipt-v2.json'),
             'reader_lifetime_pin': pin(HERE / 'reader-extraction-lifetime-v2.json'),
             'prior_preserved_entries_checked': len(original['preserved_files']),
             'pending_snapshot_files_preserved': len(pending['files']),
             'counts': audit['counts'],
             'scope': 'Finite checked 171 source-body expansions, primitive logical leaves, ordered aliases and exact canonical t/m aggregates; authored shared 24-row example; parametric 24/65 row grammar census. Compact reader is a read-only projection bound to the exact independently audited data.',
             'authority': 'Inactive finite source/aggregate evidence only; neither mapped nor primitive interfaces are labeled freshly native-admitted. No existing engine adapter activated.',
             'failures_preserved': {'producer_v1': 'UNKNOWN: actual child kernel peak 557432832 bytes exceeds 512 MiB; preserved even though serialization repair has identical scientific bytes.',
                                    'reader_v1': 'UNKNOWN: standard whole-payload parsing exceeded separate host ceiling; child killed/reaped before output. Versioned reader streams one record at a time.'},
             'costs': {'cumulative_production_outer_seconds': production['cumulative_production_seconds'],
                       'production_v2_outer_seconds': production['full_outer_seconds_before_this_receipt_write'],
                       'production_v2_conservative_host_peak_bytes': production['deliberately_conservative_all_host_peak_sum_bytes'],
                       'independent_full_audit_lifetime_seconds': audit_lifetime['full_lifetime_seconds_before_final_receipt_write'],
                       'independent_control_cost_details': completion['control_accounting'],
                       'cumulative_reader_preparation_seconds': extraction['cumulative_reader_preparation_seconds'],
                       'reader_v2_host_peak_bytes': extraction['host_kernel_peak_sum_bytes'],
                       'initial_hash_and_syntax_preparation': original['preparation_cost'],
                       'pending_export_prewrite_seconds': pending['export_prewrite_seconds'],
                       'final_export_prewrite_seconds': time.perf_counter() - started, 'final_export_peak_bytes': peak,
                       'prior_admission_provenance': 'Retained exact donor native and full replay receipts; this phase incurs zero new native queries and does not erase earlier preparation costs.'},
             'remaining_obligations': ['complete primitive placement catalog and candidate/frontier graph',
                                        'cluster proposal embedding domain and validation',
                                        'reference scheduler, propagation, exact rollback and complete primitive fallback implementation',
                                        'conditional 65-row one-way padding lift',
                                        'formal compiler/native correspondence and any fresh whole proof request'],
             'parser_scope': 'Read-only decoder used on exact pinned known-standard JSON. Its delimiter loops accept trailing commas; no general adversarial strict-parser theorem is claimed.',
             'native_queries': 0, 'target_searches': 0, 'placement_graphs': 0,
             'new_RL_training': False, 'new_discovered_chained_proof': False,
             'engine_or_authority_activation': False, 'HTML_or_publication': 'none; root owns integration'}
    save(manifest_path, final)
    print(json.dumps({'manifest_pin': pin(manifest_path), 'files': len(all_files),
                      'archive_members': len(members), 'bytes': final['total_bytes'],
                      'export_prewrite_seconds': final['costs']['final_export_prewrite_seconds']}))


if __name__ == '__main__':
    main()
