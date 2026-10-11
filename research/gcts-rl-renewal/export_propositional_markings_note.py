"""Explain actual Notebook 62 point markings, without rerunning its experiment.

All displayed placements and words come from the recorded native-accepted donor.
The reference-choice inspector uses a disclosed legal two-row context, rather
than claiming that this context was a chronological node in the donor search.
"""
import gzip
import hashlib
import json
from pathlib import Path

from native_receptor_points import Model, canonical, center, port
from turtle import CAPACITY, Graph

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs/research/gcts-rl-renewal'


def read(name):
    raw = (DOCS / name).read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)


def sha(name):
    return hashlib.sha256((DOCS / name).read_bytes()).hexdigest()


def independent_word(formula):
    # Independently spell the wire encoding; the terminator is not a JSON byte.
    return list(json.dumps(formula, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')).encode('utf-8')) + [256]


def export():
    training = read('native-inventory-training-001.json.gz')
    reader = read('native-inventory-reader-001.json')
    donor = next(d for d in training['donors'] if d['case']['id'] == 'two-premise')
    proof = next(p for p in reader['proofs'] if p['case'] == 'two-premise')
    accepted = training['records'][donor['verification_query']]
    assert accepted['result']['status'] == 'accepted'
    assert canonical(accepted['request']) == canonical(proof['request'])
    assert accepted['request']['proof'] == donor['search']['proof']
    model = Model(donor['case'], donor['compiled'])
    recorded = {tuple(p['key']): p for p in donor['model']['placements']}
    assert set(recorded) == set(model.cache)
    for key, candidate in model.cache.items():
        assert candidate.marks == tuple((tuple(p), v) for p, v in recorded[key]['marks'])
        assert candidate.occupancy == tuple((tuple(p), v) for p, v in recorded[key]['occupancy'])
    selected = [tuple(k) for k in donor['search']['placements']]
    state = model.initial()
    for key in selected:
        assert state.legal(model.placement(key))
        state.place(model.placement(key))
    assert all(state.totals[p] == CAPACITY for p in state.roots)
    assert Graph(model, state).decision(state)[0] == 'empty'

    prefix = model.initial()
    for key in selected:
        if key[0] < 2:
            assert prefix.legal(model.placement(key))
            prefix.place(model.placement(key))
    alternatives = []
    for antecedent in range(2):
        for implication in range(2):
            command = dict(rule='mp', formula=donor['case']['target'],
                           antecedent=antecedent, implication=implication)
            keys = [k for k, m in model.metadata.items()
                    if m['slot'] == 2 and m['command'] == command]
            ck = next(k for k in keys if k[1] == 0)
            guards = [k for k in keys if k[1] == 1]
            assert len(guards) <= 1
            conflicts = []
            if guards:
                candidate = model.placement(guards[0])
                conflicts = [dict(point=p, assigned=prefix.marks[p], required=v)
                             for p, v in candidate.marks
                             if p in prefix.marks and prefix.marks[p] != v]
                legal = prefix.legal(candidate)
                assert legal == (not conflicts)
                status = 'compatible' if legal else 'distant_formula_conflict'
            else:
                # Both required formula words are assigned at the same port.
                assert antecedent == implication
                assert any(c['command'] == command for c in model.conflicts)
                status = 'internally_inconsistent_guard'
            prior = donor['search']['proof']
            implication_formula = prior[implication]['formula']
            expected = (implication_formula[0] == 'imp'
                        and implication_formula[1] == prior[antecedent]['formula']
                        and implication_formula[2] == command['formula'])
            assert expected == (status == 'compatible')
            alternatives.append(dict(antecedent=antecedent, implication=implication,
                                     command=command, command_key=ck,
                                     guard_key=guards[0] if guards else None,
                                     status=status, conflicts=conflicts))
    rows = []
    for j, command in enumerate(donor['search']['proof']):
        ck = next(k for k in selected if k[0] == j and k[1] == 0)
        gk = next(k for k in selected if k[0] == j and k[1] == 1)
        word = independent_word(command['formula'])
        for k, v in enumerate(word):
            assert dict(model.placement(ck).marks)[port(j, 'formula', k)] == v
        rows.append(dict(slot=j, command=command, command_key=ck, guard_key=gk,
                         formula_word=word, requirements=model.metadata[gk]['requirements'],
                         command_tile=recorded[ck], guard_tile=recorded[gk]))
    result = dict(
        version='propositional-markings-note-001',
        role='explanatory appendix to the unchanged Notebook 62 experiment',
        source_files={name: sha(name) for name in
                      ('native-inventory-reader-001.json', 'native-inventory-training-001.json.gz',
                       'native-inventory-001-proof-1-responses.json.gz')},
        theory=donor['case']['theory'], target=donor['case']['target'],
        request_sha256=accepted['request_sha256'], native_result=accepted['result'],
        proof=rows, alternatives=alternatives, actual_placement_order=selected,
        original_metrics=donor['search']['metrics'],
        grammar=donor['model']['encoding'], transformations=donor['model']['transformations'],
        context='Inspector fixes the two discovered hypothesis rows and the original target boundary. '
                'This is a legal diagnostic context, not a claimed chronological search node.',
        validation=dict(original_placements=len(recorded), exact_solution_placements=len(selected),
                        reference_pairs=len(alternatives), compatible_pairs=sum(
                            a['status'] == 'compatible' for a in alternatives),
                        all_formula_bytes_checked=True,
                        independent_rule_agreement=True, complete_target_checked=True),
        scope='Only a three-line bounded propositional example; no new RL experiment, '
              'universal finite-palette construction, native rerun or acceleration claim.')
    (DOCS / 'propositional-markings-note-001.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result['validation']))


if __name__ == '__main__':
    export()
