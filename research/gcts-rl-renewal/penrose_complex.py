"""Independent finite hypotheses for the connected saturated-star theorem.

This is a geometry/certificate diagnostic, never a search legality filter.
The infinite completeness/covering argument is written in the accompanying
HTML proof; this program checks its finite template and star hypotheses.
"""
from collections import defaultdict
from fractions import Fraction
import cyclotomic as ring

ZERO, ONE = ring.ZERO, ring.ONE
KINDS = ("thick", "thin")
# Independently declared CCW outlines, not Model/Graph or cached point support.
VERTICES = {
    "thick": (ZERO, ONE, (1, 1, 0, 0), ring.ZETA),
    "thin": ((0, 0, -1, 0), (1, 0, -1, 0), ONE, ZERO),
}
ETA = (0, 0, 0, -1)
DIRECTIONS = tuple(ring.power(ETA, i) for i in range(10))


def sub(a, b):
    return ring.add(a, ring.neg(b))


def scale(a, factor):
    return tuple(factor * x for x in a)


def norm2(a):
    return ring.mul(a, ring.conjugate(a))


def real_sign(a):
    # Four times the real embedding is A+B sqrt(5). Rational coefficients
    # are allowed in the barycentric geometry audit, never in placements.
    a, b, c, d = a
    x, y = 4*a-b-c-d, b-c-d
    if not x:
        return (y > 0) - (y < 0)
    if not y or (x > 0) == (y > 0):
        return (x > 0) - (x < 0)
    difference = x*x-5*y*y
    return ((x > 0)-(x < 0))*((difference > 0)-(difference < 0))


def cross2(a, b):
    z = ring.mul(ring.conjugate(a), b)
    imaginary_twice = sub(z, ring.conjugate(z))
    return scale(ring.mul(imaginary_twice, imaginary_twice), Fraction(-1, 4))


def placement_key(raw):
    kind, rotation, translation = raw
    translation = tuple(translation)
    if kind not in KINDS or type(rotation) is not int or not 0 <= rotation < 10:
        raise ValueError("undeclared kind or rotation")
    if len(translation) != 4 or any(type(x) is not int for x in translation):
        raise ValueError("exact rank-four integer translation required")
    return kind, rotation, translation


def placement(raw):
    key = placement_key(raw)
    kind, rotation, translation = key
    vertices = tuple(ring.add(ring.mul(v, DIRECTIONS[rotation]), translation)
                     for v in VERTICES[kind])
    slots = set()
    corners = []
    for i, v in enumerate(vertices):
        following = DIRECTIONS.index(sub(vertices[(i+1) % 4], v))
        preceding = DIRECTIONS.index(sub(vertices[i-1], v))
        width = (preceding-following) % 10
        if not 1 <= width <= 4:
            raise ValueError("nonconvex or degenerate corner")
        occupied = tuple((following+j) % 10 for j in range(width))
        slots.update((v, s) for s in occupied)
        corners.append({"vertex": v, "start": following, "width": width,
                        "sectors": occupied})
    if len(slots) != 10:
        raise ValueError("wrong sector template")
    return {"key": key, "vertices": vertices, "slots": frozenset(slots),
            "corners": corners}


def corner_catalog():
    physical = defaultdict(list)
    for kind in KINDS:
        for rotation in range(10):
            for v in VERTICES[kind]:
                key = kind, rotation, ring.neg(ring.mul(v, DIRECTIONS[rotation]))
                tile = placement(key)
                physical[tuple(sorted(tile["vertices"]))].append(key)
    catalog = []
    for vertices, aliases in sorted(physical.items()):
        key = min(aliases)
        tile = placement(key)
        root = next(c for c in tile["corners"] if c["vertex"] == ZERO)
        catalog.append({"key": key, "aliases": sorted(aliases), "vertices": tile["vertices"],
                        "start": root["start"], "width": root["width"],
                        "sectors": root["sectors"]})
    return catalog


def star_certificate(indices, catalog=None):
    catalog = corner_catalog() if catalog is None else catalog
    indices = tuple(indices)
    if not indices or any(type(i) is not int or not 0 <= i < len(catalog) for i in indices):
        raise ValueError("exact corner indices required")
    if len(indices) != len(set(indices)):
        raise ValueError("repeated physical face")
    slots = set()
    owners = {}
    radial = defaultdict(list)
    for i in indices:
        tile = placement(catalog[i]["key"])
        if slots & tile["slots"]:
            raise ValueError("sector capacity conflict")
        slots.update(tile["slots"])
        corner = next(c for c in tile["corners"] if c["vertex"] == ZERO)
        for s in corner["sectors"]:
            owners[s] = i
        radial[corner["start"]].append((i, 1))
        radial[(corner["start"]+corner["width"]) % 10].append((i, -1))
    if set(owners) != set(range(10)):
        raise ValueError("root star is incomplete")
    seams = []
    for direction, faces in sorted(radial.items()):
        if len(faces) != 2 or {sign for _, sign in faces} != {-1, 1}:
            raise ValueError("unit edge does not have opposite partners")
        endpoint = DIRECTIONS[direction]
        for i, _ in faces:
            vertices = placement(catalog[i]["key"])["vertices"]
            if not any({a, b} == {ZERO, endpoint}
                       for a, b in zip(vertices, vertices[1:]+vertices[:1])):
                raise ValueError("same ray but different edge endpoint")
        seams.append({"direction": direction, "endpoint": endpoint,
                      "faces": sorted(i for i, _ in faces)})
    return {"corners": sorted(indices), "faces": len(indices),
            "sector_owners": [owners[s] for s in range(10)], "seams": seams}


def enumerate_stars(catalog=None):
    catalog = corner_catalog() if catalog is None else catalog
    masks = [sum(1 << s for s in c["sectors"]) for c in catalog]
    by_sector = [[i for i, mask in enumerate(masks) if mask & (1 << s)] for s in range(10)]
    results = []

    def visit(mask, slots, indices):
        if mask == 1023:
            results.append(star_certificate(indices, catalog))
            return
        s = next(s for s in range(10) if not mask & (1 << s))
        for i in by_sector[s]:
            if mask & masks[i]:
                continue
            positive = placement(catalog[i]["key"])["slots"]
            if not slots & positive:
                visit(mask | masks[i], slots | positive, indices+[i])

    visit(0, frozenset(), [])
    return sorted(results, key=lambda s: s["corners"])


def template_audit():
    triangles = edges = 0
    for kind in KINDS:
        for rotation in range(10):
            tile = placement((kind, rotation, ZERO))
            vertices = tile["vertices"]
            center = scale(tuple(sum(v[i] for v in vertices) for i in range(4)), Fraction(1, 4))
            for i, v in enumerate(vertices):
                edge = sub(vertices[(i+1) % 4], v)
                if norm2(edge) != ONE:
                    raise ValueError("nonunit edge")
                adjacent = sub(vertices[i-1], v)
                if real_sign(sub(cross2(edge, adjacent), scale(ONE, Fraction(1, 4)))) < 0:
                    raise ValueError("vertex-chart altitude is less than one half")
                edges += 1
                # Two barycentric triangles per side: corner, midpoint, center.
                midpoint = scale(ring.add(v, vertices[(i+1) % 4]), Fraction(1, 2))
                for corner in (v, vertices[(i+1) % 4]):
                    e1, e2 = sub(midpoint, corner), sub(center, corner)
                    if norm2(e1) != scale(ONE, Fraction(1, 4)):
                        raise ValueError("wrong half edge")
                    if real_sign(sub(norm2(e2), ONE)) > 0:
                        raise ValueError("corner-to-center length exceeds one")
                    if real_sign(sub(cross2(e1, e2), scale(ONE, Fraction(1, 64)))) < 0:
                        raise ValueError("degenerate or too small barycentric triangle")
                    triangles += 1
    return {"unit_edges_checked": edges, "barycentric_triangles_checked": triangles,
            "half_edge_norm_squared": [1, 4], "center_distance_squared_upper": 1,
            "determinant_squared_lower": [1, 64], "graph_distance_lipschitz_bound": 12,
            "vertex_chart_radius_lower": [1, 2],
            "infinite_argument": "analytic proof; finite checks do not formally verify covering or completeness"}


def periodic_controls(catalog=None):
    catalog = corner_catalog() if catalog is None else catalog
    u, v = ONE, ring.ZETA
    keys = [("thick", 0, t) for t in (ZERO, ring.neg(u), ring.neg(v), ring.neg(ring.add(u, v)))]
    lookup = {tuple(sorted(c["vertices"])): i for i, c in enumerate(catalog)}
    root = star_certificate([lookup[tuple(sorted(placement(k)["vertices"]))] for k in keys], catalog)
    shift = sub(ring.PHI, ONE)
    if shift[2] == 0 and shift[3] == 0:
        raise ValueError("two periodic vertex cosets intersect")
    return {"scope": "analytic comparison controls, never discovery or policy input",
            "basis": [u, v], "root_placements": keys, "root_star": root,
            "second_layer_shift": shift,
            "shifted_root_placements": [(kind, r, ring.add(t, shift)) for kind, r, t in keys],
            "vertex_cosets_disjoint": True,
            "point": "two disconnected complete periodic layers are point-legal and overlap geometrically"}


def complete_vertices(keys):
    totals = set()
    incident = defaultdict(list)
    seen = set()
    for raw in keys:
        tile = placement(raw)
        if tile["key"] in seen or totals & tile["slots"]:
            raise ValueError("invalid finite point patch")
        seen.add(tile["key"])
        totals.update(tile["slots"])
        for v in tile["vertices"]:
            incident[v].append(tile["key"])
    full = {v: cs for v, cs in incident.items() if all((v, s) in totals for s in range(10))}
    return full, len(incident)-len(full)
