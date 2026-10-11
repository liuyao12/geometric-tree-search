"""Independent exact renaming/capacity replay, with explicit wire-order recovery."""
import copy
import gzip
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
import audit_tree_kernel as T
from audit_semantic_proofs import whole_replay
from audit_certificate_boundary import initial_for, pin
from audit_proof_boundary import expected_constructor, PINNED_MICRO, PINNED_PROGRAM

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011/short-identifiers'
DOC = ROOT / 'docs/research/gcts-rl-renewal'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def need(value, message):
    if not value:
        raise ValueError(message)


def relation(old, new, aliases):
    need(len(old['blocks']) == len(new['blocks']) == len(aliases), 'complete declaration map')
    names = dict((entry['old'], entry['new']) for entry in aliases)
    need(len(names) == len(set(names.values())) == len(aliases), 'bijective declaration identities')
    need([entry['old'] for entry in aliases] == [b['name'] for b in old['blocks']], 'declaration order')
    need([entry['new'] for entry in aliases] == ['b' + str(i) for i in range(len(aliases))], 'predeclared short names')
    for block, recipient in zip(old['blocks'], new['blocks']):
        need(recipient['name'] == names[block['name']], 'declared fresh name')
        need(set(block) == set(recipient) and all(block[k] == recipient[k] for k in block if k not in ('name', 'proof')),
             'full unchanged block interface and local context')
    original_lists = [b['proof'] for b in old['blocks']] + [old['proof']]
    new_lists = [b['proof'] for b in new['blocks']] + [new['proof']]
    for original, recipient in zip(original_lists, new_lists):
        need(len(original) == len(recipient), 'all commands retained')
        for command, transformed in zip(original, recipient):
            expected = copy.deepcopy(command)
            if command['rule'] == 'block':
                need(command['name'] in names, 'every original referenced declaration')
                expected['name'] = names[command['name']]
            need(expected == transformed, 'only block-reference names may change')
    need(set(old) == set(new) and all(old[k] == new[k] for k in old if k not in ('blocks', 'proof')),
         'all non-certificate problem fields unchanged')


def alarm(*args):
    raise TimeoutError('unknown_short_identifier_audit_wall_budget')


def main():
    began = time.perf_counter()
    plan = json.loads((OUT / 'audit-plan.json').read_text())
    result = dict(status='checking_short_identifier_capacity', native_queries=0)
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, plan['ceilings']['phase_seconds'])
    try:
        for path, expected in {**plan['source_sha256'], **plan['input_sha256']}.items():
            need(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
                 'short identifier audit frozen binding ' + path)
        frozen = json.loads((OUT / 'plan.json').read_text())
        old = load(ROOT / frozen['candidate_artifact'])['candidates'][0]['original_request']
        obs = load(OUT / 'observation.json.gz')
        relation(old, obs['request'], obs['aliases'])
        need(whole_replay(old)['status'] == whole_replay(obs['request'])['status'] == 'accepted',
             'complete independent original and renamed derivations')
        corruptions = []
        for case in ('lost-premise', 'changed-formula', 'stale-reference', 'duplicate-identity'):
            wrong = copy.deepcopy(obs['request'])
            if case == 'lost-premise':
                next(b for b in wrong['blocks'] if b['premises'])['premises'].pop()
            elif case == 'changed-formula':
                wrong['proof'][-1]['formula'] = ['bot']
            elif case == 'stale-reference':
                next(c for c in wrong['proof'] if c['rule'] == 'block')['name'] = old['blocks'][0]['name']
            else:
                wrong['blocks'][1]['name'] = wrong['blocks'][0]['name']
            try:
                relation(old, wrong, obs['aliases'])
            except ValueError:
                corruptions.append(case)
            else:
                raise ValueError('renaming corruption accepted ' + case)
        micro = load(DOC / 'proof-boundary-microcode-001.json.gz')
        boundary = json.loads((DOC / 'proof-boundary-001.json').read_text())
        need(pin(micro) == PINNED_MICRO and pin(boundary['program']) == PINNED_PROGRAM,
             'fixed parser checker and computational palette')
        # The postfix encoder preserves nested object field order, whereas
        # the saved canonical JSON observation does not. Recover the actual
        # input order from the independently bound original artifact, then
        # apply the checked name bijection in place. Do not infer wire order
        # from canonical request hashes.
        ordered = copy.deepcopy(old)
        names = {a['old']: a['new'] for a in obs['aliases']}
        for block in ordered['blocks']:
            block['name'] = names[block['name']]
        for proof in [b['proof'] for b in ordered['blocks']] + [ordered['proof']]:
            for command in proof:
                if command['rule'] == 'block':
                    command['name'] = names[command['name']]
        need(ordered == obs['request'], 'same renamed AST with recovered exact field order')
        initial = initial_for(micro, boundary['cases'][0]['initial'], ordered)
        nodes, root = expected_constructor(micro, initial, ordered)
        need(initial == obs['original_initial'] and nodes == obs['constructor_nodes'] and root == obs['constructor_root'],
             'every exact syntax and constructor datum')
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
        need(len(retained) == 1 and [list(p) for p in retained[0]] == obs['final_tree_nodes'], 'all final heap pairs')
        need(replay == {k: v for k, v in obs['tree_result'].items() if k != 'seconds'}, 'every tree instruction and profile')
        required = 2
        for i, (a, b) in enumerate(retained[0], 257):
            required += len(bin(i)[2:]) + len(bin(a)[2:]) + len(bin(b)[2:]) + 3
        need(required == obs['required_heap_capacity'] and obs['request_sha256'] == pin(obs['request']),
             'complete width and canonical request binding')
        need(obs['native_queries'] == obs['native_input_encodings'] == 0, 'no native admission from preflight')
        result.update(status='passed_full_bijective_renaming_and_capacity_replay', request_sha256=pin(obs['request']),
                      required_heap_capacity=required, fixed_native_heap_cells=frozen['fixed_native_heap_cells'],
                      capacity_fits=required <= frozen['fixed_native_heap_cells'], tree_status=replay['status'],
                      tree_value=replay.get('value'), tree_steps=replay['steps'],
                      exact_bijection_and_all_commands_checked=True, corruptions_rejected=corruptions,
                      full_instruction_and_heap_replay=True)
    except (ValueError, MemoryError, TimeoutError) as exc:
        result.update(status=str(exc), failure_type=type(exc).__name__)
    finally:
        result.update(seconds=time.perf_counter() - began,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      enforcement='SIGALRM wall interruption and final kernel peak RSS; no OS hard memory limit claimed',
                      scope='Finite exact renaming and tree capacity replay only; zero native queries or native input encodings. Formal compiler/Wang correctness and native acceptance remain open.')
        result['wall_overshoot_seconds'] = max(0, result['seconds'] - plan['ceilings']['phase_seconds'])
        result['memory_overshoot_bytes'] = max(0, result['peak_rss_bytes'] - plan['ceilings']['rss_bytes'])
        if result['wall_overshoot_seconds'] or result['memory_overshoot_bytes']:
            result['status'] = 'unknown_short_identifier_audit_resource_budget'
        (OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
