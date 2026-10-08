#!/usr/bin/env python3
"""Exact character/orbit checks for short/long mixed Hat and Turtle problems.

These are deductions from the lattice mirrors, not an aperiodicity test.
The real mixed orbit sums use sine: their rotation character makes them odd
under inversion, so taking the cosine part would give zero identically.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import numpy as np
from arithmetic_spectra import mm, mv, dual, quadratic, exact_mirrors

ROOT = Path(__file__).resolve().parent


def basis(name):
    return np.array([[1., .5], [0., math.sqrt(3)/2]]) if name == 'Hat' else np.array(
        [[math.sqrt(3)/2, 0.], [.5, 1.]])


def characters(bc):
    # Group order: R^j followed by R^j S, j=0,...,5. Even j mirrors
    # carry short primitive edges in each tile's own triangular lattice.
    reflection_sign = -1 if bc == 'shortD' else 1
    return [(-1)**j for j in range(6)]+[reflection_sign*(-1)**j for j in range(6)]


def families(bc, maximum_q=80):
    group = exact_mirrors()['group_axial_matrices']
    signs = characters(bc)
    unique = defaultdict(dict)
    bound = math.ceil(math.sqrt(2*maximum_q))
    for m in range(-bound, bound+1):
        for n in range(-bound, bound+1):
            q = quadratic((m,n))
            if not 0 < q <= maximum_q:
                continue
            coefficients = defaultdict(int)
            for w, sign in zip(group, signs):
                coefficients[mv(dual(w),(m,n))] += sign
            coefficients = {k:c for k,c in coefficients.items() if c}
            if not coefficients:
                continue
            orbit = tuple(sorted(coefficients))
            assert all(quadratic(k) == q for k in orbit)
            unique[q].setdefault(orbit, {'representative': [m,n],
                                        'frequencies_axial': [list(k) for k in orbit],
                                        'coefficients': [coefficients[k] for k in orbit],
                                        'orbit_size': len(orbit)})
    return [{'q':q, 'normalized_value':16*q/3, 'constructed_multiplicity':len(orbits),
             'orbits':list(orbits.values())} for q,orbits in sorted(unique.items())]


def orbit_values(points, name, orbit, gradient=False):
    frequencies = np.linalg.solve(basis(name).T, np.array(orbit['frequencies_axial']).T).T
    coefficients = np.array(orbit['coefficients'])
    phase = 2*np.pi*np.asarray(points)@frequencies.T
    values = np.sin(phase)@coefficients
    if not gradient:
        return values
    derivatives = 2*np.pi*(np.cos(phase)*coefficients)@frequencies
    return values, derivatives


def main():
    exact = exact_mirrors()
    group = exact['group_axial_matrices']
    index = {tuple(tuple(row) for row in w):i for i,w in enumerate(group)}
    output = {'date':'2026-10-08', 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'integer_helpers_sha256':hashlib.sha256((ROOT/'arithmetic_spectra.py').read_bytes()).hexdigest(),
              'group_axial_matrices':group, 'assignments':{}, 'domains':{},
              'gluing_scope':'For placements x = w y + t with w in the displayed D6 and t in the domain lattice, character-signed restrictions are exactly the same smooth plane function. This is a compatibility theorem, not a reconstruction or verification of a tiling.'}
    for bc in ['shortD','longD']:
        signs = characters(bc)
        assert signs[0] == 1 and signs[3] == -1
        for i,a in enumerate(group):
            for j,b in enumerate(group):
                assert signs[index[mm(a,b)]] == signs[i]*signs[j]
        ladder = families(bc)
        assert ladder[0]['q'] == (1 if bc == 'shortD' else 3)
        output['assignments'][bc] = {'rotation_character':-1,
                                     'short_reflection_character':-1 if bc == 'shortD' else 1,
                                     'long_reflection_character':1 if bc == 'shortD' else -1,
                                     'group_character':signs, 'exact_ladder_to_q80':ladder}
    for name,d in exact['domains'].items():
        p = np.array(d['lattice_vertices'])@basis(name).T
        kinds = ['short' if quadratic((c['edge'][0],-c['edge'][1])) == 1 else 'long'
                 for c in d['boundary_checks']]
        # Norm in the primal lattice is a^2+ab+b^2, implemented explicitly.
        assert all((c['edge'][0]**2+c['edge'][0]*c['edge'][1]+c['edge'][1]**2 == (1 if kind == 'short' else 3))
                   for c,kind in zip(d['boundary_checks'],kinds))
        assert all((c['reflection_index'] % 2 == 0) == (kind == 'short')
                   for c,kind in zip(d['boundary_checks'],kinds))
        checks = {}
        for bc in ['shortD','longD']:
            trace, flux, covariance = 0., 0., 0.
            signs = characters(bc)
            for family in families(bc)[:3]:
                for orbit in family['orbits']:
                    for i,a in enumerate(p):
                        b = p[(i+1) % len(p)]
                        edge = b-a
                        normal = np.array([edge[1],-edge[0]])/np.linalg.norm(edge)
                        samples = np.array([a+f*edge for f in [.137,.413,.827]])
                        u, grad = orbit_values(samples,name,orbit,True)
                        condition = 'D' if (kinds[i] == 'short') == (bc == 'shortD') else 'N'
                        assert signs[6+d['boundary_checks'][i]['reflection_index']] == (-1 if condition == 'D' else 1)
                        if condition == 'D': trace = max(trace,float(np.max(abs(u))))
                        else: flux = max(flux,float(np.max(abs(grad@normal))))
                    samples = np.array([[.137,.413],[1.327,2.413],[-.827,3.781]])
                    u, grad = orbit_values(samples,name,orbit,True)
                    B = basis(name)
                    for i,w in enumerate(group):
                        W = B@np.array(w)@np.linalg.inv(B)
                        for translation in [(0,0),(1,2),(-2,1)]:
                            t = B@np.array(translation)
                            local = (samples-t)@W
                            other, gradient = orbit_values(local,name,orbit,True)
                            transported_gradient = signs[i]*gradient@W.T
                            covariance = max(covariance,float(np.max(abs(u-signs[i]*other))),
                                             float(np.max(abs(grad-transported_gradient))))
            assert max(trace,flux,covariance) < 1e-9
            checks[bc] = {'maximum_sample_D_trace':trace, 'maximum_sample_N_flux':flux,
                          'maximum_transport_value_and_gradient_discrepancy':covariance}
        output['domains'][name] = {'polygon':p.tolist(), 'lattice_basis':basis(name).tolist(),
                                   'edge_kinds':kinds, 'boundary_mirrors':d['boundary_checks'], 'sample_checks':checks}
    (ROOT/'mixed-reflections.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'first_q':{bc:d['exact_ladder_to_q80'][0]['q'] for bc,d in output['assignments'].items()},
                      'checks':{name:d['sample_checks'] for name,d in output['domains'].items()}},indent=2))


if __name__ == '__main__':
    main()
