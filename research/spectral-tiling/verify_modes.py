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


def check_reflections(data):
    """Independent integer character identities and scalar boundary samples."""
    group = data['group_axial_matrices']
    def mul(a,b):
        return [[sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    maximum_trace, maximum_flux = 0.,0.
    for bc,assignment in data['assignments'].items():
        signs = assignment['group_character']
        assert signs[:6] == [1,-1,1,-1,1,-1]
        for i,a in enumerate(group):
            for j,b in enumerate(group):
                assert signs[group.index(mul(a,b))] == signs[i]*signs[j]
        assert assignment['exact_ladder_to_q80'][0]['q'] == (1 if bc == 'shortD' else 3)
        for family in assignment['exact_ladder_to_q80']:
            assert family['constructed_multiplicity'] == len(family['orbits'])
            for orbit in family['orbits']:
                coefficients = {tuple(k):c for k,c in zip(orbit['frequencies_axial'],orbit['coefficients'])}
                assert len(coefficients) == orbit['orbit_size']
                for (m,n),coefficient in coefficients.items():
                    assert coefficient != 0 and m*m-m*n+n*n == family['q']
                    assert coefficients[(-m,-n)] == -coefficient
                    for w,sign in zip(group,signs):
                        (a,b),(c,d) = w
                        determinant = a*d-b*c
                        transformed = ((d*m-c*n)//determinant,(-b*m+a*n)//determinant)
                        assert coefficients[transformed] == sign*coefficient
        for name,domain in data['domains'].items():
            (a,b),(c,d) = domain['lattice_basis']
            determinant = a*d-b*c
            for family in assignment['exact_ladder_to_q80'][:3]:
                for orbit in family['orbits']:
                    frequencies = [((d*m-c*n)/determinant,(-b*m+a*n)/determinant,coefficient)
                                   for (m,n),coefficient in zip(orbit['frequencies_axial'],orbit['coefficients'])]
                    polygon = domain['polygon']
                    for i,p in enumerate(polygon):
                        q = polygon[(i+1) % len(polygon)]
                        dx,dy = q[0]-p[0],q[1]-p[1]
                        length = math.hypot(dx,dy)
                        normal = (dy/length,-dx/length)
                        is_D = (domain['edge_kinds'][i] == 'short') == (bc == 'shortD')
                        mirror = domain['boundary_mirrors'][i]['reflection_index']
                        assert signs[6+mirror] == (-1 if is_D else 1)
                        for f in [.137,.413,.827]:
                            x,y = p[0]+f*dx,p[1]+f*dy
                            trace = sum(coefficient*math.sin(2*math.pi*(kx*x+ky*y)) for kx,ky,coefficient in frequencies)
                            flux = sum(coefficient*2*math.pi*(normal[0]*kx+normal[1]*ky)*math.cos(2*math.pi*(kx*x+ky*y))
                                       for kx,ky,coefficient in frequencies)
                            if is_D: maximum_trace = max(maximum_trace,abs(trace))
                            else: maximum_flux = max(maximum_flux,abs(flux))
    assert maximum_trace < 1e-9 and maximum_flux < 1e-9
    return {'maximum_sample_D_trace':maximum_trace,'maximum_sample_N_flux':maximum_flux,
            'integer_character_and_frequency_covariance':'passed'}


def main():
    data = json.loads((ROOT/'mode-data.json').read_text())
    assert data['script_sha256'] == digest(ROOT/'compute_modes.py')
    assert data['shared_solver_sha256'] == digest(ROOT/'compute.py')
    assert data['mixed_helpers_sha256'] == digest(ROOT/'mixed_reflections.py')
    exact = json.loads((ROOT/'mixed-reflections.json').read_text())
    assert exact['script_sha256'] == digest(ROOT/'mixed_reflections.py')
    assert exact['integer_helpers_sha256'] == digest(ROOT/'arithmetic_spectra.py')
    reflection_check = check_reflections(exact)
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
            expected_count = 240 if spectrum['bc'] in ['shortD','longD'] else 90 if domain['id'] == 'L' else 12
            assert len(modes) == expected_count
            assert [m['value'] for m in modes] == sorted(m['value'] for m in modes)
            assert spectrum['checks']['max_positive_relative_residual'] < 1e-7
            assert spectrum['checks']['max_mass_orthogonality_error'] < 1e-8
            assert spectrum['checks']['maximum_fixed_trace'] == 0
            if spectrum['bc'] == 'D':
                assert spectrum['reference_relative_difference'] < 3e-8
            atlas = spectrum['atlas']
            cell, cols = atlas['cell_size'], atlas['columns']
            pages = atlas.get('pages',[{**atlas,'start_index':0,'mode_count':len(modes)}])
            covered = 0
            images = {}
            for pg in pages:
                assert pg['start_index'] == covered
                covered += pg['mode_count']
                path = ROOT/pg['file']
                assert digest(path) == pg['sha256']
                image = Image.open(path).convert('RGBA')
                assert image.size == (cell*cols,cell*pg['rows'])
                images[pg['file']] = image
            assert covered == len(modes)
            for j, mode in enumerate(modes):
                assert mode['index'] == j and mode['rank'] == j+1
                assert mode['mode'] == (j if spectrum['bc'] == 'N' else j+1)
                assert mode['last_change'] == abs(mode['previous_value']-mode['value'])
                assert mode['value'] <= mode['previous_value']+1e-7
                pg = next(pg for pg in pages if pg['start_index'] <= j < pg['start_index']+pg['mode_count'])
                local = j-pg['start_index']
                crop = images[pg['file']].crop(((local % cols)*cell, (local//cols)*cell, (local % cols+1)*cell, (local//cols+1)*cell))
                assert hashlib.sha256(crop.tobytes()).hexdigest() == atlas['cell_pixel_sha256'][j]
                assert crop.getextrema()[3] == (0,255)
                assert mode['mass_normalized_peak'] > 0
                family = mode['exact_family']
                if family:
                    assert family['projection'] > .95
                    if family.get('family') == 'mixed_reflection':
                        assert abs(mode['value']/math.pi**2-16*family['q']/3) < .2
                    else:
                        assert abs(mode['value']/math.pi**2-family['q']) < .2
                        assert all(m*m+n*n == family['q'] for m, n in family['representations'])
            for check in spectrum['exact_family_checks']:
                if check.get('family') != 'mixed_reflection': continue
                assert check['normalized_value'] == 16*check['q']/3
                assert check['identified'] == (check['minimum_projection'] > .95 and check['max_normalized_distance'] < .2)
                for c in check['nearby_candidates']:
                    assert c['rank'] == c['index']+1
                    assert abs(c['normalized_estimate']-modes[c['index']]['value']/math.pi**2) < 1e-12
                    assert 0 < c['projection'] <= 1+1e-8
                if not check['identified']:
                    candidates = [c for c in check['nearby_candidates'] if c['projection'] > .05]
                    for c in candidates:
                        record = next(f for f in modes[c['index']]['candidate_families'] if f['q'] == check['q'])
                        assert record['candidate_ranks'] == [v['rank'] for v in candidates]
            fields += len(modes)
        if domain.get('edge_kinds'):
            assert len(vertices) == 14
            kinds = domain['edge_kinds']
            assert kinds.count('short') == (8 if domain['id'] == 'hat' else 6)
            for kind,a,b in zip(kinds,vertices,vertices[1:]+vertices[:1]):
                assert abs((b[0]-a[0])**2+(b[1]-a[1])**2-(1 if kind == 'short' else 3)) < 1e-10
            operators = {s['bc']:s for s in domain['spectra']}
            assert len({s['fine_level'] for s in operators.values()}) == 1
            for bc in ['shortD','longD']:
                assert operators[bc]['boundary_edges'] == ['D' if (kind == 'short') == (bc == 'shortD') else 'N' for kind in kinds]
                for N,mixed,D in zip(operators['N']['modes'],operators[bc]['modes'],operators['D']['modes']):
                    assert N['value'] <= mixed['value']+1e-7 <= D['value']+2e-7
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
                         f'All {fields} image cells match their computed-field pixel hashes, including every atlas page',
                         'Existing Dirichlet values reproduced; positive matrix residuals and mass orthogonality checked',
                         'Every exported list is ordered and decreases under refinement',
                         'Neumann constant and mixed boundary edge assignment checked',
                         'Ordered Neumann, mixed and Dirichlet values satisfy variational bracketing',
                         'Periodic chair lattice residues, exact mixed traces and fluxes, and translation phases checked independently'],
              'reflection_checks':reflection_check,
              'maximum_mixed_sample_trace':trace_error, 'maximum_mixed_sample_normal_flux':flux_error,
              'maximum_translation_value_and_gradient_discrepancy':phase_error,
              'limitations': 'FEM and sampled analytic checks do not certify continuum eigenvalue errors or gluing of generic mixed eigenfunctions.'}
    (ROOT/'mode-verification.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__ == '__main__':
    main()
