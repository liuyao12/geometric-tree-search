"""Immutable production-only snapshot; independent audit remains pending."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def main():
    started = time.perf_counter()
    target = HERE / 'export-pending-v1.json'
    if target.exists():
        raise ValueError('immutable pending export exists')
    plan = json.loads((HERE / 'plan-v1.json').read_text())
    for record in plan['preserved_files'] + plan['argument_source_closure']:
        assert pin(ROOT / record['path']) == record
    for record in plan['inputs'] + plan['sources']:
        assert pin(ROOT / record['path']) == {k: record[k] for k in ('path', 'sha256', 'bytes')}
    repair = json.loads((HERE / 'plan-v2.json').read_text())
    for record in repair['sources'] + repair['input_pins'] + repair['v1_evidence_pins']:
        assert pin(ROOT / record['path']) == record
    result = json.loads((HERE / 'outer-lifetime-v2.json').read_text())
    assert result['status'] == 'passed_outer_static_production_lifetime'
    files = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    value = {'version': 'hilbert-aggregate-production-only-export-v1',
             'status': 'immutable_static_production_snapshot_independent_audit_pending',
             'files': files, 'file_count': len(files), 'total_bytes': sum(x['bytes'] for x in files),
             'input_bindings': plan['inputs'], 'argument_source_closure': plan['argument_source_closure'],
             'preserved_file_entries_checked': len(plan['preserved_files']),
             'original_v1_resource_status': 'UNKNOWN: actual child peak 557432832 bytes exceeds 512 MiB',
             'v2_streamed_scientific_bytes': 'exact full-file and decompressed byte equality with v1',
             'cumulative_production_outer_seconds': result['cumulative_production_seconds'],
             'v2_outer_conservative_peak_bytes': result['deliberately_conservative_all_host_peak_sum_bytes'],
             'export_prewrite_seconds': time.perf_counter() - started, 'export_peak_bytes': peak,
             'independent_logical_point_audit': 'pending separate frozen external gate',
             'scope': 'All171 static expansions and exact canonical aggregates, authored24 example, and parametric24/65 primitive grammar census only. No complete placement graph, new discovered chained proof or activation.',
             'native_queries': 0, 'target_searches': 0, 'engine_or_authority_activation': False,
             'formal_compiler_native_correspondence': 'open', 'HTML_or_publication': 'none; root owns integration'}
    target.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'manifest_pin': pin(target), 'files': len(files), 'bytes': value['total_bytes'],
                      'export_prewrite_seconds': value['export_prewrite_seconds']}))


if __name__ == '__main__':
    main()
