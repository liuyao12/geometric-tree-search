"""Independent finite compaction and every tree instruction/heap-pair replay.

No producer, compactor, tree_machine or search imports. Existing independent
transformation reconstruction checks all original and transformed contexts.
No native admission is granted by this audit.
"""
import gc
import gzip
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
import audit_tree_kernel as T
from audit_proof_compaction import audit_pair, pin as problem_pin
from audit_certificate_boundary import initial_for, pin
from audit_proof_boundary import expected_constructor, PINNED_MICRO, PINNED_PROGRAM

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011/representation'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def need(value, message):
    if not value:
        raise ValueError(message)


def alarm(*args):
    raise TimeoutError('unknown_representation_audit_wall_budget')


def main():
    began = time.perf_counter()
    plan = json.loads((OUT / 'audit-plan.json').read_text())
    result = dict(status='checking_full_representation', observations=[], native_queries=0)
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, plan['ceilings']['phase_seconds'])
    try:
        for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
            need(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
                 'independent representation frozen binding ' + path)
        frozen = json.loads((OUT / 'plan.json').read_text())
        candidate = load(ROOT / frozen['candidate_artifact'])['candidates'][0]
        original = candidate['original_request']
        transformed = load(OUT / 'transformation.json.gz')
        result['full_compaction_audit'] = audit_pair(original, transformed, problem_pin(original))
        need(pin(original) == frozen['original_request_sha256'], 'exact searched original')
        micro = load(DOC / 'proof-boundary-microcode-001.json.gz')
        boundary = json.loads((DOC / 'proof-boundary-001.json').read_text())
        need(pin(micro) == PINNED_MICRO and pin(boundary['program']) == PINNED_PROGRAM,
             'fixed parser checker and computational palette')
        T.static_program(boundary['program'])
        for index, (name, request) in enumerate((('original-hierarchy', original),
                                               ('context-dag-hierarchy', transformed['request']))):
            start = time.perf_counter()
            obs = load(OUT / ('observation-%02d.json.gz' % index))
            need(obs['name'] == name and obs['request'] == request and obs['request_sha256'] == pin(request),
                 'each exact representation request')
            initial = initial_for(micro, boundary['cases'][0]['initial'], request)
            nodes, root = expected_constructor(micro, initial, request)
            need(obs['original_initial'] == initial and obs['constructor_nodes'] == nodes and
                 obs['constructor_root'] == root, 'every parser constructor datum')
            retained, validate = [], T.validate_heap

            def retain(values):
                validate(values)
                retained.append(values)

            T.validate_heap = retain
            try:
                replay = T.replay(boundary['program'], dict(nodes=nodes, node=root),
                                  frozen['ceilings']['tree_steps'], frozen['ceilings']['host_tree_nodes'], keep=0)
            finally:
                T.validate_heap = validate
            need(len(retained) == 1, 'one complete final independent heap')
            need(replay == {k: v for k, v in obs['tree_result'].items() if k != 'seconds'},
                 'every instruction event and profile')
            need([list(p) for p in retained[0]] == obs['final_tree_nodes'], 'every final heap pair')
            width = 2
            for index2, pair in enumerate(retained[0], 257):
                width += len(bin(index2)[2:]) + len(bin(pair[0])[2:]) + len(bin(pair[1])[2:]) + 3
            need(width == obs['required_heap_capacity'], 'independent complete canonical heap width')
            need(request['theory'] == original['theory'] and request['target'] == original['target'],
                 'unchanged theory and target')
            need(obs['native_queries'] == obs['native_input_encodings'] == 0,
                 'capacity only, no native assertion')
            result['observations'].append(dict(name=name, request_sha256=pin(request),
                                              tree_status=replay['status'], tree_value=replay.get('value'),
                                              tree_steps=replay['steps'], required_heap_capacity=width,
                                              fixed_native_heap_cells=frozen['fixed_native_heap_cells'],
                                              capacity_fits=width <= frozen['fixed_native_heap_cells'],
                                              full_instruction_and_heap_replay=True,
                                              seconds=time.perf_counter() - start))
            print(json.dumps(result['observations'][-1]), flush=True)
            del obs, initial, nodes, retained
            gc.collect()
        result['status'] = 'passed_full_context_compaction_and_both_capacity_replays'
    except (ValueError, MemoryError, TimeoutError) as exc:
        result.update(status=str(exc), failure_type=type(exc).__name__)
    finally:
        result.update(seconds=time.perf_counter() - began,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      enforcement='SIGALRM wall interruption and final kernel peak RSS; no OS memory hard limit claimed',
                      scope='Complete finite transformation and both exact tree/heap replays only; native acceptance, input byte encoding and a formal compiler/Wang correspondence are not established.')
        result['wall_overshoot_seconds'] = max(0, result['seconds'] - plan['ceilings']['phase_seconds'])
        result['memory_overshoot_bytes'] = max(0, result['peak_rss_bytes'] - plan['ceilings']['rss_bytes'])
        if result['wall_overshoot_seconds'] or result['memory_overshoot_bytes']:
            result['status'] = 'unknown_representation_audit_resource_budget'
        (OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps({k: result[k] for k in ('status', 'seconds', 'peak_rss_bytes')}), flush=True)


if __name__ == '__main__':
    main()
