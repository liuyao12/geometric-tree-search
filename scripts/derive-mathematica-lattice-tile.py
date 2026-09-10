#!/usr/bin/env python3
"""Exact Z³ solid-angle data for the supplied oriented, nonconvex shell.

Uses integer predicates and Fraction arithmetic only. Edge exterior turns are
certified as ±π/2 or ±π/3 from integer normal products. At a vertex the spherical
link has area 2π minus the sum of those signed turns (spherical Gauss–Bonnet).
Run with --write to regenerate the catalogue asset; otherwise check it.
"""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction as Q
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def sign(x):
    return (x > 0) - (x < 0)


def on_segment(p, a, b):
    return cross(sub(p, a), sub(b, a)) == (0, 0, 0) and dot(sub(p, a), sub(p, b)) <= 0


def in_face(p, face, vertices, normal):
    if dot(normal, sub(p, vertices[face[0]])):
        return False
    axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(normal[i]))]
    x, y = (p[i] for i in axes)
    winding = 0
    for i, j in zip(face, face[1:] + face[:1]):
        a, b = vertices[i], vertices[j]
        if on_segment(p, a, b):
            return True
        ax, ay = (a[k] for k in axes)
        bx, by = (b[k] for k in axes)
        side = (bx-ax)*(y-ay)-(by-ay)*(x-ax)
        if ay <= y < by and side > 0:
            winding += 1
        elif by <= y < ay and side < 0:
            winding -= 1
    return winding != 0


def interior(p, triangles):
    # Exact oriented ray winding; retry a direction if it hits a triangulation
    # edge or lies in a triangle plane. Thus diagonals cannot double-count.
    for k in range(1, 1000):
        ray = (1, k, k*k)
        total = 0
        for a, b, c in triangles:
            normal = cross(sub(b, a), sub(c, a))
            denom = dot(normal, ray)
            numer = dot(normal, sub(a, p))
            if not denom:
                if not numer:
                    break
                continue
            distance = Q(numer, denom)
            if distance <= 0:
                continue
            hit = tuple(p[i] + distance*ray[i] for i in range(3))
            sides = [dot(normal, cross(sub(v, u), sub(hit, u)))
                     for u, v in ((a, b), (b, c), (c, a))]
            if min(sides) < 0:
                continue
            if min(sides) == 0:
                break
            total += sign(denom)
        else:
            assert total in (0, 1), (p, total)
            return bool(total)
    raise AssertionError(f"No generic ray for {p}")


def derive(source):
    vertices = [tuple(v) for v in source['vertices']]
    faces = [[i-source['face_index_base'] for i in f] for f in source['faces']]
    normals, triangles = [], []
    edges = defaultdict(list)
    links = defaultdict(list)
    for fi, f in enumerate(faces):
        a, b, c = (vertices[i] for i in f[:3])
        n = cross(sub(b, a), sub(c, a))
        assert dot(n, n) > 0
        assert all(dot(n, sub(vertices[i], a)) == 0 for i in f)
        # Every supplied face is convex, although the solid is not.
        for i, j in zip(f, f[1:]+f[:1]):
            assert all(dot(n, cross(sub(vertices[j], vertices[i]), sub(vertices[h], vertices[i]))) >= 0 for h in f)
            edges[tuple(sorted((i, j)))].append((fi, i, j))
        for k, i in enumerate(f):
            links[i].append((f[k-1], f[(k+1) % len(f)]))
        normals.append(n)
        triangles.extend((a, vertices[f[k]], vertices[f[k+1]]) for k in range(1, len(f)-1))
    assert len(vertices)-len(edges)+len(faces) == 2
    # Each vertex link is one circle, as required by the spherical area formula.
    for pairs in links.values():
        adjacency = defaultdict(set)
        for i, j in pairs:
            adjacency[i].add(j)
            adjacency[j].add(i)
        assert all(len(v) == 2 for v in adjacency.values())
        seen, todo = set(), [next(iter(adjacency))]
        while todo:
            v = todo.pop()
            if v not in seen:
                seen.add(v)
                todo.extend(adjacency[v]-seen)
        assert len(seen) == len(adjacency)
    turns, edge_values = defaultdict(list), {}
    for edge, uses in edges.items():
        assert len(uses) == 2
        (f, i, j), (g, jj, ii) = uses
        assert (i, j) == (ii, jj)
        n, m = normals[f], normals[g]
        d = dot(n, m)
        if d == 0:
            angle = Q(1, 2)
        else:
            assert d > 0 and 4*d*d == dot(n, n)*dot(m, m)
            angle = Q(1, 3)
        direction = sign(dot(cross(n, m), sub(vertices[j], vertices[i])))
        assert direction
        turn = direction*angle  # units of π
        turns[i].append(turn)
        turns[j].append(turn)
        edge_values[edge] = (1-turn)/2
    vertex_values = {v: (2-sum(turns[i]))/4 for i, v in enumerate(vertices)}
    groups = defaultdict(list)
    points = []
    bounds = [range(min(v[i] for v in vertices), max(v[i] for v in vertices)+1) for i in range(3)]
    for p in product(*bounds):
        if p in vertex_values:
            t, kind = vertex_values[p], 'vertex'
        else:
            incident = [value for (i, j), value in edge_values.items() if on_segment(p, vertices[i], vertices[j])]
            if incident:
                assert len(incident) == 1
                t, kind = incident[0], 'edge'
            elif any(in_face(p, f, vertices, n) for f, n in zip(faces, normals)):
                t, kind = Q(1, 2), 'face'
            else:
                t, kind = Q(int(interior(p, triangles))), 'interior'
        if not t:
            continue
        assert 0 < t <= 1 and (24*t).denominator == 1
        groups[t].append(list(p))
        points.append({'pos': list(p), 'weight': int(24*t), 'kind': kind})
    volume = sum(Q(dot(a, cross(b, c)), 6) for a, b, c in triangles)
    assert volume == 27
    assert sum(Q(p['weight'], 24) for p in points) == volume
    return {
        'name': source['name'], 'vertices': source['vertices'], 'faces': faces,
        'capacity': 24, 'volume': int(volume), 'points': points,
        'groups': [{'t': str(t), 'points': groups[t]} for t in sorted(groups)],
        'vertex_t_values': [str(vertex_values[v]) for v in vertices],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = json.loads((ROOT/'data/mathematica-lattice-tile.json').read_text())
    result = derive(source)
    content = '// Generated by scripts/derive-mathematica-lattice-tile.py --write.\n'
    content += '// Exact Z³ weights; preserve the supplied nonconvex shell winding.\n'
    content += 'export const MATHEMATICA_LATTICE_TILE = '+json.dumps(result, indent=2)+';\n'
    path = ROOT/'assets/mathematica-lattice-tile.js'
    if args.write:
        path.write_text(content)
    else:
        assert path.read_text() == content, 'Generated asset differs; regenerate with --write'
    print(json.dumps({'support': len(result['points']), 'volume': result['volume'],
                      'counts': {g['t']: len(g['points']) for g in result['groups']},
                      'kinds': dict(Counter(p['kind'] for p in result['points']))}, indent=2))


if __name__ == '__main__':
    main()
