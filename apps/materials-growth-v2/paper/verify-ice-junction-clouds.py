"""Check saved junction registrations without the learner's fitting routine.

Reconstruct local vectors by independent atom-to-anchor minimum images, verify
proper rotations and component/species bijections, and recompute maximum errors.
Metadata are used only for post-hoc reporting, not registration.
"""
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from ase.geometry import find_mic


def run(coordinates, cover_path, dictionary_path, selection_path, learned_path, provenance_path, output):
    paths = [coordinates, cover_path, dictionary_path, selection_path]
    raw = [Path(p).read_bytes() for p in paths]
    corpus, cover, dictionary, selection = map(json.loads, raw)
    learned_raw = Path(learned_path).read_bytes(); learned = json.loads(learned_raw)
    for name, digest in learned['codeHashes'].items():
        assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() == digest
    for key, data in zip(['coordinates', 'cover', 'dictionary', 'selection'], raw):
        assert learned['sourceHashes'][key] == hashlib.sha256(data).hexdigest()
    configs = {r['id']: r for r in corpus['configurations']}
    covers = {r['id']: r for r in cover['results']}
    dictionaries = {r['id']: r for r in dictionary['configurations']}
    selections = {r['id']: r for r in selection['results']}
    meta = {r['id']: r for r in json.loads(Path(provenance_path).read_text())['configurations']}
    assert len(learned['results']) == len(configs) and {r['id'] for r in learned['results']} == set(configs)
    count = Counter(); phases = defaultdict(Counter); training_counts = Counter(); witnessed_sources = set()
    pair_contexts = defaultdict(set); max_error = 0.; max_root_mean = 0.; output_rows = []
    for result in learned['results']:
        cid = result['id']; c = configs[cid]; cv = covers[cid]; d = dictionaries[cid]; selection = selections[cid]
        assert result['training'] == d['training']
        training = d['training']; phase = meta[cid]['phase']
        assert training == (meta[cid]['split'] == 'train')
        parts = cv['components']; pairs = cv['componentPairs']; selected = selection['selected']
        assert len(set(selected)) == len(selected)
        atom_totals = [0] * len(c['positions']); adjacency = [[] for _ in parts]
        for edge in selected:
            a, b = pairs[edge]
            assert set(d['occurrences'][edge]['ids']) == set(parts[a] + parts[b])
            assert d['occurrences'][edge]['matched']
            adjacency[a].append((b, edge)); adjacency[b].append((a, edge))
            for atom in parts[a] + parts[b]: atom_totals[atom] += 1
        assert all(t == 2 for t in atom_totals)  # integer verification of t=1/2
        assert all(len(x) == 2 for x in adjacency)
        seen = {0}; todo = [0]
        while todo:
            for other, _ in adjacency[todo.pop()]:
                if other not in seen: seen.add(other); todo.append(other)
        assert len(seen) == len(parts)
        local = []; centers = []; species = []
        for part in parts:
            ids = sorted(part, key=lambda i: (c['species'][i], i))
            p = np.array(c['positions'])[ids]
            dx, _ = find_mic(p - p[0], c['cell'], pbc=True)
            lifted = p[0] + dx; center = lifted.mean(axis=0)
            local.append(lifted - center); centers.append(center); species.append([c['species'][i] for i in ids])
        centers = np.array(centers)
        assert len(result['registrations']) == len(parts)
        assert {r['root'] for r in result['registrations']} == set(range(len(parts)))
        matches = 0
        for r in result['registrations']:
            root = r['root']; neighbors = sorted(adjacency[root], key=lambda be: (species[be[0]], be[0]))
            assert r['edges'] == [e for _, e in neighbors]
            if not r['matched']:
                assert not training
                continue
            matches += 1; ti = r['template']; t = learned['templates'][ti]
            order = [root] + [a for a, _ in neighbors]; groups = [species[a] for a in order]
            assert t['groups'] == groups
            displacement, _ = find_mic(centers[order[1:]] - centers[root], c['cell'], pbc=True)
            y = np.vstack([local[root], *[local[a] + shift for a, shift in zip(order[1:], displacement)]])
            x = np.asarray(t['vectors']); rotation = np.asarray(r['rotationRow']); perm = r['permutation']
            assert sorted(perm) == list(range(len(x))) and len(x) == len(y)
            assert np.isfinite(rotation).all() and np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-8)
            assert abs(np.linalg.det(rotation) - 1) < 1e-8
            offsets = np.cumsum([0] + [len(g) for g in groups]); mapped_groups = []
            for i, group in enumerate(groups):
                target = perm[offsets[i]:offsets[i + 1]]
                candidates = [j for j in range(len(groups)) if set(target) == set(range(offsets[j], offsets[j + 1]))]
                assert len(candidates) == 1
                j = candidates[0]; mapped_groups.append(j)
                assert all(group[k] == groups[j][v - offsets[j]] for k, v in enumerate(target))
            assert mapped_groups[0] == 0 and sorted(mapped_groups) == list(range(len(groups)))
            error = float(np.linalg.norm(x @ rotation - y[perm], axis=1).max())
            assert abs(error - r['residual']) < 1e-8 and error <= learned['epsilonAngstrom'] + 1e-10
            max_error = max(max_error, error); max_root_mean = max(max_root_mean, float(np.linalg.norm(x[:len(groups[0])].mean(axis=0))))
            if training:
                training_counts[ti] += 1
                if error < 1e-8 and np.allclose(x, y, atol=1e-8): witnessed_sources.add(ti)
                for edge in r['edges']: pair_contexts[d['occurrences'][edge]['type']].add(ti)
        assert result['matched'] == matches and result['junctions'] == len(parts)
        prefix = 'training' if training else 'development'
        count[prefix + 'Junctions'] += len(parts); count[prefix + 'Matched'] += matches
        phases[phase][prefix + 'Junctions'] += len(parts); phases[phase][prefix + 'Matched'] += matches
        count[prefix + 'ConfigurationsComplete'] += matches == len(parts)
        output_rows.append({'id': cid, 'training': training, 'junctions': len(parts), 'matched': matches})
    assert witnessed_sources == set(range(len(learned['templates'])))
    assert all(training_counts[i] == t['trainingOccurrences'] for i, t in enumerate(learned['templates']))
    assert max_root_mean < 1e-8
    for key in ['trainingJunctions', 'developmentJunctions', 'developmentMatched', 'developmentConfigurationsComplete']:
        assert count[key] == learned['summary'][key]
    out = {'scope': __doc__, 'learnedHash': hashlib.sha256(learned_raw).hexdigest(),
           'codeHashes': learned['codeHashes'],
           'sourceHashes': learned['sourceHashes'], 'verifiedRegistrations': count['trainingMatched'] + count['developmentMatched'],
           'templatesWithObservedTrainingSource': len(witnessed_sources), 'maxResidualAngstrom': max_error,
           'counts': dict(count), 'byPhase': {p: dict(v) for p, v in phases.items()},
           'basePairTypesObserved': len(pair_contexts), 'basePairTypesWithMultipleJunctionContexts': sum(len(v) > 1 for v in pair_contexts.values()),
           'results': output_rows,
           'limits': 'Selected connected covers and their junction registrations only. No independently held-out cohort, forbidden-connection proof, learned edge-marking search, or growth certification.'}
    with Path(output).open('x') as f: json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != 'results'}), flush=True)


if __name__ == '__main__': run(*sys.argv[1:])
