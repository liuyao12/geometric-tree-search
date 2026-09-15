"""Independent fixed-pool and final-state checks for the portable ice search."""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


verify = module('replay', 'verify-ice-portable.py')
cloud = module('cloud', 'portable-cloud-markings.py')
dictionary_path, cover_path, library_path, model_path, search_folder, kernel_path, output = sys.argv[1:]
sha = verify.sha
d = json.loads(Path(dictionary_path).read_text()); cv = json.loads(Path(cover_path).read_text())
library = json.loads(Path(library_path).read_text()); data = json.loads(Path(model_path).read_text())
summary = json.loads((Path(search_folder) / 'summary.json').read_text())
assert data['portableHash'] == sha(library_path) and summary['modelHash'] == sha(model_path) and summary['kernelHash'] == sha(kernel_path)
assert library['sourceHashes']['dictionary'] == sha(dictionary_path) and library['sourceHashes']['cover'] == sha(cover_path)
assert data['sourceHashes'] == library['sourceHashes']
for name, digest in summary['sourceHashes'].items(): assert sha(Path(__file__).with_name(name)) == digest
ds = {r['id']: r for r in d['configurations']}; covers = {r['id']: r for r in cv['results']}
base_ids = {json.dumps([b['pairType'], b['componentSites']]): i for i, b in enumerate(library['baseMotifs'])}
variants = defaultdict(set)
for i, motif in enumerate(library['motifs']): variants[motif['base']].add(i)
rows = []; checked_candidates = 0
for source in data['models']:
    model = source['model']; cid = source['file']; conf = ds[cid]; cover = covers[cid]
    assert model['required'] == list(map(str, range(conf['atoms']))) and model['capacity'] == 2
    assert model['cloudRadius'] == library['markingRadiusAngstrom']
    by_id = {c['id']: c for c in model['candidates']}; assert len(by_id) == len(model['candidates'])
    expected = set(); actual = set()
    for edge, o in enumerate(conf['occurrences']):
        if not o['matched']: continue
        ep = verify.ends(o, cover['components'], cover['componentPairs'][edge])
        b = base_ids.get(json.dumps([o['type'], [sites for sites, _ in ep]]))
        if b is not None: expected.update((edge, mi) for mi in variants[b])
    for c in model['candidates']:
        edge = int(c['base']); o = conf['occurrences'][edge]; mi = c['registration']['motif']; motif = library['motifs'][mi]
        assert (edge, mi) not in actual; actual.add((edge, mi))
        assert c['t'] == [{'point': str(i), 'value': 1} for i in o['ids']] and c['m'] == []
        assert c['registration']['rotationRow'] == o['rotationRow']
        r = verify.proper(o['rotationRow']); ep = verify.ends(o, cover['components'], cover['componentPairs'][edge])
        assert len(c['cloudM']) == 2
        for side, (_, root) in enumerate(ep):
            assigned = c['cloudM'][side]; value = data['clouds'][assigned['cloud']]; original = motif['cloudM'][side]
            assert assigned['point'] == f'junction:{root}' and value['colors'] == original['colors']
            assert np.max(np.abs(np.asarray(value['vectors']) - np.asarray(original['vectors']) @ r)) < 1e-10
        checked_candidates += 1
    assert actual == expected
    def check_state(selected, enabled, witnesses=None):
        assert len(set(selected)) == len(selected)
        chosen = [by_id[i] for i in selected]; assert len({c['base'] for c in chosen}) == len(chosen)
        totals = {p: 0 for p in model['required']}; marks = defaultdict(list)
        for c in chosen:
            for t in c['t']: totals[t['point']] += t['value']
            for m in c['cloudM']: marks[(m['point'], 'portable')].append(data['clouds'][m['cloud']])
        assert all(0 <= t <= 2 for t in totals.values()); complete = all(t == 2 for t in totals.values())
        if enabled:
            if witnesses is None:
                for values in marks.values(): assert cloud.propose_common_witness(values, model['cloudRadius'])['status'] == 'verified-witness'
            else:
                mapping = {tuple(json.loads(w['point'])): w for w in witnesses}
                assert len(mapping) == len(witnesses) and set(mapping) == set(marks)
                for key, values in marks.items():
                    assert all(cloud.contains(a, mapping[key]['witness'], model['cloudRadius']) is not None for a in values)
        components = None
        if complete:
            adj = [set() for _ in cover['components']]
            for c in chosen:
                a, b = cover['componentPairs'][int(c['base'])]; adj[a].add(b); adj[b].add(a)
            remaining = set(range(len(adj))); components = 0
            while remaining:
                todo = [remaining.pop()]; components += 1
                while todo:
                    for a in adj[todo.pop()] & remaining: remaining.remove(a); todo.append(a)
        return complete, components
    for lift in source['trainingLifts']: assert check_state(lift['selected'], True)[0]
    for enabled in [False, True]:
        raw = json.loads((Path(search_folder) / f"{source['fold']}-{str(enabled).lower()}.json").read_text())
        assert raw['modelHash'] == summary['modelHash'] and raw['kernelHash'] == summary['kernelHash'] and raw['sourceHashes'] == summary['sourceHashes']
        r = raw['result']; complete, components = check_state(r['selected'], enabled, raw['commonWitnesses'])
        assert complete == r['scalarComplete']
        reported = next(x for x in summary['results'] if x['fold'] == source['fold'] and x['enabled'] == enabled)
        assert reported == dict(r, selected=len(r['selected']))
        assert r['rootRollback'] and r['enabled'] == enabled
        if r['status'] == 'verified finite registered filling': assert complete
        rows.append({'id': cid, 'enabled': enabled, 'status': r['status'], 'selected': len(r['selected']),
                     'complete': complete, 'positiveSupportComponents': components, 'verifiedCommonValues': len(raw['commonWitnesses'])})
out = {'scope': __doc__, 'modelHash': sha(model_path), 'portableHash': sha(library_path), 'kernelHash': sha(kernel_path),
       'registeredCandidatesChecked': checked_candidates, 'results': rows,
       'limits': 'Fixed registered candidate pool only. Cloud witness membership checked with separate Python implementation; runtime graph/scheduler/rollback audits are recorded by the unchanged JS harness. No independent continuous-pose completeness or connected-growth claim.'}
with Path(output).open('x') as f: json.dump(out, f, indent=2)
print(json.dumps(out), flush=True)
