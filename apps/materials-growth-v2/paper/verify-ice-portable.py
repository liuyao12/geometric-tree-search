"""Independent numerical replay of exported ice markings and selected-cover lifts.

Does not import the exporter, prechecker, pose fitter or spanning-tree lift.
Uses saved permutations and direct residuals to verify every claimed witness.
"""
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path
import sys
import numpy as np
from ase.geometry import find_mic


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def proper(r):
    r = np.asarray(r); assert r.shape == (3, 3) and np.isfinite(r).all()
    assert np.max(np.abs(r.T @ r - np.eye(3))) < 1e-8 and abs(np.linalg.det(r) - 1) < 1e-8
    return r


def local_clouds(c, cover, selected):
    parts = cover['components']; pair = cover['componentPairs']; centers = []; vectors = []; labels = []; adjacency = [[] for _ in parts]
    for part in parts:
        ids = sorted(part, key=lambda i: (c['species'][i], i)); x = np.asarray(c['positions'])[ids]
        dx, _ = find_mic(x - x[0], c['cell'], pbc=True); x = x[0] + dx
        centers.append(x.mean(axis=0)); vectors.append(x - x.mean(axis=0)); labels.append([c['species'][i] for i in ids])
    assert sorted(i for part in parts for i in part) == list(range(len(c['positions'])))
    assert len(set(selected)) == len(selected)
    totals = [0] * len(c['positions'])
    for e in selected:
        a, b = pair[e]; adjacency[a].append(b); adjacency[b].append(a)
        for i in parts[a] + parts[b]: totals[i] += 1
    assert all(t == 2 for t in totals) and all(len(a) == 2 for a in adjacency)
    out = {}
    for root, neighbors in enumerate(adjacency):
        neighbors = sorted(neighbors, key=lambda i: (labels[i], i))
        shift, _ = find_mic(np.asarray(centers)[neighbors] - centers[root], c['cell'], pbc=True)
        x = np.vstack([vectors[root], *[vectors[n] + v for n, v in zip(neighbors, shift)]])
        colors = [[0, s] for s in labels[root]] + [[1, s] for n in neighbors for s in labels[n]]
        out[root] = {'vectors': x, 'colors': colors}
    return out, np.asarray(centers)


def ends(o, parts, pair):
    atoms = [o['ids'][i] for i in o['permutation']]
    return sorted((sorted(i for i, a in enumerate(atoms) if a in parts[root]), root) for root in pair)


def run(coordinates, cover_path, dictionary_path, selection_path, junction_path, portable_path, precheck_path, output):
    corpus, cover, dictionary, selection, junction, library, precheck = [json.loads(Path(p).read_text()) for p in [coordinates, cover_path, dictionary_path, selection_path, junction_path, portable_path, precheck_path]]
    assert precheck['portableHash'] == sha(portable_path) and library['junctionHash'] == sha(junction_path)
    for key, path in zip(['coordinates', 'cover', 'dictionary', 'selection'], [coordinates, cover_path, dictionary_path, selection_path]):
        assert library['sourceHashes'][key] == precheck['sourceHashes'][key] == sha(path)
    dc = {c['id']: c for c in dictionary['configurations']}; cv = {r['id']: r for r in cover['results']}; ss = {r['id']: r for r in selection['results']}
    jj = {r['id']: {q['root']: q for q in r['registrations']} for r in junction['results']}
    sources = {r['id']: r for r in library['trainingRegistrations']}
    checks = {r['id']: r for r in precheck['results']}
    assert set(checks) == {c['id'] for c in corpus['configurations']} and len(checks) == len(precheck['results'])
    origins = defaultdict(set); seen_motifs = set(); max_anchor = 0.; max_mark = 0.; fits_checked = 0; summary = Counter(); result_rows = []
    for row in library['trainingRegistrations']:
        for r in row['selected']: origins[r['motif']].add(row['id'])
    for motif in library['motifs']:
        assert set(motif) == {'base', 'cloudM'} and len(motif['cloudM']) == 2
        for m in motif['cloudM']: assert set(m) == {'vectors', 'colors'}
    for c in corpus['configurations']:
        cid = c['id']; d = dc[cid]; selected = ss[cid]['selected']; query, centers = local_clouds(c, cv[cid], selected)
        r = checks[cid]; assert r['training'] == d['training']
        assert len(r['registrations']) == len(selected) and {v['edge'] for v in r['registrations']} == set(selected)
        if d['training']:
            source = sources[cid]
            assert {x['edge'] for x in source['selected']} == set(selected) and len(source['selected']) == len(selected)
            for x in source['selected']:
                o = d['occurrences'][x['edge']]; ep = ends(o, cv[cid]['components'], cv[cid]['componentPairs'][x['edge']])
                assert x['roots'] == [root for _, root in ep]
                motif = library['motifs'][x['motif']]; base = library['baseMotifs'][motif['base']]; rotation = proper(o['rotationRow'])
                assert base['pairType'] == o['type'] and base['componentSites'] == [sites for sites, _ in ep]
                assert base['anchors'] == dictionary['types'][o['type']]['positions'] and base['t'] == [1] * len(o['ids'])
                assert base['species'] == dictionary['types'][o['type']]['species']
                placed = np.asarray(base['anchors']) @ rotation + o['translation']
                actual = np.asarray(c['positions'])[[o['ids'][j] for j in o['permutation']]]
                _, err = find_mic(placed - actual, c['cell'], pbc=True)
                assert max(err) <= library['positionToleranceAngstrom'] + 1e-8
                max_anchor = max(max_anchor, float(max(err)))
                for side, (sites, root) in enumerate(ep):
                    anchor = np.asarray(base['anchors'])[sites].mean(axis=0)
                    assert np.allclose(anchor, base['markAnchors'][side], atol=1e-12)
                    _, err = find_mic(anchor @ rotation + o['translation'] - centers[root], c['cell'], pbc=True)
                    assert float(err) <= library['positionToleranceAngstrom'] + 1e-8
                    src = jj[cid][root]; prototype = junction['templates'][src['template']]
                    expected = np.asarray(prototype['vectors']) @ proper(src['rotationRow'])
                    expected_colors = [[int(i != 0), label] for i, group in enumerate(prototype['groups']) for label in group]
                    m = motif['cloudM'][side]
                    assert m['colors'] == expected_colors
                    assert np.max(np.abs(np.asarray(m['vectors']) @ rotation - expected)) < 1e-8
                seen_motifs.add(x['motif'])
        matched = 0; other = 0
        for v in r['registrations']:
            edge = v['edge']; o = d['occurrences'][edge]; ep = ends(o, cv[cid]['components'], cv[cid]['componentPairs'][edge])
            assert v['roots'] == [root for _, root in ep]
            assert len({a['motif'] for a in v['matches']}) == len(v['matches'])
            matched += bool(v['matches']); other_here = False
            for match in v['matches']:
                motif = library['motifs'][match['motif']]; base = library['baseMotifs'][motif['base']]
                assert base['pairType'] == o['type'] and base['componentSites'] == [sites for sites, _ in ep]
                assert len(match['fits']) == 2
                rotation = proper(o['rotationRow'])
                for side, (_, root) in enumerate(ep):
                    m = motif['cloudM'][side]; fit = match['fits'][side]; target = query[root]; perm = fit['permutation']
                    assert sorted(perm) == list(range(len(m['vectors']))) and len(perm) == len(target['vectors'])
                    assert all(m['colors'][i] == target['colors'][j] for i, j in enumerate(perm))
                    error = float(np.linalg.norm(np.asarray(m['vectors']) @ rotation - target['vectors'][perm], axis=1).max())
                    assert abs(error - fit['maxResidual']) < 1e-8 and error <= library['markingRadiusAngstrom'] + 1e-8
                    max_mark = max(max_mark, error); fits_checked += 1
                other_here |= bool(origins[match['motif']] - {cid})
            assert other_here == v['otherConfigurationWitness']; other += other_here
        assert r['matchedEdges'] == matched and r['otherConfigurationEdges'] == other and r['completeLift'] == (matched == len(selected))
        if d['training']: assert r['completeLift']
        prefix = 'training' if d['training'] else 'development'
        summary[prefix + 'Edges'] += len(selected); summary[prefix + 'MatchedEdges'] += matched
        summary[prefix + 'CompleteCovers'] += r['completeLift']; summary[prefix + 'OtherConfigurationEdges'] += other
        result_rows.append({k: v for k, v in r.items() if k != 'registrations'})
    assert seen_motifs == set(range(len(library['motifs'])))
    out = {'scope': __doc__, 'portableHash': sha(portable_path), 'precheckHash': sha(precheck_path), 'sourceHashes': library['sourceHashes'],
           'sharedBaseMotifs': len(library['baseMotifs']), 'decoratedMotifs': len(library['motifs']), 'endpointFitsChecked': fits_checked,
           'maxAnchorResidualAngstrom': max_anchor, 'maxMarkResidualAngstrom': max_mark, 'counts': dict(summary), 'results': result_rows,
           'limits': 'Verifies claimed positive witnesses, not completeness of failed queries. Same saved base pose as earlier dictionary; no extra endpoint rotation. Training lifts do not establish transfer or successful search.'}
    with Path(output).open('x') as f: json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != 'results'}), flush=True)


if __name__ == '__main__': run(*sys.argv[1:])
