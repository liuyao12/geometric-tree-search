"""ROOT activation required. Preparation only; no search/checker/native calls."""
import gzip
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path
import family_proposal_v2 as proposals

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def verify(plan):
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / p['path']) != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen family prerequisite changed: ' + p['path'])


def load_lifecycle(path):
    spec = importlib.util.spec_from_file_location('frozen_family_preparation_lifecycle_v2', path)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def save(name, data, compressed=False):
    path = HERE / name
    if compressed:
        with path.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            for part in json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(',', ':')).iterencode(data):
                zipped.write(part.encode('utf-8'))
            zipped.write(b'\n')
    else:
        with path.open('x') as stream: json.dump(data, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('worker full lifetime alarm')))
    signal.alarm(60)
    planpath = HERE / 'preparation-plan-v2.json'; plan = json.loads(planpath.read_text())
    activation = json.loads((HERE / 'root-preparation-activation-v2.json').read_text())
    if (activation['status'] != 'root_authorized_bounded_family_proposal_preparation_only'
            or activation['plan'] != pin(planpath)):
        raise ValueError('exact ROOT preparation-only activation required')
    verify(plan); verified_seconds = time.perf_counter() - started
    roles = {p['role']: ROOT / p['path'] for p in plan['inputs']}
    counters, groups, authority, anchors, records = {}, [], None, (), ()
    setup_timings = {}
    preparation_started = time.perf_counter(); deadline = preparation_started + 30
    status, reason = 'complete_declared_proposal_grammar_prepared_pending_independent_audit', None
    try:
        setup_start = time.perf_counter()
        life = load_lifecycle(roles['lifecycle_kernel']); core = life.core
        graph = core.frozen_model(ROOT, json.loads(roles['original_point_model_plan'].read_text()))
        setup_timings['lifecycle_import_and_full_point_model_seconds'] = time.perf_counter() - setup_start
        if (graph.model_epoch != plan['unchanged_model_epoch'] or graph.height != 24
                or len(graph.recipes) != 229 or len(graph.formulas) != 217):
            raise ValueError('full original finite primitive model required')
        original_plan = json.loads(roles['original_56_input_body_plan'].read_text())
        if len(original_plan['inputs']) != 56 or len({p['path'] for p in original_plan['inputs']}) != 56:
            raise ValueError('accepted original 56 unique body inputs required')
        setup_start = time.perf_counter()
        original = life.frozen_family_authority(graph, original_plan)
        setup_timings['original_171_body_authority_seconds'] = time.perf_counter() - setup_start
        if len(original.bodies) != 171:
            raise ValueError('full original 171-body authority required')
        setup_start = time.perf_counter()
        projection = json.loads(roles['checked_compact_family_projection'].read_text())
        # Projection contains a decoded display example. Never offer/read its
        # rows as proposal keys or proof hints; discard the example immediately.
        projection.pop('example', None)
        setup_timings['compact_projection_decode_and_example_discard_seconds'] = time.perf_counter() - setup_start
        proposals.check_deadline(deadline)
        source_bindings = [pin(planpath)] + [{k: p[k] for k in ('path', 'sha256', 'bytes')} for p in plan['sources']]
        authority, groups, anchors, records = proposals.prepare(graph, original, projection, life,
                                                               source_bindings, deadline, counters)
        proposals.check_deadline(deadline)
    except proposals.PreparationLimit as exc:
        status, reason = 'unknown_preparation_budget', str(exc)
        # Never expose an undocumented partial pool as a completed registry.
        authority, groups, anchors, records = None, [], (), ()
    preparation_seconds = time.perf_counter() - preparation_started
    data = {'version': proposals.VERSION, 'status': status, 'reason': reason,
            'grammar': proposals.GRAMMAR, 'plan': pin(planpath), 'inputs': plan['inputs'], 'sources': plan['sources'],
            'unchanged_model_epoch': plan['unchanged_model_epoch'], 'counters': counters,
            'formula_registry_sha256': graph.registry_sha,
            'formula_codes': graph.formulas,
            'root_anchors': list(anchors), 'group_authority_epoch': authority.epoch if authority else None,
            'original_body_authority_epoch': authority.original.epoch if authority else None,
            'interface_summary': [{k: r[k] for k in ('name', 'body_sha256', 'full_projection_sha256', 'conclusion_row', 'conclusion_code')}
                                  | {'ordered_premise_codes': r['body']['premise_codes'],
                                     'canonical_input_rows': r['body']['canonical_input_rows'],
                                     'primitive_member_count': len(r['body']['primitive_members'])} for r in records],
            'groups': groups, 'preparation_seconds_including_model_and_body_setup': preparation_seconds,
            'setup_timings': setup_timings,
            'source_verification_seconds': verified_seconds, 'authored_words_used_as_hints': 0,
            'projection_example_decoded_then_discarded': True, 'new_RL_training': False,
            'target_searches': 0, 'logical_checker_runs': 0, 'point_certificates': 0, 'native_queries': 0,
            'native_accepted': False, 'native_authority_activated': False,
            'scope': 'complete frozen proposal grammar only if status is complete; no Controller/Executor call or theorem acceptance'}
    output = HERE / 'preparation-evidence-v2.json.gz'; save(output.name, data, compressed=True)
    verify(plan)
    elapsed = time.perf_counter() - started
    receipt = {'status': status, 'reason': reason, 'plan': pin(planpath), 'evidence': pin(output),
               'worker_seconds_before_receipt_write': elapsed, 'child_wall_ceiling_seconds': 60,
               'preparation_deadline_seconds': 30, 'preparation_seconds_including_model_and_body_setup': preparation_seconds,
               'source_verification_seconds': verified_seconds,
               'peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
               'complete_registered_groups': len(groups) if authority else None,
               'target_searches': 0, 'logical_checker_runs': 0, 'point_certificates': 0, 'native_queries': 0,
               'native_authority_activated': False, 'new_RL_training': False,
               'independent_pool_audit': 'pending separate source/actual gate', 'mathematical_acceptance': 'none'}
    save('preparation-outcome-v2.json', receipt)
    signal.alarm(0); print(json.dumps(receipt, allow_nan=False), flush=True)


if __name__ == '__main__': main()
