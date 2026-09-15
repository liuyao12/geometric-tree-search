"""Offer all learned decorations at every matching fixed registered base pose.

No target junction clouds or selected-cover membership filter the candidate pool.
Training cover IDs are attached after pool construction for verification only.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

spec = importlib.util.spec_from_file_location('portable', Path(__file__).with_name('ice-portable-pairs.py'))
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
dictionary_path, cover_path, portable_path, ids_string, output = sys.argv[1:]
raw = [Path(x).read_bytes() for x in [dictionary_path, cover_path, portable_path]]
dictionary, cover, library = map(json.loads, raw)
assert library['sourceHashes']['dictionary'] == hashlib.sha256(raw[0]).hexdigest()
assert library['sourceHashes']['cover'] == hashlib.sha256(raw[1]).hexdigest()
base_ids = {json.dumps([b['pairType'], b['componentSites']]): i for i, b in enumerate(library['baseMotifs'])}
variants = defaultdict(list)
for i, motif in enumerate(library['motifs']): variants[motif['base']].append(i)
cv_by = {r['id']: r for r in cover['results']}; d_by = {r['id']: r for r in dictionary['configurations']}
training = {r['id']: r for r in library['trainingRegistrations']}
clouds = []; cache = {}; models = []
def intern(value):
    key = json.dumps(value, sort_keys=True)
    if key not in cache: cache[key] = len(clouds); clouds.append(value)
    return cache[key]
for fold, cid in enumerate(ids_string.split(',')):
    d = d_by[cid]; cv = cv_by[cid]; candidates = []; lookup = {}; represented = set()
    for edge, o in enumerate(d['occurrences']):
        if not o['matched']: continue
        ends = p.endpoints(o, cv['components'], cv['componentPairs'][edge])
        bid = base_ids.get(p.base_key(o, ends))
        if bid is None: continue
        for mi in variants[bid]:
            motif = library['motifs'][mi]; key = str(len(candidates)).zfill(8)
            cm = [{'point': f'junction:{root}', 'cloud': intern(p.cloud.transform(mark, o['rotationRow']))}
                  for mark, (_, root) in zip(motif['cloudM'], ends)]
            candidates.append({'id': key, 'base': str(edge), 't': [{'point': str(i), 'value': 1} for i in o['ids']],
                               'm': [], 'cloudM': cm, 'registration': {'motif': mi, 'rotationRow': o['rotationRow']}})
            lookup[edge, mi] = key; represented.add(edge)
    # Pool is frozen before reading the training selection here.
    lifts = []
    if cid in training:
        lifts = [{'name': 'original', 'selected': [lookup[r['edge'], r['motif']] for r in training[cid]['selected']]}]
    model = {'capacity': 2, 'required': list(map(str, range(d['atoms']))),
             'cloudRadius': library['markingRadiusAngstrom'], 'candidates': candidates}
    models.append({'fold': fold, 'file': cid, 'model': model, 'trainingLifts': lifts,
                   'representedBasePlacements': len(represented), 'observedProposals': len(d['occurrences'])})
    print(json.dumps({'id': cid, 'variants': len(candidates), 'basePlacements': len(represented)}), flush=True)
out = {'scope': __doc__, 'portableHash': hashlib.sha256(raw[2]).hexdigest(),
       'sourceHashes': library['sourceHashes'], 'codeHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'clouds': clouds, 'models': models,
       'limits': 'Finite first-registered-pose universe with all matching learned decorations. No continuous-pose completeness, blind growth, same-condition validation or supplied-answer search. Undecorated bypasses are not included.'}
with Path(output).open('x') as f: json.dump(out, f)
