"""Read-only static source/pin disposition. Does not load scientific JSON traces."""
import ast
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/stochastic-replay-v5-independent-20261011'
PACKAGE = ROOT / '.gcts-active/stochastic-replay-memory-v5-20261011/review-package-v5.json'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def need(test, message):
    if not test:
        raise ValueError(message)


def main():
    began = time.perf_counter()
    package = json.loads(PACKAGE.read_bytes())
    receipt = {'status': 'source_review_in_progress', 'package_sha256': digest(PACKAGE)}
    for kind in ('sources', 'inputs'):
        for path, expected in package[kind].items():
            need(digest(ROOT / path) == expected, 'exact frozen pin ' + path)
            if kind == 'sources' and path.endswith('.py'):
                ast.parse((ROOT / path).read_bytes(), filename=path)
    for entry in package['files']:
        need(digest(ROOT / entry['path']) == entry['sha256'], 'package file SHA')
        need((ROOT / entry['path']).stat().st_size == entry['bytes'], 'package file bytes')
    snapshot = next(e for e in package['files'] if e['path'].endswith('.zip'))
    with zipfile.ZipFile(ROOT / snapshot['path']) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)), 'no duplicate ZIP entry')
        for path, expected in package['sources'].items():
            need(hashlib.sha256(archive.read(path)).hexdigest() == expected, 'exact ZIP source ' + path)

    old_worker = (ROOT / 'research/gcts-rl-renewal/arithmetic_stochastic_worker_replay_memory_v2.py').read_text()
    new_worker = (ROOT / 'research/gcts-rl-renewal/arithmetic_stochastic_worker_replay_memory_v5.py').read_text()
    normalized = new_worker.replace(
        'from arithmetic_stochastic_replay_memory_v5 import load, load_trace, statistics, exact_compact_bytes',
        'from arithmetic_stochastic_replay_memory_v2 import load, statistics, exact_compact_bytes').replace(
        'raw = load_trace(ROOT / plan[\'trace_path\'])', 'raw = load(ROOT / plan[\'trace_path\'])')
    need(normalized == old_worker, 'only loader import and saved-trace call changed')
    helper = json.loads((ROOT / package['helper_plan']['path']).read_bytes())
    evaluation = json.loads((ROOT / package['evaluation_plan']['path']).read_bytes())
    need(digest(ROOT / package['helper_plan']['path']) == package['helper_plan']['sha256'], 'helper plan SHA')
    need(digest(ROOT / package['evaluation_plan']['path']) == package['evaluation_plan']['sha256'], 'evaluation plan SHA')
    need(helper['seconds'] == 180 and helper['rss_bytes'] == 536870912, 'helper owner bounds')
    need(evaluation['seconds'] == 553.33934725 and evaluation['rss_bytes'] == 536870912, 'actual owner remaining bounds')
    need(evaluation['historical_failed_audit_seconds'] == 226.66065275, 'all historical charges preserved')
    need(package['original_audit_seconds'] == 780 and package['remaining_seconds_before_helpers'] == 553.33934725,
         'original cumulative accounting')
    need([j['job'] for j in evaluation['jobs']] ==
         ['base-r1', 'untrained-r1', 'trained-r1', 'trained-r2', 'untrained-r2', 'base-r2'],
         'unchanged balanced six-observation order')
    need(len(helper['jobs']) == 7 and len(helper['correspondence_pairs']) == 3, 'full helper schedule')
    need(helper['requires_root_activation'] is True and evaluation['requires_root_activation'] is True,
         'root activation workflow')
    job_comparisons = []
    for job in evaluation['jobs']:
        path = ROOT / job['plan_path']
        need(digest(path) == job['plan_sha256'], 'exact worker job SHA')
        current = json.loads(path.read_bytes())
        prior = json.loads((ROOT / ('.gcts-active/stochastic-replay-memory-20261011/evaluation-v2/' +
                                  job['job'] + '-plan.json')).read_bytes())
        drop = {'source_sha256', 'input_sha256', 'output_path', 'loading_only_repair'}
        need({k: v for k, v in current.items() if k not in drop} ==
             {k: v for k, v in prior.items() if k not in drop}, 'all original scientific job fields')
        need(current['seconds'] == 115 and current['rss_bytes'] == 536870912 and job['lifecycle_seconds'] == 120,
             'unchanged actual worker resource gates')
        for kind in ('source_sha256', 'input_sha256'):
            for p, h in current[kind].items():
                need(digest(ROOT / p) == h, 'actual job closure pin ' + p)
        job_comparisons.append({'job': job['job'], 'plan_sha256': job['plan_sha256'],
                                'scientific_fields_identical_to_v2': True,
                                'descriptive_loading_only_field': current['loading_only_repair']})
    for job in helper['jobs']:
        path = ROOT / job['plan_path']
        need(digest(path) == job['plan_sha256'], 'helper job SHA')
        spec = json.loads(path.read_bytes())
        need(spec['seconds'] == 25 and spec['rss_bytes'] == 536870912 and job['lifecycle_seconds'] == 30,
             'unchanged helper worker gates')
    old_phase_charges = sum(e['seconds'] for e in package['prior_inclusive_phases_preserved'])
    need(abs(old_phase_charges - 226.66065275) < 1e-9, 'inclusive historical phase sum')
    receipt.update(
        status='passed_source_ready_v5_scoped_read_only_alias_and_pin_review',
        verified_sources=len(package['sources']), verified_inputs=len(package['inputs']),
        verified_package_files=len(package['files']), verified_zip_sources=len(package['sources']),
        exact_worker_diff='Only V5 loader import and raw=load_trace(saved observation); all other worker text identical to V2.',
        complete_original_byte_gate_sha256='e7a3ebac55a2d6c1a8fb367711b8e9a98497df66b84a6f74d78a85a6761655b5',
        job_comparisons=job_comparisons,
        independent_dataflow_disposition=[
            'load_trace is used only for raw saved observation. Separate model/catalog/registry/plan/lifetime/transition/policy loads use unchanged V1/V2 load.',
            'Shared integer pairs remain plain lists; float/bool/mixed pairs remain ordinary arrays. Four-integer tuple sharing is historical.',
            'Worker passes raw.case/raw.search only into pinned read-only semantic consumers; mutations target fresh state/proposals/features/decoded model proof or result receipt.',
            'tree uses saved census/children/events/hints in comparison, indexing, iteration, hashing and scalar numerical decisions. Its active hint comes from fresh independent proposals.',
            'model_binding reads case and constructs new model placements/domains. Its assignments do not mutate case arrays.',
            'learning_update reads saved weights/features/metrics and constructs new gradient/update dictionaries. No saved pair mutation or pair-identity observation exists in reviewed closure.',
            'Unchanged C-json byte serializer reads full field values and insertion order, emitting every original byte before semantic replay.',
            'Plain-list sharing is observably different under mutation or identity-sensitive consumers; prospective negative controls expose this limitation. It is not general JSON alias equivalence.',
        ],
        scope_caveats=[
            'Disposition permits root to launch only the bounded helper phase; actual six replay requires fresh passed helper and root terminal activation.',
            'Complete byte equality is necessary but does not alone prove alias safety; manual pinned call-graph read-only argument is the additional condition.',
            'No claim that integer pairs are coordinates; sharing is generic trace-value reuse.',
            'No loader, synthetic helper, actual scientific JSON payload, graph, RNG or policy replay executed by this review.',
            'Resource success and all-six completion remain unknown. Six worst-case 120-second lifecycles do not fit current remainder; owner reserves full next lifecycle.',
            'Owned memory gate is retrospective fresh-worker plus owner kernel peaks, not a hard OS/RSS ceiling.',
            'Direct worker CLI is technically callable; root activation is the controlled owner workflow, not a security boundary.',
            'Old failures remain unchanged and helper lifetime will be charged once under original 780 seconds.',
        ],
        source_review_clock_seconds_before_receipt_write=time.perf_counter()-began,
        authoring_and_manual_inspection_seconds='uninstrumented; not included in static verifier clock',
        scientific_payload_loads=0, fixture_executions=0, graph_replays=0,
        searches=0, training_episodes=0, native_queries=0)
    target = OUT / 'source-ready-review-v5.json'
    with target.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'receipt_sha256': digest(target),
                      'sources': receipt['verified_sources'], 'inputs': receipt['verified_inputs'],
                      'package_files': receipt['verified_package_files']}))


if __name__ == '__main__':
    main()
