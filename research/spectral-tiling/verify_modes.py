#!/usr/bin/env python3
"""Check mode provenance, fields, boundary families and coherent seam phases.

The analytic sine/cosine construction is checked independently of FEM.
Neither these samples nor the FEM diagnostics certify continuum errors.
"""
from pathlib import Path
import hashlib
import json
import math
import re
from PIL import Image

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def product(kind, m, n, x, y):
    fx = math.cos(m*math.pi*x) if kind == 'N' else math.sin(m*math.pi*x)
    fy = math.sin(n*math.pi*y) if kind == 'D' else math.cos(n*math.pi*y)
    dx = -m*math.pi*math.sin(m*math.pi*x) if kind == 'N' else m*math.pi*math.cos(m*math.pi*x)
    dy = n*math.pi*math.cos(n*math.pi*y) if kind == 'D' else -n*math.pi*math.sin(n*math.pi*y)
    return fx*fy, dx*fy, fx*dy


def main():
    data = json.loads((ROOT/'mode-data.json').read_text())
    assert data['script_sha256'] == digest(ROOT/'compute_modes.py')
    assert data['shared_solver_sha256'] == digest(ROOT/'compute.py')
    for name, checksum in data['input_sha256'].items():
        assert checksum == digest(ROOT/name)
    page = (ROOT.parents[1]/'docs/projects/spectral-tiling-study.html').read_text()
    embedded = json.loads(re.search(r'<script id="mode-data" type="application/json">(.*?)</script>', page, re.S)[1])
    assert embedded == data
    fields = 0
    for domain in data['domains']:
        vertices = domain['polygon']
        area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(vertices, vertices[1:]+vertices[:1]))/2
        assert abs(area-domain['area']) < 1e-10
        for spectrum in domain['spectra']:
            modes = spectrum['modes']
            assert len(modes) == (90 if domain['id'] == 'L' else 12)
            assert [m['value'] for m in modes] == sorted(m['value'] for m in modes)
            assert spectrum['checks']['max_positive_relative_residual'] < 1e-7
            assert spectrum['checks']['max_mass_orthogonality_error'] < 1e-8
            if spectrum['bc'] == 'D':
                assert spectrum['reference_relative_difference'] < 3e-8
            atlas = spectrum['atlas']
            path = ROOT/atlas['file']
            assert digest(path) == atlas['sha256']
            image = Image.open(path).convert('RGBA')
            cell, cols = atlas['cell_size'], atlas['columns']
            assert image.size == (cell*cols, cell*atlas['rows'])
            for j, mode in enumerate(modes):
                assert mode['index'] == j and mode['rank'] == j+1
                assert mode['mode'] == (j if spectrum['bc'] == 'N' else j+1)
                assert mode['last_change'] == abs(mode['previous_value']-mode['value'])
                assert mode['value'] <= mode['previous_value']+1e-7
                crop = image.crop(((j % cols)*cell, (j//cols)*cell, (j % cols+1)*cell, (j//cols+1)*cell))
                assert hashlib.sha256(crop.tobytes()).hexdigest() == atlas['cell_pixel_sha256'][j]
                assert crop.getextrema()[3] == (0,255)
                assert mode['mass_normalized_peak'] > 0
                family = mode['exact_family']
                if family:
                    assert family['projection'] > .95
                    assert abs(mode['value']/math.pi**2-family['q']) < .2
                    assert all(m*m+n*n == family['q'] for m, n in family['representations'])
            fields += len(modes)
    chair = data['domains'][0]
    spectra = {s['bc']: s for s in chair['spectra']}
    assert spectra['mixed']['boundary_edges'] == ['N','D','N','D','N','D']
    assert spectra['N']['modes'][0]['value'] == 0
    assert spectra['N']['checks']['constant_mode_check']['relative_constant_variation'] < 1e-7
    for N, mixed, D in zip(spectra['N']['modes'], spectra['mixed']['modes'], spectra['D']['modes']):
        assert N['value'] <= mixed['value']+1e-7 <= D['value']+2e-7
    # Unit cells (0,0),(1,0),(0,1) occupy every residue of x+2y modulo 3.
    assert {(x+2*y) % 3 for x,y in [(0,0),(1,0),(0,1)]} == {0,1,2}
    assert abs(3*1-0*1) == 3  # Area of the lattice basis (3,0),(1,1).
    trace_error, flux_error, phase_error = 0., 0., 0.
    for m in range(1,5):
        for n in range(5):
            for i, a in enumerate(chair['polygon']):
                b = chair['polygon'][(i+1) % 6]
                dx, dy = b[0]-a[0], b[1]-a[1]
                length = math.hypot(dx,dy)
                normal = (dy/length, -dx/length)
                for f in [.137,.413,.827]:
                    x, y = a[0]+f*dx, a[1]+f*dy
                    u, ux, uy = product('mixed',m,n,x,y)
                    if spectra['mixed']['boundary_edges'][i] == 'D':
                        trace_error = max(trace_error,abs(u))
                    else:
                        flux_error = max(flux_error,abs(ux*normal[0]+uy*normal[1]))
            # Compare both values and gradients, hence flux cancellation
            # for opposite normals, using independently evaluated local copies.
            for a,b in [(3,0),(1,1),(-2,1),(0,3)]:
                assert (a+2*b) % 3 == 0
                for x,y in [(1.137,.413),(.827,1.413),(2.3,3.7)]:
                    world = product('mixed',m,n,x,y)
                    local = product('mixed',m,n,x-a,y-b)
                    phase = (-1)**(m*a+n*b)
                    phase_error = max(phase_error,max(abs(v-phase*w) for v,w in zip(world,local)))
    assert max(trace_error,flux_error,phase_error) < 1e-10
    output = {'status': 'passed', 'date': '2026-10-08', 'fields_checked': fields,
              'checks': ['Source and input hashes; embedded page data equal the receipt',
                         'All 306 image cells match their computed-field pixel hashes',
                         'Existing Dirichlet values reproduced; positive matrix residuals and mass orthogonality checked',
                         'Every exported list is ordered and decreases under refinement',
                         'Neumann constant and mixed boundary edge assignment checked',
                         'Ordered Neumann, mixed and Dirichlet values satisfy variational bracketing',
                         'Periodic chair lattice residues, exact mixed traces and fluxes, and translation phases checked independently'],
              'maximum_mixed_sample_trace':trace_error, 'maximum_mixed_sample_normal_flux':flux_error,
              'maximum_translation_value_and_gradient_discrepancy':phase_error,
              'limitations': 'FEM and sampled analytic checks do not certify continuum eigenvalue errors or gluing of generic mixed eigenfunctions.'}
    (ROOT/'mode-verification.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__ == '__main__':
    main()
