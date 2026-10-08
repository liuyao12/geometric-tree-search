#!/usr/bin/env python3
"""Exact lattice checks and numerical gap counts, separate from tiling search.

The exact ladders are proved by the eigenfunctions in the accompanying notes.
FEM counts are observations, not certified continuum counts or tests of
algebraicity. The existing computation and chair receipts are left intact.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import time
import numpy as np
import triangle
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from compute import AXIAL, mesh, solve, tile

ROOT = Path(__file__).resolve().parent


def mm(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(2))
                       for j in range(2)) for i in range(2))


def mv(a, b):
    return tuple(sum(a[i][j]*b[j] for j in range(2)) for i in range(2))


def transpose(a):
    return tuple(zip(*a))


def det(a):
    return a[0][0]*a[1][1]-a[0][1]*a[1][0]


def dual(a):
    d = det(a)
    return ((a[1][1]//d, -a[1][0]//d),
            (-a[0][1]//d, a[0][0]//d))


def quadratic(k):
    m, n = k
    return m*m-m*n+n*n


def exact_mirrors():
    identity = ((1, 0), (0, 1))
    rotation = ((0, -1), (1, 1))
    reflection = ((1, 1), (0, -1))
    powers = [identity]
    for _ in range(5):
        powers.append(mm(powers[-1], rotation))
    assert mm(powers[-1], rotation) == identity
    assert mm(reflection, reflection) == identity
    assert mm(mm(reflection, rotation), reflection) == powers[-1]
    mirrors = [mm(r, reflection) for r in powers]
    group = powers+mirrors
    assert len(set(group)) == 12
    gram = ((2, 1), (1, 2))
    assert all(mm(mm(transpose(w), gram), w) == gram for w in group)
    hat = [tuple(map(int, v)) for v in AXIAL]
    edges = [tuple(hat[(i+1) % len(hat)][j]-p[j] for j in range(2))
             for i, p in enumerate(hat)]
    # Natural Turtle = Tile(sqrt(3),1), in a triangular basis rotated by pi/6.
    # Short Hat edge e becomes M e; long Hat edge e becomes M e/3.
    transform = ((2, 1), (-1, 1))
    turtle_edges = []
    for e in edges:
        norm = e[0]*e[0]+e[0]*e[1]+e[1]*e[1]
        assert norm in (1, 3)
        mapped = mv(transform, e)
        assert all(x % norm == 0 for x in mapped)
        turtle_edges.append(tuple(x//norm for x in mapped))
    turtle = [(0, 0)]
    for e in turtle_edges[:-1]:
        turtle.append(tuple(turtle[-1][j]+e[j] for j in range(2)))
    assert all(sum(e[j] for e in turtle_edges) == 0 for j in range(2))
    domains = {}
    for name, vertices, vectors in [('Hat', hat, edges),
                                    ('Turtle', turtle, turtle_edges)]:
        side_checks = []
        for p, e in zip(vertices, vectors):
            matches = [i for i, s in enumerate(mirrors) if mv(s, e) == e]
            assert len(matches) == 1
            s = mirrors[matches[0]]
            offset = tuple(p[j]-mv(s, p)[j] for j in range(2))
            side_checks.append({'vertex': p, 'edge': e,
                                'reflection_index': matches[0],
                                'affine_lattice_translation': offset})
        domains[name] = {'lattice_vertices': vertices, 'boundary_checks': side_checks}
    shells = defaultdict(set)
    bound = math.ceil(math.sqrt(2*80))
    for m in range(-bound, bound+1):
        for n in range(-bound, bound+1):
            q = quadratic((m, n))
            if not 0 < q <= 80:
                continue
            orbit = tuple(sorted({mv(dual(w), (m, n)) for w in group}))
            assert all(quadratic(k) == q for k in orbit)
            if len(orbit) == 12:
                shells[q].add(orbit)
    ladder = [{'q': q, 'independent_orbits': len(orbits),
               'representatives': [orbit[0] for orbit in sorted(orbits)]}
              for q, orbits in sorted(shells.items())]
    assert ladder[0]['q'] == 7
    return {'group_axial_matrices': group, 'domains': domains,
            'dirichlet_regular_shells_to_80': ladder,
            'proof_scope': 'Integer group identities, affine mirrors and dual norm checks. The notes supply the analytic eigenfunction proof.'}


def solve_with_overlaps(seed, level, k, families):
    """Consistent-mass P1 FEM, retaining overlap with analytic eigenfunctions."""
    p, t, boundary = mesh(seed['vertices'], seed['triangles'], level, seed['segments'])
    v = p[t]
    determinant = ((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])-
                   (v[:, 1, 1]-v[:, 0, 1])*(v[:, 2, 0]-v[:, 0, 0]))
    assert np.all(determinant > 1e-13)
    areas = determinant/2
    gradients = np.stack((v[:, [1, 2, 0], 1]-v[:, [2, 0, 1], 1],
                          v[:, [2, 0, 1], 0]-v[:, [1, 2, 0], 0]), axis=2)/determinant[:, None, None]
    stiffness = areas[:, None, None]*np.einsum('tik,tjk->tij', gradients, gradients)
    mass = areas[:, None, None]/12*(np.ones((3, 3))+np.eye(3))
    rows, columns = np.repeat(t, 3, axis=1).ravel(), np.tile(t, (1, 3)).ravel()
    interior = np.setdiff1d(np.arange(len(p)), boundary)
    K = coo_matrix((stiffness.ravel(), (rows, columns)), shape=(len(p), len(p))).tocsr()[interior][:, interior]
    M = coo_matrix((mass.ravel(), (rows, columns)), shape=(len(p), len(p))).tocsr()[interior][:, interior]
    values, vectors = eigsh(K, k=k, M=M, sigma=0, which='LM', tol=1e-10,
                            v0=np.linspace(1, 2, len(interior)))
    order = np.argsort(values)
    values, vectors = values[order], vectors[:, order]
    overlaps = {}
    for label, functions in families.items():
        basis = np.column_stack([f(p[interior]) for f in functions])
        weighted = M@basis
        gram = basis.T@weighted
        coefficients = basis.T@(M@vectors)
        projection = np.sum(coefficients*np.linalg.solve(gram, coefficients), axis=0)
        assert min(projection) > -1e-8 and max(projection) < 1+1e-8
        overlaps[str(label)] = projection.tolist()
    residual = max(np.linalg.norm(K@vectors[:, j]-values[j]*(M@vectors[:, j]))/
                   (np.linalg.norm(K@vectors[:, j])+abs(values[j])*np.linalg.norm(M@vectors[:, j]))
                   for j in range(k))
    return {'eigenvalues': values.tolist(), 'nodes': len(p), 'triangles': len(t),
            'free_nodes': len(interior), 'max_relative_residual': float(residual),
            'analytic_subspace_projection_scores': overlaps}


def numerical_gaps():
    polygon = np.array([[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]], float)
    seed = triangle.triangulate({'vertices': polygon, 'segments': np.array(
        [(i, (i+1) % len(polygon)) for i in range(len(polygon))])}, 'pq28a0.008')
    representations = defaultdict(list)
    for m in range(1, 9):
        for n in range(1, 9):
            if m*m+n*n <= 37:
                representations[m*m+n*n].append([m, n])
    families = {q: [(lambda p, m=m, n=n: np.sin(np.pi*m*p[:, 0])*np.sin(np.pi*n*p[:, 1]))
                    for m, n in reps] for q, reps in representations.items()}
    meshes = {}
    for level in (1, 2, 3, 4):
        start = time.monotonic()
        meshes[str(level)] = solve_with_overlaps(seed, level, 90, families)
        print(f'L-triomino: level {level}, 90 modes in {time.monotonic()-start:.1f}s', flush=True)
    for a, b in [('1', '2'), ('2', '3'), ('3', '4')]:
        assert np.all(np.array(meshes[b]['eigenvalues']) <=
                      np.array(meshes[a]['eigenvalues'])*(1+1e-9))
    anchors = []
    for q, reps in sorted(representations.items()):
        clusters = {}
        for level, mesh in meshes.items():
            scaled = np.array(mesh['eigenvalues'])/np.pi**2
            # Identify the known modes by mass-inner-product projection onto
            # their explicit eigenfunctions, rather than proximity to q.
            scores = np.array(mesh['analytic_subspace_projection_scores'][str(q)])
            nearest = sorted(range(len(scaled)), key=lambda i: -scores[i])[:len(reps)]
            nearest.sort()
            assert nearest == list(range(nearest[0], nearest[-1]+1))
            excluded = [i for i in range(len(scores)) if i not in nearest]
            clusters[level] = {'ranks': [i+1 for i in nearest],
                               'normalized_estimates': scaled[nearest].tolist(),
                               'max_distance': float(max(abs(scaled[nearest]-q))),
                               'minimum_selected_projection': float(min(scores[nearest])),
                               'maximum_excluded_projection': float(max(scores[excluded]))}
        anchors.append({'q': q, 'constructed_multiplicity': len(reps),
                        'representations': reps, 'clusters': clusters})
    gaps = []
    for left, right in zip(anchors, anchors[1:]):
        counts, ranks = {}, {}
        for level in meshes:
            a = max(left['clusters'][level]['ranks'])
            b = min(right['clusters'][level]['ranks'])
            counts[level] = b-a-1
            ranks[level] = list(range(a+1, b))
        # Only retain intervals whose anchor identification is consistent on
        # the two finest meshes; coarser counts remain in the public receipt.
        stable = (counts['3'] == counts['4'] and
                  left['clusters']['3']['ranks'] == left['clusters']['4']['ranks'] and
                  right['clusters']['3']['ranks'] == right['clusters']['4']['ranks'])
        fine = np.array(meshes['4']['eigenvalues'])/np.pi**2
        previous = np.array(meshes['3']['eigenvalues'])/np.pi**2
        ids = [r-1 for r in ranks['4']]
        interior_margin = min([min(fine[i]-left['q'], right['q']-fine[i]) for i in ids], default=None)
        strictly_between = all(left['q'] < fine[i] < right['q'] for i in ids)
        gaps.append({'left_q': left['q'], 'right_q': right['q'],
                     'counts_by_refinement': counts,
                     'anchor_ranks_stable_on_two_finest_meshes': stable,
                     'all_fine_interior_estimates_strictly_between': strictly_between,
                     'fine_interior_ranks': ranks['4'],
                     'fine_interior_normalized_estimates': fine[ids].tolist(),
                     'last_refinement_absolute_changes': abs(previous[ids]-fine[ids]).tolist(),
                     'fine_interior_endpoint_margin': interior_margin})
    print(json.dumps([{'gap': [g['left_q'], g['right_q']],
                       'counts': g['counts_by_refinement'],
                       'stable': g['anchor_ranks_stable_on_two_finest_meshes']}
                      for g in gaps], indent=2), flush=True)
    return {'normalization': 'lambda/pi^2', 'levels': [1, 2, 3, 4], 'modes_per_mesh': 90,
            'meshes': meshes, 'anchors': anchors, 'gaps': gaps,
            'proof_scope': 'Refinement-stable numerical gap counts. Endpoint clusters use the known constructed multiplicities and mass-inner-product projections onto explicit eigenfunctions. No certified continuum count, completeness of the arithmetic subset, or proof that another eigenvalue is non-algebraic.'}


def turtle_low_modes():
    polygon = np.sqrt(3)*tile(1/np.sqrt(3))
    seed = triangle.triangulate({'vertices': polygon, 'segments': np.array(
        [(i, (i+1) % len(polygon)) for i in range(len(polygon))])}, 'pq28a0.04')
    meshes = {str(level): solve(seed['vertices'], seed['triangles'], level,
                               boundary_edges=seed['segments']) for level in (1, 2, 3)}
    change = max(abs(a/b-1) for a, b in zip(meshes['2']['eigenvalues'], meshes['3']['eigenvalues']))
    assert abs(meshes['3']['mesh_area']-10*np.sqrt(3)) < 1e-10
    print(f'Turtle: first normalized mode {meshes["3"]["area_eigenvalues"][0]:.8f}', flush=True)
    return {'geometry': 'Tile(sqrt(3),1), natural side units', 'meshes': meshes,
            'last_refinement_relative_change': change,
            'proof_scope': 'Twelve conforming FEM estimates, not certified continuum enclosures.'}


def mode_figure(mirrors):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as PolygonPath
    B = np.array([[1, .5], [0, np.sqrt(3)/2]])
    BT = np.array([[np.sqrt(3)/2, 0], [.5, 1]])
    group = mirrors['group_axial_matrices']
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout='constrained')
    L = np.array([[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]], float)
    cases = [('L-triomino', L, None),
             ('Hat', np.array(mirrors['domains']['Hat']['lattice_vertices'])@B.T, B),
             ('Turtle', np.array(mirrors['domains']['Turtle']['lattice_vertices'])@BT.T, BT)]
    for ax, (name, polygon, basis) in zip(axes, cases):
        lo, hi = polygon.min(axis=0)-.05, polygon.max(axis=0)+.05
        xx, yy = np.meshgrid(np.linspace(lo[0], hi[0], 650), np.linspace(lo[1], hi[1], 650))
        points = np.column_stack([xx.ravel(), yy.ravel()])
        if basis is None:
            field = np.sin(np.pi*points[:, 0])*np.sin(np.pi*points[:, 1])
            label = r'$\lambda=2\pi^2$'
        else:
            field = np.zeros(len(points))
            for w in group:
                frequency = np.linalg.solve(basis.T, mv(dual(w), (3, 1)))
                field += det(w)*np.cos(2*np.pi*(points@frequency))
            label = r'$\lambda=(112/3)\pi^2$'
        field /= max(abs(field))
        mask = ~PolygonPath(polygon).contains_points(points)
        masked = np.ma.array(field.reshape(xx.shape), mask=mask.reshape(xx.shape))
        ax.imshow(masked, origin='lower', extent=[lo[0], hi[0], lo[1], hi[1]],
                  cmap='RdBu_r', vmin=-1, vmax=1, interpolation='nearest')
        closed = np.vstack([polygon, polygon[0]])
        ax.plot(closed[:, 0], closed[:, 1], color='#25353a', lw=1.2)
        ax.set_aspect('equal'); ax.axis('off'); ax.set_title(name+'\n'+label, fontsize=12)
    fig.savefig(ROOT/'exact-modes.png', dpi=180)
    plt.close(fig)


def main():
    mirrors = exact_mirrors()
    receipt = {'date': '2026-10-08',
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'shared_solver_sha256': hashlib.sha256((ROOT/'compute.py').read_bytes()).hexdigest(),
               'exact_mirror_checks': mirrors, 'L_triomino': numerical_gaps(),
               'Turtle_low_modes': turtle_low_modes()}
    (ROOT/'arithmetic-spectra.json').write_text(json.dumps(receipt, indent=2)+'\n')
    mode_figure(mirrors)


if __name__ == '__main__':
    main()
