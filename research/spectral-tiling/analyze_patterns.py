#!/usr/bin/env python3
"""Compare constructed subspaces and check the new affine-reflection deductions.

Exact integer/rational identities support the proofs in the Notes. No new FEM
solve, continuum error enclosure, or algebraicity classifier is performed.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


def digest(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def mv(w, p):
    return tuple(sum(a*b for a, b in zip(row, p)) for row in w)


def mm(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)) for i in range(2))


def main():
    elementary = json.loads((ROOT/'elementary-modes.json').read_text())
    additional = json.loads((ROOT/'additional-tiles.json').read_text())
    numeric = json.loads((ROOT/'additional-mode-data.json').read_text())
    arithmetic = json.loads((ROOT/'arithmetic-spectra.json').read_text())
    domains = {d['id']: d for d in elementary['domains']+additional['domains']}
    densities = {}
    for name, denominator in [('hat', 192), ('turtle', 240), ('sphinx', 36), ('st-hexagon', 36)]:
        d = domains[name]
        p = (arithmetic['exact_mirror_checks']['domains'][name.capitalize()]['lattice_vertices']
             if name in ['hat', 'turtle'] else d['lattice_vertices'])
        if p:
            twice_area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(p, p[1:]+p[:1]))
            fraction = F(1, 6*twice_area)
            assert fraction == F(1, denominator)
            densities[name] = str(fraction)
    densities['L'] = '1/3'

    # The root-lattice basis in vertex-lattice coordinates. Its index is three.
    # Unit triangle side reflections, unlike all its median reflections, preserve
    # this larger period cell. Thus the full triangle basis can fit Sphinx/hexagon.
    C = ((2, -1), (-1, 2))
    inverse = ((F(2, 3), F(1, 3)), (F(1, 3), F(2, 3)))
    identity = ((1, 0), (0, 1))
    R, S = ((-1, -1), (1, 0)), ((1, 1), (0, -1))
    assert mm(mm(R, R), R) == identity and mm(S, S) == identity
    frequency_group = [identity, R, mm(R, R), S, mm(R, S), mm(mm(R, R), S)]
    expanded = {}
    for name in ['sphinx', 'st-hexagon']:
        d = domains[name]
        certificates = []
        for edge in d['boundary_certificates']:
            w = additional['group_axial_matrices'][edge['group_index']]
            root_w = mm(mm(inverse, w), C)
            assert all(x.denominator == 1 for row in root_w for x in row)
            (a, b), (c, e) = root_w
            determinant = a*e-b*c
            frequency_w = ((e/determinant, -c/determinant), (-b/determinant, a/determinant))
            assert frequency_w in frequency_group and determinant == -1
            translation = mv(inverse, edge['affine_translation'])
            assert all(x.denominator == 1 for x in translation)
            certificates.append({'group_index': edge['group_index'], 'root_lattice_translation': [int(x) for x in translation]})
        # A regular orbit gives two real functions; the singular Neumann orbit
        # also gives two. Each frequency has exactly the same quadratic norm.
        examples = []
        for bc, representative in [('D', (2, 1)), ('N', (1, 0))]:
            coefficients = {}
            for w in frequency_group:
                k = mv(w, representative)
                determinant = w[0][0]*w[1][1]-w[0][1]*w[1][0]
                coefficients[k] = coefficients.get(k, 0)+(determinant if bc == 'D' else 1)
            coefficients = {k: c for k, c in coefficients.items() if c}
            assert coefficients and set(coefficients).isdisjoint({(-m, -n) for m, n in coefficients})
            q = representative[0]**2+representative[0]*representative[1]+representative[1]**2
            assert all(m*m+m*n+n*n == q for m, n in coefficients)
            for w in frequency_group:
                sign = (w[0][0]*w[1][1]-w[0][1]*w[1][0]) if bc == 'D' else 1
                assert all(coefficients[mv(w, k)] == sign*c for k, c in coefficients.items())
            examples.append({'bc': bc, 'normalized_value': str(F(16*q, 9)), 'independent_real_functions': 2,
                             'frequency_orbit': [list(k) for k in coefficients]})
        expanded[name] = {'available_full_triangle_fraction': '1/6', 'edge_certificates': certificates,
                          'additional_exact_examples': examples,
                          'viewer_status': 'Not yet added to the interactive catalogue or numerically projected.'}

    # Exact quadratic-field multiplication for the irrational Penrose traces.
    def product(x, y, radicand):
        a, b = x; c, e = y
        return (a*c+radicand*b*e, a*e+b*c)
    penrose = {}
    for name, trace in [('penrose-thin', (F(-1, 2), F(1, 2))), ('penrose-thick', (F(-1, 2), F(-1, 2)))]:
        square = product(trace, trace, 5)
        assert (square[0]+trace[0]-1, square[1]+trace[1]) == (0, 0)
        assert trace[1] != 0
        penrose[name] = {'rotation_trace_in_Q_sqrt5': [str(x) for x in trace],
            'trace_minimal_polynomial': 'c^2+c-1',
            'proof': 'Doubled parallel-mirror translation T is a period. Rotated periods R^j T give integer a_j=k dot R^j T. The recurrence a_(j+2)+a_j=c a_(j+1) with irrational c forces all a_j=0, hence k=0.'}

    # AB horizontal/diagonal parallel mirrors give t1=(0,sqrt2), t2=(1,-1).
    # Twice either translation is a period for every choice of reflection signs.
    quarter_turn = ((0, -1), (1, 0))
    t2 = (2, -2)
    rotated = mv(quarter_turn, t2)
    assert rotated == (2, 2)
    assert tuple(a+b for a, b in zip(t2, rotated)) == (4, 0)
    assert tuple(b-a for a, b in zip(t2, rotated)) == (0, 4)

    comparison = []
    for d in numeric['domains'][:2]:
        D, N = d['spectra']
        comparison.append({'id': d['id'], 'area': d['area'], 'first_D_estimate': D['modes'][0]['value'],
                           'first_positive_N_estimate': N['modes'][1]['value']})
    assert abs(comparison[0]['area']-comparison[1]['area']) < 1e-12
    output = {'date': '2026-10-09', 'status': 'passed', 'script_sha256': digest('analyze_patterns.py'),
        'input_sha256': {name: digest(name) for name in ['elementary-modes.json', 'additional-tiles.json', 'additional-mode-data.json', 'arithmetic-spectra.json']},
        'catalogue_asymptotic_mode_fractions': densities, 'expanded_triangle_families': expanded,
        'penrose_affine_obstructions': penrose,
        'ammann_beenker_affine_obstruction': {'periods': ['(4,0)', '(0,4)', '(2 sqrt2,0)', '(0,2 sqrt2)'],
            'proof': 'Doubled parallel-mirror translations and their quarter-turn conjugates yield these periods. Incommensurate periods on each axis force a continuous global field to be constant.'},
        'equal_area_comparison': comparison,
        'limitations': 'The reflection proofs concern finite plane-wave Helmholtz functions with a fixed D/N type on each whole side. They do not classify eigenvalue algebraicity, encode matching rules, or prove an aperiodicity test. Mode fractions count constructed independent functions, not distinct values. Expanded triangle families are derived but not implemented in the viewer.'}
    (ROOT/'pattern-analysis.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'status': output['status'], 'catalogue_fractions': densities,
                      'expanded_triangle_families': list(expanded), 'affine_obstructions': list(penrose)+['ammann-beenker']}, indent=2))


if __name__ == '__main__':
    main()
