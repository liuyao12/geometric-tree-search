#!/usr/bin/env python3
"""Compute D/N fields for six additional bare polygons on two nested meshes."""
from pathlib import Path
import json
import time
import numpy as np
from compute_modes import seed_polygon, matrices, solve_modes, pixel_sampler, write_paged_atlas, digest

ROOT = Path(__file__).resolve().parent


def matches(points,vectors,free,mass,values,family,basis):
    """Mass projection onto exact orbit spaces, with distance and rank checks."""
    results,checks = {},[]
    for q in sorted({m['q'] for m in family['modes'] if m['q'] and m['normalized_value']*np.pi**2 < values[-1]-.2*np.pi**2}):
        orbits = [m for m in family['modes'] if m['q'] == q]
        U = []
        for m in orbits:
            frequencies = np.linalg.solve(np.array(basis).T,np.array(m['frequencies_axial']).T).T
            U.append((getattr(np,m['trig'])(2*np.pi*points@frequencies.T)@np.array(m['coefficients']))[free])
        U = np.column_stack(U)
        gram = U.T@mass@U
        normalized = U@np.linalg.inv(np.linalg.cholesky(gram).T)
        scores = np.sum((normalized.T@mass@vectors[free])**2,axis=0)
        selected = np.argsort(scores)[-len(orbits):]
        target = 16*q/3
        projection = float(np.min(scores[selected]))
        distance = float(np.max(abs(values[selected]/np.pi**2-target)))
        passed = projection > .95 and distance < .2
        check = {'family':'triangle_reflection','q':q,'normalized_value':target,
            'constructed_multiplicity':len(orbits),'minimum_projection':projection,
            'max_normalized_distance':distance,'selected_indices':sorted(map(int,selected)),
            'identified':passed}
        checks.append(check)
        if passed:
            for j in selected:
                assert int(j) not in results
                results[int(j)] = {**check,'projection':float(scores[j])}
    return results,checks


def main():
    tiles = json.loads((ROOT/'additional-tiles.json').read_text())
    domains = []
    for d in tiles['domains']:
        start = time.monotonic()
        polygon = np.array(d['polygon'])
        # About 300 seed triangles, then 64-fold subdivision: adequate for
        # the exploratory low-mode atlas. Refinement movements are retained.
        seed = seed_polygon(polygon,f'pq28a{d["area"]/250:.12g}')
        fine,prior = matrices(seed,3),matrices(seed,2)
        sampler = pixel_sampler(fine[0],fine[1],polygon)
        domain = {k:d[k] for k in ['id','label','polygon','area','tiling_status','source_url']}
        domain['spectra'] = []
        for bc in ['D','N']:
            boundary = [bc]*len(polygon)
            values,vectors,checks,free,mass,residuals = solve_modes(fine,bc,60,polygon,boundary)
            previous,_,_,_,_,_ = solve_modes(prior,bc,60,polygon,boundary)
            assert np.all(values <= previous+1e-7)
            family = next((f for f in d['families'] if f['bc'] == bc and not f.get('constant_only')),None)
            matched,exact_checks = matches(fine[0],vectors,free,mass,values,family,d['lattice_basis']) if family else ({},[])
            atlas,peaks = write_paged_atlas(d['id']+'-'+bc,vectors,sampler)
            modes = [{'index':j,'rank':j+1,'mode':j if bc == 'N' else j+1,'value':float(v),
                'previous_value':float(previous[j]),'last_change':float(abs(previous[j]-v)),
                'relative_residual':float(residuals[j]),'mass_normalized_peak':float(peaks[j]),
                'exact_family':matched.get(j)} for j,v in enumerate(values)]
            domain['spectra'].append({'bc':bc,'label':'Dirichlet' if bc == 'D' else 'Neumann',
                'boundary_edges':boundary,'fine_level':3,'previous_level':2,'checks':checks,
                'atlas':atlas,'modes':modes,'exact_family_checks':exact_checks})
            print(f'{d["label"]} / {bc}: 60 fields, {checks["nodes"]} nodes; first {values[0]:.8f}; matches {[c["q"] for c in exact_checks if c["identified"]]}; {time.monotonic()-start:.1f}s',flush=True)
        assert np.all(np.array([m['value'] for m in domain['spectra'][1]['modes']]) <= np.array([m['value'] for m in domain['spectra'][0]['modes']])+1e-7)
        domains.append(domain)
    data = {'date':'2026-10-08','script_sha256':digest(Path(__file__)),
        'input_sha256':{name:digest(ROOT/name) for name in ['additional-tiles.json','compute_modes.py','compute.py']},
        'method':'Conforming P1 FEM with consistent mass, nested levels 2 and 3. Dirichlet trace imposed strongly; Neumann zero flux imposed naturally in the weak form.',
        'limitations':'Uncertified continuum estimates. The boundary operators do not encode the matching rules or select a tiling. Pointwise P1 normal derivatives need not vanish on Neumann edges.',
        'domains':domains}
    (ROOT/'additional-mode-data.json').write_text(json.dumps(data,indent=2)+'\n')


if __name__ == '__main__':
    main()
