#!/usr/bin/env python3
"""Retain and render numerical FEM eigenfunctions, with labeled operators.

Mixed L control: vertical Dirichlet, horizontal Neumann. Its explicit
sin/cos subset has coherent translation phases on the known chair lattice.
The other mixed modes are not claimed to glue on a tiling.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import scipy
import triangle
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
import matplotlib
matplotlib.use('Agg')
from matplotlib.tri import Triangulation
from PIL import Image
from compute import area, mesh, tile, triangulate
from mixed_reflections import orbit_values

ROOT = Path(__file__).resolve().parent
CELL, COLS = 320, 10


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_polygon(p, options):
    return triangle.triangulate({'vertices': p, 'segments': np.array(
        [(i, (i+1) % len(p)) for i in range(len(p))])}, options)


def matrices(seed, level):
    p, t, boundary = mesh(seed['vertices'], seed['triangles'], level, seed['segments'])
    v = p[t]
    det = ((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])-
           (v[:, 1, 1]-v[:, 0, 1])*(v[:, 2, 0]-v[:, 0, 0]))
    assert np.all(det > 1e-13)
    a = det/2
    g = np.stack((v[:, [1, 2, 0], 1]-v[:, [2, 0, 1], 1],
                  v[:, [2, 0, 1], 0]-v[:, [1, 2, 0], 0]), axis=2)/det[:, None, None]
    k = a[:, None, None]*np.einsum('tik,tjk->tij', g, g)
    m = a[:, None, None]/12*(np.ones((3, 3))+np.eye(3))
    rows, cols = np.repeat(t, 3, axis=1).ravel(), np.tile(t, (1, 3)).ravel()
    K = coo_matrix((k.ravel(), (rows, cols)), shape=(len(p), len(p))).tocsr()
    M = coo_matrix((m.ravel(), (rows, cols)), shape=(len(p), len(p))).tocsr()
    return p, t, boundary, K, M, float(a.sum())


def solve_modes(assembled, bc, count, polygon, boundary_types):
    p, t, boundary, Kfull, Mfull, domain_area = assembled
    if bc == 'N':
        fixed = np.array([], dtype=int)
    elif bc == 'D':
        fixed = boundary
    else:
        # Classify refined nodes against labeled primitive segments, including
        # any junction belonging to a D edge. Do not infer edge type from a
        # merged straight side's length.
        points = p[boundary]
        mask = np.zeros(len(boundary), dtype=bool)
        for i,a in enumerate(polygon):
            if boundary_types[i] != 'D': continue
            edge = polygon[(i+1) % len(polygon)]-a
            delta = points-a
            along = delta@edge/(edge@edge)
            distance = abs(delta[:,0]*edge[1]-delta[:,1]*edge[0])/np.linalg.norm(edge)
            mask |= (distance < 1e-9) & (along >= -1e-9) & (along <= 1+1e-9)
        fixed = boundary[mask]
        assert len(fixed) > 0
    free = np.setdiff1d(np.arange(len(p)), fixed)
    K, M = Kfull[free][:, free], Mfull[free][:, free]
    values, vectors = eigsh(K, k=count, M=M, sigma=-1e-5 if bc == 'N' else 0,
                            which='LM', tol=1e-10, v0=np.linspace(1, 2, len(free)))
    order = np.argsort(values)
    values, vectors = values[order], vectors[:, order]
    KV, MV = K@vectors, M@vectors
    residuals = np.linalg.norm(KV-MV*values, axis=0)/np.maximum(
        np.linalg.norm(KV, axis=0)+np.abs(values)*np.linalg.norm(MV, axis=0), 1e-30)
    orthogonality = float(np.max(np.abs(vectors.T@MV-np.eye(count))))
    assert orthogonality < 1e-8
    assert max(residuals[1:] if bc == 'N' else residuals) < 1e-7
    zero_check = None
    if bc == 'N':
        zero_check = {'computed_eigenvalue': float(values[0]),
                      'relative_constant_variation': float(np.ptp(vectors[:, 0])/np.max(np.abs(vectors[:, 0]))),
                      'absolute_weak_residual': float(np.linalg.norm(KV[:, 0]))}
        assert abs(values[0]) < 1e-7 and zero_check['relative_constant_variation'] < 1e-7
        values[0] = 0.0
        residuals[0] = 0.0  # Report the separate constant-mode check, not a relative 0/0.
    full = np.zeros((len(p), count))
    full[free] = vectors
    for j in range(count):
        if full[np.argmax(np.abs(full[:, j])), j] < 0:
            full[:, j] *= -1
    assert np.max(np.abs(full[fixed]), initial=0) == 0
    return values, full, {'nodes': len(p), 'triangles': len(t), 'free_nodes': len(free),
                          'fixed_nodes': len(fixed), 'area': domain_area,
                          'maximum_fixed_trace': float(np.max(np.abs(full[fixed]),initial=0)),
                          'max_mass_orthogonality_error': orthogonality,
                          'max_positive_relative_residual': float(max(residuals[1:] if bc == 'N' else residuals)),
                          'constant_mode_check': zero_check}, free, M, residuals


def exact_matches(p, vectors, free, M, values, bc):
    families = defaultdict(list)
    for m in range(0 if bc == 'N' else 1, 9):
        for n in range(1 if bc == 'D' else 0, 9):
            q = m*m+n*n
            if q <= 30 and q+0.5 < values[-1]/np.pi**2:
                families[q].append((m, n))
    matches = {}
    checks = []
    for q, reps in sorted(families.items()):
        basis = []
        for m, n in reps:
            x = np.cos(np.pi*m*p[free, 0]) if bc == 'N' else np.sin(np.pi*m*p[free, 0])
            y = np.sin(np.pi*n*p[free, 1]) if bc == 'D' else np.cos(np.pi*n*p[free, 1])
            basis.append(x*y)
        basis = np.column_stack(basis)
        gram = basis.T@(M@basis)
        coefficients = basis.T@(M@vectors[free])
        scores = np.sum(coefficients*np.linalg.solve(gram, coefficients), axis=0)
        selected = sorted(np.argsort(scores)[-len(reps):].tolist())
        check = {'q': q, 'representations': reps, 'constructed_multiplicity': len(reps),
                 'selected_indices': selected, 'minimum_projection': float(min(scores[selected])),
                 'max_normalized_distance': float(max(abs(values[selected]/np.pi**2-q)))}
        check['identified'] = check['minimum_projection'] > .95 and check['max_normalized_distance'] < .2
        if check['identified']:
            for j in selected:
                assert j not in matches
                matches[j] = {**check, 'projection': float(scores[j])}
        checks.append(check)
    return matches, checks


def reflection_matches(p, vectors, free, M, values, name, bc, exact):
    matches, checks = {}, []
    for family in exact['assignments'][bc]['exact_ladder_to_q80']:
        target = family['normalized_value']
        if target+0.2 >= values[-1]/np.pi**2: continue
        functions = [orbit_values(p[free],name,orbit) for orbit in family['orbits']]
        basis = np.column_stack(functions)
        gram = basis.T@(M@basis)
        coefficients = basis.T@(M@vectors[free])
        scores = np.sum(coefficients*np.linalg.solve(gram,coefficients),axis=0)
        selected = sorted(np.argsort(scores)[-len(functions):].tolist())
        distance = float(max(abs(values[selected]/np.pi**2-target)))
        check = {'family':'mixed_reflection', 'q':family['q'], 'normalized_value':target,
                 'constructed_multiplicity':len(functions), 'orbits':family['orbits'],
                 'selected_indices':selected, 'minimum_projection':float(min(scores[selected])),
                 'max_normalized_distance':distance,
                 'identified':float(min(scores[selected])) > .95 and distance < .2}
        check['nearby_candidates'] = [
            {'index':int(j),'rank':int(j)+1,'normalized_estimate':float(values[j]/np.pi**2),'projection':float(scores[j])}
            for j in np.argsort(scores)[::-1][:8]
            if scores[j] > .01 and abs(values[j]/np.pi**2-target) < 1]
        checks.append(check)
        if check['identified']:
            for j in selected:
                assert j not in matches
                matches[j] = {**check,'projection':float(scores[j])}
    return matches, checks


def pixel_sampler(p, t, polygon):
    low, high = polygon.min(axis=0), polygon.max(axis=0)
    center = (low+high)/2
    side = max(high-low)*1.12
    xmin, ymin = center-side/2
    xmax, ymax = center+side/2
    x = np.linspace(xmin, xmax, CELL)
    y = np.linspace(ymax, ymin, CELL)
    X, Y = np.meshgrid(x, y)
    tr = Triangulation(p[:, 0], p[:, 1], t)
    ids = tr.get_trifinder()(X.ravel(), Y.ravel())
    inside = ids >= 0
    vertices = t[ids[inside]]
    points = np.column_stack((X.ravel()[inside], Y.ravel()[inside]))
    a, b, c = p[vertices[:, 0]], p[vertices[:, 1]], p[vertices[:, 2]]
    det = (b[:, 0]-a[:, 0])*(c[:, 1]-a[:, 1])-(b[:, 1]-a[:, 1])*(c[:, 0]-a[:, 0])
    w1 = ((points[:, 0]-a[:, 0])*(c[:, 1]-a[:, 1])-(points[:, 1]-a[:, 1])*(c[:, 0]-a[:, 0]))/det
    w2 = ((b[:, 0]-a[:, 0])*(points[:, 1]-a[:, 1])-(b[:, 1]-a[:, 1])*(points[:, 0]-a[:, 0]))/det
    weights = np.column_stack((1-w1-w2, w1, w2))
    assert np.min(weights) > -1e-8 and np.max(abs(weights.sum(axis=1)-1)) < 1e-12
    return inside, vertices, weights, [float(xmin), float(ymin), float(xmax), float(ymax)]


def write_atlas(identifier, vectors, sampler):
    inside, vertices, weights, bbox = sampler
    cols = min(COLS, vectors.shape[1])
    rows = (vectors.shape[1]+cols-1)//cols
    atlas = Image.new('RGBA', (cols*CELL, rows*CELL))
    peaks = np.max(np.abs(vectors), axis=0)
    cmap = matplotlib.colormaps['RdBu_r']
    pixel_hashes = []
    for j in range(vectors.shape[1]):
        z = np.sum(vectors[vertices, j]*weights, axis=1)/peaks[j]
        rgba = np.zeros((CELL*CELL, 4), dtype=np.uint8)
        rgba[inside] = (cmap((z+1)/2)*255).astype(np.uint8)
        rgba = rgba.reshape(CELL, CELL, 4)
        pixel_hashes.append(hashlib.sha256(rgba.tobytes()).hexdigest())
        atlas.paste(Image.fromarray(rgba), ((j % cols)*CELL, (j//cols)*CELL))
    path = ROOT/f'modes-{identifier}.png'
    atlas.save(path, optimize=True)
    return {'file': path.name, 'cell_size': CELL, 'columns': cols, 'rows': rows,
            'bbox': bbox, 'sha256': digest(path), 'cell_pixel_sha256': pixel_hashes}, peaks


def write_paged_atlas(identifier, vectors, sampler):
    """Bound image memory and download size with sixty-mode palette pages."""
    inside, vertices, weights, bbox = sampler
    peaks = np.max(np.abs(vectors),axis=0)
    colors = (matplotlib.colormaps['RdBu_r'].resampled(255)(np.linspace(0,1,255))*255).astype(np.uint8)
    lookup = np.vstack((np.zeros((1,4),dtype=np.uint8),colors))
    palette = lookup[:,:3].ravel().tolist()
    pages, hashes = [], []
    for start in range(0,vectors.shape[1],60):
        count = min(60,vectors.shape[1]-start)
        rows = (count+COLS-1)//COLS
        atlas = Image.new('P',(COLS*CELL,rows*CELL),0)
        atlas.putpalette(palette)
        for local,j in enumerate(range(start,start+count)):
            z = np.sum(vectors[vertices,j]*weights,axis=1)/peaks[j]
            indices = np.zeros(CELL*CELL,dtype=np.uint8)
            indices[inside] = 1+np.minimum(254, np.floor(np.clip((z+1)/2,0,1)*255)).astype(np.uint8)
            hashes.append(hashlib.sha256(lookup[indices].reshape(CELL,CELL,4).tobytes()).hexdigest())
            cell = Image.fromarray(indices.reshape(CELL,CELL)).convert('P')
            cell.putpalette(palette)
            atlas.paste(cell,((local % COLS)*CELL,(local//COLS)*CELL))
        path = ROOT/f'modes-{identifier}-{start//60}.png'
        atlas.save(path,optimize=True,transparency=0)
        pages.append({'file':path.name,'start_index':start,'mode_count':count,'rows':rows,'sha256':digest(path)})
    return {**pages[0], 'cell_size':CELL,'columns':COLS,'bbox':bbox,'pages':pages,
            'color_levels':255,'cell_pixel_sha256':hashes}, peaks


def main():
    original = json.loads((ROOT/'results.json').read_text())
    arithmetic = json.loads((ROOT/'arithmetic-spectra.json').read_text())
    reflection = json.loads((ROOT/'mixed-reflections.json').read_text())
    L = np.array([[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]], float)
    base = tile(1)
    quality = seed_polygon(base, 'pq28a0.025')
    weights = np.zeros((len(quality['vertices']), len(base)))
    located = np.zeros(len(weights), dtype=bool)
    for ids in triangulate(base):
        bary = np.linalg.solve(np.vstack((base[ids].T, np.ones(3))),
                               np.vstack((quality['vertices'].T, np.ones(len(weights))))).T
        select = (~located)&np.all(bary >= -1e-9, axis=1)
        weights[np.ix_(select, ids)] = bary[select]
        located[select] = True
    assert np.all(located)
    domains = []
    for identifier, label, polygon, seed, level, count, reference in [
        ('L', 'L-triomino', L, seed_polygon(L, 'pq28a0.008'), 4, 90, arithmetic['L_triomino']['meshes']['4']),
        ('hat', 'Hat', tile(np.sqrt(3)), {**quality, 'vertices': weights@tile(np.sqrt(3))}, 4, 12,
         min(original['cases'], key=lambda c: abs(c['r']-np.sqrt(3)))['meshes']['3']),
        ('turtle', 'Turtle', np.sqrt(3)*tile(1/np.sqrt(3)), seed_polygon(np.sqrt(3)*tile(1/np.sqrt(3)), 'pq28a0.04'), 3, 12,
         arithmetic['Turtle_low_modes']['meshes']['3']),
        ('equilateral', 'Equilateral polygon', base, quality, 3, 12,
         min(original['cases'], key=lambda c: abs(c['r']-1))['meshes']['3'])]:
        start = time.monotonic()
        fine, prior = matrices(seed, level), matrices(seed, level-1)
        edge_kinds = None
        if identifier in ['hat','turtle']:
            edge_kinds = reflection['domains'][label]['edge_kinds']
            polygon = np.array(reflection['domains'][label]['polygon'])
        sampler = pixel_sampler(fine[0], fine[1], polygon)
        domain = {'id': identifier, 'label': label, 'polygon': polygon.tolist(), 'area': area(polygon), 'spectra': []}
        if edge_kinds:
            domain['edge_kinds'] = edge_kinds
            domain['lattice_basis'] = reflection['domains'][label]['lattice_basis']
        operators = ['D','N','mixed'] if identifier == 'L' else ['D','N','shortD','longD'] if edge_kinds else ['D']
        for bc in operators:
            mode_count = 240 if bc in ['shortD','longD'] else count
            boundary = [('D' if bc == 'D' else 'N') if bc in ['D','N'] else
                        ('D' if abs(polygon[(i+1) % len(polygon),0]-p[0]) < 1e-12 else 'N') if bc == 'mixed' else
                        ('D' if (edge_kinds[i] == 'short') == (bc == 'shortD') else 'N')
                        for i,p in enumerate(polygon)]
            values, vectors, checks, free, mass, residuals = solve_modes(fine, bc, mode_count, polygon, boundary)
            previous, prior_vectors, _, prior_free, prior_mass, _ = solve_modes(prior, bc, mode_count, polygon, boundary)
            assert np.all(values <= previous+1e-7)
            reference_error = None
            if bc == 'D':
                reproduced = previous if identifier == 'hat' else values
                reference_error = float(np.max(np.abs(reproduced/np.array(reference['eigenvalues'])-1)))
                assert reference_error < 3e-8, (identifier, reference_error)
            matches, exact_checks = exact_matches(fine[0], vectors, free, mass, values, bc) if identifier == 'L' else ({}, [])
            if bc in ['shortD','longD']:
                matches, exact_checks = reflection_matches(fine[0],vectors,free,mass,values,label,bc,reflection)
                _, prior_checks = reflection_matches(prior[0],prior_vectors,prior_free,prior_mass,previous,label,bc,reflection)
                prior_by_q = {c['q']:c for c in prior_checks}
                for c in exact_checks:
                    if c['q'] in prior_by_q:
                        c['previous_mesh'] = prior_by_q[c['q']]
            del prior_vectors
            if identifier == 'L' and bc == 'D':
                # Preserve the established projection-based anchor identification through q=37.
                for anchor in arithmetic['L_triomino']['anchors']:
                    for rank in anchor['clusters']['4']['ranks']:
                        matches[rank-1] = {'q': anchor['q'], 'constructed_multiplicity': anchor['constructed_multiplicity'],
                                           'representations': anchor['representations'],
                                           'projection': arithmetic['L_triomino']['meshes']['4']['analytic_subspace_projection_scores'][str(anchor['q'])][rank-1]}
            atlas, peaks = (write_paged_atlas if edge_kinds and bc != 'D' else write_atlas)(identifier+'-'+bc, vectors, sampler)
            records = [{'index': j, 'rank': j+1, 'mode': j if bc == 'N' else j+1,
                        'value': float(value), 'previous_value': float(previous[j]),
                        'last_change': float(abs(previous[j]-value)), 'relative_residual': float(residuals[j]),
                        'mass_normalized_peak': float(peaks[j]), 'exact_family': matches.get(j)} for j, value in enumerate(values)]
            if bc in ['shortD','longD']:
                for c in exact_checks:
                    if c['identified']: continue
                    unresolved = [v for v in c['nearby_candidates'] if v['projection'] > .05]
                    for candidate in unresolved:
                        records[candidate['index']].setdefault('candidate_families',[]).append(
                            {'q':c['q'],'normalized_value':c['normalized_value'],'projection':candidate['projection'],
                             'candidate_ranks':[v['rank'] for v in unresolved]})
            domain['spectra'].append({'bc': bc, 'label': {'D': 'Dirichlet', 'N': 'Neumann', 'mixed': 'Mixed',
                                                       'shortD':'Short D / long N', 'longD':'Short N / long D'}[bc],
                                      'boundary_edges': boundary, 'fine_level': level, 'previous_level': level-1,
                                      'reference_level':level-1 if identifier == 'hat' else level,
                                      'checks': checks, 'reference_relative_difference': reference_error,
                                      'exact_family_checks': exact_checks, 'atlas': atlas, 'modes': records})
            print(f'{label} / {bc}: {mode_count} fields; first eigenvalue {values[0]:.9f}; exact matches {[(c["q"],c["minimum_projection"],c["identified"]) for c in exact_checks]}; elapsed {time.monotonic()-start:.1f}s', flush=True)
        domains.append(domain)
    Lspectra = domains[0]['spectra']
    ordered = {s['bc']: np.array([m['value'] for m in s['modes']]) for s in Lspectra}
    assert np.all(ordered['N'] <= ordered['mixed']+1e-7)
    assert np.all(ordered['mixed'] <= ordered['D']+1e-7)
    for domain in domains:
        if not domain.get('edge_kinds'): continue
        ordered = {s['bc']:np.array([m['value'] for m in s['modes']]) for s in domain['spectra']}
        for bc in ['shortD','longD']:
            assert np.all(ordered['N'] <= ordered[bc][:12]+1e-7)
            assert np.all(ordered[bc][:12] <= ordered['D']+1e-7)
    data = {'date': '2026-10-08', 'method': 'Conforming P1 FEM with consistent mass; nested midpoint refinement. Natural Neumann conditions in the weak form.',
            'mixed_partition': 'Hat and Turtle: both complementary short/long primitive-edge assignments. L-triomino control: D on vertical, N on horizontal. D/N junction vertices constrained by the Dirichlet trace.',
            'field_display': 'Piecewise-linear interpolation of computed eigenvectors, divided by each vector maximum absolute nodal value. Sign fixed by positive largest-magnitude node.',
            'gluing_scope': 'L: the explicit product family extends on the translation tiling. Hat/Turtle: mixed character orbit families have coherent transport for placements in their lattice semidirect D6. Generic mixed eigenfunctions are not claimed to glue.',
            'script_sha256': digest(Path(__file__)), 'shared_solver_sha256': digest(ROOT/'compute.py'),
            'input_sha256': {name: digest(ROOT/name) for name in ['results.json', 'arithmetic-spectra.json','mixed-reflections.json']},
            'mixed_helpers_sha256':digest(ROOT/'mixed_reflections.py'),
            'versions': {'numpy': np.__version__, 'scipy': scipy.__version__, 'triangle': triangle.__version__, 'matplotlib': matplotlib.__version__},
            'minmax_order_check': 'Neumann <= each mixed assignment <= Dirichlet on every shared ordered index: 90 for L and 12 for Hat/Turtle, counting the Neumann zero mode as the first entry.',
            'domains': domains, 'limitations': 'Numerical eigenvalues and fields, without certified continuum error bounds. Last refinement movement is not an error bound. Basis and sign are noncanonical in multiple eigenspaces.'}
    (ROOT/'mode-data.json').write_text(json.dumps(data, indent=2)+'\n')


if __name__ == '__main__':
    main()
