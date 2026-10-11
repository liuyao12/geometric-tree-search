"""Frozen post-search block-identifier compression and capacity preflight."""
import gzip
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from certificate_block_identifiers import shorten
from serialized_kernel import canonical, check, problem_hash
from tree_machine import Heap, run
from audit_certificate_boundary import initial_for, pin
from audit_proof_boundary import expected_constructor, PINNED_MICRO, PINNED_PROGRAM

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011/short-identifiers'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def alarm(*args):
    raise TimeoutError('unknown_short_identifier_capacity_wall_budget')


def main():
    began = time.perf_counter()
    plan = json.loads((OUT / 'plan.json').read_text())
    summary = dict(status='running_short_identifier_capacity', native_queries=0, target_searches=0)
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, plan['ceilings']['phase_seconds'])
    try:
        for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
                raise ValueError('short identifier frozen binding ' + path)
        parent = ROOT / plan['parent_audit']
        if json.loads(parent.read_text())['status'] != 'passed_full_context_compaction_and_both_capacity_replays':
            raise ValueError('independently checked hierarchical parent')
        old = load(ROOT / plan['candidate_artifact'])['candidates'][0]['original_request']
        request, aliases = shorten(old)
        for variant in (old, request):
            if check(canonical(variant), expected_problem_sha256=problem_hash(old))['status'] != 'accepted':
                raise ValueError('whole original and renamed host checks')
        if request['theory'] != old['theory'] or request['target'] != old['target']:
            raise ValueError('unchanged exact problem')
        micro = load(DOC / 'proof-boundary-microcode-001.json.gz')
        boundary = json.loads((DOC / 'proof-boundary-001.json').read_text())
        if pin(micro) != PINNED_MICRO or pin(boundary['program']) != PINNED_PROGRAM:
            raise ValueError('unchanged parser checker palette')
        initial = initial_for(micro, boundary['cases'][0]['initial'], request)
        nodes, root = expected_constructor(micro, initial, request)
        heap = Heap(nodes, limit=plan['ceilings']['host_tree_nodes'])
        result = run(boundary['program'], heap, root, limit=plan['ceilings']['tree_steps'], keep=0)
        required = 2 + sum((i + 257).bit_length() + max(1, a.bit_length()) +
                           max(1, b.bit_length()) + 3 for i, (a, b) in enumerate(heap.nodes))
        accepted = result['status'] == 'accepted' and result.get('value') == 1
        status = ('tree_accepted_capacity_fits_pending_audit' if required <= plan['fixed_native_heap_cells']
                  else 'unknown_fixed_native_heap_boundary') if accepted else 'unknown_tree_budget_or_rejected'
        observation = dict(status=status, request=request, request_sha256=pin(request), aliases=aliases,
                           original_initial=initial, constructor_nodes=nodes, constructor_root=root,
                           tree_result=result, final_tree_nodes=heap.nodes,
                           required_heap_capacity=required, requirement_is_complete=accepted,
                           native_queries=0, native_input_encodings=0,
                           stored_commands=len(request['proof']) + sum(len(b['proof']) for b in request['blocks']),
                           request_bytes=len(canonical(request)))
        (OUT / 'observation.json.gz').write_bytes(gzip.compress(canonical(observation), mtime=0))
        summary.update({k: observation[k] for k in ('status', 'request_sha256', 'required_heap_capacity',
                                                   'requirement_is_complete', 'stored_commands', 'request_bytes')})
        summary.update(tree_steps=result['steps'], tree_status=result['status'])
    except (ValueError, MemoryError, TimeoutError) as exc:
        summary.update(status=str(exc), failure_type=type(exc).__name__)
    finally:
        summary.update(seconds=time.perf_counter() - began,
                       peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       enforcement='SIGALRM wall interruption and final kernel peak RSS; no OS hard memory limit claimed',
                       scope='Post-search bijective internal block renaming only. Original formulas, theory, target, command sequence, proof interfaces, parser, checker, palette and fixed native heap are unchanged. No proof discovery, input encoding or native execution.')
        summary['wall_overshoot_seconds'] = max(0, summary['seconds'] - plan['ceilings']['phase_seconds'])
        summary['memory_overshoot_bytes'] = max(0, summary['peak_rss_bytes'] - plan['ceilings']['rss_bytes'])
        if summary['wall_overshoot_seconds'] or summary['memory_overshoot_bytes']:
            summary['status'] = 'unknown_short_identifier_phase_resource_budget'
        (OUT / 'summary.json').write_bytes(canonical(summary))
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
