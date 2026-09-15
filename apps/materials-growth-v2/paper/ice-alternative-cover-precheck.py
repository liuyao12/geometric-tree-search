"""Evaluate frozen markings on alternative covers of the same training atoms.

Both lanes use the identical training library, base motif and registered rotation.
The factorized lane allows the two ends to come from different observed motifs
of that same base. This changes the learned hypothesis; it is not sound pruning
of the original coupled marked model. Targets only supply evaluation witnesses.
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
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(coordinates, cover_path, dictionary_path, selection_path, portable_path, alternative_path, output):
    paths = [coordinates, cover_path, dictionary_path, selection_path]
    corpus, cover, dictionary, selection = [json.loads(Path(path).read_text()) for path in paths]
    library = json.loads(Path(portable_path).read_text())
    for key, path in zip(['coordinates', 'cover', 'dictionary', 'selection'], paths):
        assert library['sourceHashes'][key] == sha(path)
    cv_by = {r['id']: r for r in cover['results']}
    d_by = {r['id']: r for r in dictionary['configurations']}
    alternative = json.loads(Path(alternative_path).read_text())
    assert alternative['coverHash'] == sha(cover_path) and alternative['dictionaryHash'] == sha(dictionary_path)
    assert alternative['originalSelectionHash'] == sha(selection_path)
    s_by = {r['id']: r for r in alternative['results']}
    bases = {json.dumps([b['pairType'], b['componentSites']]): i for i, b in enumerate(library['baseMotifs'])}
    by_base = defaultdict(list); origins = defaultdict(set)
    for i, motif in enumerate(library['motifs']): by_base[motif['base']].append(i)
    for row in library['trainingRegistrations']:
        assert d_by[row['id']]['training']
        for selected in row['selected']: origins[selected['motif']].add(row['id'])
    assert set(origins) == set(range(len(library['motifs'])))
    stacks = {b: np.asarray([[m['vectors'] for m in library['motifs'][i]['cloudM']] for i in ids]) for b, ids in by_base.items()}
    start = time.monotonic(); results = []
    for c in corpus['configurations']:
        cid = c['id']; d = d_by[cid]
        if not d['training']: continue
        cv = cv_by[cid]; selected = s_by[cid]['selected']
        targets = {q['root']: p.cloud_value(q) for q in p.junction.junctions(c, cv, selected)}
        rows = []
        for edge in selected:
            occurrence = d['occurrences'][edge]
            ends = p.endpoints(occurrence, cv['components'], cv['componentPairs'][edge])
            base = bases.get(p.base_key(occurrence, ends)); accepted = [[], []]
            if base is not None:
                ids = by_base[base]; rotated = stacks[base] @ np.asarray(occurrence['rotationRow'])
                for side, (_, root) in enumerate(ends):
                    target = targets[root]
                    colors = [library['motifs'][i]['cloudM'][side]['colors'] for i in ids]
                    color_ok = np.asarray([[[a == b for b in target['colors']] for a in cc] for cc in colors])
                    distances = np.linalg.norm(rotated[:, side, :, None, :] - np.asarray(target['vectors'])[None, None, :, :], axis=3)
                    close = color_ok & (distances <= library['markingRadiusAngstrom'] + 1e-10)
                    possible = close.any(axis=1).all(axis=1) & close.any(axis=2).all(axis=1)
                    for j in np.flatnonzero(possible):
                        mi = ids[int(j)]
                        value = dict(vectors=rotated[j, side].tolist(), colors=colors[j])
                        fit = p.cloud.contains(value, target, library['markingRadiusAngstrom'])
                        if fit is not None: accepted[side].append(mi)
            coupled = sorted(set(accepted[0]) & set(accepted[1]))
            external = [[mi for mi in side if origins[mi] - {cid}] for side in accepted]
            rows.append(dict(edge=edge, base=base, roots=[root for _, root in ends],
                             endpointMatches=accepted, coupledMatches=coupled,
                             factorized=all(accepted), otherConfigurationFactorized=all(external)))
        row = dict(id=cid, training=d['training'], edges=len(rows),
                   coupledEdges=sum(bool(r['coupledMatches']) for r in rows),
                   factorizedEdges=sum(r['factorized'] for r in rows),
                   otherConfigurationEdges=sum(r['otherConfigurationFactorized'] for r in rows),
                   coupledComplete=all(r['coupledMatches'] for r in rows),
                   factorizedComplete=all(r['factorized'] for r in rows), registrations=rows)
        assert row['factorizedEdges'] >= row['coupledEdges']

        results.append(row)
        print(json.dumps({k:v for k,v in row.items() if k != 'registrations'}), flush=True)
    totals = {}
    for training in [True, False]:
        group = [r for r in results if r['training'] == training]
        totals['training' if training else 'developmental'] = dict(configurations=len(group),
            **{key:sum(r[key] for r in group) for key in ['edges','coupledEdges','factorizedEdges','otherConfigurationEdges','coupledComplete','factorizedComplete']})
    result = dict(scope=__doc__, alternativeCoverHash=sha(alternative_path), sourceHashes=library['sourceHashes'], portableHash=sha(portable_path),
                  codeHashes={name:sha(Path(__file__).with_name(name)) for name in ['ice-alternative-cover-precheck.py','ice-portable-pairs.py','portable-cloud-markings.py','ice-junction-clouds.py']},
                  summary=totals, results=results, seconds=time.monotonic()-start,
                  limits='Positive precheck against alternative covers of unchanged training coordinates. Fixed base poses, unchanged radii, no search or blind growth. Factorization admits previously unobserved endpoint combinations. Developmental data are not an independent final holdout.')
    with Path(output).open('x') as f: json.dump(result, f)
    print(json.dumps(totals), flush=True)

if __name__ == '__main__': run(*sys.argv[1:])

