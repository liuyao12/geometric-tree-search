"""A separately declared movable blank boundary; native input preparation only.

The fixed262144-cell unknown remains unchanged. This phase declares the least
4096-cell multiple covering the complete audited requirement plus64 spare cells.
It prepares and independently byte-checks an input, but executes no native query.
"""
import copy
import gzip
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path
from certificate_block_identifiers import shorten
from short_identifier_capacity_audit_v2 import relation
from audit_certificate_boundary import initial_for, pin
from audit_proof_boundary import PINNED_MICRO, PINNED_PROGRAM
from commutativity_capacity_stream import write_stream, layout
from commutativity_capacity_stream_audit import encode, layout as independent_layout

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011/movable-encoding'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def need(value, message):
    if not value:
        raise ValueError(message)


def alarm(*args):
    raise TimeoutError('unknown_movable_encoding_wall_budget')


def main():
    mode = sys.argv[1]
    need(mode in ('prepare', 'audit'), 'declared encoding stage')
    start = time.perf_counter()
    plan = json.loads((OUT / ('plan.json' if mode == 'prepare' else 'audit-plan.json')).read_text())
    result = dict(status='running_movable_encoding_' + mode, native_queries=0, target_searches=0)
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, plan['ceilings']['phase_seconds'])
    try:
        for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
            need(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
                 'movable encoding frozen binding ' + path)
        declaration = plan if mode == 'prepare' else json.loads((OUT / 'plan.json').read_text())
        previous = json.loads((ROOT / declaration['capacity_audit']).read_text())
        need(previous['status'] == 'passed_full_bijective_renaming_and_capacity_replay' and
             previous['tree_status'] == 'accepted' and previous['tree_value'] == 1,
             'complete independently accepted capacity estimate')
        need(previous['required_heap_capacity'] == 263826 and not previous['capacity_fits'],
             'fixed boundary unknown preserved')
        original = load(ROOT / declaration['candidate_artifact'])['candidates'][0]['original_request']
        if mode == 'prepare':
            request, aliases = shorten(original)
        else:
            obs = load(ROOT / declaration['renaming_observation'])
            aliases = obs['aliases']
            request = copy.deepcopy(original)
            names = {entry['old']: entry['new'] for entry in aliases}
            for block in request['blocks']:
                block['name'] = names[block['name']]
            for proof in [b['proof'] for b in request['blocks']] + [request['proof']]:
                for command in proof:
                    if command['rule'] == 'block':
                        command['name'] = names[command['name']]
            relation(original, request, aliases)
            need(request == obs['request'], 'whole ordered renamed request')
        micro = load(DOC / 'proof-boundary-microcode-001.json.gz')
        boundary = json.loads((DOC / 'proof-boundary-001.json').read_text())
        need(pin(micro) == PINNED_MICRO and pin(boundary['program']) == PINNED_PROGRAM,
             'unchanged parser checker and computational palette')
        initial = initial_for(micro, boundary['cases'][0]['initial'], request)
        old = copy.deepcopy(initial)
        old['capacities'][micro['heap']] = declaration['old_heap_cells']
        cells = ((previous['required_heap_capacity'] + 64 + 4095) // 4096) * 4096
        need(cells == declaration['new_heap_cells'] == 266240, 'prospective boundary selection rule')
        initial['capacities'][micro['heap']] = cells
        if mode == 'prepare':
            byte_record = write_stream(initial, micro['raw'], OUT / 'input.bin.gz')
            frame = dict(request_sha256=pin(request), original_initial=old, proposed_initial=initial,
                         aliases=aliases, original_layout=layout(old), proposed_layout=layout(initial),
                         native_start_state=micro['start'], physical_origin=0, heap_band=micro['heap'],
                         required_heap_cells=previous['required_heap_capacity'], old_heap_cells=262144,
                         new_heap_cells=cells, **byte_record)
            (OUT / 'frame.json.gz').write_bytes(gzip.compress(json.dumps(frame, separators=(',', ':')).encode(), mtime=0))
            result.update(status='complete_movable_encoding_pending_independent_byte_audit', **byte_record,
                          request_sha256=pin(request), new_heap_cells=cells)
        else:
            frame = load(OUT / 'frame.json.gz')
            need(frame['proposed_initial'] == initial and frame['original_initial'] == old,
                 'every initial word head and declared capacity')
            need(frame['original_layout'] == independent_layout(old) and
                 frame['proposed_layout'] == independent_layout(initial), 'every physical band coordinate')
            need(frame['native_start_state'] == micro['start'] == 88986 and frame['physical_origin'] == 0,
                 'true parser start and physical origin')
            raw = encode(initial, micro['raw'])
            need(raw == gzip.decompress((OUT / 'input.bin.gz').read_bytes()) and
                 hashlib.sha256(raw).hexdigest() == frame['input_sha256'] and len(raw) == frame['input_bytes'],
                 'every independently encoded native input byte')
            result.update(status='passed_complete_movable_encoding_byte_audit', request_sha256=pin(request),
                          input_sha256=frame['input_sha256'], input_bytes=len(raw), new_heap_cells=cells,
                          all_words_heads_capacities_bands_origin_start_and_bytes_matched=True)
    except (ValueError, MemoryError, TimeoutError) as exc:
        result.update(status=str(exc), failure_type=type(exc).__name__)
    finally:
        result.update(seconds=time.perf_counter() - start,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      enforcement='SIGALRM wall interruption plus final kernel peak RSS; no OS hard memory limit claimed',
                      scope='Explicitly moved external blank heap only; fixed262144cell unknown remains. Zero native queries or proof search. An input preparation/audit result does not establish native acceptance.')
        result['wall_overshoot_seconds'] = max(0, result['seconds'] - plan['ceilings']['phase_seconds'])
        result['memory_overshoot_bytes'] = max(0, result['peak_rss_bytes'] - plan['ceilings']['rss_bytes'])
        if result['wall_overshoot_seconds'] or result['memory_overshoot_bytes']:
            result['status'] = 'unknown_movable_encoding_resource_budget'
        (OUT / ('summary.json' if mode == 'prepare' else 'audit.json')).write_text(json.dumps(result, indent=2) + '\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
