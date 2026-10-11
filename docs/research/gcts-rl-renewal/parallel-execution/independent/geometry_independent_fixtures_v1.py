"""Independent bounded synthetic point tests. No production model is read."""
import copy
import hashlib
import importlib.util
import itertools
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CORE_PATH = ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py'
F, G, I = ['pred', 'F', []], ['pred', 'G', []], None
I = ['imp', F, G]
FORMULAS = [F, G, I]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def recipe(label, formula, premises=(), rule='fixture_zero'):
    return {'id': 'independent-synthetic-' + label,
            'primitive_witness': {'rule': rule, 'formula': copy.deepcopy(formula), 'fixture_label': label},
            'ordered_premise_formulas': copy.deepcopy(list(premises))}


RECIPES = [recipe('first-f', F), recipe('g', G), recipe('imp', I), recipe('other-f', F),
           recipe('mp', G, (F, I), 'mp'), recipe('equal-port', G, (F, F), 'opaque_pair')]
CONTEXT = {'ordered_local_premises': [], 'independent_synthetic': True}
AUTHORITY = {'label': 'nonlogical_independent_synthetic_only', 'activated': False, 'native_accepted': False}
AUTHORITY['epoch'] = digest(AUTHORITY)


def raw_domain(graph, row):
    """Translate every raw prototype; no production factors/legality/point_data."""
    answer = {}
    if graph.totals[row]:
        return answer
    codes = {canonical(f): i for i, f in enumerate(FORMULAS)}
    for index, recipe_data in enumerate(RECIPES):
        premises = recipe_data['ordered_premise_formulas']
        for offsets in itertools.product(range(1 - graph.height, 0), repeat=len(premises)):
            references = tuple(row + offset for offset in offsets)
            marks = {(1, row): codes[canonical(recipe_data['primitive_witness']['formula'])]}
            valid = True
            for port, (ref, formula, offset) in enumerate(zip(references, premises, offsets)):
                value = codes[canonical(formula)]
                if (1, ref) in marks and marks[(1, ref)] != value:
                    valid = False
                    break
                marks[(1, ref)] = value
                marks[(2 + port, row)] = offset
            if not valid or any(point in graph.marks and graph.marks[point] != value for point, value in marks.items()):
                continue
            # Negative references are removed by the explicit exterior sentinel,
            # rather than a strict-prior filter in this independent enumeration.
            key = (index, row, references)
            if any((k.recipe, k.row, k.refs) == key for k in graph.excluded[row]):
                continue
            answer[key] = ([[0, row, 1]], [[x, y, v] for (x, y), v in sorted(marks.items())])
    return answer


def graph(core, marks=(), roots=None):
    return core.PointGraph(height=3, formulas=FORMULAS, recipe_data=RECIPES,
        context=CONTEXT, authority=AUTHORITY, fixture=True, roots=roots,
        fixed_marks=[(1, -2, -1), (1, -1, -1)] + list(marks))


def compare(core, value):
    census = 0
    for row in range(3):
        direct = raw_domain(value, row)
        actual = list(value.candidates(row))
        assert [(k.recipe, k.row, k.refs) for k in actual] == sorted(direct)
        assert len(actual) == value.domains[row].count
        assert (not direct) == (value.domains[row].count == 0)
        assert (len(direct) == 1) == (value.domains[row].count == 1)
        for key in actual:
            assert value.point_data(key) == direct[(key.recipe, key.row, key.refs)]
        census += len(actual)
    return census


def reconstructed_identity(key, points):
    t, m = points
    data = RECIPES[key.recipe]
    witness = copy.deepcopy(data['primitive_witness'])
    command = copy.deepcopy(witness)
    if key.refs:
        if command['rule'] == 'mp':
            command.update(antecedent=key.refs[0], implication=key.refs[1])
        else:
            command['ordered_refs'] = list(key.refs)
    proto = {'recipe_id': data['id'], 'primitive_witness': witness,
        'ordered_premise_formulas': data['ordered_premise_formulas'],
        'relative_ordered_input_offsets': [r - key.row for r in key.refs],
        'orientation': 'identity', 't': [[x, y - key.row, v] for x, y, v in t],
        'm': [[x, y - key.row, v] for x, y, v in m],
        'marking_version': 'injective-formula-ordered-mp-offset-v1',
        'formula_registry_sha256': digest(FORMULAS), 'authority_epoch': AUTHORITY['epoch']}
    preimage = {'prototype_id': 'primitive-prototype-' + digest(proto), 'prototype_preimage': proto,
        'transform': [0, key.row], 'context_id': digest(CONTEXT), 'ordered_input_rows': list(key.refs),
        'primitive_command': command, 't': t, 'm': m, 'authority_epoch': AUTHORITY['epoch'],
        'formula_registry_sha256': digest(FORMULAS)}
    return preimage, 'aggregate-primitive-' + digest(preimage)


def rejects(action):
    try:
        action()
    except (ValueError, TypeError, IndexError):
        return
    raise AssertionError('mutant unexpectedly accepted')


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('25-second pure fixture gate')))
    signal.alarm(25)
    plan_path = HERE / 'geometry-independent-plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    for path, expected in plan['pins'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location('independent_synthetic_graph_core_v2', CORE_PATH)
    core = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = core
    spec.loader.exec_module(core)
    states = placements = 0
    ports = [()] + [(x, r, v) for x in (2, 3) for r in range(3) for v in (0, -1, -2)]
    for values in itertools.product((None, 0, 1, 2), repeat=3):
        assigned = [(1, r, v) for r, v in enumerate(values) if v is not None]
        for port in ports:
            current = graph(core, assigned + ([port] if port else []))
            placements += compare(core, current)
            states += 1
    assert states == 1216
    current = graph(core)
    identities = 0
    for row in range(3):
        direct = raw_domain(current, row)
        for key in current.candidates(row):
            preimage, identifier = reconstructed_identity(key, direct[(key.recipe, row, key.refs)])
            actual = current.decorate(key)
            assert actual['identity_preimage'] == preimage and actual['id'] == identifier
            identities += 1
    assert identities == 19
    same = core.Key(5, 2, (0, 0))
    assert current.legal(same)
    assert [2, 2, -2] in current.point_data(same)[1] and [3, 2, -2] in current.point_data(same)[1]
    assert not current.legal(core.Key(4, 2, (0, 0)))
    assert current.decorate(core.Key(0, 1))['id'] != current.decorate(core.Key(3, 1))['id']
    before, checkpoint = current.semantic_state(), current.checkpoint()
    core.Executor(current).step(core.Key(0, 0)); compare(core, current)
    mid, child = current.semantic_state(), current.checkpoint()
    core.Executor(current).step(core.Key(2, 1)); compare(core, current)
    current.rollback(child); assert current.semantic_state() == mid
    current.exclude_failed_child(next(current.candidates(1))); compare(core, current)
    current.rollback(checkpoint); assert current.semantic_state() == before
    zero = graph(core, [(2, 2, 0)])
    assert not any(k.recipe == 4 for k in zero.candidates(2))
    assert any(k.recipe == 0 for k in zero.candidates(2))
    dead = graph(core, [(1, 0, 1), (1, 2, 999)])
    assert dead.decision().kind == 'dead' and dead.decision().row == 2
    forced = graph(core, [(1, 2, 2)])
    assert forced.decision().kind == 'forced' and forced.decision().row == 2
    early = graph(core, [(1, 1, 0), (1, 2, 0)], roots=(0, 5, 5))
    assert early.decision().row == 0
    unknown = graph(core); before = unknown.semantic_state()
    assert core.Executor(unknown).solve(max_attempts=0, seconds=1)['status'] == 'unknown_budget'
    assert unknown.semantic_state() == before
    invalid = copy.deepcopy(RECIPES)
    invalid[4]['ordered_premise_formulas'][1] = ['imp', G, G]
    rejects(lambda: core.PointGraph(height=3, formulas=FORMULAS + [['imp', G, G]],
        recipe_data=invalid, context=CONTEXT, authority=AUTHORITY, fixture=True))
    for marks in ([(1, 0, True)], [(True, 0, 0)], [(1, False, 0)]):
        rejects(lambda marks=marks: graph(core, marks))
    # Direct counterexample, not a target search: after one scheduler-valid base
    # placement invalidates the full union, a surviving constituent still leads.
    current = graph(core)
    proposed = (core.Key(0, 0), core.Key(1, 1))
    assert current.validate_cluster(proposed, current.model_epoch) == proposed
    core.Executor(current).step(core.Key(3, 0))
    rejects(lambda: current.validate_cluster(proposed, current.model_epoch))
    decision = current.decision()
    assert decision.kind == 'branch' and decision.row == 1
    base = next(current.candidates(1)); preferred = next(current.candidates_with_preferences(1, proposed))
    assert base == core.Key(0, 1) and preferred == proposed[1] and base != preferred
    result = {'status': 'passed_independent_synthetic_domain_identity_scheduler_fixtures_with_cluster_gap_confirmed',
        'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        'states': states, 'accepted_placement_comparisons': placements, 'full_identity_comparisons': identities,
        'controls': ['ordered repeated/equal premises', 'same formula distinct decorated witness',
            'nested distant update/rollback', 'parent-local exclusions', 'assigned zero/absence',
            'global dead/forced/earliest generation', 'budget unknown restoration',
            'mark-consistent invalid MP', 'exact integer boolean negatives'],
        'fixed_preference_gap_counterexample': {'initial_valid_proposal': [k.data() for k in proposed],
            'scheduler_valid_competing_base': core.Key(3, 0).data(), 'full_cluster_invalid_after': True,
            'subsequent_decision': {'kind': decision.kind, 'row': decision.row},
            'complete_base_first': base.data(), 'surviving_preference_first': preferred.data(),
            'full_cluster_lifecycle_conformance': 'open'},
        'production_model_loads': 0, 'target_searches': 0, 'native_queries': 0,
        'positive_attempts_in_manual_synthetic_transactions': 3,
        'new_proof_discoveries': 0, 'independent_whole_logical_or_native_acceptance': False,
        'scope': 'Pure synthetic point contract, independent direct raw prototype checker; not production graph or proof validity.',
        'seconds_before_receipt_write': time.perf_counter() - started,
        'kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    signal.alarm(0)
    with (HERE / 'geometry-independent-result-v1.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
