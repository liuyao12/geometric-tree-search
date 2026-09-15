"""Frozen two-ended marking checks on already selected ice covers.

Use each occurrence's existing single registered pose, without refitting either
marking independently. A supplied geometric junction is a common-value witness;
it does not enter the learned library. Missing lifts remain unknown.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np

spec = importlib.util.spec_from_file_location('portable', Path(__file__).with_name('ice-portable-pairs.py'))
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def run(coordinates, cover_path, dictionary_path, selection_path, portable_path, output):
    raw = [Path(x).read_bytes() for x in [coordinates, cover_path, dictionary_path, selection_path]]
    corpus, cover, dictionary, selection = map(json.loads, raw)
    library_raw = Path(portable_path).read_bytes(); library = json.loads(library_raw)
    for k, r in zip(['coordinates', 'cover', 'dictionary', 'selection'], raw):
        assert library['sourceHashes'][k] == hashlib.sha256(r).hexdigest()
    cv_by = {r['id']: r for r in cover['results']}; d_by = {r['id']: r for r in dictionary['configurations']}
    s_by = {r['id']: r for r in selection['results']}
    base_ids = {json.dumps([b['pairType'], b['componentSites']]): i for i, b in enumerate(library['baseMotifs'])}
    by_base = defaultdict(list); origins = defaultdict(set)
    for i, motif in enumerate(library['motifs']): by_base[motif['base']].append(i)
    for r in library['trainingRegistrations']:
        for s in r['selected']: origins[s['motif']].add(r['id'])
    stacks = {b: np.asarray([[m['vectors'] for m in library['motifs'][i]['cloudM']] for i in ids]) for b, ids in by_base.items()}
    results = []; start = time.monotonic()
    for c in corpus['configurations']:
        cid = c['id']; d = d_by[cid]; cv = cv_by[cid]; selected = s_by[cid]['selected']
        queries = {q['root']: p.cloud_value(q) for q in p.junction.junctions(c, cv, selected)}
        rows = []
        for edge in selected:
            o = d['occurrences'][edge]; ends = p.endpoints(o, cv['components'], cv['componentPairs'][edge])
            bid = base_ids.get(p.base_key(o, ends)); matches = []
            if bid is not None:
                ids = by_base[bid]; targets = [queries[root] for _, root in ends]
                rotated = stacks[bid] @ np.asarray(o['rotationRow'])
                possible = np.ones(len(ids), dtype=bool)
                for side in range(2):
                    # Necessary color-aware neighbor existence bound; final fits
                    # still require a single bijection for each assignment.
                    colors = [library['motifs'][i]['cloudM'][side]['colors'] for i in ids]
                    color_ok = np.asarray([[[a == b for b in targets[side]['colors']] for a in cc] for cc in colors])
                    distances = np.linalg.norm(rotated[:, side, :, None, :] - np.asarray(targets[side]['vectors'])[None, None, :, :], axis=3)
                    close = color_ok & (distances <= library['markingRadiusAngstrom'] + 1e-10)
                    possible &= close.any(axis=1).all(axis=1) & close.any(axis=2).all(axis=1)
                for j in np.flatnonzero(possible):
                    mi = ids[int(j)]
                    fits = [p.cloud.contains({'vectors': rotated[j, side].tolist(), 'colors': library['motifs'][mi]['cloudM'][side]['colors']}, targets[side], library['markingRadiusAngstrom']) for side in range(2)]
                    if all(f is not None for f in fits): matches.append({'motif': mi, 'fits': fits})
            rows.append({'edge': edge, 'roots': [root for _, root in ends], 'matches': matches,
                         'otherConfigurationWitness': any(origins[m['motif']] - {cid} for m in matches)})
        r = {'id': cid, 'training': d['training'], 'edges': len(rows), 'matchedEdges': sum(bool(r['matches']) for r in rows),
             'otherConfigurationEdges': sum(r['otherConfigurationWitness'] for r in rows),
             'completeLift': all(r['matches'] for r in rows), 'registrations': rows}
        if d['training']: assert r['completeLift']
        results.append(r); print(json.dumps({k: v for k, v in r.items() if k != 'registrations'}), flush=True)
    out = {'scope': __doc__, 'portableHash': hashlib.sha256(library_raw).hexdigest(), 'sourceHashes': library['sourceHashes'],
           'codeHashes': {n: hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['ice-portable-precheck.py', 'ice-portable-pairs.py', 'portable-cloud-markings.py', 'ice-junction-clouds.py']},
           'results': results, 'seconds': time.monotonic() - start,
           'limits': 'Positive selected-cover precheck with observed common-value witnesses. Single existing base registration per occurrence, not exhaustive pose enumeration. No new tree search, independent holdout or blind-growth result.'}
    with Path(output).open('x') as f: json.dump(out, f)


if __name__ == '__main__': run(*sys.argv[1:])
