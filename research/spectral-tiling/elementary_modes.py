#!/usr/bin/env python3
"""Build exact elementary-cell modes before consulting the numerical spectrum.

The square catalogue is a truncated separated basis. The triangle catalogue
retains lattice-periodic scalar reflection sectors, not its entire spectrum.
No numerical eigenvalue is used to choose a frequency or boundary condition.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
from arithmetic_spectra import exact_mirrors, mv, dual, quadratic

ROOT = Path(__file__).resolve().parent


def triangle_modes(short_sign, long_sign, maximum_q=80):
    group = exact_mirrors()['group_axial_matrices']
    rotation_sign = short_sign*long_sign
    signs = [rotation_sign**j for j in range(6)]
    signs += [short_sign*rotation_sign**j for j in range(6)]
    # Inversion R^3 determines whether the real cosine or sine sum survives.
    trig = 'cos' if rotation_sign == 1 else 'sin'
    shells = defaultdict(dict)
    bound = math.ceil(math.sqrt(2*maximum_q))
    for m in range(-bound, bound+1):
        for n in range(-bound, bound+1):
            q = quadratic((m,n))
            if q > maximum_q: continue
            coefficients = defaultdict(int)
            for w,sign in zip(group,signs):
                coefficients[mv(dual(w),(m,n))] += sign
            coefficients = {k:c for k,c in coefficients.items() if c}
            if not coefficients: continue
            orbit = tuple(sorted(coefficients))
            assert all(quadratic(k) == q for k in orbit)
            divisor = math.gcd(*coefficients.values())
            coefficients = {k:c//divisor for k,c in coefficients.items()}
            shells[q].setdefault(orbit, {'q':q, 'trig':trig,
                'representative':[m,n], 'frequencies_axial':[list(k) for k in orbit],
                'coefficients':[coefficients[k] for k in orbit],
                'normalized_value':16*q/3})
    modes = []
    for q,orbits in sorted(shells.items()):
        for i,mode in enumerate(orbits.values()):
            modes.append({**mode, 'id':f'{q}:{i}', 'constructed_multiplicity':len(orbits)})
    return signs,modes


def main():
    mirrors = exact_mirrors()
    numerical = json.loads((ROOT/'mode-data.json').read_text())
    reflection_receipt = json.loads((ROOT/'mixed-reflections.json').read_text())
    domains = []
    for name in ['L','hat','turtle']:
        domain = next(d for d in numerical['domains'] if d['id'] == name)
        families = []
        if name == 'L':
            basis = [[1,0],[0,1]]
            source_polygon = [[0,0],[1,0],[1,1],[0,1]]
            for bc,x_kind,y_kind,label in [('D','sin','sin','Square: sine / sine'),
                ('mixed','sin','cos','Square: sine / cosine'),
                ('N','cos','cos','Square: cosine / cosine')]:
                modes = []
                for m in range(0 if x_kind == 'cos' else 1,7):
                    for n in range(0 if y_kind == 'cos' else 1,7):
                        q = m*m+n*n
                        if q <= 37:
                            modes.append({'id':f'{m}:{n}','m':m,'n':n,'q':q,
                                          'normalized_value':q,'x_kind':x_kind,'y_kind':y_kind})
                modes.sort(key=lambda mode:(mode['q'],mode['m'],mode['n']))
                counts = {q:sum(m['q'] == q for m in modes) for q in {m['q'] for m in modes}}
                for mode in modes: mode['constructed_multiplicity'] = counts[mode['q']]
                edges = ['D' if (abs(domain['polygon'][(i+1)%len(domain['polygon'])][0]-p[0]) < 1e-9
                                  and x_kind == 'sin') or
                                 (abs(domain['polygon'][(i+1)%len(domain['polygon'])][1]-p[1]) < 1e-9
                                  and y_kind == 'sin') else 'N'
                         for i,p in enumerate(domain['polygon'])]
                families.append({'bc':bc,'label':label,'source_kind':'square',
                    'source_boundary':['D' if y_kind == 'sin' else 'N','D' if x_kind == 'sin' else 'N']*2,
                    'boundary_edges':edges,'modes':modes})
        else:
            key = 'Hat' if name == 'hat' else 'Turtle'
            basis = reflection_receipt['domains'][key]['lattice_basis']
            source_polygon = [[0,0],[basis[0][0],basis[1][0]],[basis[0][1],basis[1][1]]]
            for bc,short_sign,long_sign,label in [
                ('shortD',-1,1,'Triangle: Dirichlet sides, even medians'),
                ('longD',1,-1,'Triangle: Neumann sides, odd medians'),
                ('D',-1,-1,'Triangle: Dirichlet sides, odd medians'),
                ('N',1,1,'Triangle: Neumann sides, even medians')]:
                signs,modes = triangle_modes(short_sign,long_sign)
                assert modes[0]['q'] == {'shortD':1,'longD':3,'D':7,'N':0}[bc]
                kinds = domain['edge_kinds']
                edges = ['D' if (short_sign if kind == 'short' else long_sign) == -1 else 'N' for kind in kinds]
                families.append({'bc':bc,'label':label,'source_kind':'triangle',
                    'source_boundary':['D' if short_sign == -1 else 'N']*3,
                    'median_boundary':'D' if long_sign == -1 else 'N',
                    'group_character':signs,'boundary_edges':edges,'modes':modes})
        domains.append({'id':name,'label':domain['label'],'area':domain['area'],
                        'polygon':domain['polygon'],'lattice_basis':basis,
                        'source_polygon':source_polygon,'families':families})
    output = {'date':'2026-10-08','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                       for name in ['arithmetic_spectra.py','mode-data.json','mixed-reflections.json']},
        'group_axial_matrices':mirrors['group_axial_matrices'],'domains':domains,
        'scope':'Exact frequencies and scalar reflection sectors are selected before numerical comparison. Square modes are complete on their source square as the cutoff increases. Triangle modes are a compatible lattice-periodic subset of the source triangle modes, not a complete triangle basis or tile spectrum.'}
    (ROOT/'elementary-modes.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'status':'generated','elementary_functions':sum(len(f['modes']) for d in domains for f in d['families'])},indent=2))


if __name__ == '__main__':
    main()
