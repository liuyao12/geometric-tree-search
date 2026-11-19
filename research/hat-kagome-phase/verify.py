"""Verify the Hat-only Kagome phase certificate using Python 3, without dependencies.

Run python3 verify.py with certificate.json beside it.

The underlying model has nonnegative integer point weights with capacity 12.
The Hat outline and the signed action come from the reference commit in the
certificate, in assets/a2-tiling-engine.js and assets/hat-rank3-marking.js.

Normalize one tile to the identity. Every tile whose positive support meets
it is obtained by aligning two support points. For each such pair that fits
the capacities but induces different periodic fields, the certificate names
a point that cannot reach capacity. The checker tries every possible local
completion at that point, using only the unmarked weights.

For every one-step neighbour outside the seed support, a second certificate
names a seed point that cannot be filled while avoiding the neighbour.
Consequently, in any complete tiling, a tile touching the seed covers that
neighbour. By symmetry, the union of the supports in any contact component
is closed under lattice steps. It therefore covers the entire lattice. All
tiles lie in that component, and the first certificate gives one common field.
"""

from collections import Counter
from functools import lru_cache
from itertools import combinations, permutations, product
import json
from math import gcd
from pathlib import Path


OUTLINE = ((0, 0), (1, 0), (1, 1), (3, 0), (4, 1), (3, 2), (3, 3),
           (1, 4), (0, 6), (-1, 6), (-1, 5), (-1, 4), (0, 3), (-1, 2))
# Primitive directions around the A2 plane in successive turns of pi/6.
DIRECTIONS = ((1, 0), (1, 1), (0, 1), (-1, 2), (-1, 1), (-2, 1),
              (-1, 0), (-1, -1), (0, -1), (1, -2), (1, -1), (2, -1))
GROUP = tuple(product((1, -1), permutations(range(3))))
SEED = (0, 0, 0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def outline_weights():
    """Read vertex angles, open edges, and interior from exact integer geometry."""
    edges = list(zip(OUTLINE, OUTLINE[1:] + OUTLINE[:1]))
    directions = []
    weights = {}
    for (x, y), (u, v) in edges:
        steps = gcd(abs(u - x), abs(v - y))
        dx, dy = (u - x) // steps, (v - y) // steps
        directions.append(DIRECTIONS.index((dx, dy)))
        for k in range(1, steps):
            weights[x + k * dx, y + k * dy] = 6
    for i, point in enumerate(OUTLINE):
        turn = (directions[i] - directions[i - 1] + 6) % 12 - 6
        weights[point] = 6 - turn
    xs, ys = zip(*OUTLINE)
    for x, y in product(range(min(xs), max(xs) + 1), range(min(ys), max(ys) + 1)):
        if (x, y) in weights:
            continue
        winding = 0
        for (a, b), (c, d) in edges:
            cross = (c - a) * (y - b) - (d - b) * (x - a)
            winding += int(b <= y < d and cross > 0) - int(d <= y < b and cross < 0)
        if winding:
            weights[x, y] = 12
    return weights


def symmetries_of(weights):
    result = []
    for sign, perm in GROUP:
        oriented = {}
        for (x, y), value in weights.items():
            xyz = (x, y, -x - y)
            oriented[sign * xyz[perm[0]], sign * xyz[perm[1]]] = value
        result.append(oriented)
    return result


SHAPES = symmetries_of(outline_weights())


@lru_cache(maxsize=None)
def placed(tile):
    k, dx, dy = tile
    return {(x + dx, y + dy): w for (x, y), w in SHAPES[k].items()}


def field(x, y):
    """Periodic vector field; absent Kagome sites are filled with zero."""
    if (x - y) % 3:
        return (0, 0, 0)
    i, j = ((-2*x-y)//3) % 2, ((-x-2*y)//3) % 2
    return {(0, 0): (1, 0, -1), (1, 1): (0, -1, 1),
            (1, 0): (-1, 1, 0), (0, 1): (0, 0, 0)}[i, j]


@lru_cache(maxsize=None)
def phase(k, dx, dy):
    # Push the field forward by a signed permutation and a translation. Every
    # point map, including its inverse, preserves the period sublattice 6 Z^2.
    sign, perm = GROUP[k]
    parity = (-1) ** sum(a > b for a, b in combinations(perm, 2))
    values = {}
    for x, y in product(range(6), repeat=2):
        xyz = (x, y, -x-y)
        image = ((sign * xyz[perm[0]] + dx) % 6, (sign * xyz[perm[1]] + dy) % 6)
        vector = field(x, y)
        values[image] = tuple(parity * vector[i] for i in perm)
    require(len(values) == 36, "The group element does not permute the period cell")
    return tuple(values[p] for p in sorted(values))


def incident(point):
    x, y = point
    for k, shape in enumerate(SHAPES):
        for (u, v), weight in shape.items():
            yield (k, x-u, y-v), weight


def totals(tiles):
    result = Counter()
    for tile in tiles:
        result.update(placed(tile))
    return result


def check_witness(fixed, point, avoid=None):
    board = totals(fixed)
    need = 12 - board[point]
    require(0 < need <= 9, ("not a deficient fixed point", fixed, point))
    choices = []
    for tile, w in incident(point):
        shape = placed(tile)
        if tile in fixed or w > need or avoid in shape:
            continue
        if all(board[p] + n <= 12 for p, n in shape.items()):
            choices.append((tile, w))
    # Every Hat contributes at least 3 whenever it contributes positively.
    # No completion can use more than floor(need/3) additional distinct tiles.
    for count in range(1, need // 3 + 1):
        for subset in combinations(choices, count):
            if sum(w for _, w in subset) == need:
                union = totals([*fixed, *(tile for tile, _ in subset)])
                require(max(union.values()) > 12, ("witness admits a completion", fixed, point, avoid))


def main():
    cert = json.loads(Path(__file__).with_name("certificate.json").read_text())
    base = placed(SEED)
    require(min(base.values()) == 3, "unexpected minimum weight")
    require(base == {(x, y): w for x, y, w in cert["occupancy_xy_twelfths"]},
            "exact geometry disagrees with reference occupancy")
    fields = {phase(k, x, y) for k, x, y in product(range(12), range(6), range(6))}
    touching = {tile for p in base for tile, _ in incident(p)}
    legal = {tile for tile in touching if max(totals([SEED, tile]).values()) <= 12}
    wrong_phase = {tile for tile in legal if phase(tile[0], tile[1] % 6, tile[2] % 6) != phase(*SEED)}
    witnesses = cert["contact_witnesses"]
    require({(k, x, y) for k, x, y, _, _ in witnesses} == wrong_phase
            and len(witnesses) == len(wrong_phase), "incomplete contact certificate")
    for k, x, y, u, v in witnesses:
        check_witness([SEED, (k, x, y)], (u, v))
    shell = {(x+dx, y+dy) for x, y in base for dx, dy in DIRECTIONS[::2]} - base.keys()
    exterior = cert["shell_witnesses"]
    require({(x, y) for x, y, _, _ in exterior} == shell
            and len(exterior) == len(shell), "incomplete shell certificate")
    for x, y, u, v in exterior:
        check_witness([SEED], (u, v), avoid=(x, y))
    extents = cert["full_marking_xy_xyz_components_by_extent"]
    require([len(rows) for rows in extents] == [24, 31, 39, 47], "incorrect reference mark sizes")
    for rows in extents:
        require(len({(x, y) for x, y, *_ in rows}) == len(rows), "duplicate mark")
        for x, y, *vector in rows:
            require(tuple(vector) == field(x, y), "reference mark disagrees with field")
    print(f"Verified {len(fields)} phases, {len(legal)} capacity-legal contacts, "
          f"{len(wrong_phase)} wrong-phase exclusions and {len(shell)} shell witnesses.")
    print("All published full Hat marking extents 0, 1, 2 and 3 restrict the common field.")


if __name__ == "__main__":
    main()
