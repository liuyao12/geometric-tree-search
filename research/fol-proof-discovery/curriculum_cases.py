"""Relay training tiers and distinct transfer benchmarks."""

from itertools import permutations
from random import Random

from benchmark import anonymize, negative, positive, relay, verify_countermodel


LEVELS = ((2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (5, 2))
LEVEL_SIZE = 12
TEST_SIZE = 15
X, Y, Z = '?X', '?Y', '?Z'


def row(name, family, split, clauses, rng, goal_index, **details):
    return dict(id=name, family=family, split=split,
                clauses=anonymize(clauses, goal_index, rng), expected='provable', **details)


def training_cases():
    for level, (depth, max_decoys) in enumerate(LEVELS, 1):
        for n in range(LEVEL_SIZE):
            rng = Random(71_500+247*level+n)
            clauses = relay(rng, depth=depth, width=max_decoys)
            yield row(f'relay-level-{level}-{n+1:02}', 'guarded-relays', 'train', clauses, rng, 1,
                      level=level, depth=depth, max_decoys=max_decoys)


def calibration_cases():
    # The same nested witness must match three independently populated relations.
    for n in range(12):
        rng = Random(80_200+n)
        clauses = [(negative('complete', 'request'),),
                   (negative('left', X, Y), negative('middle', X, Y),
                    negative('right', X, Y), positive('complete', X))]
        common = ('pair', 'shared', 'key')
        sizes = (5+n//3, 6+n%3, rng.randint(5, 10))
        for relation, size in zip(('left', 'middle', 'right'), sizes):
            clauses.append((positive(relation, 'request', common),))
            for i in range(size):
                token = ('pair', f'tag{i}', f'{relation}_only_{i % 3}')
                clauses.append((positive(relation, 'request', token),))
        yield row(f'witness-calibration-{n+1:02}', 'three-way witness join', 'calibration', clauses, rng, 0)


def coloring(length, branches):
    """The clauses assert a proper two-coloring of a cycle with leaves."""
    domain = tuple(f'vertex{i}' for i in range(length+len(branches)))
    opens = [(i, i+1) for i in range(length-1)]
    leaves = [(parent, length+i) for i, parent in enumerate(branches)]
    closure = length-1, 0
    clauses = [
        (positive('red', X), positive('blue', X)),
        (negative('red', X), negative('blue', X)),
        (negative('arc', X, Y), negative('red', X), negative('red', Y)),
        (negative('arc', X, Y), negative('blue', X), negative('blue', Y)),
    ]
    for a, b in (*opens, *leaves, closure):
        clauses.append((positive('arc', domain[a], domain[b]),))
    model = None
    if length % 2 == 0:
        colors = [i % 2 for i in range(length)] + [1-parent % 2 for parent in branches]
        model = dict(size=len(domain), constants=dict(zip(domain, range(len(domain)))), functions={},
                     predicates={'arc': (*opens, *leaves, closure),
                                 'red': tuple((i,) for i, c in enumerate(colors) if c == 0),
                                 'blue': tuple((i,) for i, c in enumerate(colors) if c == 1)})
    return clauses, model


def assembly(leaves, distractors, rng, missing=False):
    """A goal is a nested tree with a separate obligation at each leaf."""
    nodes = [f'leaf{i}' for i in range(leaves)]
    layer = list(nodes)
    if missing:
        layer[-1] = 'unavailable'
    while len(layer) > 1:
        i = rng.randrange(len(layer)-1)
        layer[i:i+2] = [('pair', *layer[i:i+2])]
    atoms = (*nodes, *(f'spare{i}' for i in range(distractors)))
    clauses = [(positive('available', leaf),) for leaf in atoms]
    clauses.extend(((negative('available', X), negative('available', Y),
                     positive('available', ('pair', X, Y))),
                    (negative('available', layer[0]),)))
    model = None
    if missing:
        model = dict(size=2, constants={**{leaf: 1 for leaf in atoms}, 'unavailable': 0},
                     functions={'pair': (0, 0, 0, 1)}, predicates={'available': ((1,),)})
    return clauses, model


def injection(objects, slots, allowed=None):
    """Ground finite choice with a lifted exclusion rule."""
    items = tuple(f'item{i}' for i in range(objects))
    boxes = tuple(f'box{i}' for i in range(slots))
    if allowed is None:
        allowed = [range(slots)]*objects
    clauses = [tuple(positive('occupies', item, boxes[i]) for i in choices)
               for item, choices in zip(items, allowed)]
    different = tuple((i, j) for i in range(objects) for j in range(i+1, objects))
    clauses.extend((positive('distinct_items', items[i], items[j]),) for i, j in different)
    clauses.append((negative('occupies', X, Y), negative('occupies', Z, Y),
                    negative('distinct_items', X, Z)))
    model = None
    if objects <= slots and all(i in allowed[i] for i in range(objects)):
        domain = (*items, *boxes)
        model = dict(size=len(domain), constants=dict(zip(domain, range(len(domain)))), functions={},
                     predicates={'occupies': tuple((i, objects+i) for i in range(objects)),
                                 'distinct_items': different})
    return clauses, model


def cycle_signature(length, branches):
    counts = tuple(branches.count(i) for i in range(length))
    return min(c[i:]+c[:i] for c in (counts, counts[::-1]) for i in range(length))


def tree_signature(term):
    if isinstance(term, str):
        return 'leaf'
    return '('+','.join(sorted(tree_signature(t) for t in term[1:]))+')'


def injection_signature(allowed, slots):
    return min(tuple(sorted(sum(1 << renaming[i] for i in choices) for choices in allowed))
               for renaming in permutations(range(slots)))


def heldout_cases():
    seen_cycles, seen_trees, seen_injections = set(), set(), set()
    for n in range(TEST_SIZE):
        rng = Random(290_670 + n)
        while True:
            length = rng.choice((3, 5, 7, 9))
            branches = [rng.randrange(length) for _ in range(rng.randint(1, 7))]
            signature = cycle_signature(length, branches)
            if signature not in seen_cycles:
                seen_cycles.add(signature)
                break
        clauses, _ = coloring(length, branches)
        yield row(f'odd-cycle-{n+1:02}', 'odd-cycle coloring', 'test', clauses, rng, len(clauses)-1)

        rng = Random(308_704 + n)
        while True:
            clauses, _ = assembly(rng.randint(2, 6), rng.randint(2, 8), rng)
            signature = len(clauses), tree_signature(clauses[-1][0][2][0])
            if signature not in seen_trees:
                seen_trees.add(signature)
                break
        yield row(f'assembly-{n+1:02}', 'nested term assembly', 'test', clauses, rng, len(clauses)-1)

        rng = Random(318_040 + n)
        while True:
            slots = rng.choice((3, 4, 5))
            allowed = [tuple(sorted(rng.sample(range(slots), rng.randint(2, slots))))
                       for _ in range(slots+1)]
            signature = slots, injection_signature(allowed, slots)
            if signature not in seen_injections:
                seen_injections.add(signature)
                break
        clauses, _ = injection(slots+1, slots, allowed)
        yield row(f'injection-{n+1:02}', 'finite injection', 'test', clauses, rng, len(clauses)-1)

    for n in range(2):
        rng = Random(750_041+n)
        controls = (
            ('even-cycle', 'odd-cycle coloring', coloring(4+2*n, [0, 1])),
            ('missing-leaf', 'nested term assembly', assembly(3+n, 3, rng, missing=True)),
            ('matching-slots', 'finite injection', injection(2+n, 2+n)),
        )
        for name, family, (clauses, model) in controls:
            verify_countermodel(clauses, model)
            yield dict(id=f'{name}-{n+1:02}', family=family, split='test',
                       clauses=tuple(clauses), expected='satisfiable', model=model)


def cases():
    return (*training_cases(), *calibration_cases(), *heldout_cases())
