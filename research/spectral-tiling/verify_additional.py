#!/usr/bin/env python3
"""Independent geometry, boundary parity, FEM receipt and rendered-field audit."""
from pathlib import Path
import hashlib
import json
import math
import re
from PIL import Image
from verify_elementary import evaluate, boundary_certificates

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tiles = json.loads((ROOT/'additional-tiles.json').read_text())
    numeric = json.loads((ROOT/'additional-mode-data.json').read_text())
    for data,script in [(tiles,'additional_tiles.py'),(numeric,'compute_additional_modes.py')]:
        assert data['script_sha256'] == digest(ROOT/script)
        for name,checksum in data['input_sha256'].items(): assert checksum == digest(ROOT/name)
    group = tiles['group_axial_matrices']
    certificates = {}
    max_trace,max_flux,functions,fields = 0.,0.,0,0
    for d in tiles['domains']:
        nd = next(n for n in numeric['domains'] if n['id'] == d['id'])
        assert d['polygon'] == nd['polygon'] and d['area'] == nd['area']
        p = d['polygon']
        area = sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))/2
        assert abs(area-d['area']) < 1e-12
        if d['id'] in ['sphinx','st-hexagon']: assert abs(area-3*math.sqrt(3)/2) < 1e-12
        if d['id'] == 'pinwheel': assert p == [[0,0],[2,0],[0,1]] and area == 1
        if d['id'].startswith('penrose') or d['id'] == 'ammann-beenker':
            assert all(abs(math.dist(a,b)-1) < 1e-12 for a,b in zip(p,p[1:]+p[:1]))
        for family in d['families']:
            certificates[d['id']+':'+family['bc']] = boundary_certificates(d,family,group,d['lattice_vertices'])
            s = next(s for s in nd['spectra'] if s['bc'] == family['bc'])
            assert family['boundary_edges'] == s['boundary_edges']
            for mode in family['modes']:
                if 'frequencies_axial' in mode:
                    coefficients = {tuple(k):v for k,v in zip(mode['frequencies_axial'],mode['coefficients'])}
                    for (m,n),v in coefficients.items():
                        assert m*m-m*n+n*n == mode['q']
                        for w,sign in zip(group,family['group_character']):
                            (a,b),(c,e) = w
                            det = a*e-b*c
                            k = ((e*m-c*n)//det,(-b*m+a*n)//det)
                            assert coefficients[k] == sign*v
                    assert mode['normalized_value'] == 16*mode['q']/3
                for polygon,conditions in [(p,family['boundary_edges']),(d['source_polygon'],family['source_boundary'])]:
                    for i,a in enumerate(polygon):
                        b = polygon[(i+1)%len(polygon)]
                        dx,dy = b[0]-a[0],b[1]-a[1]
                        for f in [.137,.413,.827]:
                            u,g = evaluate(d,mode,a[0]+f*dx,a[1]+f*dy)
                            flux = (dy*g[0]-dx*g[1])/math.hypot(dx,dy)
                            if conditions[i] == 'D': max_trace = max(max_trace,abs(u))
                            else: max_flux = max(max_flux,abs(flux))
                functions += 1
        for s in nd['spectra']:
            assert s['boundary_edges'] == [s['bc']]*len(p)
            assert s['checks']['maximum_fixed_trace'] == 0
            assert s['checks']['max_positive_relative_residual'] < 1e-7
            assert s['checks']['max_mass_orthogonality_error'] < 1e-8
            assert len(s['modes']) == 60 and s['fine_level'] == s['previous_level']+1
            assert [m['value'] for m in s['modes']] == sorted(m['value'] for m in s['modes'])
            atlas = s['atlas']
            pg = atlas['pages'][0]
            assert len(atlas['pages']) == 1 and pg['mode_count'] == 60
            path = ROOT/pg['file']
            assert digest(path) == pg['sha256']
            im = Image.open(path).convert('RGBA')
            cell,cols = atlas['cell_size'],atlas['columns']
            assert im.size == (cell*cols,cell*pg['rows'])
            for j,m in enumerate(s['modes']):
                assert m['index'] == j and m['rank'] == j+1 and m['mode'] == (j if s['bc'] == 'N' else j+1)
                assert m['value'] <= m['previous_value']+1e-7
                assert m['last_change'] == abs(m['value']-m['previous_value'])
                crop = im.crop(((j%cols)*cell,(j//cols)*cell,(j%cols+1)*cell,(j//cols+1)*cell))
                assert hashlib.sha256(crop.tobytes()).hexdigest() == atlas['cell_pixel_sha256'][j]
                assert crop.getextrema()[3] == (0,255)
                if m['exact_family']:
                    f = m['exact_family']
                    assert f['family'] == 'triangle_reflection' and f['projection'] > .95
                    assert abs(m['value']/math.pi**2-16*f['q']/3) < .2
                fields += 1
            if s['bc'] == 'N':
                assert s['modes'][0]['value'] == 0
                assert s['checks']['constant_mode_check']['relative_constant_variation'] < 1e-7
        assert all(n['value'] <= dmode['value']+1e-7 for n,dmode in zip(nd['spectra'][1]['modes'],nd['spectra'][0]['modes']))
    assert max_trace < 1e-8 and max_flux < 1e-8
    page = (ROOT.parents[1]/'docs/projects/spectral-tiling-study.html').read_text()
    for identifier,data in [('additional-elementary-data',tiles),('additional-mode-data',numeric)]:
        embedded = re.search(r'<script id="'+identifier+r'" type="application/json">(.*?)</script>',page,re.S)
        assert embedded and json.loads(embedded[1]) == data
    result = {'status':'passed','date':'2026-10-08','exact_functions_checked':functions,'numerical_fields_checked':fields,
        'boundary_certificates':certificates,'maximum_sample_D_trace':max_trace,'maximum_sample_N_flux':max_flux,
        'checks':['Input hashes and both webpage payloads','Polygon areas and unit-edge rhombi',
            'Exact affine reflection/parity certificates; integer frequency covariance; sampled boundary diagnostics',
            'Strong zero Dirichlet trace, natural Neumann operator, constant mode, matrix residual and mass orthogonality',
            'Nested refinement monotonicity and Neumann/Dirichlet minmax order','Every field image cell checksum'],
        'limitations':'No certified continuum error bounds. Neumann is imposed weakly; pointwise derivatives of P1 fields are not zero-flux certificates. Only the stated exact families are classified. Markings are not encoded in the new operators.'}
    (ROOT/'additional-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'boundary_certificates'},indent=2))


if __name__ == '__main__':
    main()
