#!/usr/bin/env python3
"""Independent standard-library checks of the new notes' receipts and HTML.

These verify algebra, bookkeeping, numerical consistency, and publication
inputs, not continuum eigenvalue enclosures or non-algebraicity.
"""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parent
PAGE = ROOT.parents[1]/'docs/projects/spectral-tiling-study.html'


def main():
    data = json.loads((ROOT/'arithmetic-spectra.json').read_text())
    assert data['script_sha256'] == hashlib.sha256((ROOT/'arithmetic_spectra.py').read_bytes()).hexdigest()
    assert data['shared_solver_sha256'] == hashlib.sha256((ROOT/'compute.py').read_bytes()).hexdigest()
    exact = data['exact_mirror_checks']
    group = exact['group_axial_matrices']
    maximum_trace, maximum_flux = 0., 0.
    for name, domain in exact['domains'].items():
        vertices = domain['lattice_vertices']
        twice_area = sum(p[0]*q[1]-q[0]*p[1] for p, q in zip(vertices, vertices[1:]+vertices[:1]))
        assert twice_area == (32 if name == 'Hat' else 40)
        # Columns of the physical lattice basis, inverted explicitly here.
        a, b, c, d = ((1., .5, 0., math.sqrt(3)/2) if name == 'Hat'
                      else (math.sqrt(3)/2, 0., .5, 1.))
        determinant = a*d-b*c
        frequencies = []
        for w in group:
            wa, wb = w[0]; wc, wd = w[1]
            sign = wa*wd-wb*wc
            m, n = (wd*3-wc)/sign, (-wb*3+wa)/sign
            assert m*m-m*n+n*n == 7
            k = ((d*m-c*n)/determinant, (-b*m+a*n)/determinant)
            assert abs(sum(x*x for x in k)-28/3) < 1e-12
            frequencies.append((k, sign))
        assert len({k for k, sign in frequencies}) == 12
        for p, q in zip(vertices, vertices[1:]+vertices[:1]):
            ex, ey = q[0]-p[0], q[1]-p[1]
            tx, ty = a*ex+b*ey, c*ex+d*ey
            length = math.hypot(tx, ty)
            normal = (ty/length, -tx/length)
            for parameter in (.127, .413, .781):
                px, py = p[0]+parameter*ex, p[1]+parameter*ey
                x, y = a*px+b*py, c*px+d*py
                trace = sum(sign*math.cos(2*math.pi*(k[0]*x+k[1]*y)) for k, sign in frequencies)
                flux = sum(-2*math.pi*(k[0]*normal[0]+k[1]*normal[1])*
                           math.sin(2*math.pi*(k[0]*x+k[1]*y)) for k, sign in frequencies)
                maximum_trace = max(maximum_trace, abs(trace))
                maximum_flux = max(maximum_flux, abs(flux))
    assert maximum_trace < 1e-10 and maximum_flux < 1e-9
    control = data['L_triomino']
    anchors = {a['q']: a for a in control['anchors']}
    meshes = control['meshes']
    for level, mesh in meshes.items():
        assert len(mesh['eigenvalues']) == 90
        assert mesh['eigenvalues'] == sorted(mesh['eigenvalues'])
        assert mesh['max_relative_residual'] < 1e-7
        for q, anchor in anchors.items():
            expected = [(m, n) for m in range(1, 7) for n in range(1, 7) if m*m+n*n == q]
            assert len(expected) == anchor['constructed_multiplicity']
            scores = mesh['analytic_subspace_projection_scores'][str(q)]
            ranks = anchor['clusters'][level]['ranks']
            selected = sorted(range(1, 91), key=lambda r: -scores[r-1])[:len(expected)]
            assert sorted(selected) == ranks
    for g in control['gaps']:
        a, b = g['left_q'], g['right_q']
        for level, mesh in meshes.items():
            lo = max(anchors[a]['clusters'][level]['ranks'])
            hi = min(anchors[b]['clusters'][level]['ranks'])
            assert hi-lo-1 == g['counts_by_refinement'][level]
        for rank, value, change in zip(g['fine_interior_ranks'], g['fine_interior_normalized_estimates'], g['last_refinement_absolute_changes']):
            assert abs(value-meshes['4']['eigenvalues'][rank-1]/math.pi**2) < 1e-12
            assert abs(change-abs(meshes['3']['eigenvalues'][rank-1]/math.pi**2-value)) < 1e-12
    source = PAGE.read_text()
    payload = json.loads(re.search(r'<script id="gap-data" type="application/json">(.*?)</script>', source, re.S)[1])
    assert len(payload['gaps']) == 13
    ready = [g for g in payload['gaps'] if g['status'] == 'refinement-stable estimate']
    assert [g['counts_by_refinement']['4'] for g in ready] == [4, 4, 3, 3, 8, 0, 2, 8, 2, 4, 6]
    assert all(all(min(v-g['left_q'], g['right_q']-v) > c for v, c in zip(
        g['fine_interior_normalized_estimates'], g['last_refinement_absolute_changes'])) for g in ready)
    assert len(payload['gaps'])-len(ready) == 2
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.ids = []; self.targets = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if 'id' in attrs: self.ids.append(attrs['id'])
            for key in ('href', 'src'):
                if key in attrs: self.targets.append(attrs[key])
    links = Links(); links.feed(source)
    assert len(links.ids) == len(set(links.ids))
    for target in links.targets:
        if target.startswith('#'): assert target[1:] in links.ids, target
        elif not target.startswith(('https:', 'http:', 'data:')):
            assert (PAGE.parent/target.split('#')[0]).exists(), target
    output = {'status': 'passed', 'date': '2026-10-08',
              'checks': ['Executed script and shared solver hashes match',
                         'Hat and Turtle lattice areas checked independently',
                         'Regular orbit norm checked; sample Dirichlet traces and Neumann fluxes vanish',
                         'Every constructed L-triomino multiplicity and endpoint projection rank checked',
                         'Gap counts, estimates and refinement movements agree with ordered spectra',
                         'Eleven numerical estimates and two pending intervals rendered consistently',
                         'HTML anchors are unique and every local reference exists'],
              'maximum_sample_boundary_trace': maximum_trace,
              'maximum_sample_boundary_normal_derivative': maximum_flux,
              'limitations': 'Sample evaluations are numerical checks of the analytic proof. Continuum gap counts, unknown extra endpoint multiplicities and algebraicity outside the constructed families remain uncertified.'}
    (ROOT/'notes-verification.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
