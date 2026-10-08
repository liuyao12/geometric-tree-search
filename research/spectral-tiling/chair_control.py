#!/usr/bin/env python3
"""Chair controls: exact lattice/parameter checks and planar FEM estimates.

The Chair44 label is supplied by the cited preprint, not by this computation.
No 3D eigenvalues or tiling-search labels are numerically inferred here.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json
import numpy as np
import triangle
from compute import invariants, solve

ROOT = Path(__file__).resolve().parent


def main():
    lattice_controls = {}
    for dimension in (2, 3):
        modulus = 2**dimension-1
        cells = [p for p in product((0, 1), repeat=dimension)
                 if p != (1,)*dimension]
        residues = [sum(2**j*x for j, x in enumerate(p)) % modulus
                    for p in cells]
        assert sorted(residues) == list(range(modulus))
        lattice_controls[str(dimension)] = {
            'cells': cells, 'modulus': modulus, 'residues': residues,
            'proof': 'Complete distinct residues: every integer cube belongs to exactly one translated chair.'}

    # At c_j=delta*j, 0<delta<=1, the only nontrivial angle condition is
    # i^2-2j^2 != delta^2*j^4/10000. Negative left sides cannot collide.
    # For positive left sides, a positive margin at delta=1 suffices.
    positive = [(i, j, Fraction(i*i-2*j*j)-Fraction(j**4, 10000))
                for i in range(1, 13) for j in range(1, 13)
                if i*i-2*j*j > 0]
    assert all(margin > 0 for _, _, margin in positive)
    assert not any(i*i == 2*j*j for i in range(1, 13) for j in range(1, 13))
    minimum = min(positive, key=lambda item: item[2])
    max_slope = Fraction(12, 100)
    assert max_slope < 1
    assert (1+max_slope**2)**2 < 2
    assert 63*max_slope**2 < 1
    assert Fraction(12, 10000) < Fraction(1, 100)
    # Sum of sixteen copies of each feature magnitude. Bump/dent volumes cancel.
    area_quadratic_bound = Fraction(4, 625)*Fraction(sum(j*j for j in range(1, 13)), 20000)
    assert area_quadratic_bound == Fraction(13, 62500)

    polygon = np.array([[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]], float)
    geometry = invariants(polygon)
    assert abs(geometry['area']-3) < 1e-12
    assert abs(geometry['perimeter']-8) < 1e-12
    assert abs(geometry['corner_heat_constant']-float(Fraction(5, 18))) < 1e-12
    seed = triangle.triangulate({'vertices': polygon, 'segments': np.array(
        [(i, (i+1) % len(polygon)) for i in range(len(polygon))])}, 'pq28a0.008')
    meshes = {str(level): solve(seed['vertices'], seed['triangles'], level,
                               boundary_edges=seed['segments']) for level in (1, 2, 3)}
    for lo, hi in (('1', '2'), ('2', '3')):
        assert np.all(np.array(meshes[hi]['eigenvalues']) <=
                      np.array(meshes[lo]['eigenvalues'])*(1+1e-9))
    refinement = max(abs(a/b-1) for a, b in zip(meshes['2']['eigenvalues'],
                                              meshes['3']['eigenvalues']))
    # This list uses approximate planar eigenvalues in the exact product formula.
    prism = sorted(v+float(np.pi**2*n*n) for v in meshes['3']['eigenvalues']
                   for n in range(1, 13))[:12]
    output = {
        'date': '2026-10-07',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'lattice_controls': lattice_controls,
        'chair44_parameter_check': {
            'source': 'https://arxiv.org/html/2609.19214v1',
            'source_section': 'Appendix E.6',
            'scaling': 'c_j=delta*j for every 0<delta<=1',
            'angle_positive_case_minimum_margin': str(minimum[2]),
            'minimum_margin_indices': list(minimum[:2]),
            'maximum_squared_slope_times_63': str(63*max_slope**2),
            'surface_excess_upper_bound_coefficient': str(area_quadratic_bound),
            'scope': 'Exact algebraic checks of the preprint parameter assumptions; no independent check of the tiling proof.'},
        'L_triomino': {
            'geometry': geometry, 'exact_corner_heat_constant': '5/18',
            'meshes': meshes, 'last_refinement_relative_change': refinement,
            'unit_height_prism_first_12_estimates': prism,
            'scope': 'Conforming P1 Dirichlet FEM estimates without certified continuum error bounds. Prism values use separation of variables.'}}
    (ROOT/'chair-control.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'lambda_1_estimate': meshes['3']['eigenvalues'][0],
                      'last_refinement_change': refinement,
                      'fine_nodes': meshes['3']['nodes'],
                      'angle_margin': str(minimum[2])}, indent=2))


if __name__ == '__main__':
    main()
