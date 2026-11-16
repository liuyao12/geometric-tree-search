"""A rectangular square tiling of the checked prime-infinitude proof."""

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

from kernel import apply, normalize, scope
from prime_marks import Port, overlap
from prime_run import boundary, obligation_inputs, replay, tuple_tree


def require(condition, message):
    if not condition:
        raise ValueError(message)


def infer_write(rule, left, right, sites, counts, check_time):
    """Fill the south mark of a write tile from its horizontal request."""
    require(rule in ('resolve', 'factor'), 'unknown inference rule')
    factor = rule == 'factor'
    require(not factor or left == right, 'factoring needs one parent clause')
    left = scope(left, 'L')
    right = left if factor else scope(right, 'R')
    first, second = sites
    require(type(first) is int and 0 <= first < len(left) and
            type(second) is int and 0 <= second < len(right), 'invalid literal mark')
    require(not factor or first != second, 'factoring needs two distinct literals')
    a, b = left[first], right[second]
    require(Port.read(a).faces(Port.read(b), factor=factor), 'incompatible literal ports')
    substitution = overlap(a[2], b[2], counts, check_time)
    if substitution is None:
        return None
    if factor:
        rest = left[:second] + left[second+1:]
    else:
        rest = left[:first] + left[first+1:] + right[:second] + right[second+1:]
    return apply(rest, substitution), substitution


def conclusion(rule, left, right, sites):
    result = infer_write(rule, left, right, sites, Counter(), lambda: None)
    require(result is not None, 'outward term marks clash')
    return normalize(result[0])[0]


@dataclass(frozen=True)
class Tile:
    north: tuple
    east: tuple
    south: tuple
    west: tuple

    def marks(self):
        return [self.north, self.east, self.south, self.west]


WEST = ('wall', 'left')
EAST = ('wall', 'right')


def register(slot, value):
    return 'register', slot, value


def check_tile(tile, moves, clauses, width):
    """Admit one square by inspecting its own four marks."""
    n, e, s, w = tile.marks()
    if n == WEST:
        require(s == WEST and w == WEST and len(e) == 2 and e[0] == 'move'
                and e[1] in moves, 'bad left wall tile')
        return 'wall'
    if n == EAST:
        require(s == EAST and e == EAST and len(w) == 2 and w[0] == 'move'
                and w[1] in moves, 'bad right wall tile')
        return 'wall'
    require(len(n) == 3 and len(s) == 3 and n[0] == 'register' and s[:2] == n[:2],
            'inconsistent register marks')
    slot, before = n[1:]
    after = s[2]
    require(type(slot) is int and 0 <= slot < width, 'unknown register')
    require((before is None or before in clauses) and (after is None or after in clauses),
            'unknown clause mark')
    require(e == w and len(e) == 2 and e[0] == 'move' and e[1] in moves,
            'a row must carry the same inference across a tile')
    move = moves[e[1]]
    a, b = move['read']
    out = move['write']
    require(all(type(k) is int and 0 <= k < width for k in (a, b, out))
            and out not in (a, b), 'invalid read or write register')
    require(move['rule'] != 'factor' or a == b, 'factoring must read a single register')
    left, right = move['claims']
    require(left in clauses and right in clauses, 'unknown parent clause')
    if slot == a:
        require(before == left, 'left parent claim does not match the north mark')
    if slot == b:
        require(before == right, 'right parent claim does not match the north mark')
    if slot == out:
        require(before is None and after is not None, 'write needs a vacant register and a clause')
        derived = conclusion(move['rule'], clauses[left], clauses[right], move['sites'])
        require(clauses[after] == derived, 'south mark is not the admitted resolvent')
        return 'write'
    require(after == before, 'a carry tile must preserve the register')
    return 'read' if slot in (a, b) else 'vacant' if before is None else 'carry'


def check_patch(patch, sources):
    """Check the fixed boundary, square membership and all neighbor contacts."""
    width = patch['registers']
    source_indices = patch['sources']
    raw_rows = patch['squares']
    require(type(width) is int and raw_rows and 0 < len(source_indices) < width,
            'invalid board dimensions')
    require(len(set(source_indices)) == len(source_indices) and all(
        type(i) is int and 0 <= i < len(sources) for i in source_indices),
        'illegal premise on the top boundary')
    clauses = {i: tuple_tree(c) for i, c in enumerate(patch['clauses'])}
    require(len(set(clauses.values())) == len(clauses), 'duplicate clause marks')
    ids = {c: i for i, c in clauses.items()}
    require(() in ids, 'the contradiction mark is missing')
    moves = dict(enumerate(patch['moves']))
    top = [ids[normalize(sources[i])[0]] for i in source_indices]
    previous = [WEST] + [register(i, top[i] if i < len(top) else None)
                         for i in range(width)] + [EAST]
    roles = []
    for raw in raw_rows:
        require(len(raw) == width + 2, 'row contains a hole or an extra square')
        squares = [Tile(*map(tuple_tree, marks)) for marks in raw]
        require([t.north for t in squares] == previous, 'north and south marks do not meet')
        require(squares[0].west == WEST and squares[-1].east == EAST, 'open side boundary')
        require(all(a.east == b.west for a, b in zip(squares, squares[1:])),
                'east and west marks do not meet')
        roles.append([check_tile(t, moves, clauses, width) for t in squares])
        previous = [t.south for t in squares]
    require(previous[-2] == register(width-1, ids[()]), 'bottom boundary has no contradiction')
    return roles


def final_context(results):
    audit = replay(results)
    require(audit['unboundedPrimes'] and audit['reusedPrimeDivisor'], 'run did not prove infinitude')
    saved = json.loads((results/'certificate.json').read_text())['library']
    library = {name: dict(entry, formula=tuple_tree(entry['formula'])) for name, entry in saved.items()}
    goal = library.pop('unbounded-primes')
    sources, names = boundary((), library)
    sources, names = obligation_inputs(sources, names, goal['formula'])
    cert = goal['certificate']
    require(cert['method'] == 'direct' and len(cert['phases']) == 1 and
            cert['phases'][0]['mode'] == 'refutation', 'expected a direct final refutation')
    return sources, names, cert['phases'][0]['records'][0]['proof']['steps']


def assemble(results):
    sources, names, steps = final_context(results)
    inputs = [i for i, line in enumerate(steps) if line['rule'] == 'input']
    derived = [i for i, line in enumerate(steps) if line['rule'] != 'input']
    slots = {line: slot for slot, line in enumerate(inputs + derived)}
    width = len(steps)
    clauses, ids = [], {}

    def mark(row):
        row = normalize(tuple_tree(row))[0]
        if row not in ids:
            ids[row] = len(clauses)
            clauses.append(row)
        return ids[row]

    source_indices = [steps[i]['source'] for i in inputs]
    frontier = [mark(sources[i]) for i in source_indices] + [None] * len(derived)
    moves, rows = [], []
    for i in derived:
        step = steps[i]
        parents = step['parents']
        left, right = slots[parents[0]], slots[parents[-1]]
        write = slots[i]
        claims = [frontier[left], frontier[right]]
        moves.append(dict(read=[left, right], write=write, claims=claims,
                          rule=step['rule'], sites=step['sites']))
        label = ('move', len(moves)-1)
        updated = frontier.copy()
        updated[write] = mark(step['clause'])
        row = [Tile(WEST, label, WEST, WEST)]
        for slot in range(width):
            row.append(Tile(register(slot, frontier[slot]), label,
                            register(slot, updated[slot]), label))
        row.append(Tile(EAST, EAST, EAST, label))
        rows.append([tile.marks() for tile in row])
        frontier = updated
    patch = dict(registers=width, sources=source_indices, clauses=clauses, moves=moves,
                 squares=rows, sourceNames=[names[i] for i in source_indices])
    patch['roles'] = check_patch(patch, sources)
    return patch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, help='output directory from prime_run.py')
    parser.add_argument('patch', type=Path, help='JSON tiling to write or verify')
    parser.add_argument('--verify', action='store_true', help='check the supplied tiling')
    args = parser.parse_args()
    if args.verify:
        patch = json.loads(args.patch.read_text())
        sources, _, _ = final_context(args.results)
        check_patch(patch, sources)
    else:
        patch = assemble(args.results)
        args.patch.write_text(json.dumps(patch, separators=(',', ':')) + '\n')
    height, width = len(patch['squares']), patch['registers']+2
    print(f'Checked {height} rows × {width} columns = {height*width} unit squares.')
