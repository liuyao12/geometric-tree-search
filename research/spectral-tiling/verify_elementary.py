#!/usr/bin/env python3
"""Independent elementary-cell / tile boundary checks; no FEM eigensolve."""
from pathlib import Path
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary_certificates(domain,family,group,lattice_vertices=None):
    """Exact affine reflection proof, independent of sampled trace/flux values."""
    if family.get('constant_only'):
        assert all(c == 'N' for c in family['boundary_edges'])
        assert all(m['m'] == m['n'] == 0 for m in family['modes'])
        return [{'domain':'tile','edge_index':i,'proof':'constant gradient is zero'} for i in range(len(domain['polygon']))]
    if family['source_kind'] == 'square':
        certificates = []
        for name,polygon,conditions in [('source',domain['source_polygon'],family['source_boundary']),('tile',domain['polygon'],family['boundary_edges'])]:
            for i,p in enumerate(polygon):
                q = polygon[(i+1)%len(polygon)]
                axis = 0 if p[0] == q[0] else 1
                assert p[axis] == q[axis] and int(p[axis]) == p[axis]
                key = 'x_kind' if axis == 0 else 'y_kind'
                assert all(conditions[i] == ('D' if m[key] == 'sin' else 'N') for m in family['modes'])
                certificates.append({'domain':name,'edge_index':i,'axis':axis,'integer_coordinate':int(p[axis]),'condition':conditions[i]})
        return certificates
    def multiply(a,b):
        return [[sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    def apply(w,p):
        return [sum(w[i][j]*p[j] for j in range(2)) for i in range(2)]
    signs = family['group_character']
    for i,a in enumerate(group):
        for j,b in enumerate(group):
            assert signs[group.index(multiply(a,b))] == signs[i]*signs[j]
    certificates = []
    assert lattice_vertices is not None
    B = domain['lattice_basis']
    reconstructed = [[sum(B[i][j]*p[j] for j in range(2)) for i in range(2)] for p in lattice_vertices]
    assert all(math.dist(a,b) < 1e-12 for a,b in zip(reconstructed,domain['polygon']))
    source = [[0,0],[1,0],[0,1]]
    for name,vertices,conditions in [('tile',lattice_vertices,family['boundary_edges']),('source',source,family['source_boundary']),('median',source,[family['median_boundary']]*3)]:
        for i,p in enumerate(vertices):
            # Median directions are doubled to avoid fractional arithmetic.
            edge = [vertices[(i+1)%3][j]+vertices[(i+2)%3][j]-2*p[j] for j in range(2)] if name == 'median' else [vertices[(i+1)%len(vertices)][j]-p[j] for j in range(2)]
            candidates = [k for k in range(6,12) if apply(group[k],edge) == edge]
            assert len(candidates) == 1
            k = candidates[0]
            offset = [p[j]-apply(group[k],p)[j] for j in range(2)]
            assert all(isinstance(t,int) for t in offset)
            assert signs[k] == (-1 if conditions[i] == 'D' else 1)
            certificates.append({'domain':name,'edge_index':i,'group_index':k,'affine_translation':offset,'condition':conditions[i]})
    return certificates


def evaluate(domain,mode,x,y):
    if 'm' in mode:
        values,derivatives = [],[]
        for coordinate,n,kind in [(x,mode['m'],mode['x_kind']),(y,mode['n'],mode['y_kind'])]:
            phase = math.pi*n*coordinate
            values.append(math.sin(phase) if kind == 'sin' else math.cos(phase))
            derivatives.append(math.pi*n*(math.cos(phase) if kind == 'sin' else -math.sin(phase)))
        return values[0]*values[1],(derivatives[0]*values[1],values[0]*derivatives[1])
    (a,b),(c,d) = domain['lattice_basis']
    determinant = a*d-b*c
    u,dx,dy = 0.,0.,0.
    for (m,n),coefficient in zip(mode['frequencies_axial'],mode['coefficients']):
        kx,ky = (d*m-c*n)/determinant,(-b*m+a*n)/determinant
        assert abs(kx*kx+ky*ky-4*mode['q']/3) < 1e-9
        phase = 2*math.pi*(kx*x+ky*y)
        trig = math.sin(phase) if mode['trig'] == 'sin' else math.cos(phase)
        derivative = math.cos(phase) if mode['trig'] == 'sin' else -math.sin(phase)
        u += coefficient*trig
        dx += coefficient*2*math.pi*kx*derivative
        dy += coefficient*2*math.pi*ky*derivative
    return u,(dx,dy)


def main():
    data = json.loads((ROOT/'elementary-modes.json').read_text())
    assert data['script_sha256'] == digest(ROOT/'elementary_modes.py')
    for name,checksum in data['input_sha256'].items(): assert checksum == digest(ROOT/name)
    numeric = json.loads((ROOT/'mode-data.json').read_text())
    mixed = json.loads((ROOT/'mixed-reflections.json').read_text())
    group = data['group_axial_matrices']
    axial = json.loads((ROOT/'arithmetic-spectra.json').read_text())['exact_mirror_checks']['domains']
    certificates = {}
    maximum_trace,maximum_flux,nonzero_count = 0.,0.,0
    for domain in data['domains']:
        reference = next(d for d in numeric['domains'] if d['id'] == domain['id'])
        assert domain['polygon'] == reference['polygon']
        source = domain['source_polygon']
        lengths = [math.dist(p,source[(i+1)%len(source)]) for i,p in enumerate(source)]
        assert all(abs(length-1) < 1e-12 for length in lengths)
        for family in domain['families']:
            vertices = axial[domain['label']]['lattice_vertices'] if domain['id'] != 'L' else None
            certificates[domain['id']+':'+family['bc']] = boundary_certificates(domain,family,group,vertices)
            expected = next(s for s in reference['spectra'] if s['bc'] == family['bc'])
            assert family['boundary_edges'] == expected['boundary_edges']
            assert [m['normalized_value'] for m in family['modes']] == sorted(m['normalized_value'] for m in family['modes'])
            for mode in family['modes']:
                if 'm' in mode:
                    assert mode['q'] == mode['m']**2+mode['n']**2
                    assert mode['normalized_value'] == mode['q']
                else:
                    assert mode['normalized_value'] == 16*mode['q']/3
                    coefficients = {tuple(k):v for k,v in zip(mode['frequencies_axial'],mode['coefficients'])}
                    signs = family['group_character']
                    assert mode['trig'] == ('cos' if signs[3] == 1 else 'sin')
                    for i,w in enumerate(group):
                        (a,b),(c,d) = w
                        determinant = a*d-b*c
                        for (m,n),v in coefficients.items():
                            assert m*m-m*n+n*n == mode['q']
                            transformed = ((d*m-c*n)//determinant,(-b*m+a*n)//determinant)
                            assert coefficients[transformed] == signs[i]*v
                    if family['bc'] in ['shortD','longD']:
                        shell = next(f for f in mixed['assignments'][family['bc']]['exact_ladder_to_q80'] if f['q'] == mode['q'])
                        assert shell['constructed_multiplicity'] == mode['constructed_multiplicity']
                        assert any(o['frequencies_axial'] == mode['frequencies_axial'] for o in shell['orbits'])
                # Nonzero on the source is also checked; samples supplement
                # the exact independence of the finite Fourier frequencies.
                samples = [(sum(weights[i]*source[i][0] for i in range(len(source))),
                            sum(weights[i]*source[i][1] for i in range(len(source))))
                           for weights in ([[.137,.281,.582],[.319,.473,.208],[.421,.187,.392]] if len(source) == 3
                                           else [[.137,.281,.319,.263],[.193,.347,.211,.249],[.419,.131,.237,.213]])]
                assert max(abs(evaluate(domain,mode,x,y)[0]) for x,y in samples) > 1e-8
                nonzero_count += 1
                edges = []
                for polygon,conditions in [(source,family['source_boundary']),
                    (domain['polygon'],family['boundary_edges'])]:
                    edges += [(p,polygon[(i+1)%len(polygon)],conditions[i]) for i,p in enumerate(polygon)]
                if family['source_kind'] == 'triangle':
                    edges += [(p,[(source[(i+1)%3][j]+source[(i+2)%3][j])/2 for j in range(2)],family['median_boundary'])
                              for i,p in enumerate(source)]
                for p,q,condition in edges:
                    dx,dy = q[0]-p[0],q[1]-p[1]
                    length = math.hypot(dx,dy)
                    for f in [.137,.413,.827]:
                        u,gradient = evaluate(domain,mode,p[0]+f*dx,p[1]+f*dy)
                        flux = (dy*gradient[0]-dx*gradient[1])/length
                        if condition == 'D': maximum_trace = max(maximum_trace,abs(u))
                        else: maximum_flux = max(maximum_flux,abs(flux))
    assert maximum_trace < 1e-8 and maximum_flux < 1e-8
    page = (ROOT.parents[1]/'docs/projects/spectral-tiling-study.html').read_text()
    payload = re.search(r'<script id="elementary-data" type="application/json">(.*?)</script>',page,re.S)
    assert payload and json.loads(payload[1]) == data
    result = {'status':'passed','date':data['date'],'elementary_functions_checked':nonzero_count,
        'checks':['Source and input hashes; webpage payload equals exact catalogue',
                  'Exact affine mirror, integer phase and D/N parity certificate for every source edge, tile edge and triangle median',
                  'Unit square and equilateral source geometry; source traces and fluxes',
                  'Triangle median parity, exact frequency norms and integer covariance',
                  'Every induced tile edge condition agrees with the numerical operator',
                  'Mixed orbit subsets agree with the preceding exact receipt'],
        'boundary_certificates':certificates,
        'maximum_sample_D_trace':maximum_trace,'maximum_sample_N_flux':maximum_flux,
        'limitations':'Sample evaluations are floating diagnostics. The reflection identities establish the exact functions; neither the catalogue nor the numerical remainder is claimed to exhaust the tile spectrum.'}
    (ROOT/'elementary-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
