"""Post-search representation study; no proof search or native execution.

Preserve the exact ordinary-control candidate's theory, target and block
interfaces. Compare its original checked hierarchy with the existing generic
context-local DAG compactor. The old flattened certificate is not altered.
"""
import copy
import gc
import gzip
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from proof_compaction import compact
from serialized_kernel import canonical, problem_hash
from tree_machine import Heap, run
from audit_certificate_boundary import initial_for, pin
from audit_proof_boundary import expected_constructor, PINNED_MICRO, PINNED_PROGRAM

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011/representation'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def save(path, value):
    path.write_bytes(gzip.compress(canonical(value), mtime=0))


def alarm(*args):
    raise TimeoutError('unknown_representation_phase_wall_budget')


def main():
    start = time.perf_counter()
    plan = json.loads((OUT / 'plan.json').read_text())
    summary = dict(status='running_post_search_representation', observations=[],
                   native_queries=0, target_searches=0)
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, plan['ceilings']['phase_seconds'])
    try:
        for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
                raise ValueError('representation frozen binding ' + path)
        old = load(ROOT / plan['candidate_artifact'])['candidates']
        if len(old) != 1 or old[0]['lane'] != 'ordinary-forward':
            raise ValueError('one independently audited automatic ordinary candidate')
        original = old[0]['original_request']
        if pin(original) != plan['original_request_sha256']:
            raise ValueError('unchanged ordinary candidate')
        transformed = compact(canonical(original), problem_hash(original))
        if transformed['status'] != 'accepted_compaction':
            raise ValueError('original and transformed full host validation')
        save(OUT / 'transformation.json.gz', transformed)
        micro = load(DOC / 'proof-boundary-microcode-001.json.gz')
        boundary = json.loads((DOC / 'proof-boundary-001.json').read_text())
        if pin(micro) != PINNED_MICRO or pin(boundary['program']) != PINNED_PROGRAM:
            raise ValueError('unchanged parser checker and computational palette')
        for index, (name, request) in enumerate((('original-hierarchy', original),
                                               ('context-dag-hierarchy', transformed['request']))):
            began = time.perf_counter()
            initial = initial_for(micro, boundary['cases'][0]['initial'], request)
            nodes, root = expected_constructor(micro, initial, request)
            heap = Heap(nodes, limit=plan['ceilings']['host_tree_nodes'])
            result = run(boundary['program'], heap, root,
                         limit=plan['ceilings']['tree_steps'], keep=0)
            required = 2 + sum((i + 257).bit_length() + max(1, a.bit_length()) +
                               max(1, b.bit_length()) + 3
                               for i, (a, b) in enumerate(heap.nodes))
            accepted = result['status'] == 'accepted' and result.get('value') == 1
            status = ('tree_accepted_capacity_fits_pending_audit' if required <= plan['fixed_native_heap_cells']
                      else 'unknown_fixed_native_heap_boundary') if accepted else 'unknown_tree_budget_or_rejected'
            observation = dict(name=name, status=status, request=request, request_sha256=pin(request),
                               original_initial=initial, constructor_nodes=nodes, constructor_root=root,
                               tree_result=result, final_tree_nodes=heap.nodes,
                               required_heap_capacity=required, requirement_is_complete=accepted,
                               native_queries=0, native_input_encodings=0,
                               root_commands=len(request['proof']), blocks=len(request['blocks']),
                               stored_commands=len(request['proof']) + sum(len(b['proof']) for b in request['blocks']),
                               request_bytes=len(canonical(request)), seconds=time.perf_counter() - began)
            save(OUT / ('observation-%02d.json.gz' % index), observation)
            summary['observations'].append({k: v for k, v in observation.items()
                                            if k not in ('request', 'original_initial', 'constructor_nodes',
                                                         'final_tree_nodes', 'tree_result')})
            summary['observations'][-1]['tree_steps'] = result['steps']
            summary['observations'][-1]['tree_status'] = result['status']
            print(json.dumps(summary['observations'][-1]), flush=True)
            del initial, nodes, heap, result, observation
            gc.collect()
        summary['status'] = 'complete_representation_observations_pending_independent_audit'
    except (ValueError, MemoryError, TimeoutError) as exc:
        summary.update(status=str(exc), failure_type=type(exc).__name__)
    finally:
        summary.update(seconds=time.perf_counter() - start,
                       peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       enforcement='SIGALRM wall interruption and final kernel peak RSS; no OS memory hard limit claimed',
                       scope='Post-search certificate representation only. Exact existing ordinary candidate; unchanged theory, target, interfaces, parser, checker, palette and fixed native heap. No GCTS discovery, new theorem, native input encoding or native execution.')
        summary['wall_overshoot_seconds'] = max(0, summary['seconds'] - plan['ceilings']['phase_seconds'])
        summary['memory_overshoot_bytes'] = max(0, summary['peak_rss_bytes'] - plan['ceilings']['rss_bytes'])
        if summary['wall_overshoot_seconds'] or summary['memory_overshoot_bytes']:
            summary['status'] = 'unknown_representation_phase_resource_budget'
        (OUT / 'summary.json').write_bytes(canonical(summary))
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps({k: summary[k] for k in ('status', 'seconds', 'peak_rss_bytes')}), flush=True)


if __name__ == '__main__':
    main()
