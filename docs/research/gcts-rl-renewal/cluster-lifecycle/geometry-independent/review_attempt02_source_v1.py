"""Metadata-only retry review. No engine import, fixture execution or model load."""
import ast
import difflib
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'
OUT = Path(__file__).resolve().parent


def pin(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return dict(path=str(path.relative_to(ROOT)), sha256=h.hexdigest(), bytes=path.stat().st_size)


def main():
    start = time.perf_counter()
    plan = json.loads((D / 'plan-attempt-02.json').read_bytes())
    original = json.loads((D / 'plan-v1.json').read_bytes())
    assert pin(D / 'plan-attempt-02.json')['sha256'] == 'bfb5fedc926c0bbccf45ffd1f9e13bb6a64f9cdbcfc511333554852542639abd'
    assert pin(D / 'plan-v1.json') == plan['original_plan_pin']
    seen = {}
    for section in ('sources', 'inputs', 'preserved_files', 'diffs'):
        for p in plan[section]:
            wanted = {k: p[k] for k in ('path', 'sha256', 'bytes')}
            actual = seen.get(p['path'])
            if actual is None:
                actual = pin(ROOT / p['path'])
                seen[p['path']] = actual
            assert actual == wanted, p['path']
            if section == 'sources':
                ast.parse((ROOT / p['path']).read_bytes())
    assert plan['sources'][0] == next(x for x in original['sources'] if x['path'] == plan['sources'][0]['path'])
    assert plan['producer_limits'] == dict(cumulative_outer_wall_seconds=60, child_alarm_seconds=50,
        supervisor_seconds=55, host_bytes=536870912, execution_authorized_by_this_freeze=False)
    assert plan['fixture_executions_at_freeze'] == plan['attempt02_fixture_executions_at_freeze'] == 0
    assert plan['actual_model_executions'] == plan['native_queries'] == plan['actual_geometry_target_searches'] == 0
    assert plan['new_RL_training'] is False
    # Recompute exact text diffs rather than trust exported difference descriptions.
    for kind in ('fixtures', 'run', 'outer'):
        old = f'hilbert_cluster_{kind}_v1.py'
        new = f'hilbert_cluster_{kind}_attempt02_v1.py'
        diff = ''.join(difflib.unified_diff((D / old).read_text().splitlines(True),
            (D / new).read_text().splitlines(True), fromfile=old, tofile=new))
        assert diff == (D / f'hilbert_cluster_{kind}_attempt02_v1-diff.txt').read_text()
    # Canonicalize only the explicit fixture metadata/output changes.
    fresh = (D / 'hilbert_cluster_fixtures_attempt02_v1.py').read_text()
    fresh = fresh.replace('import argparse\n', '').replace("EXPECTED_OUTPUT = HERE / 'attempt-02'\n", '')
    fresh = fresh.replace("str(Path(__file__).resolve().relative_to(life.ROOT))",
        "'.gcts-active/hilbert-cluster-lifecycle-20261011/hilbert_cluster_fixtures_v1.py'")
    fresh = fresh.replace("    parser=argparse.ArgumentParser()\n    parser.add_argument('--output-directory',required=True)\n    output=Path(parser.parse_args().output_directory).resolve()\n    if output!=EXPECTED_OUTPUT.resolve():raise ValueError('only isolated attempt-02 output allowed')\n", '')
    fresh = fresh.replace("path = output/'fixtures-outcome-v1.json'", "path = HERE/'fixtures-outcome-v1.json'")
    assert fresh == (D / 'hilbert_cluster_fixtures_v1.py').read_text()
    life = json.loads((D / 'fixtures-lifetime-v1.json').read_bytes())
    sup = json.loads((D / 'fixtures-supervision-v1.json').read_bytes())
    failure = plan['prior_failure']
    assert failure['seconds'] == life['full_supervisor_process_seconds_including_receipt_write']
    assert failure['conservative_host_peak_bytes'] == life['conservative_host_peak_bytes'] == 28327936
    assert sup['exit_code'] == failure['child_exit_code'] == -9
    assert sup['owned_child_terminal_wait_reaped'] is True
    assert sup['rss_samples'] == [] and 'PermissionError' in sup['watchdog_error']
    assert life['status'] == sup['status'] == 'unknown_or_failed'
    assert not (D / 'fixtures-outcome-v1.json').exists()
    outer = (D / 'hilbert_cluster_outer_attempt02_v1.py').read_text()
    assert 'wall+PRIOR_FAILED_SECONDS<=60' in outer and 'conservative<=536870912' in outer
    run = (D / 'hilbert_cluster_run_attempt02_v1.py').read_text()
    assert "'/bin/ps'" in run and 'child.kill()' in run and 'child.wait()' in run
    receipt = dict(status='passed_independent_metadata_only_tiny_retry_readiness',
        plan=pin(D / 'plan-attempt-02.json'), original_plan=pin(D / 'plan-v1.json'),
        source_entries=len(plan['sources']), input_entries=len(plan['inputs']),
        preserved_entries=len(plan['preserved_files']), unique_verified_paths=len(seen),
        sources=plan['sources'], diffs=plan['diffs'], previous_source_review=pin(OUT / 'tiny-source-review-v1.json'),
        prior_failure_lifetime=pin(D / 'fixtures-lifetime-v1.json'), prior_failure_supervision=pin(D / 'fixtures-supervision-v1.json'),
        conclusions=[
            'Logical lifecycle kernel byte-identical; every scientific fixture assertion byte-identical after exactly declared metadata/output transformations.',
            'Isolated attempt-02 output and runtime source pin identify the retry; no prior file is overwritten.',
            'Same fail-closed own-child ps/RSS/time watchdog, kill/wait/reap and final kernel peak rejection. Escalated dispatch changes metadata permission only.',
            'Prior 0.272813916-second infrastructure failure charged against original cumulative 60-second wall gate; same 50/55 seconds child/supervisor and 512 MiB cap.',
            'Prior child killed/reaped; no outcome or RSS sample. Prior unknown remains a preserved metadata failure, not logical acceptance or rejection.',
        ], caveats=[
            'Allows only root-owned bounded synthetic retry after root approval; no execution in this review.',
            'Independent actual lifecycle audit requires its own future frozen source/output gate and explicit root dispatch.',
            'No actual guarded-incidence model load, theorem search, native/compiler/authority activation or RL claim.',
            'Cross-process authoring timer remains invalid with explicit cost clarification; total owned duration charges work, saved separate controller scan/order/rollback metrics remain absent.',
            'Outer final receipt writing excluded from pre-write clock; actual resource qualification remains pending.',
        ], metadata_review_seconds_before_receipt_write=time.perf_counter()-start,
        manual_source_inspection_time='unmeasured', engine_imports=0, fixtures_executed=0,
        actual_models_loaded=0, searches=0, native_queries=0)
    target = OUT / 'tiny-attempt02-source-review-v1.json'
    with target.open('x') as f:
        json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps({'status':receipt['status'], 'receipt':pin(target)}))


if __name__ == '__main__':
    main()
