"""Two-ended ice motif markings transported by one shared proper tile rotation.

Export training-observed decoration pairs on shared six-site geometry. This
preserves their coupling rather than taking an arbitrary Cartesian product of
endpoint contexts. Coordinate-derived values have no target/configuration IDs.
Provenance and training registrations are separate from the motif values.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


junction = module('junction', 'ice-junction-clouds.py')
cloud = module('cloud', 'portable-cloud-markings.py')


def cloud_value(q):
    return {'vectors': q['vectors'], 'colors': [[int(i != 0), label] for i, group in enumerate(q['groups']) for label in group]}


def endpoints(occurrence, parts, pair):
    atom_of_site = [occurrence['ids'][p] for p in occurrence['permutation']]
    rows = [(sorted(i for i, atom in enumerate(atom_of_site) if atom in parts[root]), root) for root in pair]
    rows.sort()
    assert sorted(i for sites, _ in rows for i in sites) == list(range(len(atom_of_site)))
    assert all(sites for sites, _ in rows)
    return rows


def base_key(occurrence, ends):
    return json.dumps([occurrence['type'], [sites for sites, _ in ends]])


def run(coordinates, cover_path, dictionary_path, selection_path, junction_path, output):
    paths = [coordinates, cover_path, dictionary_path, selection_path]
    raw = [Path(p).read_bytes() for p in paths]
    corpus, cover, dictionary, selection = map(json.loads, raw)
    jr = Path(junction_path).read_bytes(); learned = json.loads(jr)
    for k, r in zip(['coordinates', 'cover', 'dictionary', 'selection'], raw):
        assert learned['sourceHashes'][k] == hashlib.sha256(r).hexdigest()
    assert learned['epsilonAngstrom'] == dictionary['epsilonAngstrom']
    cover_by = {r['id']: r for r in cover['results']}
    dictionary_by = {r['id']: r for r in dictionary['configurations']}
    selection_by = {r['id']: r for r in selection['results']}
    junction_by = {r['id']: r for r in learned['results']}
    bases = []; motifs = []; registrations = []; base_ids = {}; intern = {}; witnesses = 0
    for c in corpus['configurations']:
        d = dictionary_by[c['id']]
        if not d['training']: continue
        cv = cover_by[c['id']]; selected = selection_by[c['id']]['selected']
        roots = {r['root']: r for r in junction_by[c['id']]['registrations']}
        queries = {q['root']: q for q in junction.junctions(c, cv, selected)}
        values = {}
        for root, r in roots.items():
            assert r['matched']
            prototype = learned['templates'][r['template']]
            values[root] = cloud.transform(cloud_value(prototype), r['rotationRow'])
            assert cloud.contains(values[root], cloud_value(queries[root]), learned['epsilonAngstrom']) is not None
            witnesses += 1
        rr = []
        for edge in selected:
            o = d['occurrences'][edge]; assert o['matched']
            ends = endpoints(o, cv['components'], cv['componentPairs'][edge]); key = base_key(o, ends)
            if key not in base_ids:
                base_ids[key] = len(bases); positions = dictionary['types'][o['type']]['positions']
                bases.append({'pairType': o['type'], 'anchors': positions, 'species': dictionary['types'][o['type']]['species'],
                              't': [1] * len(positions), 'componentSites': [sites for sites, _ in ends],
                              'markAnchors': [np.asarray(positions)[sites].mean(axis=0).tolist() for sites, _ in ends]})
            rotation = np.asarray(o['rotationRow'])
            value = {'base': base_ids[key], 'cloudM': [cloud.transform(values[root], rotation.T) for _, root in ends]}
            # Exact-value deduplication only. Near clouds must not silently merge.
            serial = json.dumps(value, sort_keys=True)
            if serial not in intern:
                intern[serial] = len(motifs); motifs.append(value)
            rr.append({'edge': edge, 'motif': intern[serial], 'roots': [root for _, root in ends]})
        registrations.append({'id': c['id'], 'selected': rr})
    result = {'scope': __doc__, 'sourceHashes': learned['sourceHashes'], 'junctionHash': hashlib.sha256(jr).hexdigest(),
              'codeHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'capacity': 2,
              'positionToleranceAngstrom': dictionary['epsilonAngstrom'], 'markingRadiusAngstrom': learned['epsilonAngstrom'],
              'baseMotifs': bases, 'motifs': motifs, 'trainingRegistrations': registrations,
              'summary': {'sharedBaseMotifs': len(bases), 'decoratedMotifs': len(motifs), 'trainingConfigurations': len(registrations), 'trainingJunctionWitnesses': witnesses},
              'semantics': 'Integer t units of capacity 2. Mark-only anchors are component centroids. Cloud m is a set under species/role-preserving bijections at the declared radius. One proper rotation acts on both endpoint clouds and all anchors; translations act on anchors only. Registration snaps anchors to supplied atom/centroid identities within the position tolerance.',
              'limits': 'An empirical decoration library, not a compression result or a complete continuous pose universe. Uniform-half t is inherited from the previous restricted decomposition, not relearned here. Context pairing is training-observed, not a proof excluding unseen pairs. Configuration IDs occur in provenance only.'}
    with Path(output).open('x') as f: json.dump(result, f)
    print(json.dumps(result['summary']), flush=True)


if __name__ == '__main__': run(*sys.argv[1:])
