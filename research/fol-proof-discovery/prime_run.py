"""One growing proof library for a bounded marked arithmetic search."""

import argparse
from collections import Counter
import json
from pathlib import Path
from time import perf_counter

from checker import verify
from kernel import is_variable
from prime_logic import (FocusedSearch, ONE, PRIME_DIVISOR, UNBOUNDED_PRIMES, ZERO,
                         arithmetic_boundary, auxiliary_goals, clauses, multiply,
                         obligations, replace, successor)
from run import fingerprint


ATTEMPT_SAFETY_SECONDS = 60
DIRECT_OFFERS = 560_000
WITNESS_OFFERS = 26_000
MAX_TERM_NODES = 4
MAX_WITNESSES = 90
GENERATED_WIDTH = 4
GENERATED_DEPTH = 4
MAX_GIVEN = 2400
MAX_NODES = 110_000


def tuple_tree(value):
    return tuple(map(tuple_tree, value)) if isinstance(value, list) else value


def boundary(assumptions, library):
    sources = list(arithmetic_boundary().items()) + [
        (f'induction-hypothesis:{i}', formula) for i, formula in enumerate(assumptions)]
    sources.extend((name, entry['formula']) for name, entry in library.items())
    rows, names = [], []
    for index, (name, formula) in enumerate(sources):
        encoded = clauses(formula, index)
        rows.extend(encoded)
        names.extend([name]*len(encoded))
    return tuple(rows), names


def terms(rows):
    """Read constants from the in-scope context and enumerate constructor trees."""
    constants = {ZERO, ONE}
    stack = [t for row in rows for _, _, args in row for t in args]
    while stack:
        term = stack.pop()
        if isinstance(term, tuple):
            stack.extend(term[1:])
        elif not is_variable(term):
            constants.add(term)
    by_size = {1: tuple(sorted(constants))}
    for size in range(2, MAX_TERM_NODES+1):
        pool = [successor(term) for term in by_size[size-1]]
        for left_size in range(1, size-1):
            right_size = size-1-left_size
            pool.extend(multiply(a, b) for a in by_size[left_size] for b in by_size[right_size])
        by_size[size] = tuple(sorted(set(pool), key=repr))
    return tuple(t for stage in by_size.values() for t in stage)[:MAX_WITNESSES]


def obligation_inputs(inputs, names, formulas):
    """Assign fresh denial symbols locally to one checked subproof."""
    denial = clauses(formulas, 'goal', positive=False)
    return inputs+denial, names+['goal-denial']*len(denial)


def uses(proof, origins):
    return sorted({origins[line['source']] for line in proof['steps'] if line['rule']=='input'})


def attempt(inputs, origins, formula, preference, max_offers, stats):
    rows, names = obligation_inputs(inputs, origins, formula)
    t0 = perf_counter()
    search = FocusedSearch(rows, len(inputs), ATTEMPT_SAFETY_SECONDS,
                           GENERATED_WIDTH, GENERATED_DEPTH, max_steps=MAX_GIVEN,
                           max_offers=max_offers, max_nodes=MAX_NODES, preference=preference)
    result = search.run()
    stats['attempts'] += 1
    stats['seconds'] += perf_counter()-t0
    stats['placed_clauses'] += result['steps']
    stats['pair_offers'] += result['counters'].get('offers', 0)
    stats['marked_point_joins'] += result['counters'].get('marked_point_joins', 0)
    stats[result['limit'] or result['status']] += 1
    if result['proof'] is None:
        return None
    if not verify(rows, result['proof']):
        raise ValueError('clause checker rejected a returned proof')
    return dict(proof=result['proof'], used=uses(result['proof'], names),
                counters=result['counters'], seconds=perf_counter()-t0)


def witness_goals(formula, witness):
    if formula[0] != 'some':
        raise ValueError('witness selected for a goal that is not existential')
    _, name, body = formula
    instance = replace(body, name, witness)
    return tuple(instance[1:]) if instance[0] == 'and' else (instance,)


def prove_obligation(assumptions, goal, library, stats):
    rows, origins = boundary(assumptions, library)
    for preference in ('size', 'goal'):
        proof = attempt(rows, origins, goal, preference, DIRECT_OFFERS, stats)
        if proof is not None:
            return dict(mode='refutation', records=(proof,))
    if goal[0] == 'some':
        for witness in terms(rows):
            stats['witness_offers'] += 1
            results = []
            for formula in witness_goals(goal, witness):
                result = attempt(rows, origins, formula, 'goal', WITNESS_OFFERS, stats)
                if result is None:
                    break
                results.append(result)
            else:
                return dict(mode='witness', witness=witness, records=results)
    return None


def replay_theorem(formula, certificate, library):
    problems = obligations(formula, certificate['method'])
    phases = certificate['phases']
    if len(problems) != len(phases):
        raise ValueError('wrong number of induction obligations')
    used = set()
    for (assumptions, goal), phase in zip(problems, phases):
        rows, origins = boundary(assumptions, library)
        if phase['mode'] == 'refutation':
            targets = (goal,)
        elif phase['mode'] == 'witness':
            candidate = tuple_tree(phase['witness'])
            if candidate not in terms(rows):
                raise ValueError('witness escapes the declared in-scope term grammar')
            targets = witness_goals(goal, candidate)
        else:
            raise ValueError('unknown obligation rule')
        records = phase['records']
        if len(targets) != len(records):
            raise ValueError('wrong number of proofs for the obligation')
        for target, record in zip(targets, records):
            expanded, names = obligation_inputs(rows, origins, target)
            if not verify(expanded, record['proof']):
                raise ValueError('proof replay rejected')
            actual = uses(record['proof'], names)
            if actual != record['used']:
                raise ValueError('misreported proof dependency')
            used.update(actual)
    return sorted(used)


def solve(name, formula, library, methods, trace):
    stats = Counter()
    for method in methods:
        phases = []
        for assumptions, goal in obligations(formula, method):
            outcome = prove_obligation(assumptions, goal, library, stats)
            if outcome is None:
                break
            phases.append(outcome)
        else:
            cert = dict(method=method, phases=phases)
            used = replay_theorem(formula, cert, library)
            library[name] = dict(formula=formula, certificate=cert, used=used,
                                 imports=sorted(library))
            trace.append(dict(goal=name, status='proved', method=method, stats=stats, used=used))
            print(name, 'proved by', method, dict(stats), flush=True)
            return True
    trace.append(dict(goal=name, status='unknown', stats=stats))
    print(name, 'open under the bounds', dict(stats), flush=True)
    return False


def protocol():
    return dict(version='marked-prime-library-v1', arithmetic=arithmetic_boundary(),
                named_goals={'prime-divisor': PRIME_DIVISOR, 'unbounded-primes': UNBOUNDED_PRIMES},
                auxiliary=dict(auxiliary_goals()),
                witnessGrammar=dict(constructors=('succ', 'mul'), successorExpansion=('plus', 'x', 'one'),
                                    maxConstructorNodes=MAX_TERM_NODES,
                                    maxOffers=MAX_WITNESSES),
                bounds=dict(refutationPairOffers=DIRECT_OFFERS, witnessPairOffers=WITNESS_OFFERS,
                            attemptSafetySeconds=ATTEMPT_SAFETY_SECONDS,
                            width=GENERATED_WIDTH, termDepth=GENERATED_DEPTH,
                            given=MAX_GIVEN, nodes=MAX_NODES),
                initialLibrary=[])


def continuous(output):
    output.mkdir(parents=True, exist_ok=True)
    declaration = protocol()
    declaration_sha = fingerprint(declaration)
    (output/'boundary.json').write_text(json.dumps(declaration, indent=2)+'\n')
    library, trace = {}, []
    started = perf_counter()
    first = solve('prime-divisor', PRIME_DIVISOR, library,
                  ('direct', 'induction', 'strong-induction'), trace)
    if first:
        if not solve('unbounded-primes', UNBOUNDED_PRIMES, library, ('direct',), trace):
            for name, formula in auxiliary_goals():
                if solve(name, formula, library, ('induction', 'direct'), trace):
                    if solve('unbounded-primes', UNBOUNDED_PRIMES, library, ('direct',), trace):
                        break
    record = dict(schema='marked-prime-run-v1', declarationSha256=declaration_sha, trace=trace,
                  library=library, seconds=perf_counter()-started)
    path = output/'certificate.json'
    path.write_text(json.dumps(record, indent=2)+'\n')
    verification = replay(output)
    (output/'verification.json').write_text(json.dumps(verification, indent=2)+'\n')
    print(json.dumps(verification, indent=2), flush=True)


def replay(output):
    declaration = json.loads((output/'boundary.json').read_text())
    record = json.loads((output/'certificate.json').read_text())
    expected = protocol()
    if fingerprint(declaration) != fingerprint(expected) or record['declarationSha256'] != fingerprint(expected):
        raise ValueError('arithmetic or initial library boundary changed')
    checked = {}
    universe = {**expected['named_goals'], **expected['auxiliary']}
    for name, entry in record['library'].items():
        formula = tuple_tree(entry['formula'])
        if formula != universe.get(name) or sorted(checked) != entry['imports']:
            raise ValueError('unexpected theorem or library admission order')
        used = replay_theorem(formula, entry['certificate'], checked)
        if used != entry['used']:
            raise ValueError('misreported theorem dependencies')
        checked[name] = dict(entry, formula=formula)
    return dict(checked=list(checked), primeDivisor='prime-divisor' in checked,
                unboundedPrimes='unbounded-primes' in checked,
                reusedPrimeDivisor='prime-divisor' in checked.get('unbounded-primes', {}).get('used', ()),
                dependencies={name: entry['used'] for name, entry in checked.items()},
                declaredBoundarySize=len(expected['arithmetic']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(replay(args.directory), indent=2))
    else:
        continuous(args.directory)
